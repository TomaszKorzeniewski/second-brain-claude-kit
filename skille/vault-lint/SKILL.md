---
name: vault-lint
description: "Higiena vaultu Obsidian bez modeli AI: martwe linki, sieroty, nieaktualne notatki, szkice, sprzeczności liczbowe, stan inboxu. Użyj przy cyklicznym przeglądzie vaultu albo gdy user pyta 'co wymaga sprzątania'. Tylko raport, nic nie zmienia, chyba że user jawnie poprosi o --fix-safe --apply."
---

# vault-lint: higiena vaultu (raport, bez zmian)

Czysty Python, biblioteka standardowa, zero tokenów na samo sprawdzenie.

## Jak uruchomić (dla Claude)

1. Vault: ścieżka z instrukcji użytkownika (linia `Vault:`), w Cowork z system reminder.
2. ```bash
   python3 "<katalog tego skilla>/kod/vault_lint.py" --vault "<vault>" --max 25
   ```
3. Pokaż raport. Przy sierotach, scaleniach i sprzecznościach **pytaj**: skill nic nie usuwa
   ani nie scala sam.
4. `--fix-safe` (podgląd) i `--fix-safe --apply` (z kopią każdego pliku w
   `.vault-lint-backup/RRRR-MM-DD/`) naprawiają tylko martwe linki z dokładnie jednym
   jednoznacznym kandydatem. `--apply` wyłącznie na wyraźną prośbę.

## Co sprawdza

| klasa | co to znaczy |
|---|---|
| martwe linki | `[[...]]` wskazuje na notatkę, której nie ma |
| sieroty | do notatki nie prowadzi żaden link (poza dziennikiem, inboxem i archiwum) |
| nieaktualne | notatka nieruszana dłużej niż `lint.dni_nieaktualne` (domyślnie 90 dni) |
| szkice | marker TODO, SZKIC albo „do uzupełnienia” na starcie treści lub w tytule |
| sprzeczności | ta sama znana liczba opisana różnie w różnych notatkach |

Pomija foldery ukryte (`.obsidian`, `.kit`, kopie zapasowe) i `_kwarantanna`.

## Dopasowanie do osoby

W `<vault>/.kit/konfiguracja.json`, klucz `lint`:
- `dni_nieaktualne`: próg dla klasy „nieaktualne”,
- `foldery_bez_sierot`: dodatkowe foldery, w których brak linków jest normalny,
- `fakty`: lista `{"etykieta": ..., "wzorzec": ...}`, regex z **jedną** grupą liczby. Tak
  pilnujesz własnych liczb, które nie mogą się rozjechać (limit budżetu, stawka, termin).
  Wbudowany jest jeden fakt: budżet HOT.md w znakach.

Gdy raport pokaże tę samą sprzeczność drugi raz, zaproponuj dopisanie jej jako faktu, zamiast
naprawiać ręcznie po raz kolejny.
