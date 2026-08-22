---
name: vault-lint
description: "Higiena vaultu Obsidian bez modeli AI (martwe linki, sieroty, nieaktualne notatki, szkice/niekompletne, sprzeczności liczbowe, stan inboxu). Użyj przy cyklicznym przeglądzie/porządkowaniu vaultu albo gdy user pyta \"co wymaga sprzątania\". Tylko raport — nic nie zmienia, chyba że jawnie poproszone --fix-safe --apply."
---

# vault-lint — higiena vaultu (raport, bez zmian)

Samodzielny skill: cały kod jest w bloku „Skrypt" niżej, bez zależności poza standardową
biblioteką Pythona. Zapisz go raz gdzieś wygodnie w swoim vaulcie (np. w folderze na narzędzia
techniczne, jeśli taki masz) i uruchamiaj stamtąd, żeby nie tworzyć go od nowa co sesję.

## Jak uruchomić (dla Claude)

1. Jeśli plik `vault_lint.py` nie istnieje jeszcze w vaulcie usera — zapisz go z bloku
   „Skrypt" niżej w dowolnym stałym miejscu w vaulcie.
2. `python3 vault_lint.py --vault "<ścieżka do vaultu>" --max 25`
3. Pokaż raport użytkownikowi. Przy decyzjach o scaleniach/sierotach/sprzecznościach pytaj —
   skill tylko raportuje, nic nie usuwa ani nie scala sam.
4. `--fix-safe` (dry-run) i `--fix-safe --apply` (z backupem do `.vault-lint-backup/`) działają
   tylko na martwe linki z dokładnie jednym jednoznacznym kandydatem naprawy.

## Skrypt (kopia zapasowa, źródło prawdy to plik w vaulcie)

```python
#!/usr/bin/env python3
"""
vault_lint.py — higiena vaultu Obsidian (zero-token, bez modeli AI).

Sprawdza spójność wewnętrzną vaulta: pliki .md i wikilinki [[...]] między nimi.
Pięć klas znalezisk:
  1. Martwe linki   — wikilink wskazuje na notatkę .md, która nie istnieje.
  2. Sieroty        — notatka .md, do której nie prowadzi żaden wikilink z reszty vaulta
                       (poza naturalnymi wyjątkami: Dziennik/, _inbox/, Archiwum/).
  3. Nieaktualne    — notatka .md niemodyfikowana (mtime) od ponad 90 dni.
  4. Szkice         — notatka zawiera marker TODO/SZKIC/"do uzupełnienia" na starcie treści
                       lub w tytule.
  5. Sprzeczności   — ta sama "znana wartość" (np. budżet HOT.md w znakach) opisana różnymi
                       liczbami w różnych notatkach. Lista sprawdzanych faktów jest w
                       FACT_PATTERNS niżej — celowo krótka, dopisuj kolejne wzorce w miarę
                       potrzeby, to nie jest uniwersalny wykrywacz sprzeczności (na to trzeba
                       by modelu, nie regexu), tylko strażnik dla konkretnych, powtarzających
                       się liczb, które już raz się rozjechały.
Dodatkowo: stan Inboxu (ile plików .md leży bezpośrednio w _inbox/, jeśli folder istnieje).

Tryb domyślny: tylko raport na stdout. NIC nie zapisuje.

Tryb --fix-safe (domyślnie dry-run): dla każdego martwego linku szuka DOKŁADNIE JEDNEGO
kandydata — notatki, której znormalizowana nazwa zgadza się z celem linku — i pokazuje
podgląd naprawy (stary cel → nowy cel). Nic nie zmienia bez --apply.

Tryb --fix-safe --apply: rzeczywiście podmienia bezpieczne linki w plikach źródłowych
(zachowując alias |... i nagłówek #... z oryginału), po zrobieniu backupu KAŻDEGO
modyfikowanego pliku do <vault>/.vault-lint-backup/<RRRR-MM-DD>/<względna ścieżka>.
Nie usuwa plików, nie scala notatek, nie dopisuje nowych linków, nie zgaduje po treści.

Użycie:
    python3 vault_lint.py --vault "/ścieżka/do/vaultu"
    python3 vault_lint.py --vault "/ścieżka/do/vaultu" --max 20
    python3 vault_lint.py --vault "/ścieżka/do/vaultu" --fix-safe
    python3 vault_lint.py --vault "/ścieżka/do/vaultu" --fix-safe --apply

Kod wyjścia: 0 = czysto (brak znalezisk), 1 = są znaleziska, 2 = błąd (np. brak vaulta).
"""

import argparse
import datetime
import os
import re
import shutil
import sys
import unicodedata

BACKUP_DIR_NAME = ".vault-lint-backup"
STALE_DAYS = 90
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(#[^\]|]*)?(\|[^\]]*)?\]\]")
DRAFT_MARKERS = ("todo", "do uzupełnienia", "szkic", "[szkic]")
EXEMPT_ORPHAN_DIRS = ("dziennik", "_inbox", "archiwum")
FENCE_RE = re.compile(r"^\s*```")
# Placeholdery używane w dokumentacji/instrukcjach jako przykład składni linku, nie prawdziwe cele.
PLACEHOLDER_TARGETS = {
    "nazwa notatki", "tytuł notatki", "cel", "link", "embed", "alias", "nagłówek",
    "przykład", "rrrr-mm-dd", "...", "notatka", "nazwa", "temat",
}

