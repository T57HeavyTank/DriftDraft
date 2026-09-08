# -*- mode: python ; coding: utf-8 -*-
"""Build PyInstaller per il pacchetto distribuibile (modalita' onedir
- scelta deliberata, non onefile: onefile ri-estrarrebbe l'intero Chromium
bundlato (~430MB) ad ogni avvio, inaccettabile per un'app che si apre
spesso). Uso: pyinstaller driftdraft.spec (dalla root del progetto, con
l'ambiente virtuale attivo)."""

import glob
import os
import shutil

from PyInstaller.utils.hooks import collect_data_files

# Chromium di Playwright - cercato per prefisso invece di un numero di
# revisione fisso, cosi' lo spec non si rompe silenziosamente se in futuro
# "playwright install" scarica una revisione diversa.
#
# BUG REALE trovato dall'utente 2026-08-20 sul pacchetto v1.0 (messaggio
# d'errore Playwright "Executable doesn't exist at ...chrome-headless-shell-
# win64\chrome-headless-shell.exe" cliccando la ricerca counter): il vecchio
# commento qui diceva che chromium_headless_shell-* non serviva perche'
# "tutti lanciano chromium.launch(headless=False o True)" - FALSO, verificato
# col codice sorgente: opgg.py e lolalytics.py chiamano
# p.chromium.launch(args=[...]) SENZA passare headless=, quindi usano il
# default di Playwright (headless=True) - e Playwright 1.62 per un lancio
# headless=True usa un binario SEPARATO ("chrome-headless-shell", non il
# chromium normale) a meno che non sia headless=False esplicito (vedi
# drafter_live.py, quello si'). Va bundlato anche questo secondo binario,
# non solo chromium-*.
_PLAYWRIGHT_CACHE = os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright")


def _find_playwright_browser_dir(prefix: str) -> str:
    dirs = glob.glob(os.path.join(_PLAYWRIGHT_CACHE, f"{prefix}-*"))
    if not dirs:
        raise SystemExit(
            f"'{prefix}' di Playwright non trovato in {_PLAYWRIGHT_CACHE} - "
            "esegui 'playwright install chromium' prima di costruire il pacchetto."
        )
    return dirs[0]


_chromium_dir = _find_playwright_browser_dir("chromium")
_chromium_name = os.path.basename(_chromium_dir)
_headless_shell_dir = _find_playwright_browser_dir("chromium_headless_shell")
_headless_shell_name = os.path.basename(_headless_shell_dir)

# SOLO web/ (codice dell'app) e Chromium/driver Playwright vanno dentro il
# bundle di PyInstaller (_internal/, sola lettura, mai pensato per essere
# aperto da chi usa l'app). assets/ e data/champions.xlsx NON stanno qui -
# BUG REALE segnalato dall'utente (2026-08-20) sulla primissima versione
# del pacchetto: bundlarli come "datas" li mette dentro _internal/, dove
# sono sia difficili da trovare sia, piu' grave, A SOLA LETTURA (modificare
# quella copia non avrebbe alcun effetto - l'app legge sempre lo stesso
# percorso bundlato, mai il file modificato dall'utente). Vanno copiati
# SEPARATAMENTE accanto all'eseguibile dopo la build (vedi in fondo al
# file) - stessa cartella che driftdraft/paths.py::get_app_dir() usa per
# leggerli a runtime.
datas = [
    ("web", "web"),
    # Ad-blocker (uBlock Origin Lite, Manifest V3) per "modalita' torneo" -
    # vedi _EXTENSION_PATH/_dismiss_known_popups in driftdraft/drafter_live.py
    # per il perche' (sostituisce il vecchio watchdog generico, addormentato).
    # Stessa categoria di web/ sopra: codice/tooling dell'app, mai pensato
    # per essere aperto o modificato da chi usa l'app (a differenza di
    # assets/icons ecc. sotto, copiati invece accanto all'eseguibile) -
    # get_bundle_dir() in drafter_live.py la cerca qui. Richiesta esplicita
    # dell'utente 2026-09-04 di includerla nel pacchetto distribuito
    # (~50MB in piu' sul totale, valutato e accettato).
    ("vendor/ublock-origin-lite", "vendor/ublock-origin-lite"),
    (_chromium_dir, f"ms-playwright/{_chromium_name}"),
    (_headless_shell_dir, f"ms-playwright/{_headless_shell_name}"),
]
# Il driver di Playwright (playwright/driver/) contiene node.exe + il vero
# driver JS con cui la libreria Python parla sotto il cofano - NON e'
# codice Python, l'analisi automatica di PyInstaller non lo troverebbe mai
# da solo. Nessun hook dedicato in pyinstaller-hooks-contrib per
# "playwright" (verificato) - va incluso esplicitamente.
datas += collect_data_files("playwright")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DriftDraft",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    # Basta qui - non serve passare icon= anche a webview.start() in main.py.
    # pywebview (backend WinForms su Windows) imposta l'icona della finestra
    # SOLO se le viene passata esplicitamente, altrimenti fa da solo
    # self.Icon = ExtractIconW(..., sys.executable, 0) (winforms.py) - cioe'
    # legge in automatico l'icona gia' incorporata qui nell'exe. Un secondo
    # punto di configurazione sarebbe ridondante.
    icon=os.path.join(SPECPATH, "assets", "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DriftDraft",
)

