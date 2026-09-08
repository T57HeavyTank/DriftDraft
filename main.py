"""DriftDraft - strumento di coaching per le draft di League of Legends.

Copyright (C) 2026 T57HeavyTank

Questo programma e' software libero: puoi ridistribuirlo e/o modificarlo
secondo i termini della GNU General Public License come pubblicata dalla Free
Software Foundation, versione 3 della Licenza o (a tua scelta) una versione
successiva.

Questo programma e' distribuito nella speranza che sia utile, ma SENZA ALCUNA
GARANZIA, senza neppure la garanzia implicita di COMMERCIABILITA' o IDONEITA'
PER UNO SCOPO PARTICOLARE. Vedi la GNU General Public License per i dettagli.

Dovresti aver ricevuto una copia della GNU General Public License insieme a
questo programma (file LICENSE). In caso contrario: <https://www.gnu.org/licenses/>.

Software di terzi spedito insieme a questo programma, immagini e provenienza
dei dati: vedi THIRD-PARTY.md.
"""

import os
import sys
import threading

# Va fatto PRIMA di qualunque import che porti a "import playwright" (la
# catena driftdraft.server -> driftdraft.drafter_live) - impacchettato
# (v1.0) usiamo il Chromium BUNDLATO invece di quello scaricato a parte in
# sviluppo (playwright install chromium, mai presente sulla macchina di chi
# riceve il pacchetto). PLAYWRIGHT_BROWSERS_PATH e' la variabile ufficiale
# che Playwright legge per sapere dove cercare i browser - puntandola alla
# cartella bundlata (vedi driftdraft.spec, stessa struttura
# ms-playwright/chromium-<rev>/... del percorso normale) evita qualunque
# tentativo di download al primo avvio. In sviluppo (non frozen) NON si
# tocca nulla, resta la cache normale di Playwright.
if getattr(sys, "frozen", False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(sys._MEIPASS, "ms-playwright")

import webview

from driftdraft.server import run_server

PORT = 8721
VERSION = "1.9"


def main():
    thread = threading.Thread(
        target=run_server, kwargs={"port": PORT}, daemon=True
    )
    thread.start()

    webview.create_window(
        f"DriftDraft v{VERSION}", f"http://127.0.0.1:{PORT}/", width=1200, height=800
    )
    # private_mode=False: di default pywebview parte in modalita' "privata"
    # (localStorage/cookie MAI salvati su disco, profilo WebView2 effimero -
    # non documentato ovunque, ma esplicito nella docstring di
    # webview.start()) - causava il reset di TUTTI gli slider (icone,
    # pannelli laterali) a ogni riavvio dell'app, segnalato dall'utente
    # 2026-08-18. Nessun rischio noto nel disattivarla: questa finestra
    # carica solo http://127.0.0.1 (il nostro server locale), non visita mai
    # siti esterni - le integrazioni esterne (op.gg, drafter.lol) girano
    # tutte in sessioni Playwright separate, non in questa finestra.
    webview.start(private_mode=False)


if __name__ == "__main__":
    main()
