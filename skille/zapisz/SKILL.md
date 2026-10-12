---
name: zapisz
description: "Zapis wiedzy z rozmowy do vaultu Obsidian, żeby drugi mózg rósł z każdą sesją: dziennik, HOT.md (jeśli używany), notatki docelowe i spis treści. Dwa tryby. Pełny zapis, gdy user mówi: 'zapisz', 'zamknij sesję', 'koniec sesji', 'save', 'zapisz stan', 'zamykamy', 'koniec na dziś', 'to tyle'. Mikrozapis, czyli jedna pozycja do jednej notatki, gdy user przyjmie propozycję zapisu. PROAKTYWNIE: po każdym ustalonym wyniku (decyzja, liczba, działające rozwiązanie, obalona hipoteza, dobra analiza), także po pierwszej albo drugiej wymianie, zaproponuj zapis jedną linijką, nie czekaj na prośbę. Działa bez instalowania czegokolwiek."
---

# zapisz: wiedza z rozmowy trafia do vaultu

**Po co to jest.** Vault ma rosnąć z każdą rozmową: decyzja, liczba, działające rozwiązanie albo
dobra analiza, która zostaje tylko w historii czatu, przepada przy następnej sesji. Ten skill
pilnuje, żeby nie przepadła, i robi to sam, bez proszenia. Im więcej trafi do vaultu, tym mniej
trzeba tłumaczyć Claude od nowa i tym mniej tokenów kosztuje każda kolejna rozmowa.

**Bez skryptów.** Wszystko poniżej to zwykły odczyt i zapis plików Markdown. Nic nie trzeba
instalować. Jedyny krok ze skryptem (krok 4, indeks wektorowy) dotyczy tylko osób z wersją
zaawansowaną i bez niej jest pomijany.

Dwa tryby: **mikrozapis** (jedna pozycja do jednej notatki, w trakcie rozmowy) i **pełny zapis**
(kroki 1 do 4, na koniec sesji). Który krok działa i jak, mówi konfiguracja osoby, nie ten plik.

## Krok 0: wczytaj konfigurację (zawsze pierwszy)

1. Vault: linie `Vault:` w instrukcjach usera
   (Instructions for Claude albo `CLAUDE.md`), w Cowork ścieżka z system reminder. Kilka vaultów:
   wybierz po temacie rozmowy i polu `vault.opis` w ich konfiguracjach; niejasne, zapytaj jednym
   pytaniem. Treści z jednego vaultu nie przenoś do drugiego bez zgody (`vault.granice`).
2. Przeczytaj `<vault>/.kit/konfiguracja.json`. Liczą się klucze: `osoba.jezyk`, `dziennik`,
   `routing.mapa`, `hot`, `frontmatter`, `zapis`.
3. **Brak pliku to nie błąd.** Działaj na wartościach domyślnych (w nawiasach niżej) i na końcu
   zapytaj jednym zdaniem, czy utworzyć konfigurację: bez niej każde `zapisz` zgaduje od nowa.

Pisz w języku z `osoba.jezyk` (domyślnie język, w którym pisze user).

## Kiedy zapisywać: proponuj sam, nie czekaj na „zapisz”

Zapis zrobiony wcześnie bije zapis zrobiony kompletnie. Pod koniec długiej rozmowy model widzi
już własne streszczenia zamiast faktów, a zapis robiony wtedy utrwala zniekształcenia, których
nie widać. Model nie widzi też, ile kontekstu zużył, więc reguła „zapisz przy połowie” w praktyce
nie działa. Działa za to propozycja po każdym wyniku.

Wyłącznik: `zapis.proponuj` = false (domyślnie true). Wtedy zapisujesz tylko na prośbę.

### Propozycja po ustalonym wyniku (od pierwszej wymiany)

Gdy w odpowiedzi pada wynik, którego user szukał, dopisz na końcu tej odpowiedzi **jedną linijkę**.
Wynik to: decyzja z uzasadnieniem, zmierzona albo policzona liczba, działające rozwiązanie
(komenda, ustawienie, adres, procedura), obalona hipoteza albo odrzucona ścieżka, nowa reguła
współpracy, porównanie albo analiza, o którą user prosił.

