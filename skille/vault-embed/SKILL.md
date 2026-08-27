---
name: vault-embed
description: "Wyszukiwanie po vaulcie Obsidian z warstwą znaczeniową: BM25 plus lokalny embedding (multilingual-e5-small przez onnxruntime, indeks SQLite), łączone przez RRF. Wszystko liczy się na tej maszynie, treść notatek nie wychodzi do żadnego API. Użyj gdy pytanie jest opisowe i nie zawiera słów z notatki, albo gdy vault-ask nie trafił. Triggery: \"znajdź w vaulcie\", \"o czym była notatka o\", \"szukaj znaczeniowo\", \"vault-embed\"."
---

# vault-embed: druga warstwa nad BM25

Wyszukiwarka vaulta z dwiema warstwami. BM25 dopasowuje słowa, embedding dopasowuje
znaczenie, RRF łączy obie listy po pozycjach. To jest **nadbudowa**, nie zamiennik:
BM25 zostaje, bo na krótkich zapytaniach żargonowych bije wektor.

**Prywatność (warunek twardy).** Model chodzi lokalnie na CPU. Treść notatek nie opuszcza
maszyny. Jedyny plik, który rusza sieć, to `pobierz_model.py`, i pobiera wyłącznie wagi
modelu, jednorazowo. Po pobraniu całość działa offline.

## Instalacja (raz)

```
python3 -m venv .venv-embed && source .venv-embed/bin/activate
python3 -m pip install onnxruntime tokenizers numpy
python3 pobierz_model.py --fp32             # 470 MB, patrz uwaga niżej o wyborze wersji
python3 hybryda.py --buduj --vault "<ścieżka do vaultu>" --model model/model_fp32.onnx
```

Osobny venv, żeby te trzy pakiety nie mieszały się z resztą narzędzi w folderze.

**Wybór modelu: fp32, nie domyślny int8.** Kwantyzacja int8 w źródle tego pakietu
(`Xenova/multilingual-e5-small`) nie była zweryfikowana pod kątem architektury ARM (Apple
Silicon) w chwili wdrożenia — build int8 w POKREWNYM repo (`intfloat/...`) jest jawnie
skompilowany pod x86 AVX-512-VNNI i na ARM by nie zadziałał. Zamiast zgadywać, wzięto fp32:
działa na pewno, a różnica jakości jest zmierzona jako szum (patrz tabela int8/fp32 niżej).
Jeśli kiedyś ktoś zweryfikuje int8 z tego źródła na ARM, przełączenie to jedna flaga.

## Jak uruchomić (dla Claude)

1. Sprawdź, czy w katalogu roboczym są `bm25_pl.py`, `hybryda.py` i folder `model/`.
   Jeśli nie ma, zapisz skrypty z bloków poniżej i wykonaj instalację.
