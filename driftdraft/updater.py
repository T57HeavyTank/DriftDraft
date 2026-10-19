"""Aggiornamento di DriftDraft dall'app stessa (2026-10-19).

Richiesta dell'utente: aggiornare dalle Impostazioni "senza scaricare una
nuova repo ogni volta", e "senza aprire browser, github ecc.". Il flusso:

  1. check(): chiede a GitHub l'ultima release di DriftDraft e la confronta
     con la versione che sta girando (driftdraft/version.py);
  2. start(): scarica l'installer di quella release in una cartella
     temporanea, ne verifica dimensione e impronta SHA-256 (le dichiara
     GitHub stesso per ogni file allegato), poi lancia un piccolo script che
     ASPETTA che DriftDraft si chiuda, installa in silenzio nella stessa
     cartella e lo riapre. Infine chiude l'app.

L'ordine "prima si chiude, poi si installa" non e' un dettaglio: l'installer
deve sovrascrivere DriftDraft.exe e le DLL in _internal/, che a programma
aperto sono bloccate da Windows. Per questo l'installazione la fa un
processo separato che sopravvive alla chiusura dell'app.

Cosa sopravvive all'aggiornamento: tutto cio' che l'utente ha creato (team,
tier list, draft salvate, tag modificati, dati soloQ, immagini scaricate,
impostazioni) - l'installer scrive solo i file del pacchetto. Tornano invece
quelle del pacchetto le draft pro di Leaguepedia (un "Aggiorna dati" le
riporta aggiornate). Verificato leggendo installer/DriftDraft.iss.

Sicurezza: si scarica SOLO dalle release di T57HeavyTank/DriftDraft, SOLO un
file che si chiama come i nostri installer, e non si esegue nulla se
dimensione o impronta non tornano. Da sorgente (non impacchettato) il
controllo funziona ma l'installazione no: non c'e' nessuna installazione da
aggiornare.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

from driftdraft.version import VERSION

REPO = "T57HeavyTank/DriftDraft"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
DOWNLOAD_PREFIX = f"https://github.com/{REPO}/releases/download/"
ASSET_RE = re.compile(r"^DriftDraft-v[\d.]+-setup\.exe$")
UPDATE_DIR = Path(tempfile.gettempdir()) / "DriftDraft-update"

_HEADERS = {
    "User-Agent": f"DriftDraft/{VERSION} (aggiornamento dall'app)",
    "Accept": "application/vnd.github+json",
}


def _versione(testo: str) -> tuple[int, ...]:
    """'v2.10' -> (2, 10). Confronto numerico: come stringhe "2.10" < "2.9"."""
    return tuple(int(x) for x in re.findall(r"\d+", testo or ""))


def can_install() -> bool:
    return bool(getattr(sys, "frozen", False))


def check() -> dict:
    """Confronta la versione installata con l'ultima release su GitHub."""
    risposta = {"current": VERSION, "canInstall": can_install()}
    try:
        req = urllib.request.Request(LATEST_URL, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            rel = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {**risposta, "error": f"Non riesco a contattare GitHub: {e}"}

    tag = str(rel.get("tag_name") or "")
    asset = next(
        (
            a for a in rel.get("assets") or []
            if ASSET_RE.match(str(a.get("name") or ""))
            and str(a.get("browser_download_url") or "").startswith(DOWNLOAD_PREFIX)
        ),
        None,
    )
    disponibile = bool(tag) and _versione(tag) > _versione(VERSION) and asset is not None
    return {
        **risposta,
        "latest": tag.lstrip("v") or None,
        "available": disponibile,
        "asset": {
            "name": asset["name"],
            "url": asset["browser_download_url"],
            "size": int(asset.get("size") or 0),
            "sha256": str(asset.get("digest") or "").removeprefix("sha256:") or None,
        } if asset else None,
    }


# ------------------------------------------------------------------ stato
# Stesso schema degli scarichi di Leaguepedia e soloQ: un thread lavora, la UI
# legge l'avanzamento.
_lock = threading.Lock()
_stato: dict = {"running": False, "phase": "idle"}


def _set(**campi) -> None:
    with _lock:
        _stato.update(campi)


def progress() -> dict:
    with _lock:
        return dict(_stato)


def start(prima_di_uscire=None) -> dict:
    """Avvia scarico, verifica e installazione. Torna subito.

    `prima_di_uscire` lo passa il server: chiude cio' che terrebbe bloccati
    dei file dell'app (il Chromium della modalita' torneo vive in _internal).
    """
    if not can_install():
        return {"error": "L'aggiornamento automatico funziona solo nell'app installata."}
    with _lock:
        if _stato.get("running"):
            return {"alreadyRunning": True}
        _stato.clear()
        _stato.update({"running": True, "phase": "controllo", "done": 0, "total": 0})

    def lavoro() -> None:
        try:
            info = check()
            if info.get("error"):
                raise RuntimeError(info["error"])
            if not info.get("available"):
                raise RuntimeError("Nessun aggiornamento disponibile: hai gia' l'ultima versione.")
            setup = _scarica(info["asset"])
            _set(phase="installo")
            _lancia_installazione(setup)
            time.sleep(0.5)
            _chiudi_app(prima_di_uscire)
        except Exception as e:
            _set(running=False, phase="errore", error=str(e))

    threading.Thread(target=lavoro, daemon=True).start()
    return {"started": True}


def _scarica(asset: dict) -> Path:
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPDATE_DIR / asset["name"]
    totale = int(asset.get("size") or 0)
    _set(phase="scarico", done=0, total=totale)
    hash_ = hashlib.sha256()
    fatti = 0
    req = urllib.request.Request(asset["url"], headers={"User-Agent": _HEADERS["User-Agent"]})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        while True:
            blocco = r.read(1024 * 1024)
            if not blocco:
                break
            f.write(blocco)
            hash_.update(blocco)
            fatti += len(blocco)
            _set(done=fatti)

    _set(phase="verifico")
    if totale and fatti != totale:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"Download incompleto ({fatti} byte su {totale}): non installo niente, riprova.")
    atteso = asset.get("sha256")
    if atteso and hash_.hexdigest().lower() != atteso.lower():
        dest.unlink(missing_ok=True)
        raise RuntimeError("Il file scaricato non corrisponde a quello pubblicato: non installo niente.")
    return dest


