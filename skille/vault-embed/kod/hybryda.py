#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vault-embed: druga warstwa nad BM25, czyli lokalny embedding i hybryda.

Warunek twardy: WSZYSTKO lokalnie. Model chodzi na CPU przez onnxruntime, indeks siedzi
w SQLite obok vaultu. Zadna tresc notatki nie opuszcza maszyny, bo w tym pliku nie ma ani
jednego wywolania sieciowego (pobranie modelu to osobny, jednorazowy krok: pobierz_model.py).

Warstwy:
  bm25        : bm25_pl.py (stemming PL, wagi folderów, kwarantanna i kopie poza indeksem)
  wektor      : multilingual-e5-base (domyślnie), mean pooling + L2, cosinus
  hybryda     : router po długości zapytania (krótkie do BM25, opisowe do wektora)
  hybryda-rrf : stara fuzja RRF, zostawiona na wypadek słabszego modelu

Gdzie leżą dane (model i indeks): poza vaultem i poza folderem skilla, w katalogu danych
kitu (domyślnie ~/.cache/second-brain-kit, zmiana przez KIT_DANE albo klucz
`wyszukiwanie.katalog_danych` w .kit/konfiguracja.json). Powód: model waży ok. 1,1 GB i nie
może jechać przez iCloud razem z vaultem, a folder skilla podmienia każda aktualizacja.
Indeks ma osobny plik na każdy vault, więc dwa vaulty się nie mieszają.

Dlaczego RRF (tryb hybryda-rrf), a nie ważona suma score:
BM25 zwraca wartosci nieograniczone (tu 5 do 40), cosinus siedzi w [-1,1]. Zeby je zsumowac,
trzeba by kalibrowac skale per zapytanie, a to kolejny parametr do zestrojenia i kolejne
miejsce na cichy blad. RRF patrzy tylko na POZYCJE, wiec jest odporny na skale obu silnikow.

Uzycie:
    python3 hybryda.py "pytanie"  [--tryb bm25|wektor|hybryda|hybryda-rrf] [--top 8] [--folder PODFOLDER]
    python3 hybryda.py --buduj          # przebuduj indeks (inkrementalnie po mtime+rozmiarze)
    python3 hybryda.py --buduj --od-zera
    python3 hybryda.py --sprawdz        # kod wyjścia 1, gdy indeks jest w tyle za vaultem
