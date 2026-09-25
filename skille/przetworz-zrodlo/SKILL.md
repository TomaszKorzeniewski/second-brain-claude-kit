---
name: przetworz-zrodlo
description: "Wchłania źródło (artykuł, PDF, transkrypcję, notatkę ze spotkania, rozdział książki) do vaultu Obsidian wg wzorca LLM Wiki: źródło zostaje nietknięte, a wiedza z niego trafia do stron o osobach, firmach, pojęciach i tematach, z linkami, aliasami i oznaczonymi sprzecznościami. Użyj, gdy user mówi 'przetwórz', 'dodaj to źródło', 'wchłoń', 'ingest', 'wrzuć to do wiki', albo wkleja link lub plik do przyswojenia."
---

# przetworz-zrodlo: źródło do wiki, wiedza się kumuluje

Wzorzec z „LLM Wiki” Andreja Karpathy'ego: zamiast szukać w surowych dokumentach przy każdym
pytaniu, raz przetwarzasz źródło i wpisujesz wiedzę do trwałych, połączonych stron. Kolejne
źródła te strony wzbogacają, a nie tworzą obok nich nowych stosów.

Trzy warstwy, ale **w układzie usera, nie narzuconym**:
- **źródła**: surowy materiał, tylko do czytania (`zrodla.folder` w konfiguracji, jeśli ustawiony),
- **strony wiedzy**: notatki o osobach, firmach, pojęciach, tematach, w folderach z mapy routingu,
- **zasady**: konfiguracja kitu, mapa routingu i instrukcje usera.

## Krok 0: stan

1. Vault: linie `Vault:` w instrukcjach usera, w Cowork ścieżka z system reminder. Kilka vaultów:
   wybierz po temacie źródła i `vault.opis`; niejasne, zapytaj. Nie przenoś treści między vaultami.
2. Przeczytaj konfigurację (`<vault>/.kit/konfiguracja.json`): `zrodla`, `routing.mapa`,
   `frontmatter`, `dziennik`, `indeks`. Brak: działaj na wartościach domyślnych.

## Krok 1: przeczytaj źródło, niczego w nim nie zmieniaj

- Plik w vaultcie: czytaj. **Nigdy go nie edytuj, nie przenoś i nie zmieniaj nazwy.** Źródło
  jest dowodem, do którego wracają linki.
- Link: pobierz treść (skill do stron WWW, jeśli jest). Ustawiony `zrodla.folder`: zapisz tam
  kopię w Markdown z `url:` i datą pobrania, żeby link nie przepadł.
- PDF, obrazy: skill do PDF-ów albo odczyt obrazów. Duże źródło czytaj partiami.

## Krok 2: omów, zanim zapiszesz (tryb domyślny)

Pokaż 3 do 5 najważniejszych wniosków ze źródła, po jednym zdaniu, i zapytaj, co podkreślić,
a co pominąć. User chce szybciej? `zrodla.tryb` = `wsadowo`: pomiń ten krok, ale na końcu pokaż
pełną listę zmian.

## Krok 3: znajdź istniejące strony

Dla każdej osoby, firmy, produktu, pojęcia i tematu ze źródła sprawdź, czy strona już jest:
skill `vault-ask` (szuka też po `aliases`), a przy ogólnym temacie najpierw spis treści
(`indeks.plik`), jeśli istnieje. Lepiej dopisać do istniejącej strony niż utworzyć duplikat.

## Krok 4: zapisz

1. **Strona źródła** (jedna na źródło): streszczenie, kluczowe fakty z cytatami (krótkimi),
   lista stron, których dotyczy. Frontmatter: `typ: zrodlo`, `status`, `data`, `tagi`, plus
   `zrodlo:` (ścieżka albo URL) i `opis:` (jedno zdanie do spisu treści).
2. **Strony wiedzy**: istniejąca, dopisz sekcję `## Z <tytuł źródła> (RRRR-MM-DD)` z nowymi
   faktami i linkiem do strony źródła. Brak strony: utwórz ją w folderze z mapy routingu, z
   `aliases` (skrót, tłumaczenie, inna pisownia) i `opis`. Temat bez folderu w mapie: zapytaj.
3. **Strona ze `sprawdzone: true` we frontmatterze** jest przejrzana przez usera. Nie zmieniaj
   jej treści. Dopisz na końcu sekcję `## Do przejrzenia` z propozycją i źródłem.
4. **Sprzeczność** (nowe źródło mówi co innego niż strona): nie wybieraj zwycięzcy po cichu.
   Dopisz w obu miejscach blok:
   ```markdown
   > [!warning] Sprzeczność
   > [[Strona A]] mówi X (źródło, data), [[Źródło B]] mówi Y (data). Do rozstrzygnięcia.
   ```
   Ustalenie, które user uzna za nieaktualne, dostaje `status: obalone` (zostaje jako historia).
5. **Limit**: jedno źródło dotyka zwykle 5 do 15 stron. Więcej: zapisz najważniejsze 15,
   resztę wypisz jako propozycje do kolejnego przebiegu.

## Krok 5: spis treści i log

1. Spis treści istnieje (`indeks.plik`): odśwież go skryptem skilla `vault-ask`
   (`kod/indeks.py --zapisz`). Nie edytuj spisu ręcznie.
2. Dopisz do dzisiejszego wpisu dziennika (format ze skilla `zapisz`):
   ```markdown
   ## [RRRR-MM-DD] źródło | <tytuł źródła>
   - strona źródła: [[...]]
   - nowe strony: [[...]], [[...]]
   - uzupełnione: [[...]], [[...]]
   - sprzeczności: [[...]] (albo usuń tę linię)
   ```
   Stały prefiks nagłówka pozwala wyciągnąć historię jednym `grep "^## \["`.

## Na koniec

Jedno zdanie: ile stron nowych, ile uzupełnionych, ile sprzeczności. Wypisz linki.
Jeśli w źródle padło pytanie, na które warto poszukać dalej, zaproponuj je jednym zdaniem.