2. **W Cowork katalog roboczy bash to folder outputs, nie vault.** Podaj `--vault` ze
   ścieżką zamapowaną w bash (patrz system reminder „Shell access") — zwykle
   `/sessions/<id>/mnt/Documents/<nazwa Twojego vaulta>`.
3. Szukaj: `python3 hybryda.py "<pytanie>" --top 8 --model model/model_fp32.onnx`
4. Indeks dociąga się sam przy każdym uruchomieniu, ale tylko dla plików zmienionych
   od ostatniego razu (porównanie mtime i rozmiaru). Pierwsze uruchomienie buduje od zera
   i trwa kilka minut (zmierzone niżej), kolejne — sekundy.

Flagi: `--tryb bm25|wektor|hybryda` (domyślnie `hybryda`), `--top N`,
`--module firma|persona` (granica Persona/Firma, użyj jeśli masz taki podział), `--full`,
`--buduj`, `--od-zera`, `--model <ścieżka>` (domyślnie szuka `model_quantized.onnx`,
w tym wdrożeniu trzeba podawać `model/model_fp32.onnx` jawnie, patrz wyżej).

## Zmierzone na tym vaulcie (2026-08-27, 333 pliki, 4633 okna, model fp32)

Własny zestaw kontrolny (nie ten z vaulta pracowniczego — inny vault, inne notatki):
16 zapytań opisowych z ręcznie ustaloną poprawną odpowiedzią, osobno 5 krótkich zapytań
żargonowych, osobno 8 grup form fleksyjnych. Liczby poniżej są PO scaleniu z etapem C
(filtr `status`, waga `typ`) i po naprawie błędu opisanego w sekcji „Pułapka" niżej —
przed naprawą ten sam scaling wektor psuł katastrofalnie (top1 4/16, żargon 0/5).

| warstwa | top1 | top3 | MRR | żargon top3 | fleksja (zbiór) |
|---|---|---|---|---|---|
| BM25 (vault-ask, `bm25_pl.py`) | 7/16 | 13/16 | 0,637 | 5/5 | 7/8 |
| sam wektor | 11/16 | 13/16 | 0,760 | 5/5 | 3/8 |
| **hybryda (domyślna)** | 10/16 | 13/16 | 0,750 | 5/5 | 3/8 |

## Pułapka: waga `typ`/`status` a warstwa wektorowa (złapane i naprawione 27.08)

Scalenie z etapem C dodało wagę wg pola `typ` z frontmattera (`WAGI_TYPOW`), współdzieloną
między BM25 i tą warstwą (`_wektor()` mnoży podobieństwo kosinusowe przez `c["waga"]`).
Pierwsza wersja dawała `decyzja`/`procedura` mnożnik **1.2 — POWYŻEJ neutralnego 1.0**.

BM25 ma score w zakresie 5-40, więc boost 1.2 to nic. Podobieństwo kosinusowe siedzi w wąskim
pasie ~0,7-0,95 (różnica między trafieniem a nietrafieniem to często 0,02-0,05) — mnożnik 1.2
tam WYGRYWA z samym podobieństwem semantycznym. Efekt zmierzony na zapytaniu „hermes": notatka
„HOT — log zamkniętych wątków" (typ: procedura, tylko WSPOMINA Hermesa w jednym zdaniu)
wskoczyła na 1. miejsce ze score 0,98, przed notatką „Hermes — decyzja i plan wdrożenia"
(typ: wiedza, waga 1.0, treścią cała o Hermesie). Na całym zestawie: top1 warstwy wektorowej
4/16 zamiast 12/16, żargon 0/5 zamiast 5/5 — nie degradacja, całkowita utrata sensu warstwy.

**Naprawa:** żaden `typ` nie dostaje więcej niż 1.0 (`decyzja`/`procedura` z 1.2 na 1.0) —
waga może tylko OBNIŻAĆ (jak `log`: 0.5, albo `status: archiwum`: 0.4), nigdy podbijać ponad
brak wagi w ogóle. Ważność tematu (decyzja, procedura) ma inny, bezpieczny kanał: boost za
trafienie w tytuł/nagłówek (`BOOST_NAGLOWKA` w BM25), nie globalny mnożnik dzielony z wektorem.
**Wniosek do zapamiętania:** każda przyszła zmiana wagi dzielonej między BM25 i warstwę
wektorową musi być sprawdzona na OBU warstwach osobno, nie tylko na zagregowanym MRR hybrydy —
hybryda by tę katastrofę częściowo ukryła (RRF nadal korzysta z BM25), samą warstwę wektorową
trzeba mierzyć osobno (`--tryb wektor`), żeby złapać tego rodzaju regresję.

Na tym (mniejszym, 333-plikowym) vaulcie sam wektor ma lepsze zagregowane top1/MRR niż
hybryda — inaczej niż na vaulcie pracowniczym, gdzie hybryda wygrywała też na top1. Różnica
przy 16 zapytaniach to szum (1 zapytanie = 6 pp), więc hybryda zostaje domyślna nie z powodu
tej tabeli, tylko z powodu KONKRETNEGO przypadku niżej, zmierzonego na tym samym zestawie:

- zapytanie „plan naprawy wyszukiwarki notatek i dodania warstwy wektorowej" — cel to notatka
  `vault-ask 2.0 — plan`. **BM25 i hybryda trafiają, sam wektor NIE** (notatka wypada poza
  top 10). Odwrotność historii „kwarantanna" z vaulta pracowniczego, ten sam wniosek: żadna
  warstwa nie jest bezpieczna sama, hybryda jest ubezpieczeniem, nie kosmetyką.
- jedyne zapytanie nietrafione przez WSZYSTKIE trzy warstwy: „dlaczego długie dyktowanie
  w asystencie głosowym urywa się w środku nagrania" (cel: notatka o słowniku kontekstowym
  VantoLabs). Parafraza zbyt daleka nawet dla embeddingu — do zanotowania, nie do naprawiania
  teraz.

Strojenie wag RRF (`strojenie.py`) na tym vaulcie: 1:1 zostaje, symetryczne wagi potwierdzone
jako rozsądne, choć 3:1 (przewaga BM25) dawało wyższe zagregowane MRR (0,794 vs 0,750) i top3
14/16 zamiast 13/16 — różnica ok. jednego trafienia na 16 zapytań, dokładnie tyle, ile sami
nazywają szumem tej wielkości próbki. Bez zmiany domyślnej konfiguracji, ale gdyby ktoś kiedyś
chciał przestroić, 3:1 to pierwszy kandydat do sprawdzenia na WIĘKSZYM, mniej szumiącym
zestawie kontrolnym, nie do wdrożenia na podstawie tych 16 zapytań.

## int8 kontra fp32

**Na tej maszynie zmierzono tylko fp32** — int8 pominięty świadomie, patrz uzasadnienie
w sekcji instalacji (build w źródle tego pakietu nie był zweryfikowany pod ARM). Punkt
odniesienia to pomiar z vaulta pracowniczego (x86, tam oba warianty sprawdzone): różnica
fp32 nad int8 to jedno trafienie w top1 i jedno w sondzie żargonowej na 16 zapytań, czyli
w ich własnych słowach „dokładnie tyle, ile jest szumem". Nie ma powodu oczekiwać inaczej tu.

## Koszt (zmierzony na tym vaulcie, nie szacowany)