"""
import os, re, sys, json, math, time, sqlite3, argparse, hashlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bm25_pl
import kit_konfig


def katalog_danych(vault=None):
    """KIT_DANE, potem klucz z konfiguracji vaultu, potem ~/.cache/second-brain-kit."""
    env = os.environ.get("KIT_DANE")
    if env:
        return os.path.expanduser(env)
    z_konf = kit_konfig.wartosc(kit_konfig.wczytaj(vault), "wyszukiwanie.katalog_danych")
    return os.path.expanduser(z_konf or "~/.cache/second-brain-kit")


def domyslny_model(vault=None):
    """fp32 (domyślne pobranie), a gdy go nie ma, wersja int8."""
    folder = os.path.join(katalog_danych(vault), "model")
    fp32 = os.path.join(folder, "model_fp32.onnx")
    return fp32 if os.path.exists(fp32) else os.path.join(folder, "model_quantized.onnx")


def domyslna_baza(vault):
    """Osobny indeks na każdy vault: nazwa z hasha ścieżki."""
    klucz = hashlib.sha1(os.path.abspath(vault).encode("utf-8")).hexdigest()[:10]
    return os.path.join(katalog_danych(vault), "indeksy", "indeks-%s.sqlite" % klucz)


DOMYSLNY_MODEL = None
DOMYSLNA_BAZA = None

MAX_TOKENOW = 512          # limit pozycyjny modelu
SLOW_NA_OKNO = 260         # ok. 420 tokenow dla polszczyzny (ok. 1,6 tokena na slowo)
ZAKLADKA_SLOW = 40         # zakladka miedzy oknami, zeby zdanie na styku nie przepadlo
WYMIAR_DOMYSLNY = 384       # fallback, gdy przy modelu brak config.json z hidden_size
RRF_K = 60                 # stala tlumiaca RRF; 60 to wartosc z oryginalnej pracy Cormacka

# Fuzja RRF ze stalymi wagami (WAGA_BM25_RRF:WAGA_WEKTOR_RRF) zostaje dostepna pod trybem
# "hybryda-rrf" (uzywa jej tez strojenie.py). Historia decyzji, zeby nikt nie probowal tego
# samego pomyslu drugi raz:
#
#   1. Pomiar 26.08 (e5-small): plaska fuzja RRF 1:1 WYGRYWA z kazdym pojedynczym silnikiem
#      (MRR 0,786 vs wektor 0,698 vs BM25 0,604), bo wektor e5-small jest za slaby, zeby mu
#      ufac samodzielnie na dlugich zapytaniach opisowych, a BM25 go tam dociaga.
#   2. 16.09: test podmiany na e5-base (wiekszy model). Sam wektor e5-base bije WSZYSTKO,
#      lacznie z dzisiejsza produkcja (MRR wektor 0,822 vs produkcyjne RRF 0,786). Ale RRF
#      z e5-base w srodku wypada GORZEJ niz dzis (0,669 przy 1:1, najlepsze z 9 przetestowanych
#      wag 0,716) - RRF rozwadnia mocny top1 wektora slabszym rankiem BM25.
#   3. 17.09: proba "mocniejszej" fuzji - wagi RRF zalezne od dlugosci zapytania (krotkie
#      ufa BM25, dlugie ufa wektorowi). WYNIK: gorzej niz plaska fuzja 1:1 na OBU modelach
#      (e5-small MRR 0,786->0,747, e5-base MRR 0,669->0,635, krotkie zargonowe zapytania
#      psuja sie z 5/5 do 3/5 trafien). Kazda proba wazenia dwoch rankingow w jeden score
#      psuje to, co pojedynczy silnik robi dobrze, niezaleznie od wag.
#   4. 17.09: ROUTING zamiast mieszania (ponizej, wagi_adaptacyjne usuniete). Dla e5-base:
#      main MRR 0,822 (najlepszy wynik calego pomiaru, jak czysty wektor) + krotkie zargonowe
#      5/5 w top3 zero pudel (jak stara produkcja). Dla e5-small router wypada gorzej na
#      dlugich zapytaniach niz stara plaska fuzja (0,698 vs 0,786) - bo jego wektor jest za
#      slaby, zeby mu ufac w 100%. Wniosek: router pasuje do e5-base, nie jest uniwersalna
#      poprawka fuzji dla kazdego modelu z osobna - dlatego idzie w parze z podmiana modelu,
#      nie zamiast niej. Liczby: Narzedzia/vault-embed - wybor modelu embeddingu.md w vaulcie.
WAGA_BM25_RRF = 1.0
WAGA_WEKTOR_RRF = 1.0

# Prog routingu: zapytanie do PROG_ROUTER_SLOW slow wlacznie idzie w calosci do BM25 (nazwy
# wlasne, kody zadan typu VAN-146, pojedyncze terminy), dluzsze w calosci do wektora. Zero
# mieszania miedzy nimi, bo pomiar (patrz wyzej, punkt 3) pokazal, ze mieszanie tylko szkodzi.
PROG_ROUTER_SLOW = 2

# Maksymalna liczba sekcji z JEDNEGO pliku w wynikach. Pomiar 2026-08-26: na haslo "skill"
# caly top3 warstwy wektorowej to byly trzy sekcje tego samego pliku "SKILL (szkielet).md".
# Wyszukiwarka ma dac Claude'owi rozne zrodla do zacytowania, a nie trzy razy to samo.
MAX_SEKCJI_NA_PLIK = 2

# Powyzej tylu zmienionych plikow zapytanie NIE liczy embeddingow w locie, tylko ostrzega
# i szuka na tym, co jest. Naprawa bledu zmierzonego 02.09: po reorganizacji vaultu (98
# plikow, 27% vaultu) pierwsze zapytanie blokowalo sie na 197 s. --buduj (wymuszony=True)
# ignoruje ten limit, bo tam liczenie w tle jest wlasnie po to.
LIMIT_PLIKOW = 15


# ---------------------------------------------------------------- model lokalny

class Osadzacz:
    """multilingual-e5 (base albo small) przez onnxruntime. Tylko CPU, tylko lokalnie."""

    def __init__(self, model=DOMYSLNY_MODEL, tokenizer=None, watki=None):
        model = model or domyslny_model()
        import onnxruntime as ort
        from tokenizers import Tokenizer
        # Tokenizer nalezy DO modelu, wiec szukamy go obok modelu, a nie obok skryptu.
        # Inaczej po skopiowaniu skryptu w inne miejsce (albo na Maca) sciezka wskazuje
        # w prozne i leci "System nie moze odnalezc okreslonej sciezki (os error 3)".
        if tokenizer is None:
            obok_modelu = os.path.join(os.path.dirname(os.path.abspath(model)), "tokenizer.json")
            tokenizer = obok_modelu
        if not os.path.isfile(tokenizer):
            raise SystemExit("BLAD: brak tokenizera: %s (ma lezec w tym samym folderze "
                             "co model)" % tokenizer)
        if not os.path.isfile(model):
            raise SystemExit("BLAD: brak modelu: %s\nUruchom najpierw: python3 pobierz_model.py" % model)
        opcje = ort.SessionOptions()
        if watki:
            opcje.intra_op_num_threads = watki
        self.sesja = ort.InferenceSession(model, opcje, providers=["CPUExecutionProvider"])
        self.tok = Tokenizer.from_file(tokenizer)
        self.tok.enable_truncation(max_length=MAX_TOKENOW)
        self.wejscia = {i.name for i in self.sesja.get_inputs()}
        # Wymiar wektora NIE jest stala globalna: rozne modele (e5-small=384, e5-base=768)
        # maja rozny hidden_size, wiec czytamy go z config.json obok modelu zamiast zaszywac
        # na sztywno. Bez tego podmiana modelu psulaby odczyt starych wektorow z SQLite
        # (frombuffer.reshape z zla liczba kolumn) w milczacy, myslacy sposob.
        config = os.path.join(os.path.dirname(os.path.abspath(model)), "config.json")
        try:
            self.wymiar = int(json.load(open(config, encoding="utf-8"))["hidden_size"])
        except Exception:
            self.wymiar = WYMIAR_DOMYSLNY

    def _partia(self, teksty):
        enc = [self.tok.encode(t) for t in teksty]
        dlug = max(len(e.ids) for e in enc)
        n = len(enc)
        ids = np.zeros((n, dlug), dtype=np.int64)
        maska = np.zeros((n, dlug), dtype=np.int64)
        for i, e in enumerate(enc):
            ids[i, :len(e.ids)] = e.ids
            maska[i, :len(e.attention_mask)] = e.attention_mask
        karma = {"input_ids": ids, "attention_mask": maska}
        if "token_type_ids" in self.wejscia:
            karma["token_type_ids"] = np.zeros_like(ids)
        wyj = self.sesja.run(None, karma)[0]          # (n, dlug, 384)
        # mean pooling po masce uwagi, bo padding nie moze wejsc do sredniej
        m = maska[:, :, None].astype(np.float32)
        wek = (wyj * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
        # L2: po normalizacji iloczyn skalarny JEST cosinusem
        wek /= np.clip(np.linalg.norm(wek, axis=1, keepdims=True), 1e-9, None)
        return wek.astype(np.float32)

    def koduj(self, teksty, prefiks, partia=16, postep=None):
        """prefiks: 'query: ' albo 'passage: '. e5 jest trenowany asymetrycznie
        i BEZ tych prefiksow jakosc wyraznie spada. To nie ozdobnik."""
        teksty = [prefiks + t for t in teksty]
        # sortowanie po dlugosci: krotkie teksty nie czekaja na padding do najdluzszego
        kolejnosc = sorted(range(len(teksty)), key=lambda i: len(teksty[i]))
        out = np.zeros((len(teksty), self.wymiar), dtype=np.float32)
        for start in range(0, len(kolejnosc), partia):
            idx = kolejnosc[start:start + partia]
            out[idx] = self._partia([teksty[i] for i in idx])
            if postep:
                postep(min(start + partia, len(kolejnosc)), len(kolejnosc))
        return out


def okna(tekst, slow=SLOW_NA_OKNO, zakladka=ZAKLADKA_SLOW):
    """Dzieli dlugi tekst na okna slow z zakladka. Sekcja ma tu do 3035 tokenow (pomiar
    2026-08-26), a model widzi 512, wiec bez podzialu koncowka dlugiej sekcji w ogole nie
    istnieje dla wyszukiwarki. Kazde okno dostaje wlasny wektor, przy szukaniu bierzemy
    maksimum po oknach."""
    slowa = tekst.split()
    if len(slowa) <= slow:
        return [tekst]
    krok = slow - zakladka
    return [" ".join(slowa[i:i + slow]) for i in range(0, len(slowa), krok)
            if slowa[i:i + slow]]


# ---------------------------------------------------------------- indeks SQLite

SCHEMA = """
CREATE TABLE IF NOT EXISTS pliki (
    rel TEXT PRIMARY KEY, mtime REAL, rozmiar INTEGER, odcisk TEXT);
