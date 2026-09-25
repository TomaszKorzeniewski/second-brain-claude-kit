---
name: kit-aktualizacja
description: "Dobrowolne aktualizacje i przegląd dopasowania Second Brain Claude Kit. Pokazuje, co nowego w repo kitu (tylko dla zainstalowanych skilli), i sprawdza na liczbach z vaultu, czy ustawienia wciąż pasują do tego, jak user pracuje. Każda zmiana do wyboru osobno, nic nie instaluje się samo. Użyj, gdy user mówi 'sprawdź aktualizacje', 'co nowego w kicie', 'zaktualizuj kit', 'czy mój setup pasuje', 'dopasuj kit', 'przegląd kitu'."
---

# kit-aktualizacja: nowe wersje i przegląd dopasowania

Zasada nadrzędna: **user wybiera, Ty proponujesz.** Żadna zmiana nie wchodzi bez jego „tak”
dla tej konkretnej zmiany. „Pomiń” jest pełnoprawną odpowiedzią i zapamiętujesz ją na stałe,
żeby nie pytać drugi raz.

Skille kitu są generyczne, dopasowanie żyje w `<vault>/.kit/konfiguracja.json` i w notatkach
usera. Dlatego podmiana pliku skilla nigdy nie kasuje personalizacji. Jeśli zmiana wymaga
czegoś w konfiguracji, robisz to przez migrację opisaną we wpisie CHANGELOG, za zgodą.

## Krok 0: stan

1. Vault: ścieżka z instrukcji użytkownika (linia `Vault:`), w Cowork z system reminder.
2. Przeczytaj konfigurację. Brak pliku: ten user nie przeszedł rozmowy startowej. Zaproponuj
   ją (plik `onboarding-prompt.txt` z repo) albo utwórz konfigurację z
   `konfiguracja/konfiguracja.wzor.json`, pytając o wartości, których nie da się sprawdzić.

## Część A: co nowego w repo

1. Pobierz CHANGELOG:
   - `aktualizacje.folder_repo` ustawiony: `git -C "<folder>" pull --ff-only`, potem czytaj
     `CHANGELOG.md` stamtąd. Pull odrzucony (lokalne zmiany): powiedz o tym, nie wymuszaj.
   - inaczej: `curl -fsSL https://raw.githubusercontent.com/<właściciel>/<repo>/main/CHANGELOG.md`
     do katalogu tymczasowego, adres z `aktualizacje.zrodlo`.
   - Brak sieci: powiedz wprost i zakończ część A.
2. ```bash
   python3 "<katalog tego skilla>/kod/przeglad.py" --vault "<vault>" --zmiany "<CHANGELOG.md>"
   ```
   Wynik to JSON: `oczekujace` (wpisy do decyzji) i `nowe_skille_do_rozwazenia`.
3. Pokaż **maksymalnie 5 wpisów**, najnowsze najpierw. Każdy w jednej linii: tytuł, zysk jednym
   zdaniem, czy wymaga decyzji albo migracji. Resztę streść liczbą („i 3 drobniejsze”).
4. Zapytaj o każdy wpis: **wdrażam / pomijam na stałe / później**. Jedno pytanie wielokrotnego
   wyboru, nie pięć osobnych.
5. Nowe skille, których user nie ma: jedno zdanie, co dają. Bez naciskania.

## Część B: przegląd dopasowania

```bash
python3 "<katalog tego skilla>/kod/przeglad.py" --vault "<vault>" --dopasowanie
```

Każdy sygnał to propozycja z liczbą w uzasadnieniu (np. „412 notatek, brak vault-embed”).
Pokaż je tak samo jak w części A: maksymalnie 5, wybór per sygnał. Sygnały to hipotezy:
jeśli user mówi, że liczba myli (np. folder archiwalny zawyża licznik), przyjmij to i zaproponuj
dopisanie wyjątku do konfiguracji zamiast dyskusji.

## Wdrożenie wybranych zmian

Kolejność na każdą zmianę:
1. **Rollback najpierw.** Skopiuj obecną wersję dotkniętego skilla i konfiguracji do
   `<vault>/.kit/kopie/RRRR-MM-DD/`. Powiedz jednym zdaniem, jak wrócić (skopiować z powrotem).
2. **Pliki skilla:** z aktualnego repo (`folder_repo` albo pobrany zip gałęzi `main`) uruchom
   `python3 narzedzia/zbuduj.py`, potem zależnie od `instalacja.sposob`:
   - `claude-code`: skopiuj `skille/<nazwa>/` do `instalacja.folder_skilli` (zwykle `~/.claude/skills/`),
   - `aplikacja`: podaj ścieżkę `paczki/<nazwa>.zip` i dokładne kroki: Settings, Capabilities,
     Skills, usuń starą wersję, Upload skill, wskaż zip. Tego nie zrobisz za usera.
   Jeden plik skilla niesie wszystkie zmiany tego skilla do najnowszej wersji. Powiedz, jeśli
   razem z wybraną zmianą wchodzą inne, wcześniej pominięte.
3. **Migracja** (pole `migracja` we wpisie): nowe klucze konfiguracji dopisz z wartością
   domyślną, a o te z pola `decyzja` zapytaj. Notatek usera nie ruszaj bez osobnej zgody.
4. **Zapisz decyzje w konfiguracji:** id wdrożonych do `aktualizacje.wdrozone`, pominiętych do
   `aktualizacje.pominiete` („później” nie zapisujesz nigdzie), `ostatnie_sprawdzenie` na dziś.
   `wersja_kitu` podnieś do najnowszej dopiero, gdy w `oczekujace` nie zostało nic poza „później”.
5. Sprawdź, że działa: uruchom skrypt zaktualizowanego skilla raz na vaulcie usera.

## Tryb przypomnień

Na koniec zapytaj raz, czy tryb `aktualizacje.tryb` pasuje: `na_zadanie` (domyślny, tylko gdy
user sam zapyta), `przypominaj` (jedna linijka na koniec `zapisz` co `co_ile_dni`), `nigdy`.
Pytasz tylko przy pierwszym uruchomieniu tego skilla, potem nie.
