#!/usr/bin/env python3
"""Test dymny kitu: buduje mały vault w katalogu tymczasowym i uruchamia każdy skrypt.

Sprawdza zachowanie, nie to, czy kod się kompiluje. Każdy warunek to jedna linia OK/BŁĄD.
Warstwa wektorowa (vault-embed) jest testowana tylko wtedy, gdy model jest pobrany
i działają onnxruntime + tokenizers; inaczej test mówi wprost, że ją pominął.

Użycie:  python3 testy/test_kit.py          (kod wyjścia 1, gdy którykolwiek warunek padł)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

KORZEN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
wyniki = []


def sprawdz(warunek, opis, szczegol=""):
    wyniki.append(bool(warunek))
    print(("OK    " if warunek else "BŁĄD  ") + opis + ("" if warunek else "\n      " + szczegol[:600]))


def uruchom(skrypt, *argi, cwd=None, env=None):
    e = dict(os.environ)
    e.pop("VAULT_DIR", None)
    e.update(env or {})
    r = subprocess.run([PY, os.path.join(KORZEN, skrypt)] + list(argi), cwd=cwd, env=e,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def notatka(vault, sciezka, tresc, fm=None):
    p = os.path.join(vault, sciezka)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    naglowek = ""
    if fm:
        naglowek = "---\n" + "".join("%s: %s\n" % kv for kv in fm.items()) + "---\n"
    with open(p, "w", encoding="utf-8") as f:
        f.write(naglowek + tresc)


def zbuduj_vault(v, z_konfiguracja):
    os.makedirs(os.path.join(v, ".obsidian"))
    fm = lambda typ, status="aktualne": {"typ": typ, "status": status, "data": "2026-09-01", "tagi": "[]"}
    notatka(v, "Projekty/Remont kuchni.md",
            "# Remont kuchni\n\n## Decyzja o blacie\nWybraliśmy blat kwarcowy, bo drewno trzeba "
            "olejować co pół roku.\n\n## Wykonawca\nTermin na październik. [[Kontakty wykonawców]]\n",
            fm("decyzja"))
    notatka(v, "Projekty/Stary pomysł.md", "# Stary pomysł\nBlat dębowy, odrzucony.\n", fm("decyzja", "obalone"))
    notatka(v, "Meta/Mapa routingu.md", "# Mapa\n| Temat | Folder |\n|---|---|\n| dom | `Projekty/` |\n", fm("mapa"))
    notatka(v, "Dziennik/2026-09-20.md", "# Dziennik\nRozmowa o blacie kuchennym i olejowaniu.\n", fm("log"))
    notatka(v, "Prywatne/Zdrowie.md", "# Zdrowie\nWizyta u ortopedy, blat biurka za niski.\n", fm("wiedza"))
    notatka(v, "_kwarantanna/2026-01-01-test/kopia.md", "# śmieć\nblat blat blat kwarcowy kwarcowy\n")
    notatka(v, "Zapiski/Budżet.md", "# Budżet\nBudżet HOT.md to 4000 znaków.\n", fm("wiedza"))
    watek = "Wątek testowy (stan na 2026-09-20): " + "x" * 300
    with open(os.path.join(v, "HOT.md"), "w", encoding="utf-8") as f:
        f.write("# HOT: pointer (2026-09-20)\n\n" + watek + "\n\nBudżet HOT.md to 4500 znaków.\n")
    if z_konfiguracja:
        os.makedirs(os.path.join(v, ".kit"))
        with open(os.path.join(KORZEN, "konfiguracja", "konfiguracja.wzor.json"), encoding="utf-8") as f:
            konf = json.load(f)
        konf["hot"]["budzet_znakow"] = 200
        konf["wyszukiwanie"]["wagi_folderow"] = {"Prywatne": 0.1}
        konf["lint"]["fakty"] = [{"etykieta": "test", "wzorzec": r"olejować co (\d+)"}]
        with open(os.path.join(v, ".kit", "konfiguracja.json"), "w", encoding="utf-8") as f:
            json.dump(konf, f, ensure_ascii=False, indent=2)


def main():
    tmp = tempfile.mkdtemp(prefix="kit-test-")
    try:
        v = os.path.join(tmp, "Mój vault")
        os.makedirs(v)
        zbuduj_vault(v, z_konfiguracja=False)

        print("# vault-ask bez konfiguracji")
        kod, out = uruchom("skille/vault-ask/kod/bm25_pl.py", "blat kwarcowy", "--vault", v)
        sprawdz(kod == 0 and "Remont kuchni" in out.split("## 2.")[0], "trafia w notatkę docelową na 1. miejscu", out)
        sprawdz("_kwarantanna" not in out, "kwarantanna poza wynikami", out)
        sprawdz("Stary pomysł" not in out, "status: obalone poza wynikami", out)
        kod, out = uruchom("skille/vault-ask/kod/bm25_pl.py", "blaty kuchenne", "--vault", v)
        sprawdz("Remont kuchni" in out, "fleksja: „blaty kuchenne” znajduje „blat”", out)
        kod, out = uruchom("skille/vault-ask/kod/bm25_pl.py", "blat", "--vault", v, "--folder", "Prywatne")
        sprawdz(kod == 0 and "Zdrowie" in out and "Remont" not in out, "--folder zawęża wyniki", out)
        kod, out = uruchom("skille/vault-ask/kod/bm25_pl.py", "blat", cwd=os.path.join(v, "Projekty"))
        sprawdz(kod == 0 and "Remont kuchni" in out, "autodetekcja vaultu z podfolderu (.obsidian)", out)
        kod, out = uruchom("skille/vault-ask/kod/bm25_pl.py", "blat", cwd=tmp + "/..")
        sprawdz(kod != 0 and "nie znalazłem vaultu" in out, "brak vaultu to błąd z opisem, nie pusty wynik", out)

        print("# hot-slim i vault-lint bez konfiguracji")
        kod, out = uruchom("skille/hot-slim/kod/hot_slim.py", "--vault", v)
        sprawdz(kod == 0 and "budżet 4500" in out, "hot-slim: domyślny budżet 4500", out)
        kod, out = uruchom("skille/vault-lint/kod/vault_lint.py", "--vault", v)
        sprawdz("Kontakty wykonawców" in out, "vault-lint: wykrywa martwy link", out)
        sprawdz("4000" in out and "4500" in out, "vault-lint: wykrywa sprzeczny budżet HOT.md", out)
        sprawdz("kopia.md" not in out, "vault-lint: pomija kwarantannę", out)

        print("# z konfiguracją .kit/konfiguracja.json")
        zbuduj_vault(os.path.join(tmp, "v2"), z_konfiguracja=True)
        v2 = os.path.join(tmp, "v2")
        kod, out = uruchom("skille/hot-slim/kod/hot_slim.py", cwd=v2)
        sprawdz(kod == 1 and "budżet 200" in out and "nadwyżka" in out, "hot-slim: budżet z konfiguracji i autodetekcja", out)
        kod, out = uruchom("skille/vault-ask/kod/bm25_pl.py", "blat biurka ortopeda", "--vault", v2)
        kod2, out2 = uruchom("skille/vault-ask/kod/bm25_pl.py", "blat biurka ortopeda", "--vault", v)
        s1 = float(out.split("## 1. [")[1].split("]")[0]) if "## 1. [" in out else 0
        s2 = float(out2.split("## 1. [")[1].split("]")[0]) if "## 1. [" in out2 else 0
        sprawdz("Zdrowie" in out and s1 < s2, "vault-ask: waga folderu z konfiguracji obniża wynik", "%s vs %s" % (s1, s2))
        kod, out = uruchom("skille/vault-lint/kod/vault_lint.py", cwd=v2)
        sprawdz("test" in out, "vault-lint: własny fakt z konfiguracji jest sprawdzany", out)

        print("# kit-aktualizacja: przegląd")
        changelog = os.path.join(tmp, "CHANGELOG.md")
        with open(changelog, "w", encoding="utf-8") as f:
            f.write("## 2.1.0 (2026-10-01)\n### Nowość w zapisz\n- id: 2.1.0-a\n- dotyczy: zapisz\n"
                    "- zysk: x\n- decyzja: nie\n- migracja: nie\n### Nowość w vault-embed\n- id: 2.1.0-b\n"
                    "- dotyczy: vault-embed\n- zysk: y\n- decyzja: nie\n- migracja: nie\n"
                    "### Pominięta\n- id: 2.1.0-c\n- dotyczy: wszystkie\n- zysk: z\n- decyzja: nie\n- migracja: nie\n"
                    "## 2.0.0 (2026-09-25)\n### Stara\n- id: 2.0.0-a\n- dotyczy: wszystkie\n- zysk: s\n")
        konf_p = os.path.join(v2, ".kit", "konfiguracja.json")
        konf = json.load(open(konf_p, encoding="utf-8"))
        konf["aktualizacje"]["pominiete"] = ["2.1.0-c"]
        json.dump(konf, open(konf_p, "w", encoding="utf-8"), ensure_ascii=False)
        for i in range(5):
            notatka(v2, "Zakupy/Lista %d.md" % i, "# Lista\nmleko\n", {"typ": "dane"})
        kod, out = uruchom("skille/kit-aktualizacja/kod/przeglad.py", "--vault", v2, "--zmiany", changelog, "--dopasowanie")
        try:
            wynik = json.loads(out)
            ids = [w["id"] for w in wynik["zmiany"]["oczekujace"]]
        except (ValueError, KeyError):
            wynik, ids = {}, []
        sprawdz(ids == ["2.1.0-a"], "zmiany: tylko nowsze, dla zainstalowanych skilli, bez pominiętych", out)
        sprawdz(wynik.get("zmiany", {}).get("nowe_skille_do_rozwazenia") == ["vault-embed"],
                "zmiany: skill spoza instalacji trafia do „do rozważenia”", out)
        sygnaly = {s["id"] for s in wynik.get("dopasowanie", {}).get("sygnaly", [])}
        sprawdz("dopasowanie-mapa" in sygnaly and "Zakupy (5)" in out and "Prywatne" not in out,
                "dopasowanie: wykrywa foldery spoza mapy (od 5 notatek)", out)
        notatka(v2, "Dziennik/%s.md" % __import__("datetime").date.today().isoformat(),
                "# D\n" + "".join("## Sesja: %d\n" % i for i in range(5)), {"typ": "log"})
        kod, out = uruchom("skille/kit-aktualizacja/kod/przeglad.py", "--vault", v2, "--dopasowanie")
        sprawdz("dopasowanie-hot-wlacz" in out, "dopasowanie: kilka sesji dziennie proponuje HOT.md", out)
        with open(os.path.join(v2, ".obsidian", "daily-notes.json"), "w", encoding="utf-8") as f:
            json.dump({"folder": "Journal/Daily", "format": "DD.MM.YYYY"}, f)
        kod, out = uruchom("skille/kit-aktualizacja/kod/przeglad.py", "--vault", v2, "--dopasowanie")
        sprawdz("dopasowanie-daily-notes" in out and "Journal/Daily" in out,
                "dopasowanie: inny układ Obsidiana (Daily Notes) jest wykrywany", out)

        print("# kilka vaultów i chmur")
        chmury = {"iCloud": "Library/Mobile Documents/iCloud~md~obsidian/Documents/Prywatny",
                  "Dropbox": "Dropbox (Osobisty)/Obsidian/Praca vault",
                  "OneDrive": "OneDrive - Firma Sp. z o.o/Notatki ąęśź"}
        for nazwa, rel in chmury.items():
            vx = os.path.join(tmp, "dom", rel)
            os.makedirs(os.path.join(vx, ".obsidian"))
            notatka(vx, "Notatka %s.md" % nazwa, "# %s\nunikalneslowo%s blat\n" % (nazwa, nazwa.lower()))
        wyniki_ch = []
        for nazwa, rel in chmury.items():
            vx = os.path.join(tmp, "dom", rel)
            kod, out = uruchom("skille/vault-ask/kod/bm25_pl.py", "blat", "--vault", vx)
            inne = [n for n in chmury if n != nazwa]
            wyniki_ch.append(kod == 0 and ("Notatka %s" % nazwa) in out and not any(("Notatka %s" % i) in out for i in inne))
        sprawdz(all(wyniki_ch), "vault-ask: trzy vaulty w trzech chmurach, ścieżki ze spacjami i ogonkami, zero przecieku", str(wyniki_ch))
        vx = os.path.join(tmp, "dom", chmury["OneDrive"])
        kod, out = uruchom("skille/vault-ask/kod/bm25_pl.py", "blat", env={"VAULT_DIR": vx}, cwd=tmp)
        sprawdz("Notatka OneDrive" in out, "VAULT_DIR wskazuje vault niezależnie od katalogu", out)

        print("# vault-embed")
        try:
            import onnxruntime, tokenizers  # noqa: F401
            ma_pakiety = True
        except ImportError:
            ma_pakiety = False
        model = os.path.expanduser(os.environ.get("KIT_DANE", "~/.cache/second-brain-kit") + "/model/model_fp32.onnx")
        if ma_pakiety and os.path.exists(model):
            dane = os.path.join(tmp, "dane")
            os.makedirs(os.path.join(dane, "model"))
            for f in os.listdir(os.path.dirname(model)):
                os.symlink(os.path.join(os.path.dirname(model), f), os.path.join(dane, "model", f))
            kod, out = uruchom("skille/vault-embed/kod/hybryda.py", "--buduj", "--vault", v, env={"KIT_DANE": dane})
            sprawdz(kod == 0, "vault-embed: budowa indeksu", out)
            kod, out = uruchom("skille/vault-embed/kod/hybryda.py", "dlaczego zrezygnowaliśmy z drewna w kuchni",
                               "--vault", v, env={"KIT_DANE": dane})
            sprawdz(kod == 0 and "Remont kuchni" in out.split("## 2.")[0], "vault-embed: pytanie opisowe trafia", out)
        else:
            print("POMINIĘTE  vault-embed: brak onnxruntime/tokenizers albo modelu w %s" % model)
            kod, out = uruchom("skille/vault-embed/kod/hybryda.py", "--help")
            sprawdz("--folder" in out or "No module named" in out, "vault-embed: skrypt się uruchamia", out)
    finally:
        shutil.rmtree(tmp)

    print("\n%d/%d warunków spełnionych" % (sum(wyniki), len(wyniki)))
    sys.exit(0 if all(wyniki) else 1)


if __name__ == "__main__":
    main()
