#!/usr/bin/env python3
"""Przegląd kitu: co nowego w repo i czy ustawienia wciąż pasują do tego, jak pracujesz.

Dwa tryby, oba tylko czytają i nic nie zapisują (zero tokenów, sama biblioteka standardowa):

  --zmiany CHANGELOG.md   Wypisuje wpisy nowsze niż `wersja_kitu` z konfiguracji, dotyczące
                          zainstalowanych skilli albo wszystkich, bez tych już wdrożonych
                          i pominiętych. Format JSON, żeby Claude nie parsował prozy.
  --dopasowanie           Liczy sygnały w vaulcie i porównuje z konfiguracją. Każdy sygnał
                          to propozycja z uzasadnieniem liczbowym, nie decyzja.

Format wpisu w CHANGELOG.md (wszystko poza nagłówkami jest dla ludzi):

    ## 2.1.0 (2026-10-01)
    ### <tytuł zmiany>
    - id: 2.1.0-krotka-nazwa
    - dotyczy: zapisz            (nazwa skilla, kilka po przecinku, albo: wszystkie)
    - zysk: jedno zdanie, co user z tego ma
    - decyzja: nie | <o co trzeba zapytać>
    - migracja: nie | <co zmienić w konfiguracji albo w vaulcie>

Użycie:
    python3 przeglad.py --vault <vault> --zmiany <ścieżka do CHANGELOG.md>
    python3 przeglad.py --vault <vault> --dopasowanie
"""
import argparse
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_konfig

POMIJAJ = {".obsidian", ".git", ".kit", ".trash", "_kwarantanna", ".vault-lint-backup"}


def wersja(t):
    return tuple(int(x) for x in re.findall(r"\d+", t)[:3])


def parsuj_changelog(tekst):
    wpisy, ver, data, wpis = [], None, None, None
    for linia in tekst.splitlines():
        m = re.match(r"^## (\d+\.\d+\.\d+)(?:\s*\((.*?)\))?", linia)
        if m:
            ver, data, wpis = m.group(1), m.group(2), None
            continue
        m = re.match(r"^### (.+)", linia)
        if m and ver:
            wpis = {"wersja": ver, "data": data, "tytul": m.group(1).strip()}
            wpisy.append(wpis)
            continue
        m = re.match(r"^- (id|dotyczy|zysk|decyzja|migracja):\s*(.*)", linia)
        if m and wpis is not None:
            wpis[m.group(1)] = m.group(2).strip()
    for w in wpisy:
        w["dotyczy"] = [d.strip() for d in w.get("dotyczy", "wszystkie").split(",")]
        w.setdefault("id", "%s-%s" % (w["wersja"], re.sub(r"\W+", "-", w["tytul"].lower()).strip("-")))
    return wpisy


def zmiany(vault, sciezka):
    konf = kit_konfig.wczytaj(vault)
    mam = wersja(kit_konfig.wartosc(konf, "wersja_kitu", "0.0.0"))
    skille = set(kit_konfig.wartosc(konf, "skille", []) or [])
    zalatwione = set(kit_konfig.wartosc(konf, "aktualizacje.pominiete", []) or []) | \
        set(kit_konfig.wartosc(konf, "aktualizacje.wdrozone", []) or [])
    with open(sciezka, encoding="utf-8") as f:
        wpisy = parsuj_changelog(f.read())
    najnowsza = max((w["wersja"] for w in wpisy), key=wersja, default="0.0.0")
    oczekujace = [w for w in wpisy
                  if wersja(w["wersja"]) > mam and w["id"] not in zalatwione
                  and ("wszystkie" in w["dotyczy"] or skille & set(w["dotyczy"]) or not skille)]
    nowe_skille = sorted({d for w in wpisy for d in w["dotyczy"]
                          if wersja(w["wersja"]) > mam and d != "wszystkie"} - skille) if skille else []
    return {"zainstalowana": ".".join(map(str, mam)), "najnowsza": najnowsza,
            "oczekujace": oczekujace, "nowe_skille_do_rozwazenia": nowe_skille}


def notatki(vault):
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in POMIJAJ and not d.startswith(".")]
        for f in files:
            if f.endswith(".md"):
                yield os.path.join(root, f)


