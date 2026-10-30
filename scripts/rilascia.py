"""Rilascio di una nuova versione di DriftDraft, dall'inizio alla fine.

    python scripts/rilascia.py                   # collaudo, versione, build, prova, pubblicazione
    python scripts/rilascia.py --senza-pubblicare # tutto tranne push e release
    python scripts/rilascia.py --salta-collaudo   # se scripts/collaudo.py e' appena passato

Chiesto dall'utente il 2026-10-30: quando il collaudo periodico trova un sito
cambiato e la correzione e' pronta, la versione nuova deve arrivare a chi usa
l'app senza passaggi a mano. Sono gli stessi passi fatti a mano per la 2.4 e
la 2.5, con gli stessi controlli:

1. Repository a posto: ramo main, niente modifiche non committate al codice,
   non indietro rispetto a GitHub. data/champion_overrides.json e' il lavoro
   dell'utente sui tag e NON entra mai; le draft pro aggiornate da "Aggiorna
   dati" (data/leaguepedia_*.json) entrano, in un commit a parte.
2. Collaudo completo (scripts/collaudo.py): nessun errore, o niente rilascio.
3. Versione +0.1 in driftdraft/version.py (2.5 -> 2.6; dopo la x.9 si passa
   alla (x+1).0), commit "DriftDraft vX.Y".
4. Pacchetto e installer (PyInstaller + Inno Setup), con il controllo che
   dentro non ci siano dati personali.
5. Prova dell'installer: installa, avvia su una porta libera (DRIFTDRAFT_PORT),
   verifica versione e funzioni, disinstalla. Saltata, senza fermare il
   rilascio, se DriftDraft risulta gia' installato su questo pc: installarci
   sopra e poi disinstallare cancellerebbe l'installazione dell'utente.
6. Push di main e del tag, release "DriftDraft vX.Y" con l'installer e la
   descrizione vuota, segnata Latest. Poi la verifica: il file su GitHub ha la
   stessa impronta sha256 di quello costruito qui, e l'ultima release e'
   quella nuova - cioe' l'aggiornamento dall'app la vede.

Sull'account GitHub ci sono altre repository: lo script lavora solo su
T57HeavyTank/DriftDraft e alla fine controlla che le altre non siano cambiate.
"""

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = "T57HeavyTank/DriftDraft"
VENV_PY = RADICE / ".venv" / "Scripts" / "python.exe"
PYINSTALLER = RADICE / ".venv" / "Scripts" / "pyinstaller.exe"
VERSION_PY = RADICE / "driftdraft" / "version.py"
APP_ID_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{7C1B5E42-3F8A-4C6D-9E21-DD1F0A5B7C33}_is1"
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DriftDraft"
DATI_UTENTE = {"data/champion_overrides.json"}
DATI_PRO = {"data/leaguepedia_drafts.json", "data/leaguepedia_tables.json"}
DATI_NEL_PACCHETTO = {"champions.xlsx", "leaguepedia_drafts.json", "leaguepedia_tables.json"}
COAUTORE = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


class Stop(Exception):
    """Rilascio fermato: il messaggio dice perche' e cosa e' gia' stato fatto."""


def passo(testo: str) -> None:
    print(f"\n== {testo}", flush=True)


