# Second Brain Claude Kit

*(znane też jako **VALTOS**, jeśli wolisz krótszą nazwę)*

Moja propozycja drugiego mózgu w Obsidianie, zbudowana z myślą o Claude.

Osiem umiejętności (skilli) do Claude i jedna rozmowa startowa, które razem zamieniają
Obsidiana w drugi mózg prowadzony przez Claude: dziennik, który pisze się sam, kontekst,
który wraca między sesjami bez recapu, wyszukiwanie po notatkach bez wczytywania wszystkiego
i (opcjonalnie) wyszukiwanie znaczeniowe, gdy słowa kluczowe nie wystarczą.

**Baza rośnie z każdą rozmową.** Gdy w rozmowie pada decyzja, liczba albo działające
rozwiązanie, Claude sam proponuje zapis jedną linijką (`💾 Zapisać? ... (tak / nie)`).
Odpowiadasz „tak” i wiedza ląduje we właściwej notatce, zamiast przepaść w historii czatu.

**Nic nie trzeba instalować.** Podstawa kitu to same instrukcje dla Claude, bez Pythona,
terminala i bibliotek. Notatki to zwykłe pliki Markdown: czyta je Claude i czytasz je Ty.

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

## Dwa poziomy

| poziom | skille | czego wymaga |
|---|---|---|
| **podstawa** | `zapisz`, `vault-hot`, `przetworz-zrodlo`, `vault-ask` (tryb podstawowy) | nic, wgrywasz gotowe paczki z `paczki/` |
| **zaawansowany** | `vault-ask` (ranking BM25), `vault-embed`, `vault-lint`, `hot-slim`, przegląd w `kit-aktualizacja` | działający `python3`; `vault-embed` dodatkowo pakiety i model 1,1 GB |

Zaczynasz od podstawy. Rozmowa startowa sama sprawdzi, czy masz Pythona, i zaproponuje wersję
zaawansowaną tylko wtedy, gdy realnie coś Ci da. Bez niej kit działa w pełni.

## Co jest w środku

```
skille/
  zapisz/            zamknięcie sesji: dziennik, HOT.md, routing notatek do właściwych miejsc
  vault-ask/         wyszukiwanie po vaulcie (BM25, stemming polski, zero tokenów, zero API)
  vault-embed/       opcjonalnie: wyszukiwanie po znaczeniu, model lokalny na CPU
  vault-hot/         szybki powrót do kontekstu na starcie sesji
  hot-slim/          kontrola budżetu HOT.md, żeby nie spuchł
  vault-lint/        przegląd higieny: martwe linki, sieroty, sprzeczności
  kit-aktualizacja/  nowe wersje, przegląd dopasowania i doradztwo układu, tylko gdy chcesz
  przetworz-zrodlo/  źródło (artykuł, PDF, transkrypcja) do stron wiedzy, wiedza się kumuluje

paczki/                               gotowe zipy do wgrania w aplikacji, nic nie budujesz
konfiguracja/konfiguracja.wzor.json   wzór ustawień z opisem każdego pola
onboarding-prompt.txt                 rozmowa startowa (i menu przy powrocie)
CHANGELOG.md                          co się zmieniło, wpis po wpisie, do wyboru
narzedzia/zbuduj.py                   dla autorów: przebudowuje paczki po zmianie skilli
testy/test_kit.py                     dla autorów: test dymny skryptów na przykładowym vaulcie
```

Skrypty (tylko poziom zaawansowany) to czysty Python z biblioteką standardową. Wyjątek: `vault-embed` dokłada lokalny model
(`onnxruntime` + `tokenizers`, model pobierany raz, ok. 1,1 GB, potem offline). Nic nie wysyła
Twoich notatek do żadnego API poza samym Claude.

## Jak zacząć

1. **Pobierz repo**: zielony przycisk `Code`, potem `Download ZIP`, rozpakuj do folderu,
   z którego korzysta Twój Claude. Znasz gita? `git clone`, wtedy aktualizacje to jeden `git pull`.
2. **Otwórz nową rozmowę i wklej całą zawartość `onboarding-prompt.txt`.** Claude zapyta, jak
   pracujesz, ile masz notatek, czy żonglujesz kilkoma wątkami, i zaproponuje tylko te skille,
   które realnie Ci się przydadzą.
