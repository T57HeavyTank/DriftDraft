"""Risoluzione dei percorsi delle risorse, sensibile a se l'app gira da
sorgente (sviluppo) o "frozen" dentro un eseguibile PyInstaller (pacchetto
distribuito, v1.0) - due funzioni distinte perche' le due categorie di
risorse hanno bisogni opposti:

- get_bundle_dir(): CODICE dell'app, mai pensato per essere aperto da chi
  usa l'app (web/ - html/css/js). Usa sys._MEIPASS quando "frozen" - dentro
  _internal/, la cartella che PyInstaller usa per tutto cio' che serve
  SOLO al funzionamento interno (DLL, runtime Python, driver Playwright).
- get_app_dir(): CONTENUTO che chi usa l'app puo' legittimamente voler
  trovare/modificare - data/champions.xlsx (aggiungere campioni/patch,
  BUG REALE segnalato dall'utente 2026-08-20: la primissima versione del
  pacchetto lo bundlava dentro _internal/ come get_bundle_dir(), quindi
  praticamente introvabile E comunque a sola lettura - modificarlo non
  avrebbe avuto alcun effetto, l'app avrebbe continuato a leggere la copia
  bundlata originale), data/roster.json (salvato dall'app stessa),
  assets/icons (aggiungere l'icona di un campione nuovo). Usa la cartella
  DELL'ESEGUIBILE quando "frozen" - MAI _MEIPASS, deliberatamente fuori da
  _internal/, cosi' e' visibile subito accanto a DriftDraft.exe.
"""

import sys
from pathlib import Path


def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