def _ps(testo: str) -> str:
    """Stringa PowerShell fra apici singoli (un apice dentro si raddoppia)."""
    return "'" + str(testo).replace("'", "''") + "'"


def _lancia_installazione(setup: Path) -> None:
    """Scrive e avvia lo script che aspetta la chiusura dell'app, installa in
    silenzio e la riapre. Il registro dello script resta nella cartella
    dell'aggiornamento, per capire cosa e' successo se qualcosa va storto."""
    exe = Path(sys.executable)
    script = UPDATE_DIR / "aggiorna.ps1"
    log = UPDATE_DIR / "aggiorna.log"
    script.write_text(
        "\n".join([
            "$ErrorActionPreference = 'Continue'",
            f"Start-Transcript -Path {_ps(log)} -Force | Out-Null",
            f"Wait-Process -Id {os.getpid()} -Timeout 90 -ErrorAction SilentlyContinue",
            "Start-Sleep -Seconds 2",
            # Senza /TASKS l'installer riusa le scelte dell'installazione
            # precedente (collegamento sul desktop si' o no).
            f"$p = Start-Process -FilePath {_ps(setup)} -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -PassThru -Wait",
            "\"installer terminato, codice $($p.ExitCode)\"",
            # Installato non serve piu': senza questo ogni aggiornamento
            # lascerebbe ~280 MB nella cartella temporanea.
            f"Remove-Item -LiteralPath {_ps(setup)} -Force -ErrorAction SilentlyContinue",
            f"Start-Process -FilePath {_ps(exe)}",
            "Stop-Transcript | Out-Null",
        ]),
        encoding="utf-8-sig",
    )
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(script)],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )


def _chiudi_app(prima_di_uscire) -> None:
    """Chiude DriftDraft perche' l'installer possa sostituirne i file."""
    if prima_di_uscire:
        try:
            prima_di_uscire()
        except Exception:
            pass
    try:
        import webview

        for finestra in list(webview.windows):
            finestra.destroy()
    except Exception:
        pass
    # Se la finestra non si chiude da sola (o non c'e', come nel server di
    # prova), si esce comunque: lo script di installazione sta aspettando.
    threading.Timer(4.0, lambda: os._exit(0)).start()
