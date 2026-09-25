# Second Brain Claude Kit

*(znane też jako **VALTOS**, jeśli wolisz krótszą nazwę)*

Siedem umiejętności (skilli) do Claude i jedna rozmowa startowa, które razem zamieniają
Obsidiana w drugi mózg prowadzony przez Claude: dziennik, który pisze się sam, kontekst,
który wraca między sesjami bez recapu, wyszukiwanie po notatkach bez zużywania tokenów
i (opcjonalnie) wyszukiwanie znaczeniowe, gdy słowa kluczowe nie wystarczą.

To nie jest jeden przepis na wszystkich. To mój własny, realnie używany workflow, oddany
w formie, która **dopasowuje się do Ciebie**: przy starcie, w rozmowie, i potem, gdy zmienia
się to, jak pracujesz.

## Dla kogo

Dla każdego, kto pracuje z Claude i chce mieć obok prywatną bazę notatek w Obsidianie, zamiast
polegać na pamięci aplikacji albo historii czatu. Praca, projekt osobisty, nauka, uporządkowanie
życia: rozmowa startowa pyta o to na wstępie i dopasowuje resztę.

Działa w aplikacji Claude (Desktop, Cowork) i w Claude Code.

## Jak to jest zbudowane

Jedna zasada trzyma całość: **skille są wspólne, dopasowanie jest Twoje.**

| warstwa | gdzie | kto zmienia |
|---|---|---|
| skille (logika) | `skille/`, instalowane w Claude | aktualizacje kitu |
| Twoje ustawienia | `<vault>/.kit/konfiguracja.json` | rozmowa startowa, `kit-aktualizacja`, Ty |
| Twój profil i mapa folderów | zwykłe notatki w vaulcie | Ty, w Obsidianie |

Dlatego aktualizacja kitu podmienia skille i nie rusza Twoich ustawień ani notatek.
Konfiguracja jedzie razem z vaultem, więc działa na każdym komputerze, na którym go otwierasz.

## Co jest w środku

```
skille/
  zapisz/            zamknięcie sesji: dziennik, HOT.md, routing notatek do właściwych miejsc
  vault-ask/         wyszukiwanie po vaulcie (BM25, stemming polski, zero tokenów, zero API)
  vault-embed/       opcjonalnie: wyszukiwanie po znaczeniu, model lokalny na CPU
  vault-hot/         szybki powrót do kontekstu na starcie sesji
  hot-slim/          kontrola budżetu HOT.md, żeby nie spuchł
  vault-lint/        przegląd higieny: martwe linki, sieroty, sprzeczności
  kit-aktualizacja/  nowe wersje i przegląd dopasowania, tylko gdy chcesz

konfiguracja/konfiguracja.wzor.json   wzór ustawień z opisem każdego pola
onboarding-prompt.txt                 rozmowa startowa (i menu przy powrocie)
CHANGELOG.md                          co się zmieniło, wpis po wpisie, do wyboru
narzedzia/zbuduj.py                   buduje paczki .zip do instalacji
testy/test_kit.py                     test dymny wszystkich skryptów na przykładowym vaulcie
```

Skrypty to czysty Python z biblioteką standardową. Wyjątek: `vault-embed` dokłada lokalny model
(`onnxruntime` + `tokenizers`, model pobierany raz, ok. 1,1 GB, potem offline). Nic nie wysyła
Twoich notatek do żadnego API poza samym Claude.

## Jak zacząć

1. **Sklonuj repo** (`git clone`, wtedy aktualizacje to jeden `git pull`) albo pobierz zip
   do folderu, z którego korzysta Twój Claude.
2. **Otwórz nową rozmowę i wklej całą zawartość `onboarding-prompt.txt`.** Claude zapyta, jak
   pracujesz, ile masz notatek, czy żonglujesz kilkoma wątkami, i zaproponuje tylko te skille,
   które realnie Ci się przydadzą.