# Znane fakty, których wartość liczbowa powinna być spójna w całym vaulcie.
# Każdy wzorzec musi mieć DOKŁADNIE jedną grupę przechwytującą (liczbę).
# Znalezisko z 2026-08-22: budżet HOT.md opisany jako 4000 w SKILL.md skilla `zapisz`
# i jako 4500 w skillu `hot-slim` oraz w pamięci sesji — realna sprzeczność, niewykrywalna
# starymi czterema klasami, bo obie wartości są "poprawnym" tekstem, tylko się nie zgadzają.
FACT_PATTERNS = [
    ("budżet HOT.md (znaki)", re.compile(r"bud[żz]et\D{0,20}?(\d[\d\s]{2,6})\s*znak", re.IGNORECASE)),
]


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def norm_name(s: str) -> str:
    """Znormalizowana nazwa do porównań: NFC, lowercase, przycięte spacje."""
    return nfc(s).strip().lower()


def iter_md_files(vault: str):
    """Zwraca listę (ścieżka_bezwzględna, ścieżka_względna) dla wszystkich .md,
    pomijając katalog backupu."""
    result = []
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d != BACKUP_DIR_NAME and not d.startswith(".git")]
        rel_root = os.path.relpath(root, vault)
        if rel_root != "." and (rel_root == BACKUP_DIR_NAME or rel_root.startswith(BACKUP_DIR_NAME + os.sep)):
            continue
        for f in files:
            if f.lower().endswith(".md"):
                abspath = os.path.join(root, f)
                relpath = os.path.relpath(abspath, vault)
                result.append((abspath, relpath))
    return result