| co | ile |
|---|---|
| budowa indeksu od zera | 460 s / 4558 okien (fp32, CPU, Apple Silicon) |
| przebudowa przyrostowa | tylko pliki zmienione od ostatniego razu |
| baza SQLite | 17,2 MB |
| jedno uruchomienie CLI (proces od zera), tryb hybryda | ok. 4,8 s |

Budowa indeksu przekracza umowne 5 minut z planu (460 s vs 300 s) — throughput osadzania
spada z ok. 50 okien/s na starcie do ok. 10 okien/s pod koniec biegu (4558 okien), najpewniej
tło systemowe/termiczne na CPU, nie wada kodu. Nie blokuje: liczy się raz, potem tylko
przyrostowo. Czas pojedynczego zapytania (4,8 s) jest WYŻSZY niż cel z planu (poniżej 2 s) —
ale to koszt startu procesu (ładowanie modelu fp32 z dysku do onnxruntime przy KAŻDYM
wywołaniu CLI), nie koszt samego liczenia: sama warstwa wektorowa po załadowaniu modelu
liczy się w milisekundach (mnożenie macierzy w numpy). W praktyce nieistotne, bo to narzędzie
wywołuje Claude raz na pytanie, nie w pętli — ale warto wiedzieć, że w tej konfiguracji CLI
NIE nadaje się do wywoływania dziesiątki razy pod rząd bez utrzymywania procesu przy życiu.

## Skrypty

Zapisz oba pliki obok siebie. `hybryda.py` importuje `bm25_pl`.

### bm25_pl.py

