---
name: vault-ask
description: "Lokalne wyszukiwanie po vaulcie Obsidian (BM25, bez modeli AI, bez tokenów). Użyj gdy trzeba znaleźć w vaulcie informacje na temat zamiast wczytywać całe pliki. Zwraca trafne fragmenty z cytatami (plik + nagłówek). Triggery: \"co wiemy o\", \"znajdź w vaulcie\", \"ask\", \"przeszukaj notatki\"."
---

# vault-ask — tanie wyszukiwanie po vaulcie (BM25)

Samodzielny skill: cały kod jest w tym pliku. Bez zależności (stdlib Pythona), bez tokenów.

> Auto-detekcja vaulta szuka folderu, którego nazwa ZAWIERA „obsidian" (nie musi być dokładnie
> „Obsidian" — pasuje np. „Jan w Obsidian", „MójDrugiMózg-Obsidian"). Jeśli Twój vault nazywa
> się inaczej, podawaj `--vault` jawnie.

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

SKIP_DIRS = {".obsidian", ".git", ".claude", "node_modules", "__pycache__"}
TOKEN_RE = re.compile(r"[a-ząćęłńóśźż0-9]+", re.IGNORECASE)


def find_vault(explicit=None):
    """Znajdz folder vaultu niezaleznie od miejsca skryptu (pod Cowork/replikacje).
    Dopasowuje dowolny folder, ktorego nazwa ZAWIERA 'obsidian' (np. 'Tomek w Obsidian'),
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
            for head, body in split_sections(txt, full):
                toks = tokenize(head + " " + body)
                if toks:
                    chunks.append(
                        {"rel": rel, "head": head, "body": body.strip(), "toks": toks}
                    )
    return chunks


def bm25_rank(chunks, query, k1=1.5, b=0.75):
    q = tokenize(query)
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
        if s > 0:
            scored.append((s, i))
    scored.sort(reverse=True)
    return scored


def snippet(body, query, full=False, width=320):
    if full:
        return body
    qset = set(tokenize(query))
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