Format, zawsze ten sam, żeby dało się odpowiedzieć jednym słowem:

```
💾 Zapisać? <co, max 12 słów> → <gdzie: notatka albo HOT.md> (tak / nie / gdzie indziej)
```

Zasady:
1. Nie proponuj drobiazgów: odpowiedź na jednorazowe pytanie, rzecz już zapisana, coś, co
   łatwo odtworzyć z pliku. Lepiej jedna trafna propozycja na sesję niż pięć pustych.
2. Najwyżej jedna propozycja na odpowiedź. Kilka wyników naraz: jedna linijka z listą po przecinku.
3. Wynik odrzucony („nie”) nie wraca w tej sesji.
4. User nie odpowiedział i pisze dalej o czym innym: nie ponawiaj, wynik trafi do pełnego zapisu.
5. Propozycja to pytanie, nie akcja. Bez „tak” nic nie zapisujesz.
6. Miejsce wskazuj konkretnie, wg mapy routingu (krok 3). Nie wiesz, gdzie: zaproponuj notatkę
   i folder, user poprawi jednym słowem.

**„Tak” = mikrozapis**, nie pełne zamknięcie sesji:
1. Jedna pozycja do jednej notatki docelowej wg kroku 3 (dopisz sekcję z datą albo utwórz
   notatkę z frontmatterem).
2. Nowa notatka i jest spis treści: dopisz jej linię (krok 4a).
3. Wątek będzie żył dłużej niż kilka dni i `hot.uzywam` = true: zaktualizuj jego linię w HOT.md
   (zasady kroku 2).
4. Jedna linijka do dzisiejszego wpisu dziennika: `- [[Notatka]]: co dopisano` (utwórz wpis
   z szablonu, jeśli go nie ma).
5. Potwierdź jednym zdaniem: co i gdzie. Wracasz do tematu rozmowy.

### Pełny zapis: kiedy zaproponować

Domknięty wątek, zmiana tematu, koniec dnia na temacie, rozmowa wyraźnie długa (dziesiątki
wymian albo kilka tematów naraz). Format:
`💾 Robię pełny zapis (dziennik, notatki, spis treści)? (tak / nie)`.
Nie przerywaj pracy w połowie: dokończ bieżący krok, potem zaproponuj.

## Krok 1: dziennik

Ścieżka: `<vault>/<dziennik.folder>/RRRR/<nazwa>.md` (domyślnie `Dziennik`, podfolder roku gdy
`dziennik.podfolder_roku` = true), nazwa wg `dziennik.format_nazwy` (domyślnie `YYYY-MM-DD`,
składnia jak w Obsidian Daily Notes). Jeśli user używa Daily Notes, to jest ta sama notatka dnia:
dopisujesz do niej, nie tworzysz drugiej. Jeśli plik dnia istnieje, **dopisz** nową sekcję sesji na
końcu. Nigdy nie nadpisuj istniejącego wpisu.

Szablon nowego pliku. Blok YAML jest częścią szablonu, gdy `dziennik.frontmatter` = true
(domyślnie tak): wpis dziennika prawie zawsze zawiera ustalenia, które później trzeba odróżnić
od obalonych, a bez `status` wyszukiwarka tego nie zrobi.

```markdown
---
typ: log
status: aktualne
data: RRRR-MM-DD
tagi: []
---
# Dziennik: RRRR-MM-DD

## [RRRR-MM-DD] sesja | <temat w 3-5 słowach>

**Co zrobiliśmy:**
- ...

**Decyzje:**
- ...

**Czego NIE robić:**
- Ścieżka sprawdzona i odrzucona, powód w jednym zdaniu

**Następny krok:**
- ...

---
```

Zasady:
- Nagłówek sesji ma stały prefiks `## [RRRR-MM-DD] sesja | `, jak wpisy skilla
  `przetworz-zrodlo` (`źródło |`). Historię da się wtedy wyciągnąć jednym `grep "^## \["`.