# Copiati QUI, non tramite "datas" sopra - vanno accanto all'eseguibile
# (DIST_DIR direttamente, non _internal/), facili da trovare e DAVVERO
# rilette dall'app (driftdraft/paths.py::get_app_dir()). A questo punto
# dello script COLLECT ha gia' scritto dist/DriftDraft/ su disco (costruire
# l'oggetto e' cio' che esegue la copia in PyInstaller, non un passo
# separato successivo). roster.json/saved_drafts.json NON copiati
# deliberatamente - richiesta esplicita dell'utente, il pacchetto parte con
# un roster/draft salvate vuoti (dati PERSONALI, non avrebbe senso spedire
# pre-riempiti con quelli di chi ha compilato il pacchetto). DISTPATH/
# SPECPATH sono variabili che PyInstaller inietta automaticamente
# nell'ambiente di esecuzione dello spec, non serve importarle.
DIST_DIR = os.path.join(DISTPATH, "DriftDraft")
# assets/icons e assets/splash NON sono in questo elenco: sono le immagini dei
# campioni, materiale di Riot Games, e il pacchetto ha smesso di spedirle.
# L'app le scarica al primo avvio dai CDN ufficiali sul computer di chi la usa
# (vedi driftdraft/champion_art.py) - via 346 file e 21 MB, e soprattutto via
# la ridistribuzione. Le altre restano: role_icons e rank_icons sono poche
# icone generiche, tiermaker_refs sono riferimenti di lavoro.
for _dst_name in ["assets/role_icons", "assets/tiermaker_refs", "assets/rank_icons"]:
    _src = os.path.join(SPECPATH, _dst_name)
    _dst = os.path.join(DIST_DIR, _dst_name)
    if not os.path.exists(_src):
        continue
    if os.path.exists(_dst):
        shutil.rmtree(_dst)
    shutil.copytree(_src, _dst)

# LICENSE e THIRD-PARTY.md accanto all'eseguibile: la GPL chiede che chi
# riceve il programma riceva anche la licenza, e chi scarica uno zip non ha
# la repository sottomano. THIRD-PARTY.md ci va insieme perche' e' li' che si
# dice quale software di terzi e' spedito dentro e dove prenderne il sorgente
# - in particolare uBlock Origin Lite, che e' anch'esso GPL-3.
for _doc in ("LICENSE", "THIRD-PARTY.md", "README.md"):
    _src_doc = os.path.join(SPECPATH, _doc)
    if os.path.exists(_src_doc):
        shutil.copy2(_src_doc, os.path.join(DIST_DIR, _doc))

_data_dir = os.path.join(DIST_DIR, "data")
os.makedirs(_data_dir, exist_ok=True)
shutil.copy2(
    os.path.join(SPECPATH, "data", "champions.xlsx"),
    os.path.join(_data_dir, "champions.xlsx"),
)

# Dati Leaguepedia (feature 4 - draft/tabelle sinergia-counter, vedi
# driftdraft/leaguepedia.py) - richiesta esplicita dell'utente 2026-08-26:
# A DIFFERENZA di roster.json/saved_drafts.json sopra, questi sono dati
# GENERICI (draft pro pubbliche, non personali) - spedirli gia' pronti come
# base fa funzionare la modalita' training da subito su un'installazione
# nuova, invece di lasciarla vuota finche' non si preme "Aggiorna dati" (che
# puo' richiedere diversi minuti per via del rate limit di Leaguepedia).
# Restano comunque pienamente aggiornabili in seguito con quello stesso
# bottone, che li sovrascrive - questa e' solo la base di partenza. Copia
# OPZIONALE (a differenza di champions.xlsx sopra, che fa fallire tutto se
# manca): se non e' mai stato fatto un sync locale, il pacchetto si compila
# comunque, semplicemente senza questa base pre-caricata.
for _leaguepedia_file in ("leaguepedia_drafts.json", "leaguepedia_tables.json"):
    _src = os.path.join(SPECPATH, "data", _leaguepedia_file)
    if os.path.exists(_src):
        shutil.copy2(_src, os.path.join(_data_dir, _leaguepedia_file))