def read_text(path: str):
    """Czyta plik jako tekst, ignorując błędy dekodowania. Zwraca None jeśli nie da się."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def extract_links(content: str):
    """Zwraca listę (cel_surowy, nagłówek, alias, pozycja_linii) z treści.
    Pomija linki wewnątrz bloków kodu (```...```) i linki owinięte w inline code
    (`` `[[...]]` ``) — to zwykle przykłady składni w dokumentacji, nie prawdziwe cele."""
    links = []
    in_fence = False
    for i, line in enumerate(content.split("\n"), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in WIKILINK_RE.finditer(line):
            start, end = m.span()
            if start > 0 and end < len(line) and line[start - 1] == "`" and line[end] == "`":
                continue  # `[[...]]` inline code — przykład, nie prawdziwy link
            target, heading, alias = m.group(1), m.group(2) or "", m.group(3) or ""
            target = target.strip()
            if norm_name(target) in PLACEHOLDER_TARGETS:
                continue
            links.append((target, heading, alias, i))
    return links


def build_name_index(md_files):
    """Mapa: znormalizowana nazwa pliku (bez .md) -> lista relpath (dla wykrywania
    duplikatów nazw w różnych folderach)."""
    idx = {}
    for abspath, relpath in md_files:
        base = os.path.basename(relpath)
        stem = base[:-3] if base.lower().endswith(".md") else base
        key = norm_name(stem)
        idx.setdefault(key, []).append(relpath)
    return idx


def target_stem(target: str) -> str:
    """Cel linku Obsidian rozwiązywany po samej nazwie pliku, niezależnie od folderu.
    Odetnij ewentualny prefiks folderu (Obsidian i tak dopasowuje po basename)."""
    t = target.strip()
    if "/" in t:
        t = t.rsplit("/", 1)[-1]
    if t.lower().endswith(".md"):
        t = t[:-3]
    return t


def is_non_md_target(target: str) -> bool:
    """True jeśli link wskazuje na plik z rozszerzeniem inne niż .md (np. .py, .png)."""
    t = target.strip()
    base = t.rsplit("/", 1)[-1] if "/" in t else t
    if "." not in base:
        return False
    ext = base.rsplit(".", 1)[-1].lower()
    return ext not in ("",) and ext != "md" and 1 <= len(ext) <= 5 and ext.isalnum()


def is_exempt_orphan(relpath: str) -> bool:
    parts = [p.lower() for p in relpath.split(os.sep)]
    return any(p in EXEMPT_ORPHAN_DIRS for p in parts[:-1])


def find_contradictions(file_contents: dict):
    """Dla każdego wzorca w FACT_PATTERNS: zbiera (relpath, wartość, fragment) ze wszystkich
    plików, i jeśli padło więcej niż jedna odrębna wartość (po usunięciu spacji z liczby),
    zwraca to jako sprzeczność. Zwraca listę (etykieta, [(relpath, wartość, fragment), ...])."""
    results = []
    for label, pattern in FACT_PATTERNS:
        hits = []
        for relpath, content in file_contents.items():
            for m in pattern.finditer(content):
                value = re.sub(r"\s+", "", m.group(1))
                start = max(0, m.start() - 20)
                end = min(len(content), m.end() + 10)
                fragment = content[start:end].replace("\n", " ").strip()
                hits.append((relpath, value, fragment))
        distinct_values = {v for _, v, _ in hits}
        if len(distinct_values) > 1:
            results.append((label, hits))
    return results


def find_draft_marker(content: str, title: str):
    head = content[:500].lower()
    title_l = title.lower()
    for marker in DRAFT_MARKERS:
        if marker in head or marker in title_l:
            return marker
    return None


def do_report(vault: str, max_examples: int, fix_safe: bool, apply_fix: bool):
    md_files = iter_md_files(vault)
    if not md_files:
        print(f"BŁĄD: brak plików .md w vaulcie {vault}")
        return 2

    name_index = build_name_index(md_files)  # klucz -> [relpath,...]
    all_stems = set(name_index.keys())

    now = datetime.datetime.now()
    linked_targets = set()  # znormalizowane stemy, do których prowadzi jakiś link

    dead_links = []       # (src_relpath, linia, cel_surowy)
    fix_candidates = []   # (src_relpath, linia, cel_surowy, nagłówek, alias, nowy_cel_relpath)

    file_contents = {}

    for abspath, relpath in md_files:
        content = read_text(abspath)
        if content is None:
            print(f"UWAGA: pomijam nieczytelny plik: {relpath}")
            continue
        file_contents[relpath] = content
        links = extract_links(content)
        for target, heading, alias, lineno in links:
            if is_non_md_target(target):
                continue
            stem = target_stem(target)
            key = norm_name(stem)
            linked_targets.add(key)
            if key not in all_stems:
                dead_links.append((relpath, lineno, target))
                # kandydat do fix-safe: dokładnie jedno globalnie unikatowe dopasowanie
                candidates = name_index.get(key, [])
                if len(candidates) == 1:
                    fix_candidates.append((relpath, lineno, target, heading, alias, candidates[0]))

    # Sieroty
    orphans = []
    orphans_exempt = []
    for abspath, relpath in md_files:
        base = os.path.basename(relpath)
        stem = base[:-3] if base.lower().endswith(".md") else base
        key = norm_name(stem)
        if key not in linked_targets:
            if is_exempt_orphan(relpath):
                orphans_exempt.append(relpath)
            else:
                orphans.append(relpath)

    # Nieaktualne
    stale = []
    for abspath, relpath in md_files:
        try:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(abspath))
        except OSError:
            continue
        age_days = (now - mtime).days
        if age_days > STALE_DAYS:
            stale.append((relpath, age_days))

    # Szkice
    drafts = []
    for abspath, relpath in md_files:
        content = file_contents.get(relpath)
        if content is None:
            continue
        title = os.path.basename(relpath)[:-3]
        marker = find_draft_marker(content, title)
        if marker:
            drafts.append((relpath, marker))

    # Sprzeczności liczbowe
    contradictions = find_contradictions(file_contents)

    # Inbox
    inbox_dir = os.path.join(vault, "_inbox")
    inbox_count = None
    if os.path.isdir(inbox_dir):
        inbox_count = sum(
            1 for f in os.listdir(inbox_dir)
            if f.lower().endswith(".md") and os.path.isfile(os.path.join(inbox_dir, f))
        )

    # ---- Raport ----
    print(f"Vault: {vault}")
    print(f"Notatek .md: {len(md_files)}\n")

    print(f"=== 1. Martwe linki: {len(dead_links)} ===")
    for relpath, lineno, target in dead_links[:max_examples]:
        print(f"  {relpath}:{lineno} -> [[{target}]]")
    if len(dead_links) > max_examples:
        print(f"  ... i {len(dead_links) - max_examples} więcej")
    print()

    print(f"=== 2. Sieroty: {len(orphans)} (+ {len(orphans_exempt)} wyjątków: Dziennik/_inbox/Archiwum) ===")
    for relpath in orphans[:max_examples]:
        print(f"  {relpath}")
    if len(orphans) > max_examples:
        print(f"  ... i {len(orphans) - max_examples} więcej")
    print()

    print(f"=== 3. Nieaktualne (>{STALE_DAYS} dni): {len(stale)} ===")
    for relpath, age_days in sorted(stale, key=lambda x: -x[1])[:max_examples]:
        print(f"  {relpath} ({age_days} dni)")
    if len(stale) > max_examples:
        print(f"  ... i {len(stale) - max_examples} więcej")
    print()

    print(f"=== 4. Szkice / do uzupełnienia: {len(drafts)} ===")
    for relpath, marker in drafts[:max_examples]:
        print(f"  {relpath} (marker: {marker})")
    if len(drafts) > max_examples:
        print(f"  ... i {len(drafts) - max_examples} więcej")
    print()

    print(f"=== 5. Sprzeczności liczbowe: {len(contradictions)} ===")
    for label, hits in contradictions:
        wartosci = sorted({v for _, v, _ in hits})
        print(f"  {label}: znalezione wartości {wartosci}")
        for relpath, value, fragment in hits[:max_examples]:
            print(f"    {relpath} = {value}  (…{fragment}…)")
    if not contradictions:
        print("  (brak — ale sprawdzanych wzorców jest tylko kilka, patrz FACT_PATTERNS)")
    print()

    if inbox_count is not None:
        print(f"=== Stan Inboxu: {inbox_count} plików .md bezpośrednio w _inbox/ ===\n")
    else:
        print("=== Stan Inboxu: folder _inbox/ nie istnieje w tym vaulcie ===\n")

    exit_code = 1 if (dead_links or orphans or stale or drafts or contradictions) else 0

    if fix_safe:
        print(f"=== --fix-safe: bezpieczni kandydaci do naprawy: {len(fix_candidates)} ===")
        for src, lineno, old_target, heading, alias, new_relpath in fix_candidates[:max_examples]:
            new_stem = os.path.basename(new_relpath)
            if new_stem.lower().endswith(".md"):
                new_stem = new_stem[:-3]
            print(f"  {src}:{lineno}  [[{old_target}{heading}{alias}]]  ->  cel: {new_stem}")
        if len(fix_candidates) > max_examples:
            print(f"  ... i {len(fix_candidates) - max_examples} więcej")

        no_candidates = len(dead_links) - len(fix_candidates)
        print(f"  (pozostałe {no_candidates} martwych linków: 0 lub >1 kandydatów, zostawiam)")
        print()

        if apply_fix and fix_candidates:
            today = datetime.date.today().isoformat()
            backup_root = os.path.join(vault, BACKUP_DIR_NAME, today)
            # grupuj po pliku źródłowym
            by_file = {}
            for src, lineno, old_target, heading, alias, new_relpath in fix_candidates:
                by_file.setdefault(src, []).append((lineno, old_target, heading, alias, new_relpath))

            changed_files = 0
            changed_links = 0
            for relpath, items in by_file.items():
                abspath = os.path.join(vault, relpath)
                content = file_contents.get(relpath)
                if content is None:
                    continue
                # backup przed modyfikacją
                backup_path = os.path.join(backup_root, relpath)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(abspath, backup_path)

                new_content = content
                for lineno, old_target, heading, alias, new_relpath in items:
                    new_stem = os.path.basename(new_relpath)
                    if new_stem.lower().endswith(".md"):
                        new_stem = new_stem[:-3]
                    old_link = f"[[{old_target}{heading}{alias}]]"
                    new_link = f"[[{new_stem}{heading}{alias}]]"
                    if old_link in new_content:
                        new_content = new_content.replace(old_link, new_link)
                        changed_links += 1

                if new_content != content:
                    with open(abspath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    changed_files += 1

            print(f"ZASTOSOWANO: {changed_links} linków naprawionych w {changed_files} plikach.")
            print(f"Backup oryginałów: {backup_root}")
        elif apply_fix:
            print("Brak bezpiecznych kandydatów — nic do zastosowania.")
        else:
            print("(To był tylko podgląd. Użyj --fix-safe --apply, żeby faktycznie naprawić.)")
        print()

    if exit_code == 0:
        print("Vault czysty. Nic do zrobienia.")
    else:
        print("=== RAPORT: są znaleziska (patrz sekcje wyżej) ===")

    return exit_code


def main():
    parser = argparse.ArgumentParser(
        description="Higiena vaultu Obsidian: martwe linki, sieroty, nieaktualne, szkice, sprzeczności liczbowe, stan inboxu."
    )
    parser.add_argument("--vault", required=True, help="Ścieżka do korzenia vaultu Obsidian")
    parser.add_argument("--max", type=int, default=40, help="Limit przykładów na kategorię w raporcie (domyślnie 40)")
    parser.add_argument("--fix-safe", action="store_true", help="Pokaż/napraw bezpieczne kandydaty do naprawy martwych linków")
    parser.add_argument("--apply", action="store_true", help="Razem z --fix-safe: rzeczywiście zapisz naprawy (z backupem)")
    args = parser.parse_args()

    if not os.path.isdir(args.vault):
        print(f"BŁĄD: nie znaleziono vaulta pod {args.vault}")
        sys.exit(2)

    if args.apply and not args.fix_safe:
        print("BŁĄD: --apply wymaga --fix-safe")
        sys.exit(2)

    code = do_report(args.vault, args.max, args.fix_safe, args.apply)
    sys.exit(code)


if __name__ == "__main__":
    main()
```