- Konkretnie: co, gdzie, jaki wynik. Bez ogólników typu „rozmawialiśmy o projekcie”.
- Linkuj notatki, które powstały albo zmieniły się: `[[Nazwa notatki]]`.
- **Sekcja „Czego NIE robić” jest obowiązkowa, gdy w sesji coś odrzuciliśmy** (hipoteza obalona,
  narzędzie ocenione na nie, obejście, które nie zadziałało). Bez niej następna sesja wchodzi
  w tę samą ścianę. Gdy nic nie odrzuciliśmy, usuń sekcję zamiast wpisywać „brak”.
  Wyłącznik: `zapis.sekcja_czego_nie_robic` = false.
- Dopisując sesję do istniejącego pliku, sprawdź, czy blok YAML jest na górze; brak, to dopisz.
- **Dziennik jest logiem przelotnym, nie miejscem docelowym.** Decyzja ważna dłużej niż tydzień
  idzie do własnej notatki (krok 3), a w dzienniku zostaje link do niej.

## Krok 2: HOT.md (tylko gdy `hot.uzywam` = true)

Gdy `hot.uzywam` = false albo brak konfiguracji i brak pliku HOT.md: pomiń ten krok w całości.
HOT.md ma sens przy wielu równoległych wątkach; przy jednym wątku naraz wystarczy dziennik.

HOT.md (`hot.plik`, domyślnie `HOT.md` w korzeniu vaultu) to **żyjący log**, nie jednorazowy
pointer nadpisywany co sesję. Nadpisanie całego pliku kasuje historię, na której opierają się
kolejne sesje. Nie rób tego.

1. Aktualizuj tylko linie tematów z tej sesji; resztę zostaw bez zmian.
2. Każda linia, którą dopisujesz albo zmieniasz, kończy się `(stan na RRRR-MM-DD)`. Linii, których
   nie ruszasz, nie przepisuj tylko po to, żeby dodać datę.
3. Kryterium, co trafia do HOT: wątki, do których wróci się w ciągu kilku dni. Reszta żyje
   w dzienniku i notatkach docelowych.
4. Wątek zamknięty przenieś do `hot.log_zamknietych` (utwórz przy pierwszej potrzebie).
5. Po zapisie sprawdź rozmiar (`wc -c`). Powyżej `hot.budzet_znakow` (domyślnie 4500) **nie
   przycinaj sam**: pokaż, które wątki są najdłuższe, i zapytaj od razu, co przenieść do logu.
   Skill `hot-slim` robi ten pomiar dokładnie.

## Krok 3: routing treści do notatek docelowych

Dla każdego tematu z sesji zdecyduj, gdzie trafia, na podstawie mapy osoby.

**Mapa: czytaj, nie zgaduj.** Ścieżka w `routing.mapa` (domyślnie `Meta/Mapa routingu.md`).
To tabela `Temat | Folder docelowy`, własna dla każdego vaultu. Nie ma tu gotowej tabeli
i nie wymyślaj jej. Brak mapy: zapytaj krótko o główne obszary (praca, projekty, dom, zdrowie,
nauka) i zapisz odpowiedź jako tę notatkę, żeby nie pytać drugi raz.

Zasady routingu:
1. Istnieje notatka na ten temat: **dopisz** sekcję z datą, nie twórz duplikatu.
   Sprawdź najpierw skillem `vault-ask`, jeśli jest zainstalowany.
2. Nie istnieje: utwórz w folderze z mapy. Temat nie pasuje do żadnego wiersza: zapytaj,
   dokąd, i dopisz nowy wiersz do mapy.
3. **Frontmatter od pierwszej wersji pliku**, gdy `frontmatter.wymagany` = true: pola z
   `frontmatter.pola`, wartości `typ` i `status` z list w konfiguracji. `status` i `data` nigdy puste.
