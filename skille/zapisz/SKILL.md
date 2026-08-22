---
name: zapisz
description: "Zamknięcie sesji — zapis do dziennika, aktualizacja HOT.md i routing treści do właściwych notatek w vaulcie. Użyj gdy user mówi: 'zapisz', 'zamknij sesję', 'koniec sesji', 'save', 'zapisz stan', 'zamykamy', 'koniec na dziś', 'to tyle'. Triggeruj też gdy sesja była długa i poruszała wiele tematów — zaproponuj zapis nawet jeśli user nie poprosił wprost."
---

# zapisz — zamknięcie sesji

Jeden command robi do trzech rzeczy: dziennik, HOT.md (jeśli ten user go używa), routing treści.

Vault root: ścieżka do vaulta usera, ustalona przy onboardingu (patrz `onboarding-prompt.txt`
w tym repo). Nie zakładaj konkretnej nazwy folderu.

**Ten skill jest generyczny.** Mapa folderów w kroku 3 i to, czy w ogóle używasz kroku 2 (HOT.md),
zależą od tego, jak ten konkretny user pracuje — nie kopiuj przykładów z tego pliku jako gotowej
odpowiedzi. Jeśli w vaulcie usera istnieje notatka `Meta/Mapa routingu.md` (albo podobna, powstała
przy onboardingu), **czytaj mapę stamtąd**. Jeśli jej nie ma, zapytaj usera przy pierwszym użyciu
tego skilla, jak chce mieć poukładane notatki, i zapisz odpowiedź jako taką notatkę, żeby nie
pytać drugi raz.

## Krok 1: Dziennik

Utwórz lub zaktualizuj plik `Dziennik/RRRR-MM-DD.md` (data dzisiejsza).

Jeśli plik już istnieje (bo to druga sesja tego dnia) — dopisz nową sekcję pod istniejącą treścią z nagłówkiem `## Sesja N` i godziną.

Szablon nowego wpisu:

```markdown
# Dziennik — RRRR-MM-DD

**Data:** RRRR-MM-DD

---

## Zadania dnia

- [x] Co zostało zrobione (krótko, konkretnie)
- [ ] Co zostało otwarte

---

## Decyzje

- Decyzja → uzasadnienie (1 linia)

---

## Routing

<!-- lista notatek zaktualizowanych lub utworzonych w kroku 3 -->
- [[Nazwa notatki]] — co dodano

---

## Następny krok

- Jeden konkretny krok na następną sesję
```

Zasady:
- Pisz zwięźle — dziennik to log, nie esej
- Każde zadanie = 1 linia, max 2 zdania
- Decyzje = co + dlaczego, żeby nie wracać do tematu
- Sekcja "Routing" dokumentuje co trafiło gdzie (ślad audytu)

## Krok 2: HOT.md — log żyjący pod kontrolą budżetu (NIE nadpisuj w całości)

**Nie każdy user tego potrzebuje.** HOT.md ma sens, gdy ktoś pracuje w wielu równoległych
wątkach/sesjach i potrzebuje szybko wejść w kontekst bez recapu. Jeśli user pracuje jednym
wątkiem naraz, ten krok możesz pominąć całkowicie i przejść do routingu — mniej plików do
utrzymania, mniejszy koszt stały każdej sesji. Ustalone raz przy onboardingu, nie zgaduj sam.

Gdy user HOT.md używa: to **nie jest** jednorazowy 10-liniowy pointer nadpisywany co sesję,
to żyjący log pod kontrolą osobnego skilla `hot-slim` (budżet ustalony przy onboardingu,
przycinanie to decyzja usera, nie automat tego skilla). Nadpisanie całego pliku kasuje realną,
cross-linkowaną historię, na której opierają się kolejne sesje — nie rób tego.