3. **Zainstaluj wybrane skille.** Rozmowa poda dokładne kroki: w aplikacji wgrywasz gotowy zip
   z `paczki/` w Settings, Capabilities, Skills; w Claude Code kopiuje się folder do
   `~/.claude/skills/`.
4. Rozmowa zbuduje też tekst do `Instructions for Claude` (albo `CLAUDE.md`), z linią
   `Vault: <ścieżka>`, z której korzystają skille.

Zajmuje to 30 do 45 minut, jednym ciągiem. Przerwana rozmowa wraca do bloku, na którym
skończyliście, bo postęp zapisuje się w konfiguracji.

## Jak to działa

Moja propozycja drugiego mózgu dedykowanego dla Claude. Zamiast za każdym razem szukać
w surowych dokumentach albo tłumaczyć wszystko od nowa, Claude raz przetwarza źródło czy wynik
rozmowy i wpisuje wiedzę do trwałych, połączonych notatek, które rosną z każdym źródłem i pytaniem.

| element | w kicie |
|---|---|
| surowe źródła, tylko do czytania | źródła w Twoim folderze, `przetworz-zrodlo` ich nie zmienia |
| notatki wiedzy pisane przez Claude | strony w folderach z Twojej mapy routingu |
| zasady | konfiguracja kitu, mapa routingu, Twoje instrukcje |
| wchłanianie wiedzy | `przetworz-zrodlo` (źródła) i `zapisz` (wnioski z rozmów) |
| pytania, dobre odpowiedzi wracają do vaultu | `vault-ask`, `vault-embed`, propozycja zapisu syntezy |
| porządki | `vault-lint`, w tym „pojęcia bez własnej strony” |
| spis treści i log | spis treści prowadzony przy zapisie, dziennik z nagłówkami `## [data] rodzaj \| tytuł` |

Do tego: wyszukiwanie po polsku, ochrona stron przejrzanych przez Ciebie (`sprawdzone: true`),
sprzeczności oznaczane zamiast rozstrzyganych po cichu i dopasowanie do Twojego układu.
Podobne podejścia, jeśli chcesz porównać: [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
i plugin Obsidiana [karpathywiki](https://community.obsidian.md/plugins/karpathywiki).

## Twój układ, nie mój

Kit nie zakłada żadnej struktury. Rozmowa startowa najpierw patrzy, co już masz, i od tego zaczyna:
- **kilka vaultów** (np. prywatny w iCloud, firmowy w OneDrive, projekt w Dropboxie): każdy ma
  własną konfigurację, opis „do czego służy” i granice, czego nie wolno z niego wynosić;
  Claude wybiera vault po temacie i pyta, gdy nie jest pewien,
- **dowolna chmura i dowolna ścieżka**, także ze spacjami i polskimi znakami,
- **Daily Notes z Obsidiana**: dziennik kitu pisze do tej samej notatki dnia, w Twoim folderze
  i formacie nazwy, zamiast tworzyć drugą,
- **istniejące foldery i metadane**: mapa routingu startuje z Twoich folderów, a Twoje pola
  we frontmatterze zostają,
- **doradztwo zamiast przymusu**: kit podpowiada, co ułatwi wyszukiwanie, embedding i oszczędzi
  tokeny (nagłówki w długich notatkach, spis treści, jedno miejsce na źródła), z zyskiem w jednym
  zdaniu. Powiesz „zostaw”, to zostaje i sugestia nie wraca.

Jak w samochodzie: fotel, lusterka i kierownicę ustawiasz pod siebie, a silnik jest wspólny
i dostaje poprawki od producenta.

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

- **Prosto i tanio.** Podstawa bez instalacji; Claude czyta spis treści i fragmenty, nie
  cały vault. Kto chce zejść z tokenami jeszcze niżej, dokłada skrypty z poziomu zaawansowanego.
- **Każda rozmowa coś zostawia.** Zapis proponuje się sam, Ty tylko mówisz „tak” albo „nie”.
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
   `narzedzia/zbuduj.py` rozkłada kopie do pozostałych skilli i przebudowuje `paczki/`.
   Paczki są w repo: commituj je razem ze zmianą skilli, bo user ich nie zbuduje sam.
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