```python
#!/usr/bin/env python3
"""
vault-ask — lokalne wyszukiwanie po vaulcie Obsidian (BM25, bez modeli AI).
Zero zależności (tylko biblioteka standardowa), zero tokenów, działa offline.

Użycie:
    python bm25_search.py "twoje pytanie" [--vault SCIEZKA] [--top 8] [--full]

Zwraca najtrafniejsze fragmenty (sekcje wg nagłówków) z cytatami: plik + nagłówek.
Claude czyta sam wynik (kilka fragmentów), nie cały vault → tanio i celnie.

Uwaga (Cowork): auto-detekcja vaultu działa tylko gdy proces stoi w drzewie
vaultu. W sandboxie Cowork katalog roboczy to zwykle folder outputs — w takim
wypadku podaj --vault explicit albo ustaw zmienną VAULT_DIR.
"""
import os, re, sys, math, argparse
from collections import Counter

# Foldery calkowicie poza indeksem. Powod (pomiar 2026-08-26 na vaulcie pracowniczym):
# .vault-lint-backup to 236 plikow / 1845 sekcji, czyli 19% calego indeksu — same kopie
# zapasowe notatek, ktore juz sa w vaulcie w wersji biezacej. W pomiarze bazowym kopia
# wypchnela oryginal z top3 w 4 z 6 nietrafionych zapytan (np. "wylaczenie zwrotow" —
# pozycje 1 i 2 to byly backupy). Kopia nigdy nie moze wyjsc jako zrodlo prawdy.
SKIP_DIRS = {".obsidian", ".git", ".claude", "node_modules", "__pycache__",
             ".trash", "_kwarantanna",
             ".vault-lint-backup", ".manifest-backup", "_do_usuniecia", "_rm-backup"}
TOKEN_RE = re.compile(r"[a-ząćęłńóśźż0-9]+", re.IGNORECASE)

# Wagi folderow. Powod (pomiar 2026-08-26): Dziennik to 22% tekstu vaultu, _inbox kolejne
# 10%, i zalewaly wyniki, spychajac notatki docelowe. Nie wykluczamy ich, bo bywaja jedynym
# zrodlem, tylko obnizamy. Dopasowanie po pierwszym segmencie sciezki wzgledem vaultu.
# Wagi folderow. W tym vaulcie Dziennik i Hot NIE leza na pierwszym poziomie, tylko pod
# Persona/ (decyzja 2026-07-25: Dziennik i Hot naleza do Persony). Dopasowanie po pierwszym
# segmencie — jak w wersji z repo — nie zlapaloby ich wcale. Dlatego sprawdzamy KAZDY segment
# sciezki i bierzemy wage najnizsza (Persona/Dziennik/_archiwum dostaje 0.3, nie 0.5).
# Pomiar 2026-08-26: Dziennik to 242 pliki, Hot 127 — razem 35% plikow vaultu.
WAGI_FOLDEROW = {
    "_archiwum": 0.3,
    "Archiwum": 0.3,
    "Dziennik": 0.5,
    "Hot": 0.5,
    "INBOX_Notatki Tomek": 0.7,
    "_inbox": 0.7,
}

# Etap C (scalone tu 27.08, wczesniej osobno w bm25_search_wip.py). Waga wg pola `typ`
# z frontmattera bije wage folderu, bo jest deklarowana wprost, nie zgadywana z lokalizacji
# pliku — uzywana TYLKO gdy notatka ma frontmatter z `typ`, inaczej pozostaje waga_folderu.
#
# POPRAWKA 27.08 po pomiarze na tym vaulcie: oryginalna wersja z etapu C dawala `decyzja`
# i `procedura` wage 1.2 (boost POWYZEJ neutralnego 1.0). Dla BM25 (score 5-40) to nieszkodliwe,
# ale warstwa wektorowa mnozy przez to samo `waga` cosinus ograniczony do ~0.7-0.95 — boost 1.2
# tam wystarczyl, zeby notatka TYLKO WSPOMINAJACA temat (typ: procedura, bocznie zawierajaca
# slowo zapytania) wyprzedzila notatke FAKTYCZNIE o tym temacie (typ: wiedza, waga 1.0).
# Zmierzone na zapytaniu "hermes": notatka "HOT — log zamknietych watkow" (typ: procedura,
# tylko wzmianka) wskoczyla na 1. miejsce przed "Hermes — decyzja i plan wdrozenia" (typ: wiedza).
# Efekt na całym zestawie: sam wektor top1 spadl z 12/16 do 4/16, zargon z 5/5 do 0/5.
# Naprawa: zaden typ nie dostaje wiecej niz neutralne 1.0 — `typ` moze tylko obnizac
# (jak `log`), nigdy podbijac ponad brak wagi w ogole. Podbicie waznosci decyzji/procedur
# zostaje realizowane inaczej (BOOST_NAGLOWKA przy trafieniu w tytul), nie mnoznikiem globalnym.
WAGI_TYPOW = {
    "decyzja": 1.0,
    "procedura": 1.0,
    "wiedza": 1.0,
    "mapa": 1.0,
    "brief": 1.0,
    "dane": 1.0,
    "log": 0.5,
}
# Waga wg pola `status`. `obalone` nie jest wazone, tylko odfiltrowane w calosci
# (patrz load_chunks i hybryda.Indeks.buduj) — ustalenie odwolane nie ma prawa
# wyjsc jako odpowiedz, zostaje w vaulcie wylacznie jako historia decyzji.
WAGI_STATUSOW = {"aktualne": 1.0, "szkic": 0.8, "archiwum": 0.4}
# Indeksujemy wylacznie rdzenie, bez form doslownych. Powod (zmierzone 2026-08-26):
# przy zachowanej formie z waga 0,15 score byly tak ciasne (6,38 kontra 6,36), ze odmiana
# slowa nadal przestawiala kolejnosc, czyli cel etapu nie byl osiagniety.
RDZEN = "~"
MIN_RDZEN = 4
# Maksymalny narzut za trafienie w naglowek sekcji albo nazwe pliku.
BOOST_NAGLOWKA = 0.6

# Koncowki fleksyjne polskiego, od najdluzszych. Obcinamy pierwsza pasujaca, o ile zostaje
# co najmniej MIN_RDZEN znakow. To light-stemmer, nie pelny: nie odwraca obocznosci
# spolgloskowych (`vaulcie` zostaje `vaulc`, nie `vault`), bo to wymaga slownika.
KONCOWKI = (
    "iami", "iach", " owie", "ach", "ami", "owi", "ego", "emu", "ich", "ych",
    "imi", "ymi", "iem", "owy", "owa", "owe", "ów", "om", "em", "ie", "ia",
    "ym", "im", "ej", "ą", "ę", "a", "e", "i", "o", "u", "y",
)


def rdzen(tok):
    """Rdzen slowa po obcieciu koncowki fleksyjnej.

    Zmierzone 2026-08-26: `vault` dawalo 238 trafien, `vaulcie` 148, `vaultow` 57, kazde
    z innym topem, bo tokenizer nie ma stemmingu.

    Dwa wczesniejsze podejscia odrzucone pomiarem, zeby nie wrocily:
    prefiks o dlugosci liczonej od formy (max(4, len-3)) rozjezdzal formy tego samego slowa
    (`notatka` dawalo `nota`, `notatkach` dawalo `notatk`); prefiks stalej dlugosci rozjezdzal
    slowa o rdzeniach roznej dlugosci (`notatk` ma 6 znakow, `vault` 5).
    """
    if len(tok) < MIN_RDZEN + 1 or tok.isdigit():
        return None
    for k in KONCOWKI:
        if tok.endswith(k) and len(tok) - len(k) >= MIN_RDZEN:
            return _twardy(tok[: -len(k)])
    return _twardy(tok)


# Obocznosci spolgloskowe, ktore zostawia po sobie miejscownik: `w projekcie` daje rdzen
# `projekc`, `w liscie` daje `lisc`. Bez tej normalizacji te formy nie spotkaja sie
# w indeksie z mianownikiem (`projekt`, `list`). Sprowadzamy do postaci twardej.
OBOCZNOSCI = (("ść", "st"), ("śc", "st"), ("ci", "t"), ("c", "t"), ("dz", "d"), ("rz", "r"))


def _twardy(r):
    if len(r) < 5:
        return r
    for miekka, twarda in OBOCZNOSCI:
        if r.endswith(miekka):
            return r[: -len(miekka)] + twarda
    return r


def waga_folderu(rel):
    """Najnizsza waga sposrod wszystkich segmentow sciezki (nie tylko pierwszego)."""
    waga = 1.0
    for seg in rel.split(os.sep)[:-1]:
        waga = min(waga, WAGI_FOLDEROW.get(seg, 1.0))
    return waga


def pola_frontmattera(text):
    """Zwraca `typ` i `status` z frontmattera. Puste, gdy notatka go nie ma."""
    if not text.startswith("---"):
        return {}
    koniec = text.find("\n---", 3)
    if koniec == -1:
        return {}
    pola = {}
    for linia in text[4:koniec].splitlines():
        m = re.match(r"^(typ|status):\s*(\S+)", linia)
        if m:
            pola[m.group(1)] = m.group(2).strip()
    return pola


def waga_notatki(rel, meta):
    """Waga finalna: `typ` z frontmattera bije folder, `status` zawsze mnozy na koncu.
    `meta` puste (brak frontmattera) -> czysta waga_folderu, zachowanie sprzed etapu C."""
    baza = WAGI_TYPOW.get(meta.get("typ"), None)
    if baza is None:
        baza = waga_folderu(rel)
    return baza * WAGI_STATUSOW.get(meta.get("status", "aktualne"), 1.0)


def find_vault(explicit=None):
    """Znajdz folder vaultu niezaleznie od miejsca skryptu (pod Cowork/replikacje).
    Dopasowuje dowolny folder, ktorego nazwa ZAWIERA 'obsidian' (np. 'Jan w Obsidian'),
    nie tylko dokladne 'Obsidian' — bo nazwa vaultu bywa rozszerzona."""
    if explicit:
        return os.path.abspath(explicit)
    env = os.environ.get("VAULT_DIR")
    if env:
        return os.path.abspath(env)
    seeds = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    for seed in seeds:
        d = os.path.abspath(seed)
        for _ in range(8):
            if "obsidian" in os.path.basename(d).lower() and os.path.isdir(d):
                return d
            try:
                for sub in os.listdir(d):
                    if "obsidian" in sub.lower() and os.path.isdir(os.path.join(d, sub)):
                        return os.path.join(d, sub)
            except OSError:
                pass
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Obsidian"))


def tokenize(text):
    return [t.lower() for t in TOKEN_RE.findall(text)]


def tokenize_z_prefiksami(text):
    """Tokeny doslowne plus ich rdzenie, oznaczone przedrostkiem RDZEN."""
    return [RDZEN + (rdzen(tok) or tok) for tok in tokenize(text)]


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :]
    return text


def split_sections(text, path):
    """Dzieli plik na sekcje wg nagłówków (#, ##, ###). Każda = osobny chunk."""
    text = strip_frontmatter(text)
    lines = text.splitlines()
    sections, cur_head, cur_lines = [], os.path.basename(path)[:-3], []
    for ln in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            if "".join(cur_lines).strip():
                sections.append((cur_head, "\n".join(cur_lines)))
            cur_head, cur_lines = m.group(2).strip(), []
        else:
            cur_lines.append(ln)
    if "".join(cur_lines).strip():
        sections.append((cur_head, "\n".join(cur_lines)))
    return sections or [(os.path.basename(path)[:-3], text)]


def load_chunks(vault, module=None):
    chunks = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, vault)
            # Regula twarda 3: granica Persona <-> Firma. Wersja z repo zgubila ten filtr,
            # a tutaj jest potrzebny — przy pracy nad materialem dla zespolu Persona nie
            # ma prawa wyjsc w wynikach.
            if module:
                low = rel.lower()
                if module == "firma" and low.startswith("persona"):
                    continue
                if module == "persona" and not low.startswith("persona"):
                    continue
            try:
                txt = open(full, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            meta = pola_frontmattera(txt)
            if meta.get("status") == "obalone":
                # Ustalenie odwolane. Zostaje w vaulcie jako historia decyzji,
                # ale nie ma prawa wyjsc jako odpowiedz.
                continue
            nazwa = fn[:-3]
            waga = waga_notatki(rel, meta)
            for head, body in split_sections(txt, full):
                toks = tokenize_z_prefiksami(head + " " + body)
                if toks:
                    chunks.append(
                        {
                            "rel": rel,
                            "head": head,
                            "body": body.strip(),
                            "toks": toks,
                            # Naglowek sekcji i nazwa pliku sa mocniejszym sygnalem trafnosci
                            # niz to samo slowo w srodku akapitu, stad osobny zbior do boostu.
                            "kluczowe": set(tokenize_z_prefiksami(head + " " + nazwa)),
                            "waga": waga,
                        }
                    )
    return chunks


def bm25_rank(chunks, query, k1=1.5, b=0.75):
    q = tokenize_z_prefiksami(query)
    N = len(chunks)
    if not N or not q:
        return []
    avgdl = sum(len(c["toks"]) for c in chunks) / N
    df = Counter()
    tfs = []
    for c in chunks:
        tf = Counter(c["toks"])
        tfs.append(tf)
        for term in set(c["toks"]):
            df[term] += 1
    idf = {t: math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5)) for t in set(q) if df[t]}
    q_unikalne = set(q)
    scored = []
    for i, c in enumerate(chunks):
        dl = len(c["toks"])
        s = 0.0
        for term in q:
            if term not in idf:
                continue
            f = tfs[i][term]
            if f:
                s += idf[term] * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
        if s <= 0:
            continue
        trafione_w_naglowku = len(q_unikalne & c["kluczowe"])
        if trafione_w_naglowku:
            s *= 1 + BOOST_NAGLOWKA * trafione_w_naglowku / len(q_unikalne)
        s *= c["waga"]
        scored.append((s, i))
    scored.sort(key=lambda x: (-x[0], chunks[x[1]]["rel"]))
    return scored


def snippet(body, query, full=False, width=320):
    if full:
        return body
    qset = {rdzen(t) or t for t in tokenize(query)}
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
    pre = "…" if start > 0 else ""
    suf = "…" if end < len(body) else ""
    return pre + body[start:end].strip() + suf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--module", choices=["firma", "persona"], default=None,
                    help="ogranicz do modulu (granica Persona/Firma)")
    ap.add_argument("--full", action="store_true", help="pełna treść sekcji zamiast snippetu")
    a = ap.parse_args()

    # Windows: konsola i przekierowanie do pliku ida domyslnie przez cp1250, a vault ma
    # w tresci strzalki, mysliniki i ogonki. Bez tego skrypt przewraca sie na
    # UnicodeEncodeError w polowie wypisywania wynikow (potwierdzone 2026-08-26 na znaku
    # U+2192). errors="replace", zeby pojedynczy egzotyczny znak nigdy nie ubil calego
    # wyniku wyszukiwania.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    vault = find_vault(a.vault)
    if not os.path.isdir(vault):
        print(f"BLAD: nie ma folderu vault: {vault}", file=sys.stderr)
        sys.exit(2)
    chunks = load_chunks(vault, a.module)
    ranked = bm25_rank(chunks, a.query)
    if not ranked:
        print("Brak trafien. Sprobuj innych slow kluczowych.")
        return
    print(f'# vault-ask: "{a.query}"  ({len(ranked)} trafien, top {a.top})\n')
    for rank, (score, i) in enumerate(ranked[: a.top], 1):
        c = chunks[i]
        print(f"## {rank}. [{score:.2f}] {c['rel']} > {c['head']}")
        print(snippet(c["body"], a.query, a.full))
        print()


if __name__ == "__main__":
    main()
```