CREATE TABLE IF NOT EXISTS chunki (
    id INTEGER PRIMARY KEY, rel TEXT, naglowek TEXT, tresc TEXT, waga REAL);
CREATE TABLE IF NOT EXISTS wektory (
    chunk_id INTEGER, okno INTEGER, wek BLOB);
CREATE INDEX IF NOT EXISTS i_chunki_rel ON chunki(rel);
CREATE INDEX IF NOT EXISTS i_wektory_chunk ON wektory(chunk_id);
CREATE TABLE IF NOT EXISTS meta (klucz TEXT PRIMARY KEY, wartosc TEXT);
"""


def _w_folderze(rel, folder):
    """Czy notatka leży w podfolderze `folder` (argument --folder)."""
    return rel.lower().startswith(folder.lower().rstrip("/") + os.sep)


class Indeks:
    def __init__(self, vault=None, baza=DOMYSLNA_BAZA, model=DOMYSLNY_MODEL, cicho=False):
        self.vault = os.path.abspath(vault or bm25_pl.find_vault())
        bm25_pl.zastosuj_konfiguracje(self.vault)
        baza = baza or domyslna_baza(self.vault)
        model = model or domyslny_model(self.vault)
        self.sciezka_bazy = baza
        self.model = model
        self.cicho = cicho
        os.makedirs(os.path.dirname(baza), exist_ok=True)
        self.db = sqlite3.connect(baza)
        self.db.executescript(SCHEMA)
        self._osadzacz = None
        self._chunki_cache = None
        self._lista_cache = None
        self._wek = None          # (M, 384) macierz wszystkich okien
        self._wek_chunk = None    # (M,) chunk_id dla kazdego okna

    def _log(self, s):
        if not self.cicho:
            print(s, file=sys.stderr, flush=True)

    def osadzacz(self):
        if self._osadzacz is None:
            self._osadzacz = Osadzacz(self.model)
        return self._osadzacz

    # ---------- budowa

    def _stan_plikow(self):
        stan = {}
        for root, dirs, files in os.walk(self.vault):
            dirs[:] = [d for d in dirs if d not in bm25_pl.SKIP_DIRS]
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, self.vault)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                stan[rel] = (st.st_mtime, st.st_size)
        return stan

    def _do_przeliczenia(self):
        """Zwraca (zmienione, usuniete) wzgledem stanu zapisanego w bazie, bez zadnych
        skutkow ubocznych. Uzywane zarowno przez buduj(), jak i sprawdz()/--sprawdz,
        zeby obie sciezki liczyly to samo w ten sam sposob."""
        stan = self._stan_plikow()
        stary = {r: (m, s) for r, m, s in
                 self.db.execute("SELECT rel, mtime, rozmiar FROM pliki")}
        zmienione = [r for r, v in stan.items() if stary.get(r) != v]
        usuniete = [r for r in stary if r not in stan]
        return stan, zmienione, usuniete

    def sprawdz(self):
        """Liczy pliki do przeliczenia bez dotykania indeksu. Zwraca ich liczbe."""
        _, zmienione, usuniete = self._do_przeliczenia()
        n = len(zmienione) + len(usuniete)
        print(n)
        return n

    def buduj(self, od_zera=False, wymuszony=False, limit_plikow=LIMIT_PLIKOW):
        t0 = time.time()
        if od_zera:
            self.db.executescript("DELETE FROM pliki; DELETE FROM chunki; DELETE FROM wektory;")
            self.db.commit()

        stan, zmienione, usuniete = self._do_przeliczenia()

        if not zmienione and not usuniete:
            self._log("Indeks aktualny (%d plikow, bez zmian)." % len(stan))
            return

        if len(zmienione) > limit_plikow and not wymuszony:
            # Nic nie ruszamy: zadnego kasowania bez natychmiastowego zastapienia. Zapytanie
            # szuka na tym, co jest w bazie (nieswiezym o te pliki), zamiast blokowac sie
            # na liczeniu embeddingow w locie (zmierzone 02.09: 197 s na 98 plikow).
            self._log("UWAGA: indeks nieswiezy o %d plikow, uruchom --buduj. "
                      "Szukam na tym, co jest." % len(zmienione))
            return

        self._log("Do przeliczenia: %d plikow, do usuniecia: %d." % (len(zmienione), len(usuniete)))

        try:
            for rel in list(zmienione) + usuniete:
                ids = [i for (i,) in self.db.execute("SELECT id FROM chunki WHERE rel=?", (rel,))]
                if ids:
                    q = ",".join("?" * len(ids))
                    self.db.execute("DELETE FROM wektory WHERE chunk_id IN (%s)" % q, ids)
                    self.db.execute("DELETE FROM chunki WHERE rel=?", (rel,))
                self.db.execute("DELETE FROM pliki WHERE rel=?", (rel,))
            # Kasowanie NIE jest tu commitowane osobno (bug sprzed 02.09): jedna transakcja
            # od kasowania do wstawienia nowych wektorow i wpisow w pliki, commit dopiero
            # na koncu. Przerwany bieg cofa sie w calosci (rollback nizej), zamiast zostawiac
            # pliki bez wektorow, o czym nic by nie mowilo.

            # chunkujemy DOKLADNIE tak jak BM25, bo jedna definicja chunka dla obu warstw:
            # inaczej fuzja laczylaby dwa rozne swiaty i wynik bylby nieporownywalny
            do_osadzenia, meta = [], []
            for rel in zmienione:
                full = os.path.join(self.vault, rel)
                try:
                    txt = open(full, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                meta_fm = bm25_pl.pola_frontmattera(txt)
                if meta_fm.get("status") == "obalone":
                    # Ustalenie odwolane, poza indeksem wektorowym tak samo jak w BM25 (etap C,
                    # scalone 27.08). Stare chunki/wektory tego pliku juz usuniete wyzej w tej
                    # metodzie (petla po zmienione+usuniete), po prostu nic nowego nie wstawiamy.
                    continue
                nazwa = os.path.basename(rel)[:-3]
                waga = bm25_pl.waga_notatki(rel, meta_fm)
                for head, body in bm25_pl.split_sections(txt, full):
                    body = body.strip()
                    if not body:
                        continue
                    cur = self.db.execute(
                        "INSERT INTO chunki(rel,naglowek,tresc,waga) VALUES(?,?,?,?)",
                        (rel, head, body, waga))
                    cid = cur.lastrowid
                    # nazwa pliku i naglowek ida DO tekstu osadzanego, bo bez nich sekcja
                    # w rodzaju "## Uwagi" nie niesie zadnego tematu
                    kontekst = "%s: %s\n" % (nazwa, head)
                    for i, okno in enumerate(okna(body)):
                        do_osadzenia.append(kontekst + okno)
                        meta.append((cid, i))

            if do_osadzenia:
                self._log("Osadzanie %d okien..." % len(do_osadzenia))
                os_ = self.osadzacz()
                ostatni = [0]

                def postep(zrobione, ile):
                    if zrobione - ostatni[0] >= 500 or zrobione == ile:
                        ostatni[0] = zrobione
                        minelo = time.time() - t0
                        self._log("  %d/%d  (%.0f okien/s)" % (zrobione, ile, zrobione / max(minelo, 0.01)))

                wek = os_.koduj(do_osadzenia, "passage: ", postep=postep)
                self.db.executemany(
                    "INSERT INTO wektory(chunk_id,okno,wek) VALUES(?,?,?)",
                    [(m[0], m[1], w.tobytes()) for m, w in zip(meta, wek)])

            for rel in zmienione:
                m, s = stan[rel]
                self.db.execute("INSERT OR REPLACE INTO pliki(rel,mtime,rozmiar,odcisk) "
                                "VALUES(?,?,?,?)", (rel, m, s, ""))
            self.db.execute("INSERT OR REPLACE INTO meta(klucz,wartosc) VALUES('model',?)",
                            (os.path.basename(self.model),))
            self.db.commit()
        except BaseException:
            # BaseException, nie Exception: SIGTERM/Ctrl-C podczas dlugiego liczenia
            # embeddingow (test atomowosci: kill w trakcie --buduj) ma tak samo cofnac
            # transakcje, a nie zostawic baze w polowie zmiany.
            self.db.rollback()
            raise
        self._log("Gotowe w %.1fs." % (time.time() - t0))

    # ---------- odczyt

    def _wczytaj_wektory(self):
        if self._wek is not None:
            return
        wiersze = self.db.execute("SELECT chunk_id, wek FROM wektory").fetchall()
        if not wiersze:
            raise SystemExit("BLAD: indeks wektorowy pusty. Uruchom: py hybryda.py --buduj")
        wymiar = self.osadzacz().wymiar
        self._wek = np.frombuffer(b"".join(w for _, w in wiersze),
                                  dtype=np.float32).reshape(len(wiersze), wymiar)
        self._wek_chunk = np.array([c for c, _ in wiersze], dtype=np.int64)

    def _chunki(self):
        """Metadane chunkow z BAZY (nie z dysku), zeby numeracja zgadzala sie z wektorami."""
        if self._chunki_cache is None:
            self._chunki_cache = {}
            for cid, rel, head, tresc, waga in self.db.execute(
                    "SELECT id, rel, naglowek, tresc, waga FROM chunki"):
                self._chunki_cache[cid] = {"rel": rel, "head": head,
                                           "body": tresc, "waga": waga}
        return self._chunki_cache

    def _kolumna_tokenow(self):
        """Dokłada kolumne chunki.tokeny, jesli baza jest ze starszej wersji."""
        kolumny = {w[1] for w in self.db.execute("PRAGMA table_info(chunki)")}
        if "tokeny" not in kolumny:
            self.db.execute("ALTER TABLE chunki ADD COLUMN tokeny TEXT")
            self.db.commit()

    def _lista_bm25(self, module=None):
        """Chunki w formacie, ktorego oczekuje bm25_pl.bm25_rank.

        Rdzenie BM25 sa trzymane w bazie, a nie liczone przy kazdym starcie. Pomiar
        2026-08-26: stemming 9,5 tys. sekcji w locie kosztowal 7,0 s przy KAZDYM
        uruchomieniu CLI, a to narzedzie wola sie po kilka razy w sesji. Zapis do kolumny
        chunki.tokeny schodzi do ok. 1 s. Uniewaznienie jest darmowe: przy zmianie pliku
        jego wiersze w chunki i tak sa kasowane i wstawiane od nowa, wiec nieaktualny
        cache nie ma jak powstac."""
        if self._lista_cache is None:
            self._kolumna_tokenow()
            ch = self._chunki()
            zapisane = dict(self.db.execute("SELECT id, tokeny FROM chunki"))
            lista, do_zapisu = [], []
            for i in sorted(ch):
                c = ch[i]
                nazwa = os.path.basename(c["rel"])[:-3]
                surowe = zapisane.get(i)
                if surowe:
                    toks = surowe.split(" ")
                else:
                    toks = bm25_pl.tokenize_z_prefiksami(c["head"] + " " + c["body"])
                    do_zapisu.append((" ".join(toks), i))
                lista.append({
                    "rel": c["rel"], "head": c["head"], "body": c["body"],
                    "toks": toks,
                    "kluczowe": set(bm25_pl.tokenize_z_prefiksami(c["head"] + " " + nazwa)),
                    "waga": c["waga"], "_id": i,
                })
            if do_zapisu:
                self.db.executemany("UPDATE chunki SET tokeny=? WHERE id=?", do_zapisu)
                self.db.commit()
            self._lista_cache = lista
        if not module:
            return self._lista_cache
        return [c for c in self._lista_cache if _w_folderze(c["rel"], module)]

    def _bm25(self, query, module=None):
        lista = self._lista_bm25(module)
        return [(lista[i]["_id"], s) for s, i in bm25_pl.bm25_rank(lista, query)]

    def _wektor(self, query, module=None):
        self._wczytaj_wektory()
        ch = self._chunki()
        q = self.osadzacz().koduj([query], "query: ")[0]
        sim = self._wek @ q                       # cosinus, bo wszystko znormalizowane
        # okna tego samego chunka: bierzemy najlepsze, nie srednia, bo jedno trafne okno
        # w dlugiej sekcji ma wygrac, a srednia by je rozmyla
        najlepsze = {}
        for cid, s in zip(self._wek_chunk.tolist(), sim.tolist()):
            if s > najlepsze.get(cid, -2.0):
                najlepsze[cid] = s
        wynik = []
        for cid, s in najlepsze.items():
            c = ch.get(cid)
            if not c:
                continue
            if module and not _w_folderze(c["rel"], module):
                continue
            wynik.append((cid, s * c["waga"]))
        wynik.sort(key=lambda x: -x[1])
        return wynik

    def _rozroznij(self, pary, top, limit):
        """Przycina liste tak, zeby jeden plik nie zjadl calego topu. Kolejnosc zachowana:
        nadmiarowe sekcje tego samego pliku ida na koniec, a nie do kosza, bo przy bardzo
        waskim zapytaniu moze nie byc czym ich zastapic."""
        if not limit:
            return pary[:top]
        ch = self._chunki()
        licznik, glowne, reszta = {}, [], []
        for cid, s in pary:
            rel = ch[cid]["rel"]
            licznik[rel] = licznik.get(rel, 0) + 1
            (glowne if licznik[rel] <= limit else reszta).append((cid, s))
            if len(glowne) >= top:
                break
        return (glowne + reszta)[:top]

    def szukaj(self, query, top=8, tryb="hybryda", module=None,
               w_bm25=WAGA_BM25_RRF, w_wek=WAGA_WEKTOR_RRF, limit_pliku=MAX_SEKCJI_NA_PLIK):
        ch = self._chunki()
        zapas = max(top * 5, 50)
        if tryb == "bm25":
            pary = self._rozroznij(self._bm25(query, module)[:zapas], top, limit_pliku)
        elif tryb == "wektor":
            pary = self._rozroznij(self._wektor(query, module)[:zapas], top, limit_pliku)
        elif tryb == "hybryda":
            # Router, nie fuzja: cale zapytanie idzie do jednego silnika, wybranego po
            # dlugosci (patrz uzasadnienie i pomiar w komentarzu przy PROG_ROUTER_SLOW).
            # Zero mieszania rankingow, bo kazda przetestowana forma mieszania wypadala
            # gorzej niz pojedynczy silnik osobno.
            wewn = "bm25" if len(query.split()) <= PROG_ROUTER_SLOW else "wektor"
            zrodlo = self._bm25(query, module) if wewn == "bm25" else self._wektor(query, module)
            pary = self._rozroznij(zrodlo[:zapas], top, limit_pliku)
        else:
            # hybryda-rrf: stara fuzja wazona, do dalszego strojenia (patrz strojenie.py)
            # albo dla modelu, gdzie router nie wygrywa (np. e5-small, patrz komentarz wyzej).
            b = self._bm25(query, module)[:100]
            w = self._wektor(query, module)[:100]
            # RRF: liczy sie POZYCJA na liscie, nie surowy score
            punkty = {}
            for r, (cid, _) in enumerate(b, 1):
                punkty[cid] = punkty.get(cid, 0.0) + w_bm25 / (RRF_K + r)
            for r, (cid, _) in enumerate(w, 1):
                punkty[cid] = punkty.get(cid, 0.0) + w_wek / (RRF_K + r)
            polaczone = sorted(punkty.items(), key=lambda x: -x[1])
            pary = self._rozroznij(polaczone, top, limit_pliku)
        out = []
        for cid, s in pary:
            c = ch[cid]
            out.append({"rel": c["rel"], "head": c["head"], "body": c["body"], "score": s})
        return out


# ---------------------------------------------------------------- CLI

def snippet(body, query, width=320):
    qset = {bm25_pl.rdzen(t) or t for t in bm25_pl.tokenize(query)}
    low = body.lower()
    pos = -1
    for term in sorted(qset, key=len, reverse=True):
        pos = low.find(term)
        if pos != -1:
            break
    if pos == -1:
        return body[:width].strip()
    start = max(0, pos - width // 3)
    end = min(len(body), start + width)
    return ("..." if start else "") + body[start:end].strip() + ("..." if end < len(body) else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--baza", default=DOMYSLNA_BAZA)
    ap.add_argument("--model", default=DOMYSLNY_MODEL)
    ap.add_argument("--tryb", choices=["bm25", "wektor", "hybryda", "hybryda-rrf"], default="hybryda")
    ap.add_argument("--folder", dest="module", default=None,
                    help="szukaj tylko w tym podfolderze vaultu (ścieżka względna)")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--buduj", action="store_true")
    ap.add_argument("--od-zera", dest="od_zera", action="store_true")
    ap.add_argument("--sprawdz", action="store_true",
                    help="wypisuje liczbe plikow do przeliczenia, kod wyjscia 1 gdy >0")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    idx = Indeks(a.vault, a.baza, a.model)
    if a.sprawdz:
        sys.exit(1 if idx.sprawdz() > 0 else 0)
    if a.buduj:
        idx.buduj(od_zera=a.od_zera, wymuszony=True)
        return
    if not a.query:
        ap.error("podaj pytanie albo --buduj")
    idx.buduj()          # dociaga tylko to, co sie zmienilo (albo ostrzega i pomija, gdy duzo)
    wyniki = idx.szukaj(a.query, top=a.top, tryb=a.tryb, module=a.module)
    if not wyniki:
        print("Brak trafien.")
        return
    print('# vault-ask [%s]: "%s"\n' % (a.tryb, a.query))
    for i, r in enumerate(wyniki, 1):
        print("## %d. [%.4f] %s > %s" % (i, r["score"], r["rel"], r["head"]))
        print(r["body"] if a.full else snippet(r["body"], a.query))
        print()


if __name__ == "__main__":
    main()
