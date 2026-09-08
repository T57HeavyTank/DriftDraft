"""Riscarica a mano le immagini dei campioni (icone e splash art).

**Normalmente non serve**: l'app le scarica da sola al primo avvio, e riprende
quelle mancanti ad ogni avvio successivo (vedi driftdraft/champion_art.py).
Questo script esiste per i casi in cui si vuole forzare la cosa da riga di
comando - dopo aver aggiunto un campione nuovo all'xlsx, o per rifare da capo
un set che si sospetta corrotto.

Ha sostituito sync_ddragon_icons.py e sync_splash_art.py, che facevano la
stessa cosa con due copie separate della stessa logica di scarico. Ora la
logica sta in un posto solo, quella che usa anche l'app: se cambia il CDN o
la convenzione degli id, si corregge li' e valgono entrambe le strade.

Uso:
    python scripts/sync_champion_art.py            # solo quelle mancanti
    python scripts/sync_champion_art.py --tutte    # riscarica tutto da capo
"""

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from driftdraft import champion_art


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tutte",
        action="store_true",
        help="cancella le immagini esistenti e le riscarica tutte",
    )
    args = parser.parse_args()

    if args.tutte:
        quante = 0
        for cartella, estensione in (
            (champion_art.ICONS_DIR, "*.png"),
            (champion_art.SPLASH_DIR, "*.jpg"),
        ):
            for f in cartella.glob(estensione):
                f.unlink()
                quante += 1
        print(f"Rimosse {quante} immagini esistenti.")

    stato = champion_art.status()
    print(f"Campioni nell'xlsx: {stato['total']}")
    print(f"Da scaricare: {stato['missing']} "
          f"({stato['missingIcons']} icone, {stato['missingSplash']} splash)")
    if not stato["missing"]:
        print("Niente da fare.")
        return

    ultimo = [0]

    def avanzamento(campi):
        # Una riga ogni 20, non una per file: 346 righe di log non le legge
        # nessuno e nascondono le due che contano.
        if campi.get("phase") == "scarico" and campi["done"] - ultimo[0] >= 20:
            ultimo[0] = campi["done"]
            print(f"  ...{campi['done']}/{campi['total']}")

    esito = champion_art.sync(on_progress=avanzamento)

    print(f"\nScaricate: {esito['downloaded']}  (versione Data Dragon {esito['version']})")
    if esito["failed"]:
        print(f"NON scaricate ({len(esito['failed'])}):")
        for riga in esito["failed"]:
            print(f"  {riga}")
    if esito["unmatched"]:
        # Nome dell'xlsx che Data Dragon non conosce: differenze di apostrofo
        # o accento sono un rischio reale in questo progetto (Kai'Sa, Nunu &
        # Willump). Si segnala invece di indovinare.
        print(f"NESSUNA CORRISPONDENZA su Data Dragon per: {esito['unmatched']}")
    print("Fatto.")


if __name__ == "__main__":
    main()
