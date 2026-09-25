---
name: zapisz
description: "Zamknięcie sesji: wpis do dziennika, aktualizacja HOT.md (jeśli go używasz) i routing treści do właściwych notatek w vaulcie Obsidian. Użyj, gdy user mówi: 'zapisz', 'zamknij sesję', 'koniec sesji', 'save', 'zapisz stan', 'zamykamy', 'koniec na dziś', 'to tyle'. Zaproponuj zapis sam, gdy sesja jest długa albo wielotematyczna, nie czekaj na komendę."
---

# zapisz: zamknięcie sesji

Jeden command, do czterech kroków: dziennik, HOT.md, routing treści, odświeżenie indeksu.
Który krok działa i jak, mówi konfiguracja osoby, nie ten plik.

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

## Kiedy zapisywać: wcześnie, nie przy kompaktowaniu

Zapis zrobiony wcześnie bije zapis zrobiony kompletnie. Kompaktowanie odpala się przy pełnym
kontekście, czyli wtedy, gdy model widzi już własne streszczenia zamiast faktów, i zapis
robiony w tym momencie utrwala zniekształcenia, których nie widać.

1. Próg: około `zapis.procent_kontekstu` okna kontekstu (domyślnie 55%). Nie czekaj na
   komunikat o kompaktowaniu.
2. Naturalne momenty: domknięty wątek, zmiana tematu, koniec dnia na temacie.
3. Nie przerywaj wdrożenia w połowie: dokończ mikrokrok, potem zapisz.

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

## Sesja: <temat w 3-5 słowach>

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
4. Ustalenie, które sesja obaliła: zmień w starej notatce `status: obalone` i dopisz jedno zdanie,
   dlaczego. Nie kasuj: historia decyzji zostaje, wyszukiwarka po prostu jej nie zwraca.

## Krok 4: odśwież indeks vault-embed (tylko gdy zainstalowany)

Gdy w `skille` konfiguracji jest `vault-embed`, uruchom w tle:

```bash
~/.cache/second-brain-kit/venv/bin/python "<katalog skilla vault-embed>/kod/hybryda.py" --sprawdz --vault "<vault>"
```

Kod 0: indeks aktualny, koniec. Kod 1: odpal to samo z `--buduj` zamiast `--sprawdz`, w tle,
bez czekania. Nie blokuj zamknięcia sesji na tym kroku. Katalog skilla vault-embed: w Claude
Code zwykle `~/.claude/skills/vault-embed`, w aplikacji ścieżka z listy skilli. Inny katalog danych w
`wyszukiwanie.katalog_danych`: podmień początek ścieżki do Pythona.

## Na koniec

Jedno zdanie na krok: co powstało i gdzie. Bez podsumowania całej sesji drugi raz.

**Przypomnienie o aktualizacjach kitu, dobrowolne.** Tylko gdy `aktualizacje.tryb` =
`przypominaj` i od `aktualizacje.ostatnie_sprawdzenie` minęło więcej niż `aktualizacje.co_ile_dni`
(albo sprawdzenia nie było nigdy): dodaj jedną linię, np. „Minął miesiąc od sprawdzenia
aktualizacji kitu. Powiedz «sprawdź aktualizacje», jeśli chcesz.” Nie sprawdzaj sieci, nie
instaluj niczego. Tryb `na_zadanie`, `nigdy` albo brak konfiguracji: milcz w tym temacie.
