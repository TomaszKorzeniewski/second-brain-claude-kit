# PRZESTRZEŃ: folder roboczy, zasady pracy i mapy

> **Człowieku, to jest do przeczytania, ale nie musisz nic robić ręcznie.** Wklej do nowej rozmowy
> z Claude (Cowork, z podpiętym folderem, w którym pracujesz):
>
> `Ustaw mi przestrzeń roboczą według: https://raw.githubusercontent.com/TomaszKorzeniewski/second-brain-claude-kit/main/PRZESTRZEN.md`
>
> Zajmuje 30 do 40 minut. Ty odpowiadasz na pytania i zatwierdzasz „tak”. Nic nie znika:
> Claude niczego nie kasuje ani nie przenosi bez Twojej zgody.

## Co dostajesz i po co

Claude jest tak dobry, jak to, co wie o Twojej pracy, i tak przewidywalny, jak jasne są zasady.
Ta konfiguracja daje mu trzy rzeczy, które czyta przy każdej rozmowie:

1. **Zasady pracy** (`CLAUDE.md`): jak ma odpowiadać, czego nie robi bez pytania. Koniec z długimi
   wywodami i plikami odłożonymi „gdzieś”.
2. **Porządek plików**: wejście, praca, wyjście. Wrzucasz plik, mówisz „wrzuciłem nowe pliki”,
   wynik zawsze leży w tym samym miejscu.
3. **Wiedzę o firmie w notatkach**: strony spółek, osób, procesów i decyzji w Obsidianie. Claude
   pisze je i aktualizuje sam, Ty je czytasz i poprawiasz. Każda rozmowa zaczyna się od tego,
   co już ustalono, a nie od tłumaczenia wszystkiego od nowa.

Działa na czystym Obsidianie, bez instalowania czegokolwiek. Ze skillem `zapisz` z tego kitu
notatki rosną same po każdej rozmowie; bez niego Claude zapisuje na prośbę.

---

**Claude, dalej jest dla Ciebie.** Ustawiasz człowiekowi przestrzeń, na której będzie pracował
codziennie. Liczy się użyteczność, nie efekt. Każdy plik, który tworzysz, ma odpowiadać na
pytanie, które człowiek albo Ty będziecie zadawać w pracy. Czego nikt nie przeczyta, nie twórz.

## Zasady prowadzenia

1. Po polsku (albo w języku człowieka), krótko, bez żargonu, bez długich myślników.
2. Najwyżej 3 pytania naraz. Czekasz na odpowiedź.
3. Nic nie kasujesz, nie nadpisujesz i nie przenosisz bez „tak”. Najpierw plan, potem zmiana.
4. Nie zgadujesz. Czego człowiek nie powiedział, nie wpisujesz. Puste pole jest lepsze niż zmyślone.
5. Istniejące ustalenia rozbudowujesz, nie dublujesz. Jedna rzecz ma jedno miejsce.

## Krok 1. Rozpoznanie (sam, bez pytań)

Przejrzyj podpięty folder i pokaż wynik w najwyżej 5 punktach:

- co jest w folderze (foldery pierwszego poziomu, mniej więcej ile plików),
- gdzie jest vault Obsidiana (folder z `.obsidian`), ile ma notatek, jakie foldery,
- co już jest z kitu: `.kit/konfiguracja.json`, `Jak ze mną pracować.md`, `Mapa routingu.md`,
  spis treści (`indeks.plik` w konfiguracji, domyślnie `index.md`), `Dziennik/`, `CLAUDE.md`,
- które skille masz na liście dostępnych (zwłaszcza `zapisz`, `przetworz-zrodlo`).

Brak folderu: poproś o podpięcie jednym zdaniem (w Cowork przycisk dodania folderu) i czekaj.
Brak vaultu: zaproponuj podfolder `obsidian/` i powiedz, że w Obsidianie wystarczy potem
„Open folder as vault” i wskazać ten folder.

