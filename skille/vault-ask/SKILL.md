---
name: vault-ask
description: "Tanie wyszukiwanie po vaulcie Obsidian: najpierw spis treści, potem tylko trafione fragmenty, zamiast wczytywania całych plików. Działa bez instalacji (wbudowane szukanie w plikach); z Pythonem dochodzi BM25 ze stemmingiem polskim, zero tokenów na samo szukanie. Zwraca fragmenty z cytatami (plik i nagłówek). Triggery: 'co wiemy o', 'znajdź w vaulcie', 'ask', 'przeszukaj notatki', 'co mam o'."
---

# vault-ask: tanie wyszukiwanie po vaulcie

Cel: odpowiedzieć z vaultu, czytając jak najmniej. Każdy wczytany plik to tokeny, więc szukasz
fragmentu, a pełny plik otwierasz dopiero, gdy fragment nie wystarczył.

## Jak szukać (dla Claude)

1. Vault: linie `Vault:` w instrukcjach usera
   (Instructions for Claude albo `CLAUDE.md`), w Cowork ścieżka z system reminder. Kilka vaultów:
   wybierz po temacie rozmowy i polu `vault.opis` w ich konfiguracjach; niejasne, zapytaj jednym
   pytaniem. Treści z jednego vaultu nie przenoś do drugiego bez zgody (`vault.granice`).
2. **Pytanie ogólne** („co mam o…”, „przegląd tematu”) i istnieje spis treści (`indeks.plik`,
   domyślnie `index.md`): przeczytaj najpierw spis, potem tylko wskazane strony.
3. **Pytanie konkretne:** wybierz tryb.
   - **Podstawowy, zawsze dostępny.** Wbudowane szukanie w plikach (grep, wyszukiwanie po treści
     i nazwach plików) po 2 do 3 słowach kluczowych i ich odmianach (`faktur`, nie `faktura`).
     Pomijaj `.obsidian`, `.kit`, `_kwarantanna` i notatki ze `status: obalone`. Z wyników czytaj
     tylko okolice trafienia (kilkanaście linii), nie całe pliki.
   - **Zaawansowany, gdy działa `python3`.** Ranking BM25 ze stemmingiem polskim, wagami folderów
     i pomijaniem obalonych, ok. 1 s na zapytanie:
     ```bash
     python3 "<katalog tego skilla>/kod/bm25_pl.py" "<pytanie>" --vault "<vault>" --top 8
     ```
     Flagi: `--top N`, `--full` (cała sekcja zamiast wycinka), `--folder <podfolder>` (szukaj
     tylko tam). Skrypt nie działa (brak Pythona, błąd): przejdź na tryb podstawowy bez dyskusji.
   - **Brak dostępu do plików** (zwykły czat bez narzędzi): poproś usera o wyszukanie w Obsidianie
     (Ctrl/Cmd+Shift+F) i wklejenie trafień. Nie zgaduj treści notatek.
4. Zwróć wynik z cytatami (plik › nagłówek), **zanim** doczytasz pełne pliki. Doczytuj tylko
   te, których fragment nie wystarczył. Nic nie znalazłeś: powiedz wprost, nie uzupełniaj z pamięci.

Odpowiedź była syntezą kilku notatek (porównanie, analiza)? Zaproponuj jednym zdaniem zapis
jako nową notatkę: dobre odpowiedzi to wiedza, nie historia czatu.

## Spis treści (opcjonalnie, wzorzec LLM Wiki)

Jeden plik z listą notatek i opisem w jednym zdaniu, pogrupowany po folderach, bez dziennika
i notatek obalonych. Na co dzień prowadzi go skill `zapisz` (linia na nową notatkę, bez
skryptu). Opłaca się do ok. 250 notatek (zmierzone: 321 notatek to ok. 8,5 tys. tokenów na
jedno czytanie); w większym vaultcie tańsze jest szukanie.

Wersja zaawansowana: skrypt składa cały spis od zera, np. przy starcie w vaultcie, który ma
już setki notatek. Zero tokenów, ale wymaga `python3`:

```bash
python3 "<katalog tego skilla>/kod/indeks.py" --vault "<vault>"            # podgląd i koszt w tokenach
python3 "<katalog tego skilla>/kod/indeks.py" --vault "<vault>" --zapisz   # zapis
```

Istniejącego pliku o tej nazwie, który nie powstał ze skryptu, skrypt nie nadpisze.

## Co tryb zaawansowany robi inaczej niż zwykły BM25

- Stemming polski bez słownika: `notatka` i `notatki` to to samo, `projekcie` to `projekt`.
- Kwarantanna, kopie zapasowe i foldery ukryte są poza indeksem.
- Notatki ze `status: obalone` nie wychodzą w wynikach: zostają w vaulcie jako historia decyzji.
- Wagi: dziennik, inbox i archiwum są obniżone (nie wykluczone), bo zalewają wyniki.
  Waga to niższa z wag folderu i pola `typ`, pomnożona przez wagę `status`.
- Boost za trafienie w nazwę pliku, nagłówek sekcji, `aliases` i `opis` z frontmattera.

## Dopasowanie do osoby

W `<vault>/.kit/konfiguracja.json`, klucz `wyszukiwanie`:
- `wagi_folderow`: np. `{"Stare projekty": 0.4}` obniża folder w wynikach,
- `pomijaj_foldery`: foldery całkiem poza indeksem.

Gdy user drugi raz narzeka, że jakiś folder „zaśmieca wyniki”, zaproponuj wpis w `wagi_folderow`.

## Zmierzone na realnym vaulcie autora (357 plików, 16 zapytań kontrolnych)

| metryka | wynik |
|---|---|
| top1 / top3 / MRR | 8/16, 12/16, 0,654 |
| fleksja (8 grup odmian) | 7/8 |
| czas jednego zapytania | ok. 1 s |

## Kiedy to nie wystarczy

BM25 dopasowuje słowa, nie znaczenie. Pytanie opisowe bez wspólnych słów z notatką („o czym
była ta rozmowa z klientem, który się wściekł”) to przypadek dla `vault-embed`, jeśli jest
zainstalowany. Jeśli nie jest, a takie pytania wracają, zaproponuj go jednym zdaniem.
