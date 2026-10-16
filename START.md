# START: instrukcja dla Claude

> **Człowieku, nic tu nie musisz czytać.** Wklej do nowej rozmowy z Claude jedno zdanie:
>
> `Zainstaluj albo zaktualizuj mi to: https://github.com/TomaszKorzeniewski/second-brain-claude-kit`
>
> Claude zrobi resztę. Ty odpowiadasz na pytania i klikasz „Zapisz” przy skillach.
> Najlepiej w Cowork, z podpiętym folderem, w którym pracujesz z Claude.

---

**Claude, ten plik jest dla Ciebie.** Prowadzisz człowieka od linku do działającego drugiego
mózgu. Ma klikać jak najmniej i nie musi znać żadnych pojęć technicznych. Mógł nigdy wcześniej
tego nie robić. Wszystko, co możesz zrobić sam, robisz sam.

Adres repo: `https://github.com/TomaszKorzeniewski/second-brain-claude-kit`
Pliki surowe: `https://raw.githubusercontent.com/TomaszKorzeniewski/second-brain-claude-kit/main/<ścieżka>`
Całe repo jako zip: `https://github.com/TomaszKorzeniewski/second-brain-claude-kit/archive/refs/heads/main.zip`

## Zasady prowadzenia (obowiązują cały czas)

1. Po polsku (albo w języku człowieka), krótko, bez żargonu. Bez długich myślników.
2. Najwyżej 3 pytania naraz. Czekasz na odpowiedź.
3. Każdy krok człowieka to jedna konkretna czynność: co kliknąć albo co napisać. Nigdy „skonfiguruj”.
4. Nic nie kasujesz, nie nadpisujesz i nie przenosisz bez „tak”. Najpierw pokazujesz plan.
5. Nie zgadujesz za człowieka. Czego nie powiedział, nie wpisujesz.
6. Coś nie działa? Mówisz wprost, co i dlaczego, i przechodzisz do planu B z kroku 2. Nie każesz
   człowiekowi szukać rozwiązania.

## Krok 1. Rozpoznanie (sam, bez pytań)

Sprawdź po cichu i pokaż wynik w maksymalnie 4 punktach:

- **Gdzie pracujesz:** czy masz narzędzie do zapisywania skilli z kartą do kliknięcia (np.
  `propose_skills`), czy masz terminal z zapisem do `~/.claude/skills/` (Claude Code), czy nic z tego.
- **Folder:** czy masz podpięty folder roboczy. Jeśli nie, poproś o podpięcie jednym zdaniem
  (w Cowork: przycisk dodania folderu) i wyjaśnij po co: tam będą notatki. Bez folderu da się
  zainstalować skille, ale nie da się ułożyć vaultu.
- **Stan kitu:** czy w folderze jest vault Obsidiana (folder z `.obsidian`) i plik
  `<vault>/.kit/konfiguracja.json`. Jest: przeczytaj `wersja_kitu` i `skille`.
  Porównaj z plikiem `VERSION` w repo. Czy na liście dostępnych skilli widzisz `zapisz` i inne
  skille kitu.
- **Zasady pracy:** czy w folderze jest `CLAUDE.md` i notatka z mapą folderu.

Z tego wybierasz tryb:

| sytuacja | tryb |
|---|---|
| brak konfiguracji i brak skilli kitu | **NOWY**: kroki 2, 3, 4, 5 |
| konfiguracja albo skille kitu są, wersja starsza niż w repo | **AKTUALIZACJA**: kroki 2 i 5 |
| wszystko aktualne | powiedz to jednym zdaniem |

**Prośba węższa wygrywa.** Człowiek prosi o konkretny skill („zaktualizuj `zapisz`”)? Robisz tylko
to: krok 2 dla tego skilla i krok 5. Pozostałe skille i krok 4 proponujesz na końcu jednym
zdaniem, bez nalegania. Krok 4 w trybie AKTUALIZACJA zawsze tylko proponujesz.

Powiedz człowiekowi, który tryb wybrałeś i ile to potrwa (NOWY: 30 do 45 min, AKTUALIZACJA: 5 do 10 min).

## Krok 2. Instalacja albo aktualizacja skilli

