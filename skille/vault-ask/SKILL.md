---
name: vault-ask
description: "Lokalne wyszukiwanie po vaulcie Obsidian (BM25, bez modeli AI, bez tokenów). Użyj gdy trzeba znaleźć w vaulcie informacje na temat zamiast wczytywać całe pliki. Zwraca trafne fragmenty z cytatami (plik + nagłówek). Triggery: \"co wiemy o\", \"znajdź w vaulcie\", \"ask\", \"przeszukaj notatki\"."
---

# vault-ask — tanie wyszukiwanie po vaulcie (BM25)

Samodzielny skill: cały kod jest w tym pliku. Bez zależności (stdlib Pythona), bez tokenów.

> Auto-detekcja vaulta szuka folderu, którego nazwa ZAWIERA „obsidian" (nie musi być dokładnie
> „Obsidian" — pasuje np. „Jan w Obsidian", „MójDrugiMózg-Obsidian"). Jeśli Twój vault nazywa
> się inaczej, podawaj `--vault` jawnie.

## Co robi inaczej niż zwykły BM25

1. **Stemming polski bez słownika.** Indeksowane są rdzenie, nie formy, więc `notatka`,
   `notatki` i `notatkach` trafiają w to samo. Normalizowane są też oboczności spółgłoskowe
   z miejscownika: `projekcie` sprowadza się do `projekt`, `vaulcie` do `vault`.
2. **Foldery mają wagi** (`WAGI_FOLDEROW`). Dziennik i inbox to zwykle największa objętość
   tekstu w vaulcie i potrafią zalać wyniki, spychając notatki docelowe. Nie są wykluczone,
   tylko obniżone. Dopasuj nazwy folderów do swojego układu.
3. **Kwarantanna jest wykluczona** (`SKIP_DIRS`). Materiał odłożony do skasowania nie ma
   prawa wyjść jako źródło prawdy.
4. **Nazwa pliku i nagłówek sekcji podbijają wynik** (`BOOST_NAGLOWKA`), bo trafienie
   w tytuł jest mocniejszym sygnałem niż to samo słowo w środku akapitu.

Zmierzone na 12 zapytaniach kontrolnych w vaulcie z 327 notatek: trafienie w top 3 wzrosło
z 4/12 do 10/12, MRR z 0,271 do 0,725, a odmiana słowa przestała zmieniać wynik
(0 na 8 grup kontrolnych przed zmianą, 8 na 8 po).

## Jak uruchomić (dla Claude)
1. Jeśli plik `bm25_search.py` nie istnieje w katalogu roboczym sesji — zapisz go z bloku „Skrypt" poniżej.
2. **W Cowork katalog roboczy bash to folder outputs, nie vault.** Auto-detekcja działa tylko gdy skrypt stoi wewnątrz drzewa vaulta. Najpewniej: podaj `--vault` ze ścieżką zamapowaną w bash (patrz system reminder „Shell access" na starcie sesji) — zwykle ma postać `/sessions/<id>/mnt/Documents/<nazwa Twojego vaulta>`. Przykład: `python bm25_search.py "<pytanie>" --vault "/sessions/<id>/mnt/Documents/<nazwa Twojego vaulta>" --top 8`.
3. Zwróć użytkownikowi wynik z cytatami (plik › nagłówek). Najpierw vault-ask, dopiero potem ewentualnie doczytaj pełne pliki — oszczędza tokeny.

Flagi: `--top N`, `--full`.

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

SKIP_DIRS = {".obsidian", ".git", ".claude", "node_modules", "__pycache__",
             ".trash", "_kwarantanna"}
TOKEN_RE = re.compile(r"[a-ząćęłńóśźż0-9]+", re.IGNORECASE)

# Wagi folderow. Powod (pomiar 2026-08-26): Dziennik to 22% tekstu vaultu, _inbox kolejne
# 10%, i zalewaly wyniki, spychajac notatki docelowe. Nie wykluczamy ich, bo bywaja jedynym
# zrodlem, tylko obnizamy. Dopasowanie po pierwszym segmencie sciezki wzgledem vaultu.
WAGI_FOLDEROW = {
    "Archiwum": 0.3,
    "Dziennik": 0.5,
    "_inbox": 0.7,
}
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
    return WAGI_FOLDEROW.get(rel.split(os.sep)[0], 1.0)


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


def load_chunks(vault):
    chunks = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, vault)
            try:
                txt = open(full, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            nazwa = fn[:-3]
            waga = waga_folderu(rel)
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
    ap.add_argument("--full", action="store_true", help="pełna treść sekcji zamiast snippetu")
    a = ap.parse_args()

    vault = find_vault(a.vault)
    if not os.path.isdir(vault):
        print(f"BLAD: nie ma folderu vault: {vault}", file=sys.stderr)
        sys.exit(2)
    chunks = load_chunks(vault)
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