3. **Zainstaluj wybrane skille.** Rozmowa zbuduje paczki i poda dokładne kroki: w aplikacji
   wgrywasz zip w Settings, Capabilities, Skills; w Claude Code kopiuje się folder do
   `~/.claude/skills/`.
4. Rozmowa zbuduje też tekst do `Instructions for Claude` (albo `CLAUDE.md`), z linią
   `Vault: <ścieżka>`, z której korzystają skille.

Zajmuje to 30 do 45 minut, jednym ciągiem. Przerwana rozmowa wraca do bloku, na którym
skończyliście, bo postęp zapisuje się w konfiguracji.

## Jak kit się dopasowuje później

- **Wróć do rozmowy startowej**, kiedy chcesz. Przy istniejącej konfiguracji zamiast wywiadu
  dostajesz menu: zmień ustawienia, dodaj skill, przejdź jeden blok od nowa.
- **Powiedz „sprawdź aktualizacje”.** Skill `kit-aktualizacja` pokazuje nowe zmiany z tego repo,
  tylko dla skilli, które masz, każdą z jednym zdaniem o tym, co zyskujesz. Wybierasz: wdrażam,
  pomijam na stałe, później. Pominięte nie wracają.
- **Powiedz „czy mój setup pasuje”.** Ten sam skill liczy sygnały w vaulcie (liczba notatek,
  rytm dziennika, nieużywany HOT.md, notatki bez metadanych, foldery spoza mapy) i proponuje
  zmiany z liczbą w uzasadnieniu, np. „412 notatek, rozważ vault-embed”.
- **Nic nie dzieje się samo.** Domyślnie kit milczy o aktualizacjach, dopóki nie zapytasz.
  Możesz włączyć jedną linijkę przypomnienia raz na miesiąc albo wyłączyć temat całkiem.

## Filozofia, w skrócie

- **Zero tokenów tam, gdzie się da.** Szukanie, sprzątanie i przegląd dopasowania to czysty
  Python, bez modeli AI w środku.
- **Twoje notatki zostają Twoje.** Aplikacje AI się zmieniają, pliki Markdown zostają.
- **Dziennik jest logiem przelotnym, nie miejscem docelowym.** Trwałe decyzje dostają własną
  notatkę; dziennik pokazuje, co się działo i kiedy.
- **Nikt nie zgaduje za Ciebie.** Rozmowa pyta, zamiast zakładać. Luka jest lepsza niż
  wymyślona odpowiedź.
- **Zmiana to Twoja decyzja.** Kit proponuje z uzasadnieniem, Ty wybierasz.

## Czego to NIE robi

Nie synchronizuje niczego z chmurą, nie wysyła notatek poza Twój komputer, nie narzuca struktury
folderów i nie aktualizuje się samo. Jeśli szukasz firmowej bazy wiedzy z automatyczną
synchronizacją, to inny projekt.

## Dla autorów zmian

1. Kod wspólny edytuj w `wspolne/kit_konfig.py` i `skille/vault-ask/kod/bm25_pl.py`;
   `narzedzia/zbuduj.py` rozkłada kopie do pozostałych skilli.
2. `python3 testy/test_kit.py` musi przejść. Test vault-embed uruchamia się, gdy model jest pobrany.
3. `python3 narzedzia/zbuduj.py --sprawdz` pilnuje, żeby w skillach nie było ścieżek konkretnego
   komputera ani danych osobowych. Własne prywatne słowa dopisz do
   `narzedzia/.zakazane-lokalne.txt` (poza gitem).
4. Każda zmiana dla użytkowników dostaje wpis w `CHANGELOG.md` (format opisany na górze pliku)
   i podbicie `VERSION`.

## Kontakt

Tomasz Korzeniewski, [LinkedIn](https://www.linkedin.com/in/tomasz-korzeniewski-b590ba1b1)

## Licencja

MIT: rób z tym, co chcesz, adaptuj do siebie, nie musisz pytać o zgodę.