## Krok 2. Układ folderu

Docelowo (nazwy dopasuj do tego, co człowiek już ma, zamiast budować obok):

| Folder | Co tam leży | Kto pisze |
|---|---|---|
| `wejscie/` | pliki od człowieka: eksporty, PDF-y, arkusze, maile. **Oryginały, nie edytujesz ich.** | człowiek |
| `praca/<temat>/` | robota w toku, pliki pośrednie, jeden folder na zadanie | Claude |
| `wyjscie/<obszar>/` | gotowe wyniki dla człowieka | Claude |
| `_archiwum/` | zamknięte tematy, do wglądu | Claude za zgodą |
| `_kwarantanna/` | rzeczy do usunięcia, z `MANIFEST.md`: co, skąd, jak odtworzyć | Claude za zgodą |
| `obsidian/` | vault, wiedza (krok 4) | Claude i człowiek |
| `CLAUDE.md` | zasady pracy (krok 3) | oboje |

Zapytaj, czy wyniki dzielić na obszary (spółki, działy, klienci). Pokaż plan, czekaj na „tak”,
utwórz. Istniejących plików nie przenoś w tym kroku; zaproponuj przeniesienie osobno, z listą.

## Krok 3. Zasady pracy (`CLAUDE.md`)

Zadaj pytania (najwyżej 3 naraz):

1. Długość odpowiedzi: sam wynik, wynik z jednym zdaniem uzasadnienia, czy pełny wywód?
2. Gdy się mylisz: mam mówić wprost czy łagodnie?
3. Przed większym zadaniem: plan do zatwierdzenia czy od razu działanie?
4. Co Cię najbardziej irytuje w odpowiedziach AI?
5. Czego nigdy nie robię bez pytania (np. wysyłka, kasowanie, zmiany widoczne dla innych)?

Napisz `CLAUDE.md` w głównym folderze roboczym, najwyżej ok. 70 linii. Jeśli jest
`Jak ze mną pracować.md`, nie przepisuj go: zostaw tam szczegóły stylu, a w `CLAUDE.md` daj
odnośnik. Pokaż, czekaj na „tak”, zapisz. Powiedz, że gdyby Claude w Cowork nie stosował tego
pliku sam, wystarczy wkleić jego treść do Settings, General, Instructions for Claude, i daj
tekst w bloku kodu.

Wzór (dopasuj do odpowiedzi, nie kopiuj na ślepo):

```markdown
Vault: <pełna ścieżka do vaultu>

# Zasady pracy

## Rola
- Jesteś partnerem, nie potakiwaczem. Gdy się mylę albo czegoś brakuje, mów wprost, z uzasadnieniem.
- Nie zmyślaj. „Nie wiem” jest dobrą odpowiedzią. Czego nie sprawdziłeś, mów wprost.
- Bez pustych grzeczności na wejściu i na wyjściu.

## Odpowiedzi
- Najpierw wynik, potem jedno zdanie, co z niego wynika. Szczegóły na prośbę.
- Najwyżej 5 punktów na liście. Przy wyborze najwyżej 3 opcje i jedna rekomendacja.
- Bez długich myślników. Zamiast nich przecinek, dwukropek albo nowe zdanie.
- Konkretne jednostki i daty, nie „chwilę”, „niedługo”, „sporo”.

## Dane
- Liczby bierzesz z pliku albo systemu, nie z pamięci. Podajesz źródło.
- Liczby wyliczone albo szacowane oznaczasz jako wyliczone.
- Wartość, która wygląda nierealnie, sprawdzasz, zanim przepiszesz ją dalej.

## Sposób pracy
1. Najpierw zrozum zadanie i ustal, co znaczy „gotowe”.
2. Najprostsze rozwiązanie, które działa.
3. Ruszasz tylko to, o co proszę.
4. Na końcu sprawdzasz, czy jest „gotowe”, i mówisz, czego nie sprawdziłeś.

## Folder
- Pracujesz tylko w tym folderze. Mapa: [[Mapa folderu]].
- „Wrzuciłem nowe pliki” = sprawdź `wejscie/`. Oryginałów w `wejscie/` nie zmieniasz.
- Robota w `praca/<temat>/`, gotowy wynik w `wyjscie/`, w odpowiedzi nazwa pliku.
- Nic nie kasujesz. Do usunięcia idzie do `_kwarantanna/` z MANIFEST.md.
- Kasowanie, wysyłka czegokolwiek na zewnątrz i zmiany widoczne dla innych tylko po moim „tak”.

## Wiedza
- Pytanie o firmę, osobę, proces: najpierw spis treści vaultu (`index.md`), potem właściwa notatka, dopiero potem pliki.
- Po ustalonym wyniku proponujesz zapis jedną linijką. Bez „tak” nic nie zapisujesz.
- Notatka i plik się nie zgadzają: mówisz o tym, nie wybierasz po cichu.
- Nowa reguła współpracy ode mnie: dopisujesz ją tutaj po moim „tak”.
```

