#!/usr/bin/env python3
"""Wspólny czytnik konfiguracji Second Brain Claude Kit.

Po co to istnieje. Skille z tego repo są generyczne i mają takie zostać: każda aktualizacja
podmienia je w całości. Wszystko, co jest dopasowaniem do konkretnej osoby (ścieżka vaultu,
budżet HOT.md, wagi folderów w wyszukiwaniu, wersja kitu), żyje w jednym pliku w vaulcie:

    <vault>/.kit/konfiguracja.json

Folder `.kit` jest ukryty w Obsidianie i jedzie razem z vaultem (iCloud, Syncthing, git),
więc ta sama konfiguracja działa na każdym komputerze, na którym otwierasz vault.

Kolejność szukania vaultu (pierwsze trafienie wygrywa):
  1. argument `--vault`,
  2. zmienna środowiskowa `VAULT_DIR`,
  3. w górę od bieżącego katalogu: folder z `.kit/konfiguracja.json`, potem folder z `.obsidian`,
  4. jeden poziom w dół od bieżącego katalogu: podfolder z `.kit/` albo `.obsidian/`.
Brak trafienia to błąd z opisem, nie cicha zgadywanka: skrypt przeszukujący zły katalog
melduje „brak wyników” i nikt nie zauważa, że szukał nie tam.

Ten plik jest kopiowany do `kod/` każdego skilla przez `narzedzia/zbuduj.py`. Źródło prawdy:
`wspolne/kit_konfig.py`. Edytuj tylko tutaj.
"""
import json
import os

PLIK_KONFIGURACJI = os.path.join(".kit", "konfiguracja.json")


def _jest_vaultem(d):
    return os.path.isfile(os.path.join(d, PLIK_KONFIGURACJI)) or os.path.isdir(os.path.join(d, ".obsidian"))


def znajdz_vault(jawny=None):
    """Ścieżka vaultu albo None. Kolejność opisana w docstringu modułu."""
    if jawny:
        return os.path.abspath(os.path.expanduser(jawny))
    env = os.environ.get("VAULT_DIR")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    d = os.path.abspath(os.getcwd())
    while True:
        if _jest_vaultem(d):
            return d
        rodzic = os.path.dirname(d)
        if rodzic == d:
            break
        d = rodzic
    try:
        for pod in sorted(os.listdir(os.getcwd())):
            p = os.path.join(os.getcwd(), pod)
            if os.path.isdir(p) and _jest_vaultem(p):
                return os.path.abspath(p)
    except OSError:
        pass
    return None


def wczytaj(vault):
    """Konfiguracja jako dict. Brak pliku to nie błąd: skille działają na wartościach domyślnych."""
    if not vault:
        return {}
    try:
        with open(os.path.join(vault, PLIK_KONFIGURACJI), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def wartosc(konf, klucz, domyslna=None):
    """Wartość spod klucza z kropkami, np. `hot.budzet_znakow`. Klucze z `_` to komentarze."""
    v = konf
    for czesc in klucz.split("."):
        if not isinstance(v, dict) or czesc not in v:
            return domyslna
        v = v[czesc]
    return v