def dopasowanie(vault):
    konf = kit_konfig.wczytaj(vault)
    skille = set(kit_konfig.wartosc(konf, "skille", []) or [])
    pominiete = set(kit_konfig.wartosc(konf, "aktualizacje.pominiete", []) or [])
    dzis = datetime.date.today()
    sygnaly = []

    def sygnal(id_, propozycja, uzasadnienie):
        if id_ not in pominiete:
            sygnaly.append({"id": id_, "propozycja": propozycja, "uzasadnienie": uzasadnienie})

    pliki = list(notatki(vault))
    n = len(pliki)

    # 1. Rozmiar vaultu kontra zestaw wyszukiwarek.
    if n >= 300 and "vault-embed" not in skille:
        sygnal("dopasowanie-vault-embed", "rozważ vault-embed (wyszukiwanie po znaczeniu)",
               "%d notatek; od ok. 300 pytania opisowe coraz częściej nie trafiają samym BM25" % n)
    if n >= 50 and "vault-ask" not in skille:
        sygnal("dopasowanie-vault-ask", "zainstaluj vault-ask", "%d notatek, a szukanie czyta całe pliki" % n)

    # 2. Rytm pracy kontra HOT.md.
    folder_dz = os.path.join(vault, kit_konfig.wartosc(konf, "dziennik.folder", "Dziennik"))
    sesje_14 = dni_14 = 0
    for p in notatki(folder_dz) if os.path.isdir(folder_dz) else []:
        # Data z nazwy, gdy jest w formacie ISO; inny format nazwy (np. DD.MM.YYYY z Daily
        # Notes) nie może wyłączyć sygnału, więc wtedy data modyfikacji pliku.
        m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(p))
        try:
            d = datetime.date.fromisoformat(m.group(1)) if m else \
                datetime.date.fromtimestamp(os.path.getmtime(p))
        except ValueError:
            continue
        if (dzis - d).days <= 14:
            dni_14 += 1
            with open(p, encoding="utf-8", errors="ignore") as f:
                # Stary nagłówek „## Sesja:” i nowy, parsowalny „## [RRRR-MM-DD] sesja | temat”.
                sesje_14 += len(re.findall(r"(?mi)^## (?:Sesja|\[\d{4}-\d{2}-\d{2}\] sesja)", f.read()))
    hot_on = bool(kit_konfig.wartosc(konf, "hot.uzywam", False))
    hot_p = os.path.join(vault, kit_konfig.wartosc(konf, "hot.plik", "HOT.md"))
    if not hot_on and dni_14 and sesje_14 / dni_14 >= 2:
        sygnal("dopasowanie-hot-wlacz", "włącz HOT.md (vault-hot + hot-slim)",
               "%d sesji w %d dniach dziennika z ostatnich 2 tygodni; przy kilku wątkach dziennie "
               "HOT skraca wejście w kontekst" % (sesje_14, dni_14))
    if hot_on and os.path.exists(hot_p):
        wiek = (dzis - datetime.date.fromtimestamp(os.path.getmtime(hot_p))).days
        if wiek > 30:
            sygnal("dopasowanie-hot-wylacz", "wyłącz HOT.md albo odśwież go",
                   "HOT.md nieruszany od %d dni, a skille dalej go czytają na starcie sesji" % wiek)

    # 2b. Układ Obsidiana kontra konfiguracja: Daily Notes w innym folderze albo formacie
    # znaczy dwie notatki dnia zamiast jednej.
    try:
        with open(os.path.join(vault, ".obsidian", "daily-notes.json"), encoding="utf-8") as f:
            dn = json.load(f)
    except (OSError, ValueError):
        dn = {}
    dn_folder = (dn.get("folder") or "").strip("/")
    dn_format = dn.get("format") or "YYYY-MM-DD"
    kf_folder = kit_konfig.wartosc(konf, "dziennik.folder", "Dziennik")
    kf_format = kit_konfig.wartosc(konf, "dziennik.format_nazwy", "YYYY-MM-DD")
    if dn and (dn_folder and not dn_folder.startswith(kf_folder) or dn_format != kf_format):
        sygnal("dopasowanie-daily-notes", "ustaw dziennik na folder i format z Obsidian Daily Notes",
               "Obsidian tworzy notatki dnia w `%s` jako `%s`, kit pisze dziennik w `%s` jako `%s`; "
               "powstają dwie notatki na jeden dzień" % (dn_folder or "/", dn_format, kf_folder, kf_format))

    # 3. Frontmatter.
    if kit_konfig.wartosc(konf, "frontmatter.wymagany", True) and n:
        bez = sum(1 for p in pliki if not open(p, encoding="utf-8", errors="ignore").read(4).startswith("---"))
        if bez / n > 0.3:
            sygnal("dopasowanie-frontmatter", "uzupełnij frontmatter w starszych notatkach (partiami, za zgodą)",
                   "%d z %d notatek (%d%%) bez metadanych; wyszukiwarka nie odróżni w nich ustaleń "
                   "aktualnych od obalonych" % (bez, n, 100 * bez // n))

    # 4. Mapa routingu kontra realne foldery.
    mapa_p = os.path.join(vault, kit_konfig.wartosc(konf, "routing.mapa", "Meta/Mapa routingu.md"))
    if os.path.exists(mapa_p):
        mapa = open(mapa_p, encoding="utf-8", errors="ignore").read()
        licznik = {}
        for p in pliki:
            rel = os.path.relpath(p, vault)
            if os.sep in rel:
                licznik[rel.split(os.sep)[0]] = licznik.get(rel.split(os.sep)[0], 0) + 1
        dz = kit_konfig.wartosc(konf, "dziennik.folder", "Dziennik")
        poza = sorted((k for k, v in licznik.items() if v >= 5 and k not in mapa and k != dz),
                      key=lambda k: -licznik[k])
        if poza:
            sygnal("dopasowanie-mapa", "dopisz do mapy routingu: " + ", ".join(poza[:5]),
                   "foldery z co najmniej 5 notatkami, których mapa nie zna: " +
                   ", ".join("%s (%d)" % (k, licznik[k]) for k in poza[:5]))
    elif n >= 10:
        sygnal("dopasowanie-mapa-brak", "utwórz mapę routingu", "brak pliku %s, `zapisz` zgaduje foldery" %
               os.path.relpath(mapa_p, vault))

    return {"notatek": n, "sygnaly": sygnaly, "sugestie_ukladu": uklad(vault, konf, pliki, pominiete)}


def uklad(vault, konf, pliki, pominiete):
    """Sugestie układu pod wyszukiwanie, embedding, tokeny i porządek. Tylko sugestie:
    użytkownik może mieć powód, żeby zostało po staremu, a „zostaw” zapisuje się w
    `aktualizacje.pominiete` i nie wraca."""
    sug = []

    def dodaj(id_, sugestia, dlaczego, zysk):
        if id_ not in pominiete:
            sug.append({"id": id_, "sugestia": sugestia, "dlaczego": dlaczego, "zysk": zysk})

    n = len(pliki)
    dlugie_bez_naglowkow, bardzo_dlugie = [], []
    # HOT.md i spis treści mają celowo płaską budowę, nie są to notatki z wiedzą.
    celowo_plaskie = {os.path.normpath(kit_konfig.wartosc(konf, "hot.plik", "HOT.md")),
                      os.path.normpath(kit_konfig.wartosc(konf, "indeks.plik", "index.md"))}
    for p in pliki:
        if os.path.normpath(os.path.relpath(p, vault)) in celowo_plaskie:
            continue
        try:
            t = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        rel = os.path.relpath(p, vault)
        naglowki = len(re.findall(r"(?m)^#{1,6} ", t))
        if len(t) > 20000:
            bardzo_dlugie.append((rel, len(t)))
        elif len(t) > 4000 and naglowki < 2:
            dlugie_bez_naglowkow.append((rel, len(t)))

    # 1. Wyszukiwanie dzieli notatki po nagłówkach. Długa ściana tekstu to jeden kawałek:
    #    BM25 i embedding widzą ją jako całość i trafiają gorzej.
    if dlugie_bez_naglowkow:
        dodaj("uklad-naglowki", "dodaj nagłówki w długich notatkach bez struktury",
              "notatki ponad 4000 znaków bez nagłówków: %d, np. %s" % (
                  len(dlugie_bez_naglowkow), ", ".join(r for r, _ in dlugie_bez_naglowkow[:3])),
              "wyszukiwanie zwraca konkretną sekcję zamiast całej notatki, mniej tokenów na odpowiedź")
    if bardzo_dlugie:
        dodaj("uklad-podzial", "rozważ podział bardzo długich notatek",
              "notatki ponad 20 000 znaków: %d, np. %s" % (
                  len(bardzo_dlugie), ", ".join(r for r, _ in sorted(bardzo_dlugie, key=lambda x: -x[1])[:3])),
              "Claude czyta część, której potrzebuje, zamiast całości")

    # 2. Spis treści (index.md): opłaca się w mniejszych vaultach.
    plik_ind = kit_konfig.wartosc(konf, "indeks.plik", "index.md")
    ma_indeks = os.path.exists(os.path.join(vault, plik_ind))
    if 20 <= n <= 250 and not ma_indeks:
        dodaj("uklad-indeks", "wygeneruj spis treści (vault-ask, indeks.py)",
              "%d notatek: spis zmieści się w ok. %d tysiącach tokenów" % (n, max(1, n * 27 // 1000)),
              "przy pytaniach ogólnych Claude czyta jeden plik zamiast kilkunastu")
    if n > 250 and ma_indeks:
        dodaj("uklad-indeks-duzy", "zawęź spis treści albo polegaj na wyszukiwaniu",
              "%d notatek: pełny spis kosztuje ok. %d tysięcy tokenów przy każdym czytaniu" % (n, n * 27 // 1000),
              "tańsze pytania ogólne; archiwa wyłączysz przez indeks.pomijaj_foldery")

    # 3. Źródła (artykuły, PDF-y) rozsiane po vaulcie zamiast w jednej, nietykanej warstwie.
    foldery_zrodel = set()
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in POMIJAJ and not d.startswith(".")]
        for f in files:
            if f.lower().endswith(".pdf"):
                foldery_zrodel.add(os.path.relpath(root, vault).split(os.sep)[0])
    for p in pliki:
        glowa = open(p, encoding="utf-8", errors="ignore").read(600)
        if re.search(r"(?m)^(source|zrodlo|źródło|url):\s*https?://", glowa):
            foldery_zrodel.add(os.path.relpath(p, vault).split(os.sep)[0])
    folder_zr = kit_konfig.wartosc(konf, "zrodla.folder")
    if len(foldery_zrodel) >= 3 and not folder_zr:
        dodaj("uklad-zrodla", "trzymaj źródła (artykuły, PDF-y) w jednym folderze, osobno od notatek",
              "źródła leżą w %d folderach: %s" % (len(foldery_zrodel), ", ".join(sorted(foldery_zrodel)[:5])),
              "źródło zostaje nietknięte, wiedza z niego trafia do notatek; "
              "wyszukiwanie nie miesza surowego artykułu z Twoimi wnioskami")

    # 4. Załączniki: Obsidian bez stałego folderu wrzuca obrazy obok notatek.
    try:
        with open(os.path.join(vault, ".obsidian", "app.json"), encoding="utf-8") as f:
            app = json.load(f)
    except (OSError, ValueError):
        app = {}
    foldery_zal = set()
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in POMIJAJ and not d.startswith(".")]
        if any(f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")) for f in files):
            foldery_zal.add(os.path.relpath(root, vault))
    if len(foldery_zal) >= 4 and not app.get("attachmentFolderPath"):
        dodaj("uklad-zalaczniki", "ustaw stały folder załączników (Settings, Files and links)",
              "liczba folderów z obrazami: %d" % len(foldery_zal),
              "porządek w drzewie folderów; obrazy nie mieszają się z notatkami")

    return sug


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=None)
    ap.add_argument("--zmiany", metavar="CHANGELOG")
    ap.add_argument("--dopasowanie", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    vault = kit_konfig.znajdz_vault(a.vault)
    if not vault:
        sys.exit("BŁĄD: nie znalazłem vaultu. Podaj --vault albo ustaw VAULT_DIR.")
    wynik = {"vault": vault}
    if a.zmiany:
        wynik["zmiany"] = zmiany(vault, a.zmiany)
    if a.dopasowanie:
        wynik["dopasowanie"] = dopasowanie(vault)
    if len(wynik) == 1:
        ap.error("podaj --zmiany i/albo --dopasowanie")
    print(json.dumps(wynik, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
