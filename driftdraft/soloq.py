"""Dati soloQ (lolalytics, Emerald+, ultimi 30 giorni) scaricati in locale.

Perche' esiste (utente, 2026-09-23, dopo tre settimane d'uso e i feedback di
altri tester): campioni come Briar ed Evelynn non si vedono MAI nelle partite
pro - "hanno un modo di giocare altamente punibile da giocatori competenti" -
ma in Emerald rendono anche piu' dei pick classici. Nei dati pro quindi non
esiste nessuna risposta a Briar, e l'app davanti a Briar diceva in pratica
"non possiamo fare niente": proprio i campioni che dovrebbero avere piu'
suggerimenti ne avevano zero. "E' un paradosso, ma allo stato attuale dei dati
e' cosi'". Gli stessi dati servono ai ban suggeriti (quanto un campione soffre
contro un altro) e alla ricerca counter, che non deve piu' aprire un browser.

COSA SI E' MISURATO PRIMA DI USARLI (script in DriftDraft-analisi/lolalytics,
fuori dalla repo; dettagli nella memoria di progetto):
  - i pro rispondono seguendo i counter soloQ in tutte e cinque le corsie
    (chi pesca dopo nella stessa corsia ha +0.26 punti di vantaggio soloQ
    contro -0.02 del caso, z +23), anche al netto di blind/counter pick;
  - la sinergia soloQ la seguono solo in bot-support (z +39): nelle altre
    coppie di corsie non corrisponde a niente, e qui non si scarica nemmeno;
  - nei ban di seconda fase i pro colpiscono le corsie ancora aperte del
    nemico e i campioni che counterano i loro pick (z +61 e +20).
I pesi con cui questi numeri entrano nei suggerimenti sono tarati sulle stesse
partite: vedi training_bot (SOLOQ_*, BAN_*).

DA DOVE VENGONO. Il sito non ha un'API pubblica documentata, ma le sue pagine
leggono i dati da un endpoint JSON (visto osservando il traffico della pagina
build, 2026-09-23):
  a1.lolalytics.com/mega/?ep=counter   stats del campione nella corsia (winrate,
                                       pick rate, quota di partite per corsia)
                                       + matchup contro una corsia avversaria,
                                       solo quelli con ~100+ partite, gli
                                       stessi che mostra la pagina counter;
  a1.lolalytics.com/mega/?ep=build-team i compagni di tutte e 4 le altre corsie.
Una GET semplice, niente browser: circa 470 richieste da 10-20 KB invece delle
5 ore dello scarico fatto col browser per l'analisi. Endpoint NON documentato:
puo' cambiare senza preavviso. Se smette di funzionare lo scarico fallisce con
un messaggio e i dati gia' su disco restano quelli di prima; la ricerca counter
ripiega da sola sul metodo col browser (lolalytics.fetch_counters).

COSA SI SCARICA. Solo le corsie in cui un campione gioca almeno il 5% delle
sue partite (339 pagine su 865, il 97% delle partite): la prima richiesta per
campione, senza corsia, restituisce proprio quella distribuzione. Per ogni
pagina i counter della STESSA corsia; per tiratori e support anche l'altra
corsia del bot (la lane e' 2 contro 2); per i support i compagni tiratori.

I dati li scarica l'app di chi la usa e restano su quel computer: non vanno
nell'installer (decisione presa quando si e' valutato lolalytics: robots.txt
permette, "use=reference", nessun termine d'uso pubblicato). Richieste una
alla volta con una pausa fra l'una e l'altra, una volta per patch.
"""

import json
import threading
import time
import urllib.error
import urllib.request

from driftdraft.data import load_champions, slugify_champion_name
from driftdraft.paths import get_app_dir

SOLOQ_PATH = get_app_dir() / "data" / "soloq.json"

API_URL = "https://a1.lolalytics.com/mega/"
TIER = "emerald_plus"
PATCH = "30"  # "ultimi 30 giorni" nel vocabolario del sito
LANES = ("top", "jungle", "middle", "bottom", "support")
# Vocabolario dell'app (Champion.roles, ROLE_ORDER) <-> corsie del sito.
ROLE_TO_LANE = {"Top": "top", "Jungle": "jungle", "Mid": "middle", "Bot": "bottom", "Support": "support"}
LANE_TO_ROLE = {v: k for k, v in ROLE_TO_LANE.items()}

