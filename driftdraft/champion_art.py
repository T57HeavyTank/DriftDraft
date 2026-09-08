"""Immagini dei campioni: scaricate sul computer di chi usa l'app, non
spedite dentro il pacchetto.

**Perche' non le spediamo piu'.** Icone e splash art sono materiale di Riot
Games. La loro policy per i progetti amatoriali ("Legal Jibber Jabber",
letta il 2026-09-08) e' restrittiva su chi ridistribuisce quel materiale.
Facendole scaricare al primo avvio, da Data Dragon e Community Dragon che
sono i CDN ufficiali/di riferimento, DriftDraft smette di essere un
ridistributore: chi usa l'app prende le immagini dalla fonte, come farebbe
aprendo il sito. Effetto collaterale gradito: 21 MB e 346 file in meno nella
repository e nel pacchetto.

**Da dove.** Le icone quadrate da **Data Dragon** (CDN ufficiale Riot,
versionato); le splash "centered" 16:9 da **Community Dragon** - le stesse
che usa drafter.lol per il banner del campione pickato, verificato
ispezionando il suo DOM. Sono due fonti diverse perche' Data Dragon non ha
l'inquadratura centrata che serve ai riquadri dei giocatori.

**L'id.** Entrambe usano l'id Data Dragon ("Kaisa", "MonkeyKing", "Nunu"),
non il nome visualizzato ("Kai'Sa", "Wukong", "Nunu & Willump"). Community
Dragon accetta lo stesso id, quindi non serve una seconda mappatura - cosa
che eviterebbe comunque un suo insieme di doppioni da filtrare.

I file finiscono in `get_app_dir()/assets/`, cioe' accanto all'eseguibile e
scrivibile: la stessa cartella da cui il server li serve gia' oggi, e dove chi
usa l'app puo' metterne di suoi per un campione nuovo.
"""

import json
import threading
import time
import urllib.request
from pathlib import Path

from driftdraft.data import load_champions
from driftdraft.paths import get_app_dir

DDRAGON_VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"

ICONS_DIR = get_app_dir() / "assets" / "icons"
SPLASH_DIR = get_app_dir() / "assets" / "splash"

# Senza uno User-Agent realistico questa classe di CDN Riot/CommunityDragon
# risponde spesso 403 - gia' incontrato negli script di sincronizzazione.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
}

_lock = threading.Lock()
_state: dict = {"running": False}


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def _fetch_bytes(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def icon_path(champion: str) -> Path:
    return ICONS_DIR / f"{champion}.png"


def splash_path(champion: str) -> Path:
    return SPLASH_DIR / f"{champion}.jpg"


def status() -> dict:
    """Cosa manca, senza toccare la rete.

    Serve all'avvio per decidere se mostrare la schermata di scaricamento, e
    dev'essere istantaneo: e' solo un giro di `exists()` sul disco.
    """
    try:
        champs = load_champions()
    except Exception as e:
        return {"total": 0, "missingIcons": 0, "missingSplash": 0, "error": str(e)}
    mancanti_icone = [c.name for c in champs if not icon_path(c.name).exists()]
    mancanti_splash = [c.name for c in champs if not splash_path(c.name).exists()]
    return {
        "total": len(champs),
        "missingIcons": len(mancanti_icone),
        "missingSplash": len(mancanti_splash),
        "missing": len(mancanti_icone) + len(mancanti_splash),
        "error": None,
    }


def sync(on_progress=None) -> dict:
    """Scarica solo quello che manca. Sincrona: usare start_sync() dall'app.

    Le ICONE per prime e le splash dopo, deliberatamente: le icone sono la
    griglia, cioe' cio' che rende l'app usabile, mentre le splash sono
    decorazione nei riquadri dei giocatori. Su una connessione lenta e' la
    differenza fra "posso lavorare dopo 5 MB" e "aspetto 21 MB".

    Un file che non si scarica NON interrompe il resto: viene contato fra i
    falliti e si va avanti. Un campione senza immagine e' un buco visivo, non
    un'applicazione rotta, e riprovare piu' tardi costa un click.
    """
    champs = load_champions()
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    SPLASH_DIR.mkdir(parents=True, exist_ok=True)

    def avanzamento(**campi):
        if on_progress:
            on_progress(campi)

    avanzamento(phase="versione", done=0, total=0)
    version = _fetch_json(DDRAGON_VERSIONS_URL)[0]

    avanzamento(phase="elenco", done=0, total=0, version=version)
    ddragon = _fetch_json(
        f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    )["data"]
    # nome visualizzato -> id usato negli URL
    per_nome = {v["name"]: v["id"] for v in ddragon.values()}

    lavoro = []
    senza_corrispondenza = []
    for c in champs:
        ddragon_id = per_nome.get(c.name)
        if not ddragon_id:
            # Nome dell'xlsx che Data Dragon non conosce: si segnala invece di
            # indovinare. Apostrofi e "&" sono un rischio reale e gia' visto.
            senza_corrispondenza.append(c.name)
            continue
        if not icon_path(c.name).exists():
            lavoro.append(("icon", c.name, ddragon_id))
    for c in champs:
        ddragon_id = per_nome.get(c.name)
        if ddragon_id and not splash_path(c.name).exists():
            lavoro.append(("splash", c.name, ddragon_id))

    totale = len(lavoro)
    falliti = []
    for i, (tipo, nome, ddragon_id) in enumerate(lavoro, 1):
        avanzamento(phase="scarico", done=i - 1, total=totale, champion=nome)
        try:
            if tipo == "icon":
                url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{ddragon_id}.png"
                icon_path(nome).write_bytes(_fetch_bytes(url))
            else:
                url = f"https://cdn.communitydragon.org/latest/champion/{ddragon_id}/splash-art/centered"
                splash_path(nome).write_bytes(_fetch_bytes(url))
        except Exception as e:
            falliti.append(f"{nome} ({tipo}): {e}")

    avanzamento(phase="fatto", done=totale, total=totale)
    return {
        "downloaded": totale - len(falliti),
        "failed": falliti,
        "unmatched": senza_corrispondenza,
        "version": version,
    }


def sync_progress() -> dict:
    with _lock:
        return dict(_state)


def start_sync() -> dict:
    """Avvia lo scaricamento in un thread e torna subito.

    Un solo scaricamento per volta: due in parallelo scriverebbero sugli
    stessi file e si darebbero fastidio a vicenda sul CDN.
    """
    with _lock:
        if _state.get("running"):
            return {"alreadyRunning": True}
        _state.clear()
        _state.update({"running": True, "phase": "avvio", "done": 0, "total": 0,
                       "startedAt": time.time()})

    def aggiorna(campi):
        with _lock:
            _state.update(campi)

    def worker():
        try:
            esito = sync(on_progress=aggiorna)
        except Exception as e:
            with _lock:
                _state.update({"running": False, "phase": "errore", "error": str(e),
                               "finishedAt": time.time()})
            return
        with _lock:
            _state.update({
                "running": False,
                "phase": "fatto",
                "error": None,
                "failed": esito["failed"],
                "unmatched": esito["unmatched"],
                "finishedAt": time.time(),
            })

    threading.Thread(target=worker, daemon=True).start()
    return {"started": True}
