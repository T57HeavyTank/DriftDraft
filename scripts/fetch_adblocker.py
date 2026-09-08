"""Scarica uBlock Origin Lite e lo installa in vendor/ublock-origin-lite/.

A cosa serve
------------
La modalita' torneo apre drafter.lol in una finestra Chromium guidata da
Playwright, e carica questa estensione per tenere fuori la pubblicita' del
sito: senza, i banner finiscono sopra i bottoni di ban/pick e intercettano i
click (vedi driftdraft/drafter_live.py, _EXTENSION_PATH). L'estensione viene
anche impacchettata nella distribuzione (vedi driftdraft.spec).

L'estensione E' committata nella repo, quindi per un clone normale questo
script NON serve. Serve per AGGIORNARLA quando ne esce una versione nuova,
senza rifare a mano download/scompattamento.

    python scripts/fetch_adblocker.py                # ultima release
    python scripts/fetch_adblocker.py --tag 2026.901.1442
    python scripts/fetch_adblocker.py --dest /tmp/prova   # senza toccare vendor/

Perche' uBlock Origin Lite e non uBlock Origin "classico": quest'ultimo e'
Manifest V2 e questo Chromium si RIFIUTA di caricarlo ("Impossibile
installare l'estensione perche' utilizza una versione del manifest non
supportata" - errore reale, visto in un test del 2026-09-04). Lite e' la
riscrittura MV3 dello stesso autore.

Solo stdlib apposta: nessuna dipendenza in piu' in requirements.txt per uno
script che gira una volta ogni tanto.
"""

import argparse
import io
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO = "uBlockOrigin/uBOL-home"
API = f"https://api.github.com/repos/{REPO}/releases"
DEFAULT_DEST = Path(__file__).resolve().parent.parent / "vendor" / "ublock-origin-lite"

# L'API di GitHub risponde 403 alle richieste senza User-Agent.
HEADERS = {"User-Agent": "DriftDraft-fetch-adblocker"}


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def find_release(tag: str | None) -> tuple[str, str]:
    """Restituisce (tag, url dello zip chromium) della release richiesta."""
    data = _get_json(f"{API}/tags/{tag}" if tag else f"{API}/latest")

    for asset in data.get("assets", []):
        name = asset["name"]
        # Le release contengono anche il pacchetto firefox e altri file:
        # a noi serve lo zip chromium, che e' quello che Playwright carica
        # con --load-extension.
        if "chromium" in name and name.endswith(".zip"):
            return data["tag_name"], asset["browser_download_url"]

    raise SystemExit(
        f"Nessuno zip chromium nella release {data.get('tag_name')!r}. "
        f"Asset trovati: {[a['name'] for a in data.get('assets', [])]}"
    )


def install(url: str, dest: Path) -> None:
    print(f"Scarico {url}")
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=180) as r:
        blob = r.read()
    print(f"  {len(blob) / 1024 / 1024:.1f} MB scaricati")

    # Scompattare SOPRA una cartella esistente lascerebbe in giro i file
    # della versione vecchia che in quella nuova non esistono piu' - meglio
    # ripartire pulito.
    if dest.exists():
        print(f"Rimuovo la versione precedente in {dest}")
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        z.extractall(dest)

    # Alcune release impacchettano tutto dentro una sottocartella: in quel
    # caso la si "appiattisce", perche' drafter_live.py si aspetta il
    # manifest.json direttamente in vendor/ublock-origin-lite/.
    if not (dest / "manifest.json").exists():
        sub = [p for p in dest.iterdir() if p.is_dir()]
        if len(sub) == 1 and (sub[0] / "manifest.json").exists():
            print(f"Appiattisco la sottocartella {sub[0].name}/")
            for item in sub[0].iterdir():
                shutil.move(str(item), str(dest / item.name))
            sub[0].rmdir()

    manifest = dest / "manifest.json"
    if not manifest.exists():
        raise SystemExit(f"manifest.json non trovato in {dest}: pacchetto inatteso.")

    version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    print(f"OK - uBlock Origin Lite {version} installato in {dest}")
    if not (dest / "LICENSE.txt").exists():
        print("ATTENZIONE: LICENSE.txt assente. E' GPL-3.0, va conservato.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tag", help="release specifica (default: l'ultima)")
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST,
                    help="cartella di destinazione (default: vendor/ublock-origin-lite)")
    args = ap.parse_args()

    tag, url = find_release(args.tag)
    print(f"Release: {tag}")

    current = args.dest / "manifest.json"
    if current.exists():
        installed = json.loads(current.read_text(encoding="utf-8")).get("version")
        print(f"Versione gia' presente: {installed}")
        if installed == tag:
            print("E' gia' l'ultima: niente da fare.")
            return

    install(url, args.dest)
    print("\nRicorda: l'estensione e' committata nella repo, quindi dopo un "
          "aggiornamento va fatto un commit di vendor/ublock-origin-lite/.")


if __name__ == "__main__":
    sys.exit(main())
