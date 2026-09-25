---
name: vault-ask
description: "Lokalne wyszukiwanie po vaulcie Obsidian (BM25 ze stemmingiem polskim, bez modeli AI, zero tokenów na samo szukanie). Użyj, gdy trzeba znaleźć w vaulcie informację na temat, zamiast wczytywać całe pliki. Zwraca trafne fragmenty z cytatami (plik i nagłówek). Triggery: 'co wiemy o', 'znajdź w vaulcie', 'ask', 'przeszukaj notatki'."
---

# vault-ask: tanie wyszukiwanie po vaulcie (BM25)

Czysty Python, biblioteka standardowa, działa offline. Kod leży w `kod/`, nie wchodzi do kontekstu.

## Jak uruchomić (dla Claude)

1. Vault: linie `Vault:` w instrukcjach usera
   (Instructions for Claude albo `CLAUDE.md`), w Cowork ścieżka z system reminder. Kilka vaultów:
   wybierz po temacie rozmowy i polu `vault.opis` w ich konfiguracjach; niejasne, zapytaj jednym
   pytaniem. Treści z jednego vaultu nie przenoś do drugiego bez zgody (`vault.granice`).
2. ```bash
   python3 "<katalog tego skilla>/kod/bm25_pl.py" "<pytanie>" --vault "<vault>" --top 8
   ```
3. Zwróć wynik z cytatami (plik › nagłówek), **zanim** doczytasz pełne pliki. Doczytuj tylko
   te, których fragment nie wystarczył.

Flagi: `--top N`, `--full` (cała sekcja zamiast wycinka), `--folder <podfolder>` (szukaj tylko
tam, np. gdy materiał dla zespołu nie może wyciągnąć notatek prywatnych).

## Co robi inaczej niż zwykły BM25

- Stemming polski bez słownika: `notatka` i `notatki` to to samo, `projekcie` to `projekt`.
- Kwarantanna, kopie zapasowe i foldery ukryte są poza indeksem.
- Notatki ze `status: obalone` nie wychodzą w wynikach: zostają w vaulcie jako historia decyzji.
- Wagi: dziennik, inbox i archiwum są obniżone (nie wykluczone), bo zalewają wyniki.
  Waga to niższa z wag folderu i pola `typ`, pomnożona przez wagę `status`.
- Boost za trafienie w nazwę pliku i nagłówek sekcji.

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