### hybryda.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vault-embed: druga warstwa nad BM25, czyli lokalny embedding i hybryda.

Warunek twardy: WSZYSTKO lokalnie. Model chodzi na CPU przez onnxruntime, indeks siedzi
w SQLite obok vaultu. Zadna tresc notatki nie opuszcza maszyny, bo w tym pliku nie ma ani
jednego wywolania sieciowego (pobranie modelu to osobny, jednorazowy krok: pobierz_model.py).

Warstwy:
  bm25    : bm25_pl.py (stemming PL, wagi folderow, kwarantanna i kopie poza indeksem)
  wektor  : multilingual-e5-small, mean pooling + L2, cosinus
  hybryda : RRF (Reciprocal Rank Fusion) po obu listach

Dlaczego RRF, a nie wazona suma score:
BM25 zwraca wartosci nieograniczone (tu 5 do 40), cosinus siedzi w [-1,1]. Zeby je zsumowac,
trzeba by kalibrowac skale per zapytanie, a to kolejny parametr do zestrojenia i kolejne
miejsce na cichy blad. RRF patrzy tylko na POZYCJE, wiec jest odporny na skale obu silnikow.

Uzycie:
    py hybryda.py "pytanie"  [--tryb bm25|wektor|hybryda] [--top 8] [--module firma|persona]
    py hybryda.py --buduj          # przebuduj indeks (inkrementalnie po mtime+rozmiarze)
    py hybryda.py --buduj --od-zera
