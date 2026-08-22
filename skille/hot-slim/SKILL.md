---
name: hot_slim
description: Kontrola budżetu HOT.md w vaulcie Obsidian (zero-token, bez modeli AI). Mierzy całkowity rozmiar HOT.md względem budżetu (domyślnie 4500 znaków) i długość każdego wątku względem limitu (domyślnie 700 znaków), zwraca raport. Skrypt sam nic nie zapisuje, HOT.md jest append-only, ale przy przekroczeniu i obecnym userze pytaj go od razu (AskUserQuestion), co przenieść do logu zamkniętych, zamiast tylko zostawiać TODO. Użyj gdy user mówi "sprawdź budżet HOT.md", "hot_slim", "czy HOT.md nie spuchło", albo w ramach cotygodniowego zadania dziennik-maintenance.
---

# hot_slim — kontrola budżetu HOT.md

## Cel

`HOT.md` to akumulator wątków między sesjami (jeden wpis = jeden wątek, append-only,
nigdy nie nadpisywany całościowo). Ten skill mierzy, czy plik i poszczególne wątki
mieszczą się w budżecie, i **tylko raportuje** — nie edytuje pliku.

## Kiedy używać

- Cotygodniowe zadanie `dziennik-maintenance`, krok 2 (kontrola budżetu HOT.md).
- Na żądanie: "sprawdź HOT.md", "czy hot nie spuchło", "hot_slim".

## Jak działać

1. Znajdź korzeń vaultu Obsidian (folder zawierający `HOT.md`).
2. Uruchom skrypt:
   ```bash
   python3 scripts/hot_slim.py --vault "<ścieżka do vaultu>"
   ```
   Opcjonalnie: `--budget <N>` (domyślnie 4500) i `--thread-limit <N>` (domyślnie 700).
3. Skrypt wypisuje: całkowitą liczbę znaków, listę wątków z długością każdego, i na
   końcu raport przekroczeń (jeśli są). Kod wyjścia 0 = w budżecie, 1 = przekroczenie.
4. **Jeśli jest przekroczenie i user jest obecny w tej samej rozmowie: pytaj od razu.**
   `AskUserQuestion` z listą wątków, które wyglądają na zamknięte/nieaktualne, multiSelect.
   Decyzja co przenieść do notatki z logiem zamkniętych wątków (utwórz ją przy pierwszej
   potrzebie, jeśli user jeszcze takiej nie ma) należy do człowieka, ale zbieranie jej ma
   być natychmiastowe, nie odłożone na później: czekanie
   produkuje wielogodzinne opóźnienie i większy dług do spłacenia naraz. Po zgodzie: skróć
   własny/bieżący wpis bez pytania (to Twoja treść), przenieś zaakceptowane wątki do logu,
   zweryfikuj ponownym uruchomieniem skryptu.
   **Jeśli usera nie ma (np. zadanie w tle, `dziennik-maintenance`):** nie edytuj `HOT.md`
   sam. Dopisz notatkę (np. na końcu dziennika dnia) z wklejonym raportem, pod nagłówkiem
   `## Do zrobienia: HOT.md przekracza budżet, patrz raport hot_slim.py`.
5. Jeśli w budżecie — jedno zdanie potwierdzenia wystarczy, nic więcej nie rób.

## Model pliku HOT.md

Wątki to bloki tekstu oddzielone pustą linią, zwykle zaczynające się od pogrubienia
(`**...**`) i kończące linkiem `[[...]]`. Nagłówek (`# ...`), separatory (`---`) i
linia `**Skróty:**` na końcu nie są liczone jako wątki.
