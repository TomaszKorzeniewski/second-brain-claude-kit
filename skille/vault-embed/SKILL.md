---
name: vault-embed
description: "Wyszukiwanie po vaulcie Obsidian z warstwą znaczeniową: BM25 plus lokalny embedding (multilingual-e5-base przez onnxruntime, indeks SQLite). Krótkie zapytania idą do BM25, opisowe do wektora. Wszystko liczy się na tej maszynie, treść notatek nie wychodzi do żadnego API. Użyj, gdy pytanie jest opisowe i nie zawiera słów z notatki, albo gdy vault-ask nie trafił. Triggery: 'znajdź w vaulcie', 'o czym była notatka o', 'szukaj znaczeniowo', 'vault-embed'."
---

# vault-embed: druga warstwa nad BM25

BM25 dopasowuje słowa, embedding dopasowuje znaczenie. **Router, nie fuzja:** zapytanie do
2 słów idzie w całości do BM25 (nazwy własne, kody, pojedyncze terminy), dłuższe w całości do
wektora (pytania opisowe, parafrazy). Nadbudowa nad `vault-ask`, nie zamiennik.

**Prywatność.** Model chodzi lokalnie na CPU. Sieć dotyka tylko `pobierz_model.py`, jednorazowo,
po same wagi modelu z Hugging Face.

## Gdzie co leży

Katalog danych kitu: `~/.cache/second-brain-kit/` (zmiana: `KIT_DANE` albo
`wyszukiwanie.katalog_danych` w konfiguracji). Tam `venv/`, `model/` (ok. 1,1 GB) i `indeksy/`
(osobna baza SQLite na każdy vault, ok. 30 MB na 400 notatek). **Nie w vaulcie**, bo 1 GB nie
może jechać przez iCloud, i nie w folderze skilla, bo ten podmienia każda aktualizacja.

**Aplikacja Claude (Cowork):** bash chodzi w piaskownicy, jej `~/.cache` znika po sesji.
Ustaw `wyszukiwanie.katalog_danych` na folder wewnątrz folderu roboczego, ale poza vaultem
(np. `<folder roboczy>/.second-brain-kit`), i w komendach niżej podmień `~/.cache/second-brain-kit`
na tę ścieżkę. Venv zbudowany w piaskownicy działa tylko tam; na Macu poza Cowork zbuduj osobny.

## Instalacja (raz, ok. 10 minut plus budowa indeksu)

Zrób to za usera krok po kroku, pytając o zgodę przed pobraniem modelu (1,1 GB):

```bash
D=~/.cache/second-brain-kit; mkdir -p "$D"
python3 -m venv "$D/venv"
"$D/venv/bin/python" -m pip install onnxruntime tokenizers numpy
"$D/venv/bin/python" "<katalog tego skilla>/kod/pobierz_model.py"
"$D/venv/bin/python" "<katalog tego skilla>/kod/hybryda.py" --buduj --vault "<vault>"
```

Pierwsza budowa indeksu trwa długo (zmierzone: ok. 30 minut na 400 notatek na laptopie),
puść ją w tle. Mniejszy, słabszy model: `pobierz_model.py --model small` (470 MB).
Na koniec dopisz `vault-embed` do `skille` w `<vault>/.kit/konfiguracja.json`, żeby `zapisz`
odświeżał indeks.

## Jak uruchomić (dla Claude)

```bash
~/.cache/second-brain-kit/venv/bin/python "<katalog tego skilla>/kod/hybryda.py" "<pytanie>" --vault "<vault>" --top 8
```

Indeks nieświeży: przy dużej zmianie vaultu narzędzie ostrzega na stderr zamiast liczyć w locie.
Wtedy `--buduj` osobno, w tle. Skill `zapisz` robi to sam na koniec sesji.

Flagi: `--tryb bm25|wektor|hybryda|hybryda-rrf` (domyślnie hybryda, czyli router), `--top N`,
`--full`, `--folder <podfolder>`, `--buduj`, `--od-zera`, `--sprawdz` (kod 1, gdy indeks w tyle),
`--model <ścieżka>`.

## Zmierzone na realnym vaulcie autora (394 pliki, 16 zapytań kontrolnych)

| konfiguracja | top1 | top3 | top10 | MRR | fleksja |
|---|---|---|---|---|---|
| sam BM25 (`vault-ask`) | 8/16 | 12/16 | n/d | 0,654 | 7/8 |
| e5-small + fuzja RRF | 11/16 | 14/16 | 15/16 | 0,786 | 3/8 |
| **e5-base + router (domyślne)** | **12/16** | 14/16 | **16/16** | **0,822** | **7/8** |

Fuzja RRF z e5-base wypadła gorzej niż router (top1 8/16): mieszanie rankingów rozwadnia mocny
top1 wektora słabszym rankiem BM25. Dlatego router.

## Pułapka, która już raz ugryzła

Waga `typ` jest wspólna z BM25. Mnożnik powyżej 1.0 był nieszkodliwy dla BM25 (wyniki 5 do 40),
ale katastrofalny dla wektora (kosinus 0,7 do 0,95): top1 spadał z 12/16 do 4/16. Dlatego
żaden `typ` nie podbija ponad 1.0, może tylko obniżać. Nie zmieniaj tego bez pomiaru.
