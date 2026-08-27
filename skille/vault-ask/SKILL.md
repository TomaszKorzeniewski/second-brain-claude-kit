---
name: vault-ask
description: "Lokalne wyszukiwanie po vaulcie Obsidian (BM25 ze stemmingiem polskim, bez modeli AI, bez tokenów). Użyj gdy trzeba znaleźć w vaulcie informacje na temat zamiast wczytywać całe pliki. Zwraca trafne fragmenty z cytatami (plik + nagłówek). Triggery: \"co wiemy o\", \"znajdź w vaulcie\", \"ask\", \"przeszukaj notatki\"."
---

# vault-ask: tanie wyszukiwanie po vaulcie (BM25)

Samodzielny skill: cały kod jest w tym pliku. Bez zależności (stdlib Pythona), bez tokenów.

## Jak uruchomić (dla Claude)
1. Jeśli plik `bm25_pl.py` nie istnieje w katalogu roboczym sesji, zapisz go z bloku „Skrypt" poniżej.
2. Uruchom: `python3 bm25_pl.py "<pytanie>" --top 8` (vault wykrywa się sam po folderze zawierającym „obsidian" w nazwie; w razie potrzeby `--vault <ścieżka>` albo zmienna `VAULT_DIR`).
3. **W Cowork katalog roboczy bash to folder outputs, nie vault.** Auto-detekcja działa tylko gdy skrypt stoi wewnątrz drzewa vaulta. Podaj `--vault` ze ścieżką zamapowaną w bash (patrz system reminder „Shell access" na starcie sesji) — zwykle `/sessions/<id>/mnt/Documents/<nazwa Twojego vaulta>`.
4. Zwróć użytkownikowi wynik z cytatami (plik › nagłówek). Najpierw vault-ask, dopiero potem ewentualnie doczytaj pełne pliki, bo to oszczędza tokeny.

Flagi: `--top N`, `--module firma|persona` (granica Persona/Firma, użyj jeśli masz taki podział w vaulcie), `--full`.

## Co ta wersja robi inaczej niż zwykły BM25

1. **Stemming polski bez słownika.** Indeksowane są rdzenie, nie formy, więc `notatka`,
   `notatki` i `notatkach` trafiają w to samo. Normalizowane są też oboczności spółgłoskowe
   z miejscownika: `projekcie` sprowadza się do `projekt`, `vaulcie` do `vault`.
2. **Kopie zapasowe i kwarantanna są poza indeksem** (`SKIP_DIRS`). Materiał odłożony do
   skasowania albo kopia sprzed zmiany nie mają prawa wyjść jako źródło prawdy.
3. **Foldery mają wagi** (`WAGI_FOLDEROW`), dopasowywane po KAŻDYM segmencie ścieżki, nie
   tylko po pierwszym. Dziennik i Hot leżą pod `Persona/`, więc dopasowanie po pierwszym
   segmencie w ogóle by ich nie złapało. Nie są wykluczone, tylko obniżone.
4. **Nazwa pliku i nagłówek sekcji podbijają wynik** (`BOOST_NAGLOWKA`), bo trafienie
   w tytuł jest mocniejszym sygnałem niż to samo słowo w środku akapitu.

## Zmierzone na tym vaulcie (2026-08-27, 16 zapytań kontrolnych, 333 pliki)

| wersja | top1 | top3 | MRR | stabilność fleksji |
|---|---|---|---|---|
| z publicznego repo (etap A, stemming) | 7/16 | 13/16 | 0,637 | 7/8 |
| ta (`bm25_pl.py`, konfiguracja z drugiego, bliźniaczego vaultu + filtr `status`/`typ`) | 7/16 | 13/16 | 0,637 | 7/8 |

**Bez różnicy na tym vaulcie** — i to jest oczekiwany wynik, nie błąd pomiaru. Rozszerzenia
w `bm25_pl.py` (więcej folderów kopii zapasowych w `SKIP_DIRS`, dopasowanie wag po każdym
segmencie ścieżki dla układu Persona/Firma, filtr `status: obalone`, waga wg `typ`) naprawiają
problemy zmierzone na INNYCH vaultach (kopie zapasowe na firmowym, brak jeszcze żadnej notatki
`status: obalone` tu). Silnik zachowuje się prawie identycznie jak wersja z repo — ale jest
gotowy na wszystkie te przypadki, gdy się pojawią. Sprawdź `python3 vault_stats.py "<vault>"`
po każdej większej reorganizacji.

**Znany limit, złapany pomiarem 27.08 (nie wróci, opisane w komentarzu przy `WAGI_TYPOW`):**
pierwsza wersja wagi `typ` dawała `decyzja`/`procedura` mnożnik 1.2 — POWYŻEJ neutralnego 1.0.
Dla samego BM25 (score 5-40) to nieszkodliwe, ale ta sama waga jest współdzielona z warstwą
wektorową w skillu `vault-embed`, gdzie mnoży podobieństwo kosinusowe (zakres ~0,7-0,95).
Boost 1.2 tam wystarczył, żeby notatka TYLKO WSPOMINAJĄCA temat (typ: procedura) wyprzedziła
notatkę FAKTYCZNIE o tym temacie (typ: wiedza, waga 1.0) — na zapytaniu „hermes" top1 warstwy
wektorowej spadł z 12/16 do 4/16, żargon z 5/5 do 0/5. Naprawione: żaden `typ` nie dostaje
więcej niż 1.0, może tylko obniżać (jak `log`), nigdy podbijać.

## Kiedy to nie wystarczy

BM25 dopasowuje słowa. Jeśli pytanie nie ma wspólnych słów z notatką („kiedy oddać robotę
tańszemu modelowi" kontra notatka „Tiering i delegacja modeli"), trafienie jest przypadkowe —
w pomiarze niżej to jeden z dwóch nietrafionych przypadków BM25. Do takich pytań jest druga
warstwa: skill `vault-embed` (embedding lokalny + hybryda). Na tych samych 16 zapytaniach
hybryda daje top3 13/16 i MRR 0,750, sam wektor 13/16 i MRR 0,760 — ale wektor sam gubi
rzeczy, które BM25 łapie bez trudu (patrz `vault-embed`, sekcja pomiaru).

## Skrypt

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