# Corsie da scaricare: quelle con almeno questa quota delle partite del campione.
LANE_SHARE_MIN = 0.05
# Pausa fra due richieste: il sito non ci deve nulla, e 470 richieste in fila
# senza respiro sarebbero scortesi. Con ~0.3 s di risposta fanno 5-6 minuti.
REQUEST_PAUSE_S = 0.35
REQUEST_TIMEOUT_S = 20
MAX_ATTEMPTS = 4
# Oltre questa quota di richieste fallite lo scarico si considera guasto e NON
# sostituisce i dati buoni su disco (stesso principio del sync Leaguepedia).
MAX_FAILED_SHARE = 0.1

# Restringimento verso zero secondo le partite: valore * n / (n + k). Un
# matchup da 150 partite ha un rumore di ~4 punti di winrate, uno da 20.000 di
# 0.35. k e' 2500 / varianza VERA fra i matchup molto giocati, stimata sui dati
# scaricati per l'analisi nelle stesse condizioni dell'app (un lato solo,
# 100+ partite): 1788 per i counter, 1664 per la sinergia bot-support.
SHRINK_COUNTER = 1788.0
SHRINK_SYNERGY = 1664.0

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _get(params: dict) -> dict:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(f"{API_URL}?{query}", headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_retry(params: dict, on_wait=None) -> dict:
    for tentativo in range(1, MAX_ATTEMPTS + 1):
        try:
            return _get(params)
        except (urllib.error.URLError, TimeoutError, ValueError, ConnectionError) as e:
            if tentativo == MAX_ATTEMPTS:
                raise
            attesa = 2 ** tentativo
            if on_wait:
                on_wait(attesa, tentativo, str(e))
            time.sleep(attesa)
    raise RuntimeError("irraggiungibile")


def _base(slug: str) -> dict:
    return {"ep": "counter", "v": "1", "patch": PATCH, "c": slug, "tier": TIER, "queue": "ranked", "region": "all"}


def fetch_all(on_progress=None) -> dict:
    """Scarica tutto e ritorna il dizionario da salvare. Non scrive su disco."""
    champions = [c for c in load_champions() if c.riot_id]
    by_id = {c.riot_id: c.name for c in champions}
    avanzamento = {"phase": "corsie", "done": 0, "target": len(champions), "failed": 0}

    def notify(**campi):
        avanzamento.update(campi)
        if on_progress:
            on_progress(dict(avanzamento))

    def wait_cb(secondi, tentativo, motivo):
        notify(phase="attesa", seconds=secondi, attempt=tentativo, reason=motivo)

    pages: dict[str, dict] = {}
    shares: dict[str, dict[str, float]] = {}
    avg_wr = None
    falliti = 0

    def counters_list(raw: dict) -> dict:
        out = {}
        for x in raw.get("counters") or []:
            nome = by_id.get(x.get("cid"))
            if nome and x.get("n"):
                # [d2, partite, winrate della pagina contro l'avversario]
                out[nome] = [x.get("d2") or 0.0, int(x["n"]), x.get("vsWr")]
        return out

    # 1. una richiesta per campione nella sua corsia principale: porta anche
    #    la quota di partite per corsia, che decide le altre pagine da scaricare
    lavoro = []
    for i, champ in enumerate(champions):
        slug = slugify_champion_name(champ.name)
        try:
            raw = _get_retry(_base(slug), wait_cb)
        except Exception:
            falliti += 1
            notify(phase="corsie", done=i + 1, failed=falliti)
            continue
        stats = raw.get("stats") or {}
        lane = stats.get("lane")
        quote = {l: float(v) / 100.0 for l, v in (stats.get("lanes") or {}).items() if l in LANES}
        shares[champ.name] = quote
        if avg_wr is None and stats.get("avgWr"):
            avg_wr = float(stats["avgWr"])
        if lane in LANES:
            pages[f"{champ.name}|{lane}"] = {
                "wr": float(stats.get("wr") or 0) or None,
                "pr": float(stats.get("pr") or 0),
                "counters": {lane: counters_list(raw)},
            }
            if lane in ("bottom", "support"):
                lavoro.append(("vs", champ.name, slug, lane, "support" if lane == "bottom" else "bottom"))
            if lane == "support":
                lavoro.append(("team", champ.name, slug, lane, None))
        for altra, q in quote.items():
            if altra != lane and q >= LANE_SHARE_MIN:
                lavoro.append(("page", champ.name, slug, altra, altra))
                if altra in ("bottom", "support"):
                    lavoro.append(("vs", champ.name, slug, altra, "support" if altra == "bottom" else "bottom"))
                if altra == "support":
                    lavoro.append(("team", champ.name, slug, altra, None))
        notify(phase="corsie", done=i + 1, failed=falliti)
        time.sleep(REQUEST_PAUSE_S)

    # 2. le altre corsie, l'altra corsia del bot e i compagni dei support.
    #    L'ordine conta: una "page" crea la pagina che "vs" e "team" completano.
    ordine = {"page": 0, "vs": 1, "team": 2}
    lavoro.sort(key=lambda t: ordine[t[0]])
    totale = len(champions) + len(lavoro)
    notify(phase="pagine", done=len(champions), target=totale)
    for j, (tipo, nome, slug, lane, vslane) in enumerate(lavoro):
        chiave = f"{nome}|{lane}"
        try:
            if tipo == "team":
                raw = _get_retry({**_base(slug), "ep": "build-team", "lane": lane}, wait_cb)
                intest = raw.get("team_h") or ["id", "wr", "d1", "d2", "pr", "n"]
                col = {k: intest.index(k) for k in ("id", "d2", "n") if k in intest}
                compagni = {}
                for riga in (raw.get("team") or {}).get("bottom") or []:
                    nome_b = by_id.get(riga[col["id"]])
                    if nome_b and riga[col["n"]]:
                        compagni[nome_b] = [riga[col["d2"]] or 0.0, int(riga[col["n"]])]
                if chiave in pages:
                    pages[chiave]["synergy_bottom"] = compagni
            else:
                raw = _get_retry({**_base(slug), "lane": lane, "vslane": vslane}, wait_cb)
                stats = raw.get("stats") or {}
                pagina = pages.setdefault(chiave, {"counters": {}})
                if tipo == "page":
                    pagina["wr"] = float(stats.get("wr") or 0) or None
                    pagina["pr"] = float(stats.get("pr") or 0)
                pagina["counters"][vslane] = counters_list(raw)
        except Exception:
            falliti += 1
        notify(phase="pagine", done=len(champions) + j + 1, failed=falliti)
        time.sleep(REQUEST_PAUSE_S)

    if falliti > MAX_FAILED_SHARE * totale:
        raise RuntimeError(
            f"{falliti} richieste su {totale} non sono andate a buon fine: i dati soloQ "
            "gia' presenti NON sono stati toccati. lolalytics potrebbe aver cambiato il "
            "suo sistema, o la connessione e' instabile."
        )
    return {
        "fetched_at": time.time(),
        "tier": TIER,
        "patch": PATCH,
        "avg_wr": avg_wr or 51.8,
        "lane_share": shares,
        "pages": pages,
        "failed": falliti,
        "requests": totale,
    }


# ------------------------------------------------------------------ lettura
_cache: "SoloQ | None" = None
_cache_key: tuple | None = None


class SoloQ:
    """I dati scaricati, con le domande che servono all'app. Tutto per NOME
    campione (quello di DriftDraft) e CORSIA del sito (top/jungle/...)."""

    def __init__(self, raw: dict):
        self.raw = raw
        self.avg_wr = float(raw.get("avg_wr") or 51.8)
        self.shares: dict[str, dict[str, float]] = raw.get("lane_share") or {}
        self.pages: dict[tuple[str, str], dict] = {}
        for chiave, pagina in (raw.get("pages") or {}).items():
            nome, _, lane = chiave.rpartition("|")
            self.pages[(nome, lane)] = pagina

    # --- chi gioca dove
    def lane_share(self, name: str) -> dict[str, float]:
        return self.shares.get(name, {})

    def plays(self, name: str, lane: str) -> bool:
        return (name, lane) in self.pages

    def pick_rate(self, name: str, lane: str) -> float:
        """Percentuale delle partite di quella corsia in cui compare il campione."""
        p = self.pages.get((name, lane))
        return float(p.get("pr") or 0.0) if p else 0.0

    def strength(self, name: str, lane: str) -> float:
        """Winrate nella corsia meno la media del tier (0 se ignoto)."""
        p = self.pages.get((name, lane))
        if not p or not p.get("wr"):
            return 0.0
        return float(p["wr"]) - self.avg_wr

    def champions_in(self, lane: str) -> list[str]:
        return [n for (n, l) in self.pages if l == lane]

    # --- counter
    def _d2(self, page: str, page_lane: str, other: str, other_lane: str):
        p = self.pages.get((page, page_lane))
        if not p:
            return None
        x = (p.get("counters") or {}).get(other_lane, {}).get(other)
        return x

    def advantage(self, a: str, a_lane: str, b: str, b_lane: str) -> float | None:
        """Vantaggio soloQ di a su b, in punti di winrate e al netto della
        forza dei due (Delta 2), ristretto verso zero secondo le partite.
        Dalla pagina di b (d2 di b contro a, cambiato di segno) e/o da quella
        di a: se ci sono entrambe si fa la media, che dimezza il rumore - le
        due pagine guardano partite diverse (ognuna filtra sul rango del suo
        campione). None se nessuna delle due ha il matchup."""
        valori = []
        pesi = []
        x = self._d2(b, b_lane, a, a_lane)
        if x:
            valori.append(-float(x[0]))
            pesi.append(int(x[1]))
        y = self._d2(a, a_lane, b, b_lane)
        if y:
            valori.append(float(y[0]))
            pesi.append(int(y[1]))
        if not valori:
            return None
        v = sum(valori) / len(valori)
        n = sum(pesi) / len(pesi)
        return v * n / (n + SHRINK_COUNTER)

    def lane_counters(self, name: str, lane: str) -> list[dict] | None:
        """La tabella della ricerca counter: gli avversari nella stessa corsia
        con il LORO winrate contro `name` (stessa convenzione di
        lolalytics.fetch_counters, che mostra in griglia il winrate
        dell'avversario), dal piu' forte. None se la pagina non c'e'."""
        p = self.pages.get((name, lane))
        if not p or lane not in (p.get("counters") or {}):
            return None
        righe = []
        for avv, (d2, n, vs_wr) in p["counters"][lane].items():
            if vs_wr is None:
                continue
            righe.append({"champion": avv, "winrate": round(100.0 - float(vs_wr), 2), "games": int(n)})
        righe.sort(key=lambda r: r["winrate"], reverse=True)
        return righe

    # --- sinergia bot-support
    def duo_synergy(self, support: str, bottom: str) -> float | None:
        """Delta 2 della coppia support-tiratore, ristretto per partite."""
        p = self.pages.get((support, "support"))
        if not p:
            return None
        x = (p.get("synergy_bottom") or {}).get(bottom)
        if not x:
            return None
        d2, n = float(x[0]), int(x[1])
        return d2 * n / (n + SHRINK_SYNERGY)


def load() -> SoloQ | None:
    """I dati su disco, o None se non sono mai stati scaricati. Con cache
    sulla data di modifica: i suggerimenti lo chiedono ad ogni pick."""
    global _cache, _cache_key
    if not SOLOQ_PATH.exists():
        return None
    st = SOLOQ_PATH.stat()
    key = (st.st_mtime_ns, st.st_size)
    if _cache_key == key and _cache is not None:
        return _cache
    try:
        raw = json.loads(SOLOQ_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    _cache = SoloQ(raw)
    _cache_key = key
    return _cache


def status() -> dict:
    if not SOLOQ_PATH.exists():
        return {"synced": False}
    dati = load()
    if dati is None:
        return {"synced": False}
    return {
        "synced": True,
        "fetchedAt": dati.raw.get("fetched_at"),
        "pages": len(dati.pages),
        "tier": dati.raw.get("tier"),
    }


def save(raw: dict) -> None:
    SOLOQ_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SOLOQ_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(SOLOQ_PATH)


# ------------------------------------------------------------------ sync in un thread
# Stesso schema di leaguepedia.start_sync/sync_progress: parte, torna subito, e
# la UI ne legge l'avanzamento. I due scarichi girano INSIEME dallo stesso
# bottone "Aggiorna dati" (siti diversi, nessuna ragione di aspettare).
_sync_lock = threading.Lock()
_sync_state: dict = {"running": False}


def _set_sync_state(**fields) -> None:
    with _sync_lock:
        _sync_state.update(fields)


def sync_progress() -> dict:
    with _sync_lock:
        state = dict(_sync_state)
    state["data"] = status()
    return state


def start_sync() -> dict:
    with _sync_lock:
        if _sync_state.get("running"):
            return {"alreadyRunning": True}
        _sync_state.clear()
        _sync_state.update({"running": True, "phase": "avvio", "done": 0, "target": 0, "startedAt": time.time()})

    def worker() -> None:
        try:
            raw = fetch_all(on_progress=lambda p: _set_sync_state(**p))
            _set_sync_state(phase="salvo")
            save(raw)
        except Exception as e:
            _set_sync_state(running=False, phase="errore", error=str(e), finishedAt=time.time())
            return
        _set_sync_state(running=False, phase="fatto", error=None, finishedAt=time.time())

    threading.Thread(target=worker, daemon=True).start()
    return {"started": True}