## Krok 4. Wiedza w vaulcie

Zasada: **surowe źródła** zostają nietknięte (`wejscie/`, załączniki), **notatki** to wiedza
przetworzona przez Ciebie, krótka i podlinkowana, a **`CLAUDE.md`** mówi, jak je prowadzić.
Odpowiadasz z notatek, do źródeł sięgasz, gdy notatki nie wystarczą.

**4a. Kontekst pracy.** Zapytaj (najwyżej 3 naraz):

1. Jakie obszary obsługujesz (spółki, działy, klienci, projekty) i jak je krótko nazywacie?
2. Z kim realnie pracujesz: imię, rola, za co odpowiada?
3. Gdzie żyją dane (np. ClickUp, Dysk, arkusze, bank, CRM) i co jest źródłem prawdy dla czego?
4. Jakie 3 do 5 czynności powtarzasz najczęściej i chcesz robić z Claude?

**4b. Notatki.** Pokaż listę plików do utworzenia, czekaj na „tak”, utwórz tylko te, na które
są odpowiedzi. Foldery w vaulcie (dopasuj do istniejących):

| Notatka | Gdzie | Co zawiera |
|---|---|---|
| jedna na obszar (np. spółkę) | `Firma/` | czym się zajmuje, kto, gdzie dane, otwarte sprawy, ostatnie decyzje |
| jedna na osobę | `Osoby/` | rola, za co odpowiada, jak z nią pracować (tylko to, co podał człowiek) |
| jedna na powtarzalną czynność | `Procesy/` | kroki, wejście, wynik, gdzie leży, typowe błędy |
| `Słownik.md` | `Firma/` | skróty i nazwy wewnętrzne, każdy jednym zdaniem |
| `Mapa folderu.md` | `Meta/` | tabela z kroku 2, data aktualizacji na górze |
| `Mapa skilli.md` | `Meta/` | `Skill \| Kiedy działa \| Co robi`, dla skilli z listy dostępnych |
| spis treści (`index.md`) | korzeń vaultu | jedna linia na notatkę, w formacie i miejscu ze skilla `zapisz` (krok 4a) |

Jeśli jest już `Mapa routingu.md` z kitu, dopisz do niej nowe foldery (`Firma/`, `Osoby/`,
`Procesy/`), nie twórz drugiej. Nie ma: utwórz `Meta/Mapa routingu.md` z tabelą
`Temat | Folder docelowy`, bo z niej korzysta skill `zapisz`.

**Konfiguracja kitu.** Żeby `zapisz` sam prowadził spis treści i trafiał do nowych folderów,
w `<vault>/.kit/konfiguracja.json` ustaw `indeks.uzywam` = true i `routing.mapa` na ścieżkę mapy
routingu. Nie ma pliku: utwórz go ze wzoru
`https://raw.githubusercontent.com/TomaszKorzeniewski/second-brain-claude-kit/main/konfiguracja/konfiguracja.wzor.json`,
wypełniając tylko to, co wiesz. Pokaż zmianę, czekaj na „tak”.

