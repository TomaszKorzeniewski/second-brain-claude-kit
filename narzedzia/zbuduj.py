#!/usr/bin/env python3
"""Buduje kit do wydania: synchronizuje wspólne pliki, sprawdza czystość, pakuje skille.

Trzy kroki, w tej kolejności:
  1. Kopie wspólnego kodu. `wspolne/kit_konfig.py` trafia do `kod/` każdego skilla, który
     ma kod, a `bm25_pl.py` z vault-ask do vault-embed. Źródło prawdy jest jedno, kopie
     są po to, żeby każdy skill dało się zainstalować osobno.
  2. Bramka czystości. Skille mają być generyczne: zero ścieżek konkretnego komputera,
     zero danych osobowych. Wzorce ogólne są niżej; prywatne słowa (imię, nazwy własnych
     folderów) dopisz do `narzedzia/.zakazane-lokalne.txt`, plik jest w .gitignore.
  3. Paczki. `paczki/<skill>.zip` do wgrania w aplikacji Claude (Settings, Skills, Upload).
     Folder `paczki/` jest w .gitignore, bo odtwarza się tym skryptem.

Użycie:
    python3 narzedzia/zbuduj.py              # wszystkie trzy kroki
    python3 narzedzia/zbuduj.py --sprawdz    # tylko bramka, nic nie zapisuje (kod 1 = brud)
"""
import argparse
import os
import re
import shutil
import sys
import zipfile

KORZEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLE = os.path.join(KORZEN, "skille")
PACZKI = os.path.join(KORZEN, "paczki")

KOPIE = [
    ("wspolne/kit_konfig.py", ["vault-ask", "vault-embed", "vault-lint", "hot-slim", "kit-aktualizacja"]),
    ("skille/vault-ask/kod/bm25_pl.py", ["vault-embed"]),
]

ZAKAZANE = [
    (re.compile(r"/Users/[A-Za-z]"), "ścieżka macOS konkretnego użytkownika"),
    (re.compile(r"[A-Z]:\\\\Users\\\\", re.IGNORECASE), "ścieżka Windows konkretnego użytkownika"),
    (re.compile(r"/home/[a-z]"), "ścieżka Linux konkretnego użytkownika"),
    (re.compile(r"/sessions/[a-z0-9-]+/mnt"), "ścieżka konkretnej sesji Cowork"),
    (re.compile("[—–]"), "długi myślnik albo półpauza (reguła stylu kitu)"),
]


PRYWATNE = "słowo z listy prywatnej"
# Linie z adresem repo albo kontaktem autora są celowo publiczne: słowa prywatne tam nie są brudem.
DOZWOLONE_ADRESY = re.compile(r"github\.com/|linkedin\.com/in/|^Copyright")


def zakazane_lokalne():
    p = os.path.join(KORZEN, "narzedzia", ".zakazane-lokalne.txt")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [(re.compile(r"\b%s\b" % re.escape(l.strip()), re.IGNORECASE), PRYWATNE)
                for l in f if l.strip() and not l.startswith("#")]


def pliki_do_sprawdzenia():
    for baza in ("skille", "wspolne", "konfiguracja"):
        for root, dirs, files in os.walk(os.path.join(KORZEN, baza)):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if f.endswith((".md", ".py", ".json", ".txt")):
                    yield os.path.join(root, f)
    for f in ("README.md", "CHANGELOG.md", "onboarding-prompt.txt"):
        p = os.path.join(KORZEN, f)
        if os.path.exists(p):
            yield p


def bramka():
    wzorce = ZAKAZANE + zakazane_lokalne()
    bledy = 0
    for p in pliki_do_sprawdzenia():
        with open(p, encoding="utf-8", errors="replace") as f:
            for nr, linia in enumerate(f, 1):
                for wz, opis in wzorce:
                    if opis == PRYWATNE and DOZWOLONE_ADRESY.search(linia):
                        continue
                    if wz.search(linia):
                        print("BRUD  %s:%d  %s\n      %s" % (os.path.relpath(p, KORZEN), nr, opis, linia.strip()[:110]))
                        bledy += 1
    print("Bramka czystości: %s" % ("czysto" if not bledy else "%d znalezisk" % bledy))
    return bledy


def synchronizuj():
    for zrodlo, cele in KOPIE:
        for skill in cele:
            cel = os.path.join(SKILLE, skill, "kod", os.path.basename(zrodlo))
            os.makedirs(os.path.dirname(cel), exist_ok=True)
            shutil.copyfile(os.path.join(KORZEN, zrodlo), cel)
    print("Kopie wspólnego kodu: zsynchronizowane")


def spakuj():
    os.makedirs(PACZKI, exist_ok=True)
    for skill in sorted(os.listdir(SKILLE)):
        folder = os.path.join(SKILLE, skill)
        if not os.path.isfile(os.path.join(folder, "SKILL.md")):
            continue
        zip_p = os.path.join(PACZKI, skill + ".zip")
        with zipfile.ZipFile(zip_p, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for f in files:
                    pelna = os.path.join(root, f)
                    z.write(pelna, os.path.join(skill, os.path.relpath(pelna, folder)))
        print("Paczka: paczki/%s.zip" % skill)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sprawdz", action="store_true")
    a = ap.parse_args()
    if a.sprawdz:
        sys.exit(1 if bramka() else 0)
    synchronizuj()
    if bramka():
        sys.exit("Nie pakuję: popraw znaleziska bramki.")
    spakuj()


if __name__ == "__main__":
    main()
