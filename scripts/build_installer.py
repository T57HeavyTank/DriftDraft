"""Costruisce l'installer .exe per Windows a partire da dist/DriftDraft.

Prima serve il pacchetto:

    pyinstaller driftdraft.spec
    python scripts/build_installer.py

Serve **Inno Setup 6** installato (gratuito, jrsoftware.org). Non e' una
dipendenza Python e non sta in requirements.txt: e' uno strumento di
compilazione, come PyInstaller stesso.

**Perche' uno script invece di lanciare ISCC a mano**: la versione. Sta in
main.py, e se l'installer la tenesse scritta per conto suo diventerebbe il
secondo posto da ricordarsi di aggiornare ad ogni release - il tipo di
duplicazione che prima o poi produce un installer "v1.9" che dentro ha la 2.0.
Qui si legge da main.py e si passa a Inno, quindi resta un posto solo.
"""

import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RADICE = Path(__file__).resolve().parent.parent
ISS = RADICE / "installer" / "DriftDraft.iss"
PACCHETTO = RADICE / "dist" / "DriftDraft"

# Percorsi tipici di Inno Setup 6. Cercati invece di richiedere che sia nel
# PATH: il suo installer non ce lo mette.
#
# Il terzo e' quello PER-UTENTE, ed e' dove finisce installandolo con winget -
# scoperto provandolo: cercavo solo in Program Files e non lo trovavo pur
# essendo appena stato installato con successo.
import os

CANDIDATI_ISCC = [
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
]


def versione() -> str:
    testo = (RADICE / "main.py").read_text(encoding="utf-8")
    m = re.search(r'^VERSION\s*=\s*"([^"]+)"', testo, re.MULTILINE)
    if not m:
        sys.exit("Non trovo VERSION in main.py.")
    return m.group(1)


def trova_iscc() -> Path:
    for p in CANDIDATI_ISCC:
        if p.exists():
            return p
    import shutil

    trovato = shutil.which("ISCC.exe") or shutil.which("iscc")
    if trovato:
        return Path(trovato)
    sys.exit(
        "Inno Setup 6 non trovato.\n"
        "Scaricalo da https://jrsoftware.org/isdl.php (gratuito) oppure:\n"
        "  winget install JRSoftware.InnoSetup"
    )


def main() -> None:
    if not PACCHETTO.is_dir():
        sys.exit(
            f"Manca {PACCHETTO}.\nCostruisci prima il pacchetto: pyinstaller driftdraft.spec"
        )

    # Controllo che vale la pena fare qui e non scoprire a installazione
    # avvenuta: se il pacchetto contiene ancora le immagini dei campioni,
    # vuol dire che e' stato costruito con uno spec vecchio, e l'installer
    # ridistribuirebbe materiale Riot che abbiamo deciso di non spedire.
    for cartella in ("icons", "splash"):
        d = PACCHETTO / "assets" / cartella
        if d.is_dir() and any(d.iterdir()):
            sys.exit(
                f"{d} non e' vuota: il pacchetto contiene le immagini dei campioni.\n"
                "Ricostruiscilo con lo spec aggiornato (pyinstaller driftdraft.spec):\n"
                "quelle immagini non vanno ridistribuite, le scarica l'app."
            )

    v = versione()
    iscc = trova_iscc()
    print(f"Versione da main.py: {v}")
    print(f"Inno Setup:          {iscc}")
    print(f"Pacchetto:           {PACCHETTO}")
    print()

    esito = subprocess.run(
        [str(iscc), f"/DMyAppVersion={v}", str(ISS)],
        cwd=str(ISS.parent),
    )
    if esito.returncode != 0:
        sys.exit(f"ISCC ha restituito {esito.returncode}.")

    prodotto = RADICE / "dist" / f"DriftDraft-v{v}-setup.exe"
    if prodotto.exists():
        mb = prodotto.stat().st_size / 1024 / 1024
        print(f"\nFatto: {prodotto}  ({mb:.0f} MB)")
    else:
        print("\nISCC e' andato a buon fine ma non trovo il file atteso:", prodotto)


if __name__ == "__main__":
    main()
