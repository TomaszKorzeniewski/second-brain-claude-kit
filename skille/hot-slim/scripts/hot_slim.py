#!/usr/bin/env python3
"""
hot_slim.py — kontrola budżetu HOT.md (zero-token, bez modeli AI).

Mierzy rozmiar HOT.md w vaulcie Obsidian i zgłasza przekroczenia budżetu.
NIC NIE ZAPISUJE — czysty raport. HOT.md jest append-only / one-line-per-thread,
decyzję co skrócić podejmuje człowiek.

Model pliku: HOT.md to lista "wątków" — bloków tekstu oddzielonych pustą linią,
każdy zaczyna się zwykle od pogrubienia (**...**) i kończy linkiem [[...]].
Nagłówek (#), separatory (---) i linia "Skróty:" na końcu nie są wątkami.

Użycie:
    python3 hot_slim.py --vault "/ścieżka/do/vaultu"
    python3 hot_slim.py --vault "/ścieżka/do/vaultu" --budget 4500 --thread-limit 700

Kod wyjścia: 0 = w budżecie, 1 = przekroczenie (budżetu całości lub któregoś wątku).
"""

import argparse
import os
import sys


def split_threads(content: str):
    """Dzieli treść HOT.md na wątki: bloki oddzielone pustą linią, z pominięciem
    nagłówka, separatorów '---' i linii 'Skróty:'."""
    blocks = [b.strip("\n") for b in content.split("\n\n")]
    threads = []
    for b in blocks:
        stripped = b.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            continue
        if stripped == "---" or set(stripped) == {"-"}:
            continue
        if stripped.startswith("**Skróty:**") or stripped.startswith("Skróty:"):
            continue
        threads.append(stripped)
    return threads


def main():
    parser = argparse.ArgumentParser(description="Kontrola budżetu HOT.md.")
    parser.add_argument("--vault", required=True, help="Ścieżka do korzenia vaultu Obsidian")
    parser.add_argument("--budget", type=int, default=4500, help="Budżet całkowity znaków (domyślnie 4500)")
    parser.add_argument("--thread-limit", type=int, default=700, help="Limit znaków na wątek (domyślnie 700)")
    args = parser.parse_args()

    hot_path = os.path.join(args.vault, "HOT.md")
    if not os.path.isfile(hot_path):
        print(f"BŁĄD: nie znaleziono {hot_path}")
        sys.exit(2)

    with open(hot_path, "r", encoding="utf-8") as f:
        content = f.read()

    total_chars = len(content)
    threads = split_threads(content)

    print(f"HOT.md: {hot_path}")
    print(f"Całość: {total_chars} znaków (budżet {args.budget})")
    print(f"Liczba wątków: {len(threads)} (limit {args.thread_limit} znaków/wątek)\n")

    over_budget_total = total_chars > args.budget
    over_threads = []

    for i, t in enumerate(threads, 1):
        n = len(t)
        first_line = t.split("\n", 1)[0][:70]
        flag = ""
        if n > args.thread_limit:
            flag = "  ⚠️ PRZEKROCZONY"
            over_threads.append((i, n, first_line))
        print(f"[{i:2}] {n:4} zn.{flag} | {first_line}")

    print()
    if over_budget_total or over_threads:
        print("=== RAPORT: PRZEKROCZENIE BUDŻETU ===")
        if over_budget_total:
            print(f"- Całość {total_chars} zn. > budżet {args.budget} zn. (nadwyżka {total_chars - args.budget} zn.)")
        for i, n, first_line in over_threads:
            print(f"- Wątek [{i}] ma {n} zn. > limit {args.thread_limit} zn. ({first_line})")
        print("\nNie edytuję HOT.md automatycznie — decyzję co skrócić podejmuje człowiek.")
        sys.exit(1)
    else:
        print("W budżecie. Nic do zrobienia.")
        sys.exit(0)


if __name__ == "__main__":
    main()