1. **Nigdy nie nadpisuj całego pliku.** Edytuj istniejące linie in-place, dopisuj nowe.
2. Na początku pliku zaktualizuj blok pointer — to jedyna część, którą faktycznie zastępujesz
   w całości, reszta poniżej zostaje:
   ```markdown
   # HOT — pointer (RRRR-MM-DD)

   Ostatnia sesja: RRRR-MM-DD
   Temat: [główny temat sesji, max 5 słów]
   Następny krok: [konkretna akcja]
   Otwarte: [2-3 tematy w toku, po przecinku]
   Kontekst: [[RRRR-MM-DD]] | [[link do głównego projektu]]
   ```
3. Dla tematu poruszonego w tej sesji, który **już ma linię w HOT.md**: znajdź ją i
   zaktualizuj w miejscu (np. dopisz `✅ ZAMKNIĘTE RRRR-MM-DD` na początku, zaktualizuj treść),
   zamiast dopisywać duplikat.
4. Dla **nowego** tematu wartego HOT: dopisz nową linię — jedno zdanie stanu + link do
   notatki docelowej.
5. **Kryterium, co w ogóle trafia do HOT:** decyzje i wątki, do których wróci się w ciągu
   najbliższych dni/tygodni. Jednorazowe drobiazgi zostają tylko w dzienniku.
6. Po zapisie sprawdź rozmiar pliku (np. `wc -c HOT.md`). Jeśli przekracza budżet — **nie
   przycinaj sam**, zasygnalizuj Tomkowi, że warto odpalić `hot-slim` (to jego decyzja co
   skrócić, nie tego skilla).

Nigdy nie duplikuj treści dziennika. Nigdy nie rób z HOT.md listy wszystkich decyzji — od tego jest dziennik.

## Krok 3: Routing treści do właściwych notatek

Dla każdego tematu poruszanego w sesji zdecyduj, gdzie trafia, na podstawie mapy folderów usera.

### Mapa folderów: czytaj, nie zgaduj

**Nie ma tu gotowej tabeli — musi być własna, dla tego vaulta.** Sprawdź `Meta/Mapa routingu.md`
(albo notatkę o tej samej roli, jeśli user nazwał ją inaczej przy onboardingu). Struktura tej
notatki to zawsze tabela: `Temat → Folder docelowy`, dokładnie w formacie z przykładu niżej —
tylko treść wierszy jest inna dla każdego usera, bo każdy ma inne obszary życia i pracy.

Przykład (nie kopiuj, to tylko pokazuje kształt, nie zawartość):

```markdown
| Temat | Folder docelowy |
|-------|----------------|
| <słowa kluczowe tematu A> | `<Folder A/>` |
| <słowa kluczowe tematu B> | `<Folder B/>` |
```

Jeśli notatki z mapą nie ma jeszcze w vaulcie: to znaczy, że onboarding nie doszedł do tego
kroku albo user zaczął od zera. Zapytaj krótko, jakie ma główne obszary (praca, projekty
poboczne, dom, zdrowie, itd.) i zapisz odpowiedź jako `Meta/Mapa routingu.md`, żeby przy
kolejnym `zapisz` nie pytać drugi raz.

### Logika routingu

1. **Notatka istnieje** → dopisz nową sekcję z datą (`## Aktualizacja RRRR-MM-DD`) na końcu. Nie nadpisuj istniejącej treści.
2. **Notatka nie istnieje, ale temat jest istotny** → utwórz nową notatkę w odpowiednim folderze. Nazwa pliku = temat (bez daty w nazwie, chyba że to spotkanie).
3. **Temat jest drobny / jednorazowy** → nie routuj, zostaje tylko w dzienniku. Nie twórz notatki dla każdej drobnostki.
4. **Temat nie pasuje do żadnego folderu** → `Inbox/`. Użyj tego rzadko — jeśli temat jest na tyle ważny żeby routować, to prawdopodobnie pasuje gdzieś w mapie.

Każdy zroutowany temat odnotuj w sekcji "Routing" dziennika.