def git(*args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=RADICE, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise Stop(f"git {' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], cwd=RADICE, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise Stop(f"gh {' '.join(args[:3])}: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def commit(messaggio: str, *file: str) -> None:
    git("add", *file)
    git("commit", "-q", "-m", messaggio, "-m", COAUTORE)


def versione_attuale() -> str:
    m = re.search(r'^VERSION\s*=\s*"(\d+)\.(\d+)"', VERSION_PY.read_text(encoding="utf-8"), re.M)
    if not m:
        raise Stop("VERSION in driftdraft/version.py non e' nel formato X.Y")
    return f"{m.group(1)}.{m.group(2)}"


def prossima(v: str) -> str:
    maggiore, minore = (int(x) for x in v.split("."))
    return f"{maggiore + 1}.0" if minore >= 9 else f"{maggiore}.{minore + 1}"


def porta_libera() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def sha256(percorso: Path) -> str:
    h = hashlib.sha256()
    with percorso.open("rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


def gia_installato() -> str | None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, APP_ID_KEY) as k:
            return winreg.QueryValueEx(k, "DisplayVersion")[0]
    except OSError:
        return None


def processi_installati(ferma: bool) -> list[int]:
    """PID dei processi che girano dalla cartella d'installazione (e solo da
    li': un DriftDraft lanciato da sorgente non viene mai toccato)."""
    comando = (
        f"Get-Process | Where-Object {{ $_.Path -and $_.Path.StartsWith('{INSTALL_DIR}') }} | "
        + ("Stop-Process -Force -PassThru | " if ferma else "")
        + "ForEach-Object { $_.Id }"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", comando], capture_output=True, text=True)
    return [int(x) for x in r.stdout.split() if x.isdigit()]


# ------------------------------------------------------------------ i passi
def controlla_repository() -> list[str]:
    passo("Repository")
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise Stop("non sono sul ramo main")
    sporchi = []
    for riga in git("status", "--porcelain").splitlines():
        percorso = riga[3:].strip().strip('"')
        if percorso in DATI_UTENTE or percorso in DATI_PRO:
            continue
        sporchi.append(riga)
    if sporchi:
        raise Stop("ci sono modifiche non committate che non so se vadano rilasciate:\n  " + "\n  ".join(sporchi))
    git("fetch", "-q", "origin")
    dietro, avanti = (int(x) for x in git("rev-list", "--left-right", "--count", "origin/main...main").split())
    if dietro:
        raise Stop(f"main e' indietro di {dietro} commit rispetto a GitHub: prima va allineato a mano")
    dati_pro = [f for f in DATI_PRO if git("status", "--porcelain", f)]
    print(f"ok: main, {avanti} commit da pubblicare, draft pro aggiornate: {'si' if dati_pro else 'no'}")
    return dati_pro


def collaudo() -> None:
    passo("Collaudo completo (scripts/collaudo.py)")
    r = subprocess.run([str(VENV_PY), "-u", str(RADICE / "scripts" / "collaudo.py")], cwd=RADICE)
    if r.returncode != 0:
        raise Stop("il collaudo ha trovato errori: niente rilascio")


def costruisci(v: str) -> Path:
    passo(f"Pacchetto e installer v{v}")
    log = Path(tempfile.gettempdir()) / f"driftdraft-build-{v}.log"
    with log.open("w", encoding="utf-8") as out:
        for comando in ([str(PYINSTALLER), "--noconfirm", "driftdraft.spec"], [str(VENV_PY), "scripts/build_installer.py"]):
            if subprocess.run(comando, cwd=RADICE, stdout=out, stderr=subprocess.STDOUT).returncode != 0:
                raise Stop(f"build non riuscita ({comando[0]}): vedi {log}")
    dati = {p.name for p in (RADICE / "dist" / "DriftDraft" / "data").iterdir()}
    if not dati <= DATI_NEL_PACCHETTO:
        raise Stop(f"nel pacchetto ci sono file di dati inattesi: {sorted(dati - DATI_NEL_PACCHETTO)}")
    setup = RADICE / "dist" / f"DriftDraft-v{v}-setup.exe"
    if not setup.exists():
        raise Stop(f"installer non trovato: {setup}")
    print(f"ok: {setup.name}, {setup.stat().st_size // (1024 * 1024)} MB, dati: {sorted(dati)}")
    return setup


def prova_installer(setup: Path, v: str) -> str:
    passo("Prova dell'installer")
    gia = gia_installato()
    if gia or INSTALL_DIR.exists():
        return f"saltata: DriftDraft e' gia' installato su questo pc (v{gia}), non lo tocco"
    # Il collegamento sul desktop e' spuntato di default nell'installer: va
    # escluso esplicitamente, altrimenti sovrascriverebbe quello dell'utente
    # e la disinstallazione qui sotto lo cancellerebbe. Si controlla anche
    # che il suo resti identico.
    lnk = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / "DriftDraft.lnk"
    lnk_prima = lnk.read_bytes() if lnk.exists() else None
    try:
        subprocess.run([str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/MERGETASKS=!desktopicon"], check=True)
        if gia_installato() != v:
            raise Stop(f"dopo l'installazione la versione registrata e' {gia_installato()}, non {v}")
        porta = porta_libera()
        subprocess.Popen([str(INSTALL_DIR / "DriftDraft.exe")], env={**os.environ, "DRIFTDRAFT_PORT": str(porta)})
        base = f"http://127.0.0.1:{porta}"
        risposta = None
        for _ in range(120):
            try:
                risposta = json.loads(urllib.request.urlopen(base + "/api/version", timeout=2).read())
                break
            except OSError:
                time.sleep(1)
        if not risposta or risposta.get("version") != v:
            raise Stop(f"l'app installata non risponde come v{v}: {risposta}")
        req = urllib.request.Request(
            base + "/api/pick-suggestions",
            data=json.dumps({"bluePicks": ["Rakan"], "redPicks": ["Xin Zhao"], "taken": []}).encode(),
            headers={"Content-Type": "application/json"},
        )
        s = json.loads(urllib.request.urlopen(req, timeout=60).read())
        if not s.get("blue", {}).get("suggestions"):
            raise Stop("l'app installata non da' pick suggeriti")
        urllib.request.urlopen(base + "/web/lang/en.json", timeout=10).read()
        return f"installata, avviata come v{v}, suggerimenti e lingue ok"
    finally:
        processi_installati(ferma=True)
        time.sleep(3)
        disinstalla = INSTALL_DIR / "unins000.exe"
        if disinstalla.exists():
            subprocess.run([str(disinstalla), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"])
            time.sleep(5)
        if INSTALL_DIR.exists():
            import shutil

            shutil.rmtree(INSTALL_DIR, ignore_errors=True)
        lnk_dopo = lnk.read_bytes() if lnk.exists() else None
        if lnk_dopo != lnk_prima:
            raise Stop("il collegamento DriftDraft.lnk sul desktop e' cambiato durante la prova: controllare a mano")


def altre_repo() -> dict[str, str]:
    dati = json.loads(gh("repo", "list", "T57HeavyTank", "--limit", "100", "--json", "name,pushedAt"))
    return {r["name"]: r["pushedAt"] for r in dati if r["name"] != "DriftDraft"}


def pubblica(setup: Path, v: str) -> str:
    passo(f"Pubblicazione v{v} su GitHub")
    prima = altre_repo()
    git("tag", f"v{v}")
    git("push", "-q", "origin", "main")
    git("push", "-q", "origin", f"v{v}")
    vuoto = Path(tempfile.gettempdir()) / "driftdraft-note-vuote.txt"
    vuoto.write_text("", encoding="utf-8")
    gh("release", "create", f"v{v}", str(setup), "--repo", REPO, "--title", f"DriftDraft v{v}", "--notes-file", str(vuoto), "--latest")
    rel = json.loads(gh("release", "view", f"v{v}", "--repo", REPO, "--json", "assets,body,isDraft"))
    asset = next((a for a in rel["assets"] if a["name"] == setup.name), None)
    if not asset or asset.get("digest", "").removeprefix("sha256:") != sha256(setup):
        raise Stop("il file pubblicato non coincide con quello costruito: controllare la release a mano")
    ultima = gh("api", f"repos/{REPO}/releases/latest", "--jq", ".tag_name")
    if ultima != f"v{v}":
        raise Stop(f"l'ultima release su GitHub risulta {ultima}, non v{v}")
    if altre_repo() != prima:
        print("ATTENZIONE: nel frattempo e' cambiato qualcosa in un'altra repository (non da questo script)")
    return f"https://github.com/{REPO}/releases/tag/v{v}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Rilascio di una nuova versione di DriftDraft")
    parser.add_argument("--senza-pubblicare", action="store_true", help="fa tutto tranne push e release")
    parser.add_argument("--salta-collaudo", action="store_true", help="non rilancia scripts/collaudo.py")
    args = parser.parse_args()

    fatto: list[str] = []
    try:
        dati_pro = controlla_repository()
        if not args.salta_collaudo:
            collaudo()
            fatto.append("collaudo senza errori")
        if dati_pro:
            commit("Draft pro aggiornate", *dati_pro)
            fatto.append("commit delle draft pro aggiornate")
        v_vecchia = versione_attuale()
        v = prossima(v_vecchia)
        if git("tag", "-l", f"v{v}") or git("ls-remote", "--tags", "origin", f"v{v}"):
            raise Stop(f"il tag v{v} esiste gia'")
        testo = VERSION_PY.read_text(encoding="utf-8").replace(f'VERSION = "{v_vecchia}"', f'VERSION = "{v}"')
        VERSION_PY.write_bytes(testo.encode("utf-8"))
        commit(f"DriftDraft v{v}", "driftdraft/version.py")
        fatto.append(f"versione {v_vecchia} -> {v} (commit locale)")
        setup = costruisci(v)
        fatto.append(f"installer {setup.name}")
        fatto.append("prova installer: " + prova_installer(setup, v))
        if args.senza_pubblicare:
            fatto.append("NON pubblicato (--senza-pubblicare)")
        else:
            fatto.append("pubblicato: " + pubblica(setup, v))
    except Stop as e:
        print("\n================ RILASCIO FERMATO ================")
        print(e)
        for f in fatto:
            print("gia' fatto:", f)
        return 1
    print("\n================ RILASCIO COMPLETATO ================")
    for f in fatto:
        print("-", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
