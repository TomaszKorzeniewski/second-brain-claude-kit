# Second Brain Claude Kit

*(znane też jako **VALTOS**, jeśli wolisz krótszą nazwę)*

Zestaw sześciu umiejętności (skilli) do Claude i jedna rozmowa startowa, które razem
zamieniają Obsidiana w drugi mózg prowadzony przez Claude: dziennik, który pisze się
sam, kontekst, który wraca między sesjami bez recapu, wyszukiwanie po notatkach
bez zużywania tokenów, i (opcjonalnie) wyszukiwanie znaczeniowe, gdy słowa kluczowe
nie wystarczą.

To nie jest jeden gotowy przepis na wszystkich. To jest mój własny, realnie
używany od tygodni workflow, oddany w formie, którą możesz zainstalować i dostosować
do siebie w jedną rozmowę.

## Dla kogo

Dla każdego, kto pracuje z Claude i chce mieć obok solidną, prywatną bazę notatek
w Obsidianie, zamiast polegać na pamięci aplikacji albo historii czatu. Nieważne,
czy to praca, projekt osobisty, nauka czy uporządkowanie życia — rozmowa startowa
pyta Cię o to na wstępie i dopasowuje resztę.

## Co jest w środku

```
skille/
  zapisz/         zamknięcie sesji: dziennik + routing notatek do właściwych miejsc
  vault-ask/       lokalne wyszukiwanie po vaulcie (BM25 ze stemmingiem polskim, zero tokenów, zero API)
  vault-embed/     opcjonalna druga warstwa nad vault-ask: embedding lokalny + hybryda,
                   dla pytań opisowych bez wspólnych słów z notatką (patrz niżej)
  vault-hot/       szybki powrót do kontekstu na starcie sesji, bez recapu
  hot-slim/        kontrola budżetu pliku HOT.md, żeby nie spuchł bez kontroli
  vault-lint/      cotygodniowa higiena vaulta: martwe linki, sieroty, sprzeczności

onboarding-prompt.txt   rozmowa startowa z Claude, która buduje Twoją konfigurację
```

Wszystkie skille to zwykłe pliki tekstowe (`SKILL.md`), część z nich niesie w środku
mały skrypt w Pythonie. Pięć z sześciu to czysta biblioteka standardowa, zero zależności.
Wyjątek to `vault-embed`: dokłada lokalny model embeddingu (`onnxruntime` + `tokenizers`,
model pobierany raz, ok. 470 MB, potem działa offline). Nic z tego nie dzwoni do żadnego
zewnętrznego API poza samym Claude — `vault-embed` liczy się lokalnie na CPU Twojej maszyny.

## Jak zacząć

1. **Sklonuj albo pobierz to repo** do folderu, z którego korzysta Twój Claude.
2. **Otwórz nową rozmowę i wklej całą zawartość `onboarding-prompt.txt`.**
   Claude zada Ci pytania o to, jak pracujesz, ile masz notatek, czy żonglujesz
   kilkoma wątkami naraz czy jednym — i na tej podstawie zaproponuje, które
   z sześciu skilli realnie Ci się przydadzą. Nie każdy potrzebuje wszystkich sześciu.
3. **Zainstaluj wybrane skille** przez Settings → Skills → Add w aplikacji Claude,
   wskazując odpowiedni podfolder `skille/<nazwa>/SKILL.md`. `vault-embed` zainstaluj
   tylko jeśli faktycznie masz pytania, na które `vault-ask` nie trafia — wymaga
   jednorazowej instalacji pakietów Pythona i pobrania modelu, opisane w jego SKILL.md.
4. Rozmowa zbuduje Ci też gotowy tekst do pola `Instructions for Claude`
   (Settings → General) i powie, jaką rolę wybrać w polu `What best describes
   your work`.

Zajmie to 30-45 minut, jednym ciągiem. Rozbicie na kilka dni sprawia, że połowa
rzeczy zostaje niedokończona.

## Filozofia, w skrócie

- **Zero-token tam, gdzie się da.** `vault-ask`, `vault-lint`, `hot-slim` to czysty
  Python, bez modeli AI w środku. Szukanie po notatkach i sprzątanie vaulta nie
  powinno kosztować tokenów. Jedyny wyjątek to `vault-embed`: dokłada lokalny model
  (zero tokenów Claude, zero API, ale nie zero obliczeń — liczy się na Twoim CPU).
- **Skille żyją w Twoim vaulcie, nie tylko w aplikacji.** Jeśli kiedyś zmienisz
  narzędzie, zabierasz je ze sobą. Aplikacje AI się zmieniają, Twoje notatki zostają.
- **Dziennik jest logiem przelotnym, nie miejscem docelowym.** Trwałe decyzje
  dostają własną notatkę. Dziennik tylko pokazuje, co się działo i kiedy.
- **Nikt nie zgaduje za Ciebie.** Rozmowa startowa pyta, zamiast zakładać. Jeśli
  czegoś nie powiedziałeś, zostaje luka, nie wymyślona odpowiedź.

## Czego to NIE robi

Nie synchronizuje niczego z chmurą, nie wysyła Twoich notatek nigdzie poza Twoim
komputerem, nie zakłada konkretnej struktury folderów — to Ty i rozmowa startowa
ją ustalacie. Jeśli szukasz gotowej bazy wiedzy firmowej z automatyczną
synchronizacją, to inny projekt niż ten.

## Stan projektu

Wczesna wersja, w testach z pierwszymi użytkownikami. Struktura i nazwy mogą się
jeszcze zmienić.

## Kontakt

Tomasz Korzeniewski — [LinkedIn](https://www.linkedin.com/in/tomasz-korzeniewski-b590ba1b1)

## Licencja

MIT — rób z tym, co chcesz, adaptuj do siebie, nie musisz pytać o zgodę.