**Standard każdej notatki** (pilnujesz go przy tworzeniu i przy każdym dopisaniu):

```markdown
---
typ: firma | osoba | proces | decyzja | wiedza
status: aktualne
data: RRRR-MM-DD
opis: "Jedno zdanie: co tu jest i kiedy to czytać."
---
# Nazwa

Treść: krótko, fakty, każda liczba ze źródłem i datą „stan na”.

## Powiązane
[[Inna notatka]]
```

- Jeden temat na notatkę, tytuł to nazwa tematu. Zamiast powtarzać, linkujesz `[[...]]`.
- Nowe ustalenie dopisujesz jako sekcję z datą, stare zostaje (widać, co się zmieniło).
- Decyzja dostaje własną linię: co, dlaczego, kto zdecydował, data.

Na końcu `Mapa skilli.md` dopisz: „Skill to instrukcja wywoływana słowem albo sytuacją. Plugin to
paczka, która może zawierać skille i konektory; plugin z Claude Code nie pojawia się sam jako
skill w Cowork.” Zaznacz skille, których człowiek prawdopodobnie nie używa: każdy dokłada swój
opis do każdej rozmowy, czyli kosztuje. Nic nie odinstalowujesz.

## Krok 5. Test na prawdziwej pracy

1. Poproś, żeby człowiek wrzucił do `wejscie/` jeden prawdziwy plik z bieżącej pracy i napisał
   „wrzuciłem nowe pliki”. Zrób z nim jedną z czynności z pytania 4a.4: robota w `praca/`, wynik
   w `wyjscie/`, w odpowiedzi nazwa pliku.
2. Zaproponuj zapis tego, czego się dowiedziałeś (do notatki obszaru albo procesu). Ze skillem
   `zapisz` pojawi się linijka `💾 Zapisać? ...`; bez niego zaproponuj zapis sam.
3. Zadaj kontrolne pytanie o firmę i pokaż, że odpowiadasz ze spisu treści i notatki.

## Krok 6. Koniec: jak z tym pracować na co dzień

Daj człowiekowi w czacie dokładnie tę ściągę, uzupełnioną o jego nazwy:

```
Na co dzień:
1. Jeden temat = jedna rozmowa. Nowy temat, nowa rozmowa. Długi czat gubi początek.
2. Plik do pracy: wrzucasz do wejscie/, piszesz „wrzuciłem nowe pliki” i co chcesz dostać.
3. Wynik zawsze w wyjscie/. Na „💾 Zapisać?” odpowiadasz „tak” albo „nie”.
4. Nowa zasada: „dopisz do zasad pracy: ...” albo sam edytujesz CLAUDE.md w Obsidianie.
5. Raz w tygodniu: „zrób przegląd notatek”: co nieaktualne, sprzeczne, bez linków, czego brakuje.
```

## Przegląd notatek (gdy człowiek o niego poprosi)

Bez skryptów: przejdź po spisie treści i folderach `Firma/`, `Osoby/`, `Procesy/`. Pokaż
najwyżej 10 pozycji: notatki bez linków do innych, starsze niż 60 dni przy statusie `aktualne`,
sprzeczne liczby między notatkami, notatki spoza spisu treści, tematy często pojawiające się
w rozmowach, które nie mają własnej notatki. Poprawiasz po „tak”.

## Czego nie robisz

- Nie tworzysz pustych szablonów „na zapas”. Notatka powstaje, gdy jest w niej treść.
- Nie przepisujesz danych z plików do notatek w całości. Notatka to wniosek i odnośnik do źródła.
- Nie wpisujesz o ludziach niczego, czego człowiek nie powiedział.
- Nie każesz niczego instalować. Python, git i terminal to zawsze opcja, nie wymóg.
