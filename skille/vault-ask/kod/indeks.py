#!/usr/bin/env python3
"""Spis treści vaultu (index.md) generowany bez tokenów.

Po co to istnieje. Przy pytaniu ogólnym („co mam o remoncie?”) Claude czyta jeden plik ze
spisem zamiast przeszukiwać i otwierać kilkanaście notatek. Taki spis
wystarcza do ok. setek stron bez embeddingu. Tu spis składa skrypt, nie model, więc jego
utrzymanie nie kosztuje ani jednego tokena.

Opis notatki: pole `opis` z frontmattera, a gdy go nie ma, pierwszy akapit treści (przycięty).
Pomija: dziennik (to log, nie wiedza), HOT.md (pamięć robocza), notatki `status: obalone`,
foldery ukryte, kwarantannę.

Bezpiecznik: istniejący plik spisu, który nie ma znacznika generatora, jest ręczną pracą
użytkownika. Skrypt go nie nadpisze i powie, jak ustawić inną nazwę.

Użycie:
    python3 indeks.py --vault <vault>            # podgląd: ile notatek, ile znaków, nic nie zapisuje
    python3 indeks.py --vault <vault> --zapisz   # zapisuje spis (domyślnie index.md w korzeniu)

Konfiguracja w <vault>/.kit/konfiguracja.json, klucz `indeks`: `plik`, `limit_znakow`,
`pomijaj_foldery`.
"""
import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bm25_pl
import kit_konfig

ZNACZNIK = "<!-- spis treści kitu (second-brain-claude-kit) -->"
# Starszy znacznik (2.1.0): plik z nim też jest nasz i wolno go przebudować.
ZNACZNIKI = (ZNACZNIK, "<!-- wygenerowane: indeks.py (second-brain-claude-kit) -->")
DL_OPISU = 110


def pierwszy_akapit(tekst):
    for linia in bm25_pl.strip_frontmatter(tekst).splitlines():
        linia = linia.strip()
        if not linia or linia.startswith(("#", "---", "|", "```", "![", "<!--", ">")):
            continue
        linia = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), linia)
        linia = re.sub(r"[*_`]", "", linia).lstrip("-• ").strip()
        if len(linia) > 15:
            return linia
    return ""


def przytnij(t):
    t = " ".join(t.split())
    return t if len(t) <= DL_OPISU else t[:DL_OPISU].rsplit(" ", 1)[0] + "…"


def zbierz(vault, konf, plik_indeksu):
    pomijaj = set(bm25_pl.SKIP_DIRS) | set(kit_konfig.wartosc(konf, "indeks.pomijaj_foldery", []) or [])
    dziennik = kit_konfig.wartosc(konf, "dziennik.folder", "Dziennik")
    grupy = {}
    for root, dirs, files in os.walk(vault):
        dirs[:] = sorted(d for d in dirs if d not in pomijaj and not d.startswith("."))
        rel_root = os.path.relpath(root, vault)
        if rel_root == dziennik or rel_root.startswith(dziennik + os.sep):
            continue
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            rel = os.path.normpath(os.path.join(rel_root, fn))
            if rel in (os.path.normpath(plik_indeksu),
                       os.path.normpath(kit_konfig.wartosc(konf, "hot.plik", "HOT.md"))):
                continue
            try:
                txt = open(os.path.join(root, fn), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            meta = bm25_pl.pola_frontmattera(txt)
            if meta.get("status") == "obalone":
                continue
            grupa = rel.split(os.sep)[0] if os.sep in rel else "(korzeń vaultu)"
            dodatki = [meta[k] for k in ("typ",) if meta.get(k)]
            if meta.get("status") and meta["status"] != "aktualne":
                dodatki.append(meta["status"])
            grupy.setdefault(grupa, []).append(
                (fn[:-3], dodatki, przytnij(meta.get("opis") or pierwszy_akapit(txt))))
    return grupy


def zloz(grupy):
    dzis = datetime.date.today().isoformat()
    n = sum(len(v) for v in grupy.values())
    linie = ["---", "typ: mapa", "status: aktualne", "data: %s" % dzis, "tagi: [indeks]", "---",
             ZNACZNIK, "# Spis treści vaultu", "",
             "Mapa notatek: jedna linia na notatkę. Na co dzień dopisuje ją Claude przy zapisie, skrypt "
             "`indeks.py` składa ją od zera. Opis notatki zmieniasz polem `opis` w jej frontmatterze.",
             "", "%d notatek, stan na %s." % (n, dzis), ""]
    for grupa in sorted(grupy, key=lambda g: (g == "(korzeń vaultu)", g.lower())):
        linie.append("## %s (%d)" % (grupa, len(grupy[grupa])))
        for nazwa, dodatki, opis in grupy[grupa]:
            linie.append("- [[%s]]%s%s" % (nazwa, " (%s)" % ", ".join(dodatki) if dodatki else "",
                                           ": " + opis if opis else ""))
        linie.append("")
    return "\n".join(linie)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=None)
    ap.add_argument("--zapisz", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    vault = kit_konfig.znajdz_vault(a.vault)
    if not vault:
        sys.exit("BŁĄD: nie znalazłem vaultu. Podaj --vault albo ustaw VAULT_DIR.")
    bm25_pl.zastosuj_konfiguracje(vault)
    konf = kit_konfig.wczytaj(vault)
    plik = kit_konfig.wartosc(konf, "indeks.plik", "index.md")
    limit = int(kit_konfig.wartosc(konf, "indeks.limit_znakow", 30000))
    tresc = zloz(zbierz(vault, konf, plik))
    n = tresc.count("\n- [[")
    print("Spis: %d notatek, %d znaków (ok. %d tokenów), limit %d znaków." % (n, len(tresc), len(tresc) // 4, limit))
    if len(tresc) > limit:
        print("UWAGA: spis przekracza limit. Przy takim vaulcie tańsze jest szukanie (vault-ask) niż czytanie "
              "całego spisu; rozważ `indeks.pomijaj_foldery` dla archiwów albo podniesienie limitu.")
    if not a.zapisz:
        print("Podgląd, nic nie zapisano. Dodaj --zapisz, żeby utworzyć %s." % plik)
        return
    cel = os.path.join(vault, plik)
    if os.path.exists(cel):
        with open(cel, encoding="utf-8", errors="ignore") as f:
            poczatek = f.read(2000)
            if not any(z in poczatek for z in ZNACZNIKI):
                sys.exit("STOP: %s istnieje i nie jest wygenerowany przez kit (to Twoja praca). Nie nadpisuję. "
                         "Ustaw inną nazwę w konfiguracji: indeks.plik." % plik)
    os.makedirs(os.path.dirname(cel) or vault, exist_ok=True)
    with open(cel, "w", encoding="utf-8") as f:
        f.write(tresc)
    print("Zapisano: %s" % cel)


if __name__ == "__main__":
    main()
