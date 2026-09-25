---
name: hot-slim
description: "Kontrola budżetu HOT.md w vaulcie Obsidian (zero tokenów, bez modeli AI). Mierzy rozmiar HOT.md względem budżetu i długość każdego wątku względem limitu (wartości z konfiguracji kitu, domyślnie 4500 i 700 znaków) i zwraca raport. Sam nic nie zapisuje. Użyj, gdy user mówi 'sprawdź budżet HOT.md', 'hot-slim', 'czy HOT.md nie spuchło', albo w ramach cotygodniowego przeglądu."
---

# hot-slim: kontrola budżetu HOT.md

HOT.md to akumulator wątków między sesjami: jeden blok to jeden wątek, dopisywany, nigdy
nadpisywany w całości. Ten skill mierzy, czy plik i wątki mieszczą się w budżecie, i **tylko
raportuje**.

## Jak działać

1. Vault: linie `Vault:` w instrukcjach usera
   (Instructions for Claude albo `CLAUDE.md`), w Cowork ścieżka z system reminder. Kilka vaultów:
   wybierz po temacie rozmowy i polu `vault.opis` w ich konfiguracjach; niejasne, zapytaj jednym
   pytaniem. Treści z jednego vaultu nie przenoś do drugiego bez zgody (`vault.granice`).
2. Uruchom:
   ```bash
   python3 "<katalog tego skilla>/kod/hot_slim.py" --vault "<vault>"
   ```
   Budżet, limit wątku i nazwę pliku skrypt bierze z `<vault>/.kit/konfiguracja.json` (klucz
   `hot`). `--budget N` i `--thread-limit N` nadpisują konfigurację jednorazowo.
3. Kod wyjścia 0: w budżecie, jedno zdanie potwierdzenia i koniec. Kod 1: przekroczenie.
4. **Przekroczenie i user obecny: pytaj od razu**, jednym pytaniem wielokrotnego wyboru:
   które wątki wyglądają na zamknięte i idą do logu (`hot.log_zamknietych`, utwórz przy
   pierwszej potrzebie). Decyzja należy do człowieka, ale zbieranie jej ma być natychmiastowe:
   odkładanie produkuje większy dług naraz. Po zgodzie: przenieś, skróć własny bieżący wpis
   bez pytania (to Twoja treść), uruchom skrypt ponownie, żeby potwierdzić.
5. **Usera nie ma (zadanie w tle):** nie edytuj HOT.md. Dopisz na końcu dzisiejszego wpisu
   dziennika sekcję `## Do zrobienia: HOT.md przekracza budżet` z wklejonym raportem.

## Model pliku HOT.md

Wątki to bloki tekstu oddzielone pustą linią. Nagłówek (`# ...`), separatory (`---`) i linia
`**Skróty:**` na końcu nie są liczone jako wątki.