**Które skille.** Podstawa, bez instalowania czegokolwiek: `zapisz`, `vault-hot`, `vault-ask`,
`przetworz-zrodlo`, `kit-aktualizacja`. W trybie AKTUALIZACJA: te, które człowiek już ma, plus
`kit-aktualizacja`, jeśli go brak. Skille z wersji zaawansowanej (`vault-embed`, `vault-lint`,
`hot-slim`) tylko na wyraźną prośbę albo po rozmowie startowej, bo wymagają Pythona.

Wybierz pierwszą działającą drogę:

**Droga A, karta do kliknięcia (Cowork i aplikacja, jeśli masz takie narzędzie).** Pobierz
`skille/<nazwa>/SKILL.md` z plików surowych i zaproponuj każdy skill do zapisania w całości,
bez zmian (nazwa i opis z nagłówka pliku). Najwyżej 3 skille na jedną kartę. Powiedz: „Kliknij
Zapisz przy każdym skillu na karcie.” Przy aktualizacji karta zastępuje starą wersję. Stary skill
pochodzi z pluginu (karta go nie podmieni)? Powiedz to wprost i przejdź do drogi C.

**Droga B, terminal (Claude Code).** Za zgodą pobierz zip repo do katalogu tymczasowego,
skopiuj `skille/<nazwa>/` do `~/.claude/skills/<nazwa>/` (stary folder najpierw przenieś do
`~/.claude/skills/_stare/<data>/`, nie kasuj). Człowiek nic nie klika.

**Droga C, plan awaryjny.** Daj człowiekowi bezpośrednie linki do pobrania, jeden na skill:
`https://github.com/TomaszKorzeniewski/second-brain-claude-kit/raw/main/paczki/<nazwa>.zip`
i dokładne kroki: Settings, Capabilities, Skills, Upload skill, wskaż pobrany plik. Jeśli
aplikacja nie przyjmie pliku, bo skill o tej nazwie już jest: najpierw usuń stary w tym samym
miejscu, potem wgraj nowy. Jeden skill na raz, potwierdzasz każdy.

**Tryb AKTUALIZACJA, dodatkowo:** pobierz `CHANGELOG.md`. Dla wpisów nowszych niż `wersja_kitu`
pokaż najwyżej 5 jednym zdaniem każdy (co zyskuje człowiek). Pola `migracja` wykonaj w
`.kit/konfiguracja.json` za jedną zgodą na całość, potem ustaw `wersja_kitu` na wersję z repo.

## Krok 3. Rozmowa startowa (tylko tryb NOWY)

Pobierz `onboarding-prompt.txt` z plików surowych i prowadź według niego w tej samej rozmowie.
Repo nie leży obok? Wszędzie, gdzie prompt mówi o plikach repo (`paczki/`, `konfiguracja/`,
`skille/`), bierzesz je z plików surowych. Instalację skilli z jego części „Na koniec” już
zrobiłeś w kroku 2: dograj tylko to, co rozmowa dodatkowo wybrała, tą samą drogą.

## Krok 4. Folder roboczy, zasady pracy i mapy

Pobierz `PRZESTRZEN.md` z plików surowych i prowadź według niego. Pomiń, jeśli `CLAUDE.md`
i `Mapa folderu.md` już są i człowiek nie chce zmian.

## Krok 5. Sprawdzenie i koniec

Nowe skille działają w **nowej** rozmowie. Daj człowiekowi dokładnie to:

1. „Otwórz nową rozmowę (w tym samym folderze) i napisz: `Ustalmy testowo: spotkanie zespołu
   jest we wtorki o 9:00.`”
2. „Na końcu odpowiedzi powinna być linijka `💾 Zapisać? ...`. Odpowiedz `tak`.”
3. „Nie ma tej linijki? Wróć tutaj i napisz «nie ma», naprawimy.”

Na koniec w czacie najwyżej 5 punktów: co zainstalowane, gdzie są zasady i mapy, jak dopisać
nową zasadę (edycja `CLAUDE.md` w Obsidianie albo zdanie „dopisz to do zasad pracy”), że kolejne
wersje sprawdza zdanie „sprawdź aktualizacje”, i że na `💾 Zapisać?` wystarczy odpowiadać „tak”.

## Czego nie robisz

- Nie edytujesz treści skilli. Dopasowanie idzie do `.kit/konfiguracja.json` i notatek.
- Nie kopiujesz przykładów z tego pliku ani z promptu startowego do vaultu jako danych.
- Nie każesz człowiekowi niczego instalować (Python, git, terminal). To zawsze opcja, nie wymóg.
- Nie zostawiasz go z błędem bez następnego kroku.
