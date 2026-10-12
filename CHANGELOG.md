# Zmiany w Second Brain Claude Kit

Każda zmiana ma własny wpis, żeby dało się ją wybrać albo pominąć osobno (skill
`kit-aktualizacja` czyta ten plik). Pola `id`, `dotyczy`, `zysk`, `decyzja`, `migracja` są
czytane przez skrypt, więc trzymaj ich format. Najnowsza wersja na górze.

## 2.2.0 (2026-10-12)

### Zapis proponowany po każdym wyniku
- id: 2.2.0-propozycja-zapisu
- dotyczy: zapisz
- zysk: Claude sam proponuje zapis jedną linijką, gdy pada decyzja, liczba albo działające rozwiązanie, więc vault rośnie z każdą rozmową, a nie tylko wtedy, gdy pamiętasz o „zapisz”; na „tak” robi mikrozapis do jednej notatki
- decyzja: nie
- migracja: klucz `zapis.proponuj` = true w konfiguracji; stary `zapis.procent_kontekstu` można usunąć, nie jest już czytany

### Kit działa bez Pythona
- id: 2.2.0-bez-skryptow
- dotyczy: wszystkie
- zysk: podstawa (zapisz, vault-hot, przetworz-zrodlo, vault-ask) to same instrukcje, nic nie trzeba instalować; gotowe paczki leżą w `paczki/`; skrypty zostają jako wersja zaawansowana dla chętnych
- decyzja: nie
- migracja: klucz `instalacja.python` (true, jeśli działa `python3`)

### Spis treści prowadzony przy zapisie, bez skryptu
- id: 2.2.0-spis-bez-skryptu
- dotyczy: zapisz, przetworz-zrodlo, vault-ask
- zysk: nowa notatka od razu dostaje linię w spisie treści, bez odpalania skryptu; skrypt `indeks.py` składa spis od zera tylko przy dużym vaultcie
- decyzja: nie
- migracja: nie

## 2.1.0 (2026-09-25)

### Przetwarzanie źródeł wg wzorca LLM Wiki
- id: 2.1.0-przetworz-zrodlo
- dotyczy: przetworz-zrodlo
- zysk: artykuł, PDF albo transkrypcja raz przetworzone zasilają strony o osobach, firmach i pojęciach, więc wiedza się kumuluje, zamiast być szukana od nowa przy każdym pytaniu
- decyzja: tak: czy źródła mają mieć jeden folder, tryb wspólny albo wsadowy
- migracja: klucz `zrodla` w konfiguracji; zainstaluj skill `przetworz-zrodlo`

### Spis treści składany skryptem
- id: 2.1.0-indeks
- dotyczy: vault-ask, zapisz
- zysk: przy pytaniach ogólnych Claude czyta jeden plik zamiast kilkunastu, a utrzymanie spisu kosztuje zero tokenów (opłaca się do ok. 250 notatek)
- decyzja: tak: czy chcesz spis treści
- migracja: klucz `indeks` w konfiguracji; `indeks.py --zapisz` raz, potem odświeża `zapisz`

### Doradztwo układu vaultu, bez przymusu
- id: 2.1.0-doradztwo-ukladu
- dotyczy: kit-aktualizacja
- zysk: podpowiedzi pod wyszukiwanie, embedding i tokeny (nagłówki w długich notatkach, podział bardzo długich, jedno miejsce na źródła, folder załączników); każdą można odrzucić na stałe
- decyzja: nie
- migracja: nie

### Aliasy i opis w wyszukiwaniu
- id: 2.1.0-aliasy
- dotyczy: vault-ask, vault-embed
- zysk: notatka trafia też po skrócie, tłumaczeniu albo starej nazwie z pola `aliases`, a pole `opis` wzmacnia trafienie
- decyzja: nie
- migracja: nie

### Pojęcia bez własnej strony w przeglądzie higieny
- id: 2.1.0-lint-pojecia
- dotyczy: vault-lint
- zysk: temat linkowany z kilku notatek, a bez własnej strony, wychodzi jako propozycja nowej notatki
- decyzja: nie
- migracja: nie

### Ochrona przejrzanych notatek, odpowiedzi wracają do vaultu, log do grepowania
- id: 2.1.0-sprawdzone-log
- dotyczy: zapisz, vault-ask
- zysk: notatka ze `sprawdzone: true` nie jest przepisywana, synteza z rozmowy trafia do vaultu zamiast przepaść w czacie, a historię sesji wyciąga jedno `grep "^## \["`
- decyzja: nie
- migracja: nie

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
