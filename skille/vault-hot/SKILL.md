---
name: vault-hot
description: "Pamięć między sesjami: czyta HOT.md na starcie sesji, żeby wejść w kontekst bez recapu. Użyj na starcie sesji, gdy user mówi 'kontynuuj', 'na czym skończyliśmy', 'co dalej', albo po prostu zaczyna nową sesję. NIE zapisuje HOT.md, od tego jest skill 'zapisz'."
---

# vault-hot: szybki kontekst na start sesji

HOT.md to żyjący log otwartych wątków w korzeniu vaultu. Wskazuje, gdzie skończyliśmy i co dalej,
nie duplikuje dziennika. Ma sens przy wielu równoległych wątkach; przy jednym wystarczy dziennik.

## Na starcie sesji

1. Vault: ścieżka z instrukcji użytkownika (linia `Vault:`), w Cowork z system reminder.
2. Przeczytaj `<vault>/.kit/konfiguracja.json`, jeśli istnieje. `hot.uzywam` = false: powiedz
   jednym zdaniem, że HOT jest wyłączony, i zaproponuj ostatni wpis dziennika zamiast niego.
3. Przeczytaj HOT.md (`hot.plik`, domyślnie `HOT.md`). Brak pliku: nowy vault albo pierwszy raz,
   to normalne, powiedz to i nie twórz pliku sam.
4. **Linia ze `(stan na RRRR-MM-DD)` starszym niż `hot.dni_do_weryfikacji` (domyślnie 14 dni)
   to hipoteza, nie fakt.** Zanim na niej oprzesz odpowiedź, sprawdź u źródła (notatka, plik,
   system). Linia bez daty: traktuj tak samo.
5. Potrzeba więcej kontekstu: przeczytaj wpis dziennika wskazany w HOT.md, nie cały dziennik.

## Zapis HOT.md

**Nie robisz tego tutaj.** Na koniec sesji HOT.md aktualizuje skill `zapisz`.
