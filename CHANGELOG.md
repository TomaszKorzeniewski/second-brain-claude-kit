# Zmiany w Second Brain Claude Kit

Każda zmiana ma własny wpis, żeby dało się ją wybrać albo pominąć osobno (skill
`kit-aktualizacja` czyta ten plik). Pola `id`, `dotyczy`, `zysk`, `decyzja`, `migracja` są
czytane przez skrypt, więc trzymaj ich format. Najnowsza wersja na górze.

## 2.0.0 (2026-09-25)

### Twoje dopasowanie w jednym pliku, osobno od skilli
- id: 2.0.0-konfiguracja
- dotyczy: wszystkie
- zysk: aktualizacja skilla już nigdy nie nadpisze Twoich ustawień, bo te żyją w `.kit/konfiguracja.json` w vaulcie
- decyzja: tak: wartości, które dotąd były wpisane na sztywno albo ustalone w rozmowie (budżet HOT, folder dziennika, mapa routingu)
- migracja: utwórz `<vault>/.kit/konfiguracja.json` ze wzoru `konfiguracja/konfiguracja.wzor.json`; `wersja_kitu` = 2.0.0

### Aktualizacje i przegląd dopasowania na żądanie
- id: 2.0.0-kit-aktualizacja
- dotyczy: wszystkie
- zysk: nowy skill `kit-aktualizacja` pokazuje zmiany z repo do wyboru i na liczbach z vaultu sprawdza, czy ustawienia wciąż pasują do tego, jak pracujesz
- decyzja: tak: tryb przypomnień (na żądanie, przypominaj, nigdy)
- migracja: zainstaluj skill `kit-aktualizacja`

### Kod skilli w osobnych plikach zamiast w SKILL.md
- id: 2.0.0-kod-osobno
- dotyczy: vault-ask, vault-embed, vault-lint, hot-slim
- zysk: skill ładuje do kontekstu ok. 2 KB zamiast 19 do 48 KB, a skrypt nie musi być kopiowany do vaultu
- decyzja: nie
- migracja: przeinstaluj skille jako folder (zip), stary `vault_lint.py` w vaulcie można przenieść do kwarantanny

### Wcześniejszy zapis sesji i sekcja „Czego NIE robić”
- id: 2.0.0-zapisz-wczesnie
- dotyczy: zapisz
- zysk: zapis przy ok. 55% kontekstu zamiast przy kompaktowaniu (mniej zniekształceń), a odrzucone ścieżki są zapisane, więc następna sesja w nie nie wchodzi
- decyzja: nie
- migracja: nie

### Metadane w dzienniku i w nowych notatkach
- id: 2.0.0-frontmatter
- dotyczy: zapisz
- zysk: każda nowa notatka dostaje `typ`, `status`, `data`, `tagi`, więc wyszukiwarka odróżnia ustalenia aktualne od obalonych
- decyzja: tak: czy chcesz metadane (domyślnie tak)
- migracja: `frontmatter.wymagany` w konfiguracji

### Daty ważności w HOT.md
- id: 2.0.0-hot-stan-na
- dotyczy: zapisz, vault-hot
- zysk: linia w HOT.md starsza niż 14 dni jest sprawdzana u źródła, zanim Claude na niej oprze odpowiedź
- decyzja: nie
- migracja: nie

### vault-embed: model e5-base i router zamiast fuzji
- id: 2.0.0-embed-router
- dotyczy: vault-embed
- zysk: top1 11/16 do 12/16, top10 15/16 do 16/16, fleksja 3/8 do 7/8 (pomiar na 394 notatkach)
- decyzja: tak: zgoda na pobranie większego modelu (1,1 GB zamiast 470 MB)
- migracja: model, venv i indeks przenoszą się do `~/.cache/second-brain-kit/`; pobierz model ponownie i zbuduj indeks od zera

### Wagi folderów działają także przy metadanych
- id: 2.0.0-wagi-min
- dotyczy: vault-ask, vault-embed
- zysk: waga to teraz niższa z wag folderu i pola `typ`; wcześniej `typ` wyłączał wagę folderu, więc archiwum z metadanymi nie było obniżane
- decyzja: nie
- migracja: nie

### Własne wagi, foldery i fakty w konfiguracji
- id: 2.0.0-dopasowanie-skryptow
- dotyczy: vault-ask, vault-embed, vault-lint, hot-slim
- zysk: obniżasz „zaśmiecające” foldery, dopisujesz własne liczby do pilnowania i zmieniasz budżet HOT bez edycji kodu
- decyzja: nie
- migracja: nie

### Kilka vaultów, dowolna chmura, Twój układ Obsidiana
- id: 2.0.0-wiele-vaultow
- dotyczy: wszystkie
- zysk: każdy vault (iCloud, OneDrive, Dropbox) ma własną konfigurację z opisem i granicami, a dziennik pisze do notatki dnia z Obsidian Daily Notes zamiast tworzyć drugą
- decyzja: tak: opis i granice każdego vaultu, folder i format notatki dnia
- migracja: klucze `vault` i `dziennik.format_nazwy` w konfiguracji; kilka linii `Vault (<nazwa>): <ścieżka>` w instrukcjach

### Szukanie w podfolderze
- id: 2.0.0-folder
- dotyczy: vault-ask, vault-embed
- zysk: `--folder Praca` szuka tylko tam, np. gdy materiał dla zespołu nie może wyciągnąć notatek prywatnych
- decyzja: nie
- migracja: nie

## 1.3.0 (2026-08-27)

### Rozmowa startowa: vault jako podfolder, sześć skilli
- id: 1.3.0-onboarding
- dotyczy: wszystkie
- zysk: notatki nie mieszają się z resztą plików w folderze roboczym
- decyzja: nie
- migracja: nie

## 1.2.0 (2026-08-27)

### vault-embed i filtr statusu
- id: 1.2.0-vault-embed
- dotyczy: vault-ask, vault-embed
- zysk: druga warstwa wyszukiwania po znaczeniu; notatki `status: obalone` znikają z wyników
- decyzja: nie
- migracja: nie

## 1.1.0 (2026-08-26)

### Stemming polski i wagi folderów
- id: 1.1.0-stemming
- dotyczy: vault-ask
- zysk: odmiana słów przestaje psuć wyniki, dziennik nie zalewa trafień
- decyzja: nie
- migracja: nie

## 1.0.0 (2026-08-22)

### Pierwsza wersja
- id: 1.0.0-start
- dotyczy: wszystkie
- zysk: pięć skilli i rozmowa startowa
- decyzja: nie
- migracja: nie