"""
import os, re, sys, json, math, time, sqlite3, argparse, hashlib
import numpy as np

import bm25_pl

BAZA = os.path.dirname(os.path.abspath(__file__))
DOMYSLNY_MODEL = os.path.join(BAZA, "model", "model_quantized.onnx")
DOMYSLNY_TOKENIZER = os.path.join(BAZA, "model", "tokenizer.json")
DOMYSLNA_BAZA = os.path.join(BAZA, "dane", "indeks.sqlite")

MAX_TOKENOW = 512          # limit pozycyjny modelu
SLOW_NA_OKNO = 260         # ok. 420 tokenow dla polszczyzny (ok. 1,6 tokena na slowo)
ZAKLADKA_SLOW = 40         # zakladka miedzy oknami, zeby zdanie na styku nie przepadlo
WYMIAR = 384
RRF_K = 60                 # stala tlumiaca RRF; 60 to wartosc z oryginalnej pracy Cormacka

# Wagi warstw w fuzji. Pomiar 2026-08-26 na 16 zapytaniach kontrolnych: warstwa wektorowa
# wygrywa na zapytaniach opisowych (parafraza 5/5), ale WYRAZNIE przegrywa na krotkich
# zapytaniach zargonowych. Przyklad z pomiaru: na haslo "kwarantanna" BM25 zwraca notatke
# "Folder Desktop-Claude, struktura i utrzymanie" (poprawnie), a sam wektor zwraca
# "README.md" i "_frontmatter_braki.md" (bez zwiazku). Dlatego BM25 zostaje jako kotwica
# leksykalna, a nie jest zastepowany.
WAGA_BM25 = 1.0
WAGA_WEKTOR = 1.0

# Maksymalna liczba sekcji z JEDNEGO pliku w wynikach. Pomiar 2026-08-26: na haslo "skill"
# caly top3 warstwy wektorowej to byly trzy sekcje tego samego pliku "SKILL (szkielet).md".
# Wyszukiwarka ma dac Claude'owi rozne zrodla do zacytowania, a nie trzy razy to samo.
MAX_SEKCJI_NA_PLIK = 2


# ---------------------------------------------------------------- model lokalny

class Osadzacz:
    """multilingual-e5-small przez onnxruntime. Tylko CPU, tylko lokalnie."""

    def __init__(self, model=DOMYSLNY_MODEL, tokenizer=None, watki=None):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        # Tokenizer nalezy DO modelu, wiec szukamy go obok modelu, a nie obok skryptu.
        # Inaczej po skopiowaniu skryptu w inne miejsce (albo na Maca) sciezka wskazuje
        # w prozne i leci "System nie moze odnalezc okreslonej sciezki (os error 3)".
        if tokenizer is None:
            obok_modelu = os.path.join(os.path.dirname(os.path.abspath(model)), "tokenizer.json")
            tokenizer = obok_modelu if os.path.isfile(obok_modelu) else DOMYSLNY_TOKENIZER
        if not os.path.isfile(tokenizer):
            raise SystemExit("BLAD: brak tokenizera: %s (ma lezec w tym samym folderze "
                             "co model)" % tokenizer)
        if not os.path.isfile(model):
            raise SystemExit("BLAD: brak modelu: %s\nUruchom najpierw: py pobierz_model.py" % model)
        opcje = ort.SessionOptions()
        if watki:
            opcje.intra_op_num_threads = watki
        self.sesja = ort.InferenceSession(model, opcje, providers=["CPUExecutionProvider"])
        self.tok = Tokenizer.from_file(tokenizer)
        self.tok.enable_truncation(max_length=MAX_TOKENOW)
        self.wejscia = {i.name for i in self.sesja.get_inputs()}

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
        out = np.zeros((len(teksty), WYMIAR), dtype=np.float32)
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


class Indeks:
    def __init__(self, vault=None, baza=DOMYSLNA_BAZA, model=DOMYSLNY_MODEL, cicho=False):
        self.vault = os.path.abspath(vault or bm25_pl.find_vault())
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

    def buduj(self, od_zera=False):
        t0 = time.time()
        if od_zera:
            self.db.executescript("DELETE FROM pliki; DELETE FROM chunki; DELETE FROM wektory;")
            self.db.commit()

        stan = self._stan_plikow()
        stary = {r: (m, s) for r, m, s in
                 self.db.execute("SELECT rel, mtime, rozmiar FROM pliki")}
        zmienione = [r for r, v in stan.items() if stary.get(r) != v]
        usuniete = [r for r in stary if r not in stan]

        if not zmienione and not usuniete:
            self._log("Indeks aktualny (%d plikow, bez zmian)." % len(stan))
            return

        self._log("Do przeliczenia: %d plikow, do usuniecia: %d." % (len(zmienione), len(usuniete)))

        for rel in list(zmienione) + usuniete:
            ids = [i for (i,) in self.db.execute("SELECT id FROM chunki WHERE rel=?", (rel,))]
            if ids:
                q = ",".join("?" * len(ids))
                self.db.execute("DELETE FROM wektory WHERE chunk_id IN (%s)" % q, ids)
                self.db.execute("DELETE FROM chunki WHERE rel=?", (rel,))
            self.db.execute("DELETE FROM pliki WHERE rel=?", (rel,))
        self.db.commit()

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
                # metodzie (petla po zmienione+usuniete) — po prostu nic nowego nie wstawiamy.
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
        self._log("Gotowe w %.1fs." % (time.time() - t0))

    # ---------- odczyt

    def _wczytaj_wektory(self):
        if self._wek is not None:
            return
        wiersze = self.db.execute("SELECT chunk_id, wek FROM wektory").fetchall()
        if not wiersze:
            raise SystemExit("BLAD: indeks wektorowy pusty. Uruchom: py hybryda.py --buduj")
        self._wek = np.frombuffer(b"".join(w for _, w in wiersze),
                                  dtype=np.float32).reshape(len(wiersze), WYMIAR)
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
        return [c for c in self._lista_cache
                if c["rel"].lower().startswith("persona") == (module == "persona")]

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
            if module and (c["rel"].lower().startswith("persona")) != (module == "persona"):
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
               w_bm25=WAGA_BM25, w_wek=WAGA_WEKTOR, limit_pliku=MAX_SEKCJI_NA_PLIK):
        ch = self._chunki()
        zapas = max(top * 5, 50)
        if tryb == "bm25":
            pary = self._rozroznij(self._bm25(query, module)[:zapas], top, limit_pliku)
        elif tryb == "wektor":
            pary = self._rozroznij(self._wektor(query, module)[:zapas], top, limit_pliku)
        else:
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
    ap.add_argument("--tryb", choices=["bm25", "wektor", "hybryda"], default="hybryda")
    ap.add_argument("--module", choices=["firma", "persona"], default=None)
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--buduj", action="store_true")
    ap.add_argument("--od-zera", dest="od_zera", action="store_true")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    idx = Indeks(a.vault, a.baza, a.model)
    if a.buduj:
        idx.buduj(od_zera=a.od_zera)
        return
    if not a.query:
        ap.error("podaj pytanie albo --buduj")
    idx.buduj()          # dociaga tylko to, co sie zmienilo
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
```

### pobierz_model.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jednorazowe pobranie modelu multilingual-e5-small (ONNX) do folderu model/.

To JEDYNY plik w tym projekcie, ktory rusza siec, i rusza ja tylko po wagi modelu.
Tresc notatek nie wychodzi stad nigdzie i nigdy. Po pobraniu caly folder model/ mozna
przeniesc na inna maszyne (np. na Maca) i wyszukiwarka dziala bez sieci.

Uzycie:
    py pobierz_model.py                 # wersja skwantyzowana int8 (118 MB), domyslna
    py pobierz_model.py --fp32          # pelna precyzja (470 MB)
    py pobierz_model.py --obie

Uwaga dla Windows z Nortonem: Norton podmienia certyfikat TLS, przez co urllib i certifi
potrafia odmowic polaczenia (objaw: "certificate verify failed" albo "UnknownIssuer").
Skrypt sam sprobuje wtedy magazynu certyfikatow systemu Windows.
"""
import os, sys, ssl, argparse, urllib.request, hashlib

