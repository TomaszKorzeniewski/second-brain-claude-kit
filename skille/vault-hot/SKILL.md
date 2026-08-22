---
name: vault-hot
description: "Pamięć między sesjami — czyta HOT.md na starcie sesji, żeby wejść w kontekst bez recapu. Użyj na starcie każdej sesji, gdy user mówi 'kontynuuj', 'na czym skończyliśmy', 'co dalej', albo po prostu zaczyna nową sesję. NIE zapisuje HOT.md — od tego jest skill 'zapisz'."
---

# vault-hot — szybki kontekst na start sesji

HOT.md to **pointer** (max 10 linii) w korzeniu vaultu (`Twój vault/HOT.md`). Wskazuje ostatnią sesję i następny krok — nie duplikuje dziennika.

**Ten skill (i HOT.md w ogóle) ma sens głównie dla kogoś, kto pracuje w wielu równoległych
wątkach i potrzebuje szybko wrócić w kontekst bez recapu.** Jeśli pracujesz jednym wątkiem
naraz, wystarczy Ci sam dziennik (skill `zapisz`) i możesz w ogóle pominąć HOT.md — mniej
plików do utrzymania. Ustalone przy onboardingu.

## Na starcie sesji

1. Przeczytaj `Twój vault/HOT.md`
2. Na podstawie pointera — wiesz jaka była ostatnia sesja, jaki jest następny krok, i gdzie szukać szczegółów
3. Jeśli potrzebujesz więcej kontekstu — przeczytaj plik dziennika wskazany w HOT.md (`Dziennik/RRRR-MM-DD.md`)
4. Jeśli HOT.md nie istnieje — to nowy vault lub pierwszy raz, normalne

## Format HOT.md (referencja)

```
# HOT — pointer (RRRR-MM-DD)

Ostatnia sesja: RRRR-MM-DD
Temat: [max 5 słów]
Następny krok: [konkretna akcja]
Otwarte: [2-3 tematy, po przecinku]
Kontekst: [[RRRR-MM-DD]] | [[link do projektu]]
```

## Zapis HOT.md

**Nie robisz tego tutaj.** Skill `zapisz` odpowiada za aktualizację HOT.md na koniec sesji. Jeśli user mówi „zapisz" / „zamknij sesję" → triggeruj skill `zapisz`, nie vault-hot.