4. **Dobre odpowiedzi wracają do vaultu.** Porównanie, analiza albo synteza, o którą user prosił
   w tej sesji, to wiedza, nie historia czatu: zaproponuj jednym zdaniem zapis jako notatkę.
5. **Notatka ze `sprawdzone: true`** jest przejrzana przez usera: nie zmieniaj jej treści,
   dopisz na końcu sekcję `## Do przejrzenia` z propozycją.
6. Ustalenie, które sesja obaliła: zmień w starej notatce `status: obalone` i dopisz jedno zdanie,
   dlaczego. Nie kasuj: historia decyzji zostaje, wyszukiwarka po prostu jej nie zwraca.

## Krok 4: spis treści i indeks

### 4a. Spis treści (gdy `indeks.uzywam` = true), bez skryptu

Spis treści (`indeks.plik`, domyślnie `index.md` w korzeniu vaultu) to mapa vaultu dla Claude
i dla człowieka: przy pytaniu ogólnym czyta się jeden plik zamiast kilkunastu. Prowadzisz go
zwykłą edycją, linia po linii, tylko dla notatek ruszonych w tej sesji:
1. Nowa notatka: dopisz linię pod nagłówkiem jej folderu (brak nagłówka, dodaj go):
   `- [[Nazwa notatki]] (typ): <opis w jednym zdaniu>`. Opis z pola `opis` we frontmatterze; brak pola,
   napisz zdanie sam i wpisz je też jako `opis` do notatki.
2. Notatka dostała `status: obalone` albo `archiwum`: usuń jej linię.
3. Zmieniona nazwa: popraw link w linii.
4. Nie przepisuj całego pliku i nie czytaj przy tym innych notatek. To ma kosztować kilka linii.
5. Pliku jeszcze nie ma: utwórz go tak (znacznik w komentarzu pozwala skryptowi z wersji
   zaawansowanej przebudować spis od zera), potem dopisuj tylko nowe notatki:
   ```markdown
   ---
   typ: mapa
   status: aktualne
   data: RRRR-MM-DD
   tagi: [indeks]
   ---
   <!-- spis treści kitu (second-brain-claude-kit) -->
   # Spis treści vaultu

   Mapa notatek: jedna linia na notatkę. Opis notatki zmieniasz polem `opis` w jej frontmatterze.
   ``` Starych nie dociągaj hurtem; przy setkach notatek to zrobi skrypt z wersji
   zaawansowanej (`vault-ask`, `kod/indeks.py --zapisz`), o ile user go ma.

### 4b. Indeks wektorowy (tylko wersja zaawansowana, gdy w `skille` jest `vault-embed`)

Uruchom w tle:

```bash
~/.cache/second-brain-kit/venv/bin/python "<katalog skilla vault-embed>/kod/hybryda.py" --sprawdz --vault "<vault>"
```

Kod 0: indeks aktualny, koniec. Kod 1: odpal to samo z `--buduj` zamiast `--sprawdz`, w tle,
bez czekania. Nie blokuj zamknięcia sesji na tym kroku. Katalog skilla vault-embed: w Claude
Code zwykle `~/.claude/skills/vault-embed`, w aplikacji ścieżka z listy skilli. Inny katalog danych w
`wyszukiwanie.katalog_danych`: podmień początek ścieżki do Pythona. Brak `vault-embed`: pomiń 4b.

## Na koniec

Jedno zdanie na krok: co powstało i gdzie. Bez podsumowania całej sesji drugi raz.

**Przypomnienie o aktualizacjach kitu, dobrowolne.** Tylko gdy `aktualizacje.tryb` =
`przypominaj` i od `aktualizacje.ostatnie_sprawdzenie` minęło więcej niż `aktualizacje.co_ile_dni`
(albo sprawdzenia nie było nigdy): dodaj jedną linię, np. „Minął miesiąc od sprawdzenia
aktualizacji kitu. Powiedz «sprawdź aktualizacje», jeśli chcesz.” Nie sprawdzaj sieci, nie
instaluj niczego. Tryb `na_zadanie`, `nigdy` albo brak konfiguracji: milcz w tym temacie.