BAZA = os.path.dirname(os.path.abspath(__file__))
DOCELOWY = os.path.join(BAZA, "model")
ZRODLO = "https://huggingface.co/Xenova/multilingual-e5-small/resolve/main"

PLIKI_WSPOLNE = [
    ("tokenizer.json", "tokenizer.json"),
    ("config.json", "config.json"),
    ("tokenizer_config.json", "tokenizer_config.json"),
]
PLIK_INT8 = ("onnx/model_quantized.onnx", "model_quantized.onnx")
PLIK_FP32 = ("onnx/model.onnx", "model_fp32.onnx")


def kontekst_ssl():
    """Domyslny kontekst; przy zerwanym lancuchu (Norton) magazyn systemu Windows."""
    try:
        ctx = ssl.create_default_context()
        urllib.request.urlopen(urllib.request.Request(ZRODLO + "/config.json",
                                                      method="HEAD"),
                               context=ctx, timeout=20)
        return ctx
    except Exception as e:
        print("  Domyslny lancuch TLS odrzucony (%s)." % type(e).__name__)
        print("  Probuje magazynu certyfikatow systemu...")
        ctx = ssl.create_default_context()
        try:
            ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
            if sys.platform == "win32":
                import wincertstore  # opcjonalnie
        except Exception:
            pass
        return ctx


