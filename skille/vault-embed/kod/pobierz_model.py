#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jednorazowe pobranie modelu embeddingu (ONNX) do ~/.cache/second-brain-kit/model/.

To JEDYNY plik w tym projekcie, ktory rusza siec, i rusza ja tylko po wagi modelu.
Tresc notatek nie wychodzi stad nigdzie i nigdy. Po pobraniu caly folder model/ mozna
przeniesc na inna maszyne (np. na Maca) i wyszukiwarka dziala bez sieci.

Domyslny model to multilingual-e5-base (768 wym.), nie -small: pomiar 17.09.2026 (patrz
Narzedzia/vault-embed - wybor modelu embeddingu.md w vaulcie) pokazal, ze e5-base w parze
z routingiem BM25/wektor po dlugosci zapytania (hybryda.py, PROG_ROUTER_SLOW) bije e5-small
na kazdej mierzonej metryce. e5-small zostaje dostepny przez --model small, jako rollback,
gdyby ktos wolal stary, mniejszy model (118-470 MB zamiast 480 MB-1,1 GB).

Uzycie:
    py pobierz_model.py                 # e5-base, pelna precyzja (1,1 GB), domyslne
    py pobierz_model.py --model small   # e5-small (stary domyslny sprzed 17.09.2026)
    py pobierz_model.py --int8          # wersja skwantyzowana zamiast fp32
    py pobierz_model.py --obie          # int8 i fp32 naraz

Uwaga dla Windows z Nortonem: Norton podmienia certyfikat TLS, przez co urllib i certifi
potrafia odmowic polaczenia (objaw: "certificate verify failed" albo "UnknownIssuer").
Skrypt sam sprobuje wtedy magazynu certyfikatow systemu Windows.
"""
import os, sys, ssl, argparse, urllib.request, hashlib

# Model trafia do katalogu danych kitu, nie do folderu skilla (ten podmienia każda
# aktualizacja) i nie do vaultu (1,1 GB nie może jechać przez iCloud). Zmiana: KIT_DANE.
DOCELOWY = os.path.join(os.path.expanduser(os.environ.get("KIT_DANE") or "~/.cache/second-brain-kit"), "model")
ZRODLA = {
    "base":  "https://huggingface.co/Xenova/multilingual-e5-base/resolve/main",
    "small": "https://huggingface.co/Xenova/multilingual-e5-small/resolve/main",
}

PLIKI_WSPOLNE = [
    ("tokenizer.json", "tokenizer.json"),
    ("config.json", "config.json"),
    ("tokenizer_config.json", "tokenizer_config.json"),
]
PLIK_INT8 = ("onnx/model_quantized.onnx", "model_quantized.onnx")
PLIK_FP32 = ("onnx/model.onnx", "model_fp32.onnx")


def kontekst_ssl(zrodlo):
    """Domyslny kontekst; przy zerwanym lancuchu (Norton) magazyn systemu Windows."""
    try:
        ctx = ssl.create_default_context()
        urllib.request.urlopen(urllib.request.Request(zrodlo + "/config.json",
                                                      method="HEAD"),
                               context=ctx, timeout=20)
        return ctx
    except Exception as e:
        print("  Domyslny lancuch TLS odrzucony (%s)." % type(e).__name__)
        print("  Probuje magazynu certyfikatow systemu...")
        ctx = ssl.create_default_context()
        try:
            ctx.load_default_certs(ssl.Purpose.SERVER_AUTH)
            if sys.platform == "win32":
                import wincertstore  # opcjonalnie
        except Exception:
            pass
        return ctx


def pobierz(zdalny, lokalny, ctx, zrodlo):
    cel = os.path.join(DOCELOWY, lokalny)
    if os.path.isfile(cel) and os.path.getsize(cel) > 0:
        print("  jest juz: %-26s %12s B" % (lokalny, format(os.path.getsize(cel), ",")))
        return
    url = "%s/%s" % (zrodlo, zdalny)
    print("  pobieram: %s" % lokalny, flush=True)
    tmp = cel + ".czesciowy"
    with urllib.request.urlopen(url, context=ctx, timeout=600) as r, open(tmp, "wb") as f:
        ile = 0
        while True:
            kawalek = r.read(1 << 20)
            if not kawalek:
                break
            f.write(kawalek)
            ile += len(kawalek)
            print("\r    %s MB" % format(ile >> 20, ","), end="", flush=True)
    print()
    os.replace(tmp, cel)
    print("  gotowe:   %-26s %12s B" % (lokalny, format(os.path.getsize(cel), ",")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["base", "small"], default="base",
                    help="base (768 wym., domyslny od 17.09.2026) albo small (rollback)")
    ap.add_argument("--int8", action="store_true", help="skwantyzowana zamiast fp32")
    ap.add_argument("--obie", action="store_true", help="int8 i fp32 naraz")
    a = ap.parse_args()

    zrodlo = ZRODLA[a.model]
    os.makedirs(DOCELOWY, exist_ok=True)
    print("Folder docelowy: %s (model: %s)" % (DOCELOWY, a.model))
    ctx = kontekst_ssl(zrodlo)

    lista = list(PLIKI_WSPOLNE)
    if a.obie:
        lista += [PLIK_INT8, PLIK_FP32]
    elif a.int8:
        lista += [PLIK_INT8]
    else:
        lista += [PLIK_FP32]

    for zdalny, lokalny in lista:
        pobierz(zdalny, lokalny, ctx, zrodlo)

    print("\nGotowe. Teraz zbuduj indeks:  python3 hybryda.py --buduj --vault <sciezka do vaultu>")


if __name__ == "__main__":
    main()