def pobierz(zdalny, lokalny, ctx):
    cel = os.path.join(DOCELOWY, lokalny)
    if os.path.isfile(cel) and os.path.getsize(cel) > 0:
        print("  jest juz: %-26s %12s B" % (lokalny, format(os.path.getsize(cel), ",")))
        return
    url = "%s/%s" % (ZRODLO, zdalny)
    print("  pobieram: %s" % lokalny, flush=True)
    tmp = cel + ".czesciowy"
    with urllib.request.urlopen(url, context=ctx, timeout=600) as r, open(tmp, "wb") as f:
        ile = 0
        while True:
            kawalek = r.read(1 << 20)
            if not kawalek:
                break
            f.write(kawalek)
            ile += len(kawalek)
            print("\r    %s MB" % format(ile >> 20, ","), end="", flush=True)
    print()
    os.replace(tmp, cel)
    print("  gotowe:   %-26s %12s B" % (lokalny, format(os.path.getsize(cel), ",")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fp32", action="store_true", help="pelna precyzja zamiast int8")
    ap.add_argument("--obie", action="store_true", help="obie wersje modelu")
    a = ap.parse_args()

    os.makedirs(DOCELOWY, exist_ok=True)
    print("Folder docelowy: %s" % DOCELOWY)
    ctx = kontekst_ssl()

    lista = list(PLIKI_WSPOLNE)
    if a.obie:
        lista += [PLIK_INT8, PLIK_FP32]
    elif a.fp32:
        lista += [PLIK_FP32]
    else:
        lista += [PLIK_INT8]

    for zdalny, lokalny in lista:
        pobierz(zdalny, lokalny, ctx)

    print("\nGotowe. Teraz zbuduj indeks:  python3 hybryda.py --buduj --vault <sciezka do vaultu>")


if __name__ == "__main__":
    main()
```
