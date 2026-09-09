"""Server locale (Bottle) che espone i dati campioni/comp al frontend.

Usato sia per l'app reale (pywebview carica questo server in una finestra
nativa) sia per lo sviluppo/test (si apre semplicemente in un browser).
"""

import json
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse
from wsgiref.simple_server import WSGIServer

from bottle import Bottle, request, response, run, static_file

from driftdraft.champion_overrides import reset_override, save_override
from driftdraft import champion_art
from driftdraft.comps import (
    COMP_INNER_CYCLE,
    COMP_OUTER_CYCLE,
    COMP_REQUIREMENTS,
    detect_comps,
)
from driftdraft.data import COMP_COLUMNS, ROLE_COLUMNS, TAG_COLUMNS, load_champions
from driftdraft.drafter_live import get_session as get_live_draft_session
from driftdraft import leaguepedia
from driftdraft import training_bot
from driftdraft.draft_evaluation import EvaluationError, evaluate_live_draft, evaluate_session
from driftdraft.lolalytics import DEFAULT_TIER, ROLE_TO_LANE, VALID_TIERS, NoCounterDataError, fetch_counters
from driftdraft.opgg import (
    PlayerChampion,
    PlayerPool,
    aggregate_pool,
    fetch_player_champions,
    fetch_team_pool,
)
from driftdraft.ugg import ROLE_TO_UGG_ROLE, fetch_lane_counters
from driftdraft.paths import get_app_dir, get_bundle_dir
from driftdraft.roster import (
    ROLES,
    TIERS,
    delete_profile,
    list_profiles,
    load_profile,
    rename_profile,
    save_profile,
)
from driftdraft.saved_drafts import add_saved_draft, delete_saved_draft, list_saved_drafts
from driftdraft.tierlist_detect import detect_tierlist

# Due basi DIVERSE (v1.0, vedi driftdraft/paths.py): WEB_DIR e' codice
# dell'app (html/css/js), resta dentro _internal/ - get_bundle_dir(). Le
# icone in ASSETS_DIR invece l'utente potrebbe volerle ampliare (icona di
# un campione nuovo aggiunto a mano nell'xlsx) - vivono accanto
# all'eseguibile, get_app_dir(), stessa cartella di data/champions.xlsx.
WEB_DIR = get_bundle_dir() / "web"
ASSETS_DIR = get_app_dir() / "assets"

# Colori tematici delle 5 comp - NON derivano dalla palette UI, restano fissi.
# Mappatura confermata dall'utente (2026-08-16): rosso/giallo/blu erano gia'
# corretti, verde e viola erano invertiti rispetto al suo sistema originale.
COMP_COLORS = {
    "TeamFight \\ WomboCombo": "#d64545",  # rosso
    "Pick": "#e0b83d",  # giallo
    "Proteggi il presidente": "#4caf6d",  # verde
    "Poke \\ Siege": "#3ea8d8",  # blu ciano
    "Split": "#9b59b6",  # viola
}

# Condizione di vittoria / vantaggi / svantaggi per comp, dal diagramma
# fornito dall'utente (2026-08-16). Mostrati in UI solo quando la comp e'
# rilevata (member_count >= MEMBER_THRESHOLD). "Requisiti" non e' incluso
# qui perche' e' gia' rappresentato dai tag nella stessa card.
COMP_PROFILES = {
    "TeamFight \\ WomboCombo": {
        "win_condition": ["Combattimento 5 vs 5 con supreme active"],
        "pros": ["Facile da eseguire"],
        "cons": ["Comp dipesa troppo dalla ultimate"],
    },
    "Pick": {
        "win_condition": [
            "Combattimenti impari",
            "Controllo e rimozione della visione gioco dentro la nebbia di guerra",
        ],
        "pros": ["Molto facile punire gli sbagli nemici"],
        "cons": ["Combattimenti 5 vs 5 più deboli delle altre comp"],
    },
    "Proteggi il presidente": {
        "win_condition": [
            "Combattimento 5 vs 5 con carry in mid\\lategame",
            "Mantenere il carry vivo",
        ],
        "pros": [
            "Composizione molto facile da seguire",
            "Composizione prone al tilt nemico",
            "Forte contro altre composizioni più popolari",
        ],
        "cons": [
            "Bisogna stare sempre in 5",
            "Estremamente dipendente dalla forza macromeccanica del proprio carry",
        ],
    },
    "Poke \\ Siege": {
        "win_condition": [
            "Lenta demolizione dei nemici per costringere la ritirata e lo scontro impari"
        ],
        "pros": ["Grande controllo sugli obbiettivi"],
        "cons": ["Richiede estrema pazienza e coordinazione"],
    },
    "Split": {
        "win_condition": ["Divisione dei nemici in più punti della mappa"],
        "pros": ["Grande pressione in multiple lane"],
        "cons": ["Alto rischio, e facile da sbagliare"],
    },
}

# Regione fissa per il fetch individuale da roster (vedi api_opgg_roster_team):
# il riot_id salvato nel roster e' solo "Nome#TAG", senza regione - EUW e'
# l'assunzione ragionevole per questo utente (il suo stesso link di esempio
# usa EUW), facile da cambiare qui se in futuro serve altro.
OPGG_REGION = "euw"

app = Bottle()


def _no_cache(res):
    # Cache-Control da solo non basta: se il browser ha gia' una copia in
    # cache da prima (heuristic caching su Last-Modified), puo' continuare a
    # servirla senza nemmeno ricontattare il server - non vedrebbe mai questo
    # header su una richiesta nuova. Per questo index() sotto aggiunge anche
    # un "?v=<mtime>" agli asset: cambia l'URL, non solo l'header.
    res.set_header("Cache-Control", "no-store")
    return res


_index_html_cache: str | None = None
_index_html_key: tuple | None = None


@app.get("/")
def index():
    global _index_html_cache, _index_html_key
    index_path = WEB_DIR / "index.html"
    try:
        key = tuple(
            (path.stat().st_mtime_ns, path.stat().st_size)
            for path in (index_path, WEB_DIR / "style.css", WEB_DIR / "app.js")
        )
    except OSError:
        response.content_type = "text/html; charset=utf-8"
        return "<html><body>index.html not found</body></html>"

    if _index_html_cache is None or key != _index_html_key:
        html = index_path.read_text(encoding="utf-8")
        for asset in ("style.css", "app.js"):
            asset_mtime = int((WEB_DIR / asset).stat().st_mtime)
            html = html.replace(f'/web/{asset}"', f'/web/{asset}?v={asset_mtime}"')
        _index_html_cache = html
        _index_html_key = key

    response.content_type = "text/html; charset=utf-8"
    _no_cache(response)
    return _index_html_cache


@app.get("/web/<filepath:path>")
def web_assets(filepath):
    return _no_cache(static_file(filepath, root=WEB_DIR))


@app.get("/assets/<filepath:path>")
def project_assets(filepath):
    # Niente no-store qui, a differenza di index()/web_assets(): queste sono
    # le icone dei campioni/ruoli, cambiano solo quando l'utente le
    # risincronizza dall'xlsx. Lasciarle in cache (comportamento di default
    # di static_file, Last-Modified/ETag) evita di riscaricare ~170 immagini
    # ad ogni cambio di filtro - era la causa del "deve ricaricare ogni volta".
    return static_file(filepath, root=ASSETS_DIR)


def _icon_url(champion_name: str) -> str:
    path = ASSETS_DIR / "icons" / f"{champion_name}.png"
    try:
        mtime = int(path.stat().st_mtime)
    except OSError:
        return f"/assets/icons/{champion_name}.png"
    return f"/assets/icons/{champion_name}.png?v={mtime}"


def _splash_url(champion_name: str) -> str:
    path = ASSETS_DIR / "splash" / f"{champion_name}.jpg"
    try:
        mtime = int(path.stat().st_mtime)
    except OSError:
        return f"/assets/splash/{champion_name}.jpg"
    return f"/assets/splash/{champion_name}.jpg?v={mtime}"


@app.get("/api/champions")
def api_champions():
    champs = load_champions()
    payload = [
        {
            "name": c.name,
            "comps": sorted(c.comps),
            "tags": sorted(c.tags),
            "roles": sorted(c.roles),
            "icon": _icon_url(c.name),
            "splash": _splash_url(c.name),
        }
        for c in champs
    ]
    response.content_type = "application/json"
    return json.dumps(payload, ensure_ascii=False)


@app.get("/api/comp-meta")
def api_comp_meta():
    # I counter naturali viaggiano PER COMP e non come chiave a se': il
    # frontend fa Object.entries(compMeta) e una voce che non fosse una comp
    # gli finirebbe in mezzo. `inner`/`outer` restano distinti perche' il
    # diagramma disegna le diagonali diversamente dai lati.
    inner = dict(COMP_INNER_CYCLE)
    outer = dict(COMP_OUTER_CYCLE)
    payload = {}
    for comp, reqs in COMP_REQUIREMENTS.items():
        profile = COMP_PROFILES[comp]
        payload[comp] = {
            "color": COMP_COLORS[comp],
            "mandatory": reqs["mandatory"],
            "optional": reqs["optional"],
            "win_condition": profile["win_condition"],
            "pros": profile["pros"],
            "cons": profile["cons"],
            "innerBeats": inner.get(comp),
            "outerBeats": outer.get(comp),
        }
    response.content_type = "application/json"
    return json.dumps(payload, ensure_ascii=False)


@app.post("/api/champion-tags")
def api_champion_tags_save():
    """Modifica di comp/tag/ruoli di UN campione fatta dal coach in app -
    richiesto esplicitamente dall'utente (2026-08-27): "non tutti hanno
    excel sul proprio pc... vorrei introdurre un modo per dare modo ai
    coach di poter modificare i tag direttamente in app". Salva in un file
    JSON separato (vedi champion_overrides.py per il perche' NON si scrive
    mai nell'xlsx sorgente), applicato automaticamente ad ogni successiva
    load_champions() - il chiamante ricarica /api/champions dopo questa
    chiamata per vedere il risultato, non serve che questo endpoint
    ritorni gia' l'elenco completo.

    Body: {champion, comps?, tags?, roles?} - una categoria ASSENTE dal
    body non viene toccata (l'xlsx resta la fonte per quella categoria);
    una categoria PRESENTE (anche []) sostituisce interamente quella del
    campione."""
    body = request.json or {}
    name = str(body.get("champion", "")).strip()
    response.content_type = "application/json"
    if not name:
        return json.dumps({"error": "Nome campione mancante."})

    valid_champion_names = {c.name for c in load_champions()}
    if name not in valid_champion_names:
        return json.dumps({"error": f"Campione sconosciuto: {name}"})

    def _validate(field_name, values, allowed):
        if values is None:
            return None, None
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            return None, f"{field_name} non valido."
        unknown = [v for v in values if v not in allowed]
        if unknown:
            return None, f"{field_name} sconosciuti: {unknown}"
        return values, None

    comps, err = _validate("comps", body.get("comps"), COMP_COLUMNS)
    if err:
        return json.dumps({"error": err})
    tags, err = _validate("tags", body.get("tags"), TAG_COLUMNS)
    if err:
        return json.dumps({"error": err})
    roles, err = _validate("roles", body.get("roles"), ROLE_COLUMNS)
    if err:
        return json.dumps({"error": err})

    entry = save_override(name, comps=comps, tags=tags, roles=roles)
    return json.dumps({"champion": name, "override": entry}, ensure_ascii=False)


@app.post("/api/champion-tags/reset")
def api_champion_tags_reset():
    """Rimuove l'intero override di un campione - torna a mostrare
    esattamente cio' che dice l'xlsx per tutte e 3 le categorie."""
    body = request.json or {}
    name = str(body.get("champion", "")).strip()
    response.content_type = "application/json"
    if not name:
        return json.dumps({"error": "Nome campione mancante."})
    reset_override(name)
    return json.dumps({"champion": name})


@app.post("/api/detect")
def api_detect():
    picked_names = request.json or []
    champs_by_name = {c.name: c for c in load_champions()}
    picked = [champs_by_name[n] for n in picked_names if n in champs_by_name]

    results = detect_comps(picked)
    payload = {
        comp: {
            "satisfied": status.satisfied,
            "member_count": status.member_count,
            "member_threshold": status.member_threshold,
            "covered": sorted(status.covered_tags),
            "missing": sorted(status.missing_tags),
            "optional_covered": sorted(status.optional_covered),
            "mandatory_count": status.mandatory_count,
        }
        for comp, status in results.items()
    }
    response.content_type = "application/json"
    return json.dumps(payload, ensure_ascii=False)


@app.post("/api/opgg-team")
def api_opgg_team():
    """Fetch on-demand (bottone "Aggiorna" nel frontend, non polling
    automatico) del pool di campioni giocati da una squadra, da un link
    multisearch di op.gg. Risponde sempre 200: gli errori sono nel body
    come {"error": "..."} cosi' il frontend li gestisce con un solo path."""

    url = (request.json or {}).get("url", "").strip()
    response.content_type = "application/json"

    if not url:
        return json.dumps({"error": "Incolla prima un link op.gg multisearch."})

    parsed = urlparse(url)
    if "op.gg" not in parsed.netloc:
        return json.dumps({"error": "Non sembra un link op.gg valido."})

    summoners_param = parse_qs(parsed.query).get("summoners", [""])[0]
    requested_summoners = [s for s in summoners_param.split(",") if s]
    if not requested_summoners:
        return json.dumps({"error": "Nessun invocatore trovato in questo link."})
    # Richiesta esplicita dell'utente (2026-08-18): molti team mandano il
    # link op.gg con l'intero roster, sub compresi - fino a 10 (5 titolari +
    # 5 sub) va supportato, oltre e' quasi certamente un link malformato o
    # un errore di chi lo ha copiato - meglio un errore chiaro subito che
    # lanciare comunque Playwright su un input probabilmente sbagliato.
    if len(requested_summoners) > 10:
        return json.dumps(
            {"error": f"Troppi invocatori nel link ({len(requested_summoners)}, massimo 10)."}
        )

    try:
        players = fetch_team_pool(url, requested_summoners)
    except Exception as e:
        return json.dumps({"error": f"Errore durante il caricamento da op.gg: {e}"})

    payload = {
        "pool": aggregate_pool(players),
        "players": [
            {
                "summoner": p.summoner,
                "champions": [
                    {"champion": c.champion, "games": c.games, "winrate": c.winrate}
                    for c in p.champions
                ],
                # Corsie dichiarate da op.gg (vuote per i profili singoli del
                # roster, che quella sezione non ce l'hanno): servono al
                # frontend solo per rimandarcele indietro quando chiede i pick
                # suggeriti, cosi' il profilo si ricostruisce identico a
                # quello del bot senza rifare il giro su op.gg.
                "roles": getattr(p, "roles", None) or {},
            }
            for p in players
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@app.post("/api/opgg-roster-team")
def api_opgg_roster_team():
    """Come /api/opgg-team, ma la fonte non e' un link multisearch incollato
    a mano: per ogni ruolo si interroga individualmente il titolare (primo
    giocatore della lista, non i sub) sulla tab "Campioni" del suo profilo
    op.gg (fetch_player_champions) - qui interessa lo storico COMPLETO della
    persona gestita nel roster, non un resoconto sintetico come nel
    multisearch. Stessa forma di risposta di /api/opgg-team cosi' il
    frontend riusa la stessa renderizzazione (pool-chip + player-chip) senza
    percorsi paralleli. Un fallimento singolo (Riot ID sbagliato, profilo
    privato) non blocca gli altri - riportato come "warning", non "error",
    a meno che falliscano tutti."""

    team_name = str((request.json or {}).get("team_name", "")).strip()
    response.content_type = "application/json"

    if not team_name:
        return json.dumps({"error": "Nessun team specificato."})

    profile = load_profile(team_name)
    titolari = []
    for role in ROLES:
        players = profile.get(role, [])
        riot_id = players[0]["riot_id"] if players else ""
        if riot_id:
            titolari.append((role, riot_id))

    if not titolari:
        return json.dumps({"error": "Nessun titolare del roster ha un Riot ID impostato."})

    players = []
    failures = []
    for role, riot_id in titolari:
        try:
            players.append(fetch_player_champions(OPGG_REGION, riot_id))
        except Exception as e:
            failures.append(f"{role} ({riot_id}): {e}")

    if not players:
        return json.dumps({"error": "Errore durante il caricamento da op.gg: " + "; ".join(failures)})

    payload = {
        "pool": aggregate_pool(players),
        "players": [
            {
                "summoner": p.summoner,
                "champions": [
                    {"champion": c.champion, "games": c.games, "winrate": c.winrate}
                    for c in p.champions
                ],
                # Corsie dichiarate da op.gg (vuote per i profili singoli del
                # roster, che quella sezione non ce l'hanno): servono al
                # frontend solo per rimandarcele indietro quando chiede i pick
                # suggeriti, cosi' il profilo si ricostruisce identico a
                # quello del bot senza rifare il giro su op.gg.
                "roles": getattr(p, "roles", None) or {},
            }
            for p in players
        ],
    }
    if failures:
        payload["warning"] = "Alcuni giocatori non caricati: " + "; ".join(failures)
    return json.dumps(payload, ensure_ascii=False)


@app.post("/api/counters")
def api_counters():
    """Winrate degli avversari contro un campione di riferimento gia'
    piazzato in uno slot, per il ruolo scelto - fetch on-demand (bottone
    "cerca counter" nel frontend). Risponde sempre 200 con {"error": "..."}
    sugli errori, stesso pattern delle altre integrazioni esterne."""

    body = request.json or {}
    champion = str(body.get("champion", "")).strip()
    role = str(body.get("role", "")).strip()
    tier = str(body.get("tier", DEFAULT_TIER)).strip()
    response.content_type = "application/json"

    if not champion:
        return json.dumps({"error": "Nessun campione specificato."})
    if role not in ROLE_TO_LANE:
        return json.dumps({"error": "Ruolo non valido."})
    if tier not in VALID_TIERS:
        return json.dumps({"error": "Fascia elo non valida."})

    try:
        entries = fetch_counters(champion, role, tier)
    except NoCounterDataError:
        return json.dumps({"error": "Dati insufficienti su lolalytics per questo campione/ruolo in questa fascia elo."})
    except Exception as e:
        return json.dumps({"error": f"Errore durante la ricerca counter: {e}"})

    payload = [{"champion": e.champion, "winrate": e.winrate, "games": e.games} for e in entries]
    return json.dumps({"counters": payload}, ensure_ascii=False)


@app.post("/api/lane-counters")
def api_lane_counters():
    """Come /api/counters ma per il dato di CORSIA (differenza oro a 15',
    fonte u.gg invece di lolalytics) - toggle "Counter corsia" nel
    frontend. Stesso pattern di validazione/risposta dell'endpoint gemello,
    duplicato deliberatamente invece di un parametro "source" condiviso: le
    due fonti hanno vocabolari ruolo diversi (ROLE_TO_LANE vs
    ROLE_TO_UGG_ROLE) e forme di risposta diverse (winrate% vs GD15)."""

    body = request.json or {}
    champion = str(body.get("champion", "")).strip()
    role = str(body.get("role", "")).strip()
    tier = str(body.get("tier", DEFAULT_TIER)).strip()
    response.content_type = "application/json"

    if not champion:
        return json.dumps({"error": "Nessun campione specificato."})
    if role not in ROLE_TO_UGG_ROLE:
        return json.dumps({"error": "Ruolo non valido."})
    if tier not in VALID_TIERS:
        return json.dumps({"error": "Fascia elo non valida."})

    try:
        entries = fetch_lane_counters(champion, role, tier)
    except Exception as e:
        return json.dumps({"error": f"Errore durante la ricerca counter di corsia: {e}"})

    payload = [{"champion": e.champion, "gd15": e.gd15, "games": e.games} for e in entries]
    return json.dumps({"laneCounters": payload}, ensure_ascii=False)


@app.post("/api/live-draft/connect")
def api_live_draft_connect():
    """"Modalita' torneo": connessione a una draft room REALE di
    drafter.lol via una sessione Playwright che resta aperta (vedi
    drafter_live.py). Questo e' il solo passo di lettura/specchio - inviare
    le scelte fatte in DriftDraft come azioni vere sulla draft e' un passo
    successivo, non ancora costruito."""

    body = request.json or {}
    url = str(body.get("url", "")).strip()
    response.content_type = "application/json"

    if "drafter.lol" not in url:
        return json.dumps({"error": "Incolla un link drafter.lol valido."})

    session = get_live_draft_session()
    try:
        options = session.connect(url)
    except Exception as e:
        return json.dumps({"error": f"Errore durante la connessione: {e}"})

    # Non e' ancora una draft: e' il dialogo di ingresso, con i team veri
    # della room e i lati liberi. La scelta passa da /join-options e /join.
    return json.dumps({"connected": True, **options}, ensure_ascii=False)


@app.post("/api/live-draft/join-options")
def api_live_draft_join_options():
    """Rilegge il dialogo di ingresso, opzionalmente dopo aver selezionato un
    team: i lati disponibili dipendono dal team scelto, ed e' il sito stesso
    a legarli (vedi _JOIN_OPTIONS_JS in drafter_live.py)."""
    body = request.json or {}
    team = str(body.get("team", "")).strip() or None
    response.content_type = "application/json"
    session = get_live_draft_session()
    return json.dumps(session.join_options(team), ensure_ascii=False)


@app.post("/api/live-draft/join")
def api_live_draft_join():
    """Secondo tempo della connessione: entra nella draft con il team e il
    lato scelti fra quelli letti dalla pagina."""
    body = request.json or {}
    team = str(body.get("team", "")).strip()
    side = str(body.get("side", "")).strip()
    response.content_type = "application/json"

    if not team:
        return json.dumps({"error": "Scegli il tuo team."})
    if side not in ("blue", "red"):
        return json.dumps({"error": "Scegli un lato (Blue o Red)."})

    session = get_live_draft_session()
    return json.dumps(session.join(team, side), ensure_ascii=False)


@app.post("/api/live-draft/ready")
def api_live_draft_ready():
    """Segnala "pronto" sulla draft connessa - a differenza di una scelta
    di campione non e' un'azione a rischio (non sceglie/invia nulla)."""
    response.content_type = "application/json"
    session = get_live_draft_session()
    return json.dumps(session.click_ready(), ensure_ascii=False)


@app.post("/api/live-draft/select")
def api_live_draft_select():
    """FASE 2 - seleziona (senza confermare) un campione nella draft VERA
    connessa. Il frontend chiama questa route solo quando "modalita' torneo"
    e' connessa ed e' effettivamente il turno del nostro lato (fase letta da
    /api/live-draft/state) - qui non si ripete quel controllo lato server,
    ci si affida al fatto che un click fuori contesto su drafter.lol fallisce
    in modo innocuo (Playwright non trova/non clicca) invece di avere
    effetti indesiderati."""
    body = request.json or {}
    champion = str(body.get("champion", "")).strip()
    response.content_type = "application/json"
    if not champion:
        return json.dumps({"error": "Nessun campione specificato."})

    session = get_live_draft_session()
    return json.dumps(session.select_champion(champion), ensure_ascii=False)


@app.post("/api/live-draft/confirm")
def api_live_draft_confirm():
    """FASE 2 - blocca la selezione corrente (click sul bottone azione reale
    della draft, Ban o Pick a seconda della fase). side/kind/index
    identificano lo slot atteso, servono a verificare che il click abbia
    davvero funzionato (vedi confirm_selection in drafter_live.py)."""
    body = request.json or {}
    side = str(body.get("side", "")).strip()
    kind = str(body.get("kind", "")).strip()
    index = body.get("index")
    response.content_type = "application/json"
    if side not in ("blue", "red") or kind not in ("ban", "pick") or not isinstance(index, int):
        return json.dumps({"error": "Richiesta di conferma non valida."})

    session = get_live_draft_session()
    return json.dumps(session.confirm_selection(side, kind, index), ensure_ascii=False)


@app.post("/api/live-draft/confirm-role-order")
def api_live_draft_confirm_role_order():
    """Role confirmation (dopo i 20 pick/ban) - replica sul sito VERO
    l'ordine ruoli scelto localmente in DriftDraft (nessuna fretta, quel
    riordino e' puramente locale finche' non si preme questo bottone). Il
    frontend chiama questa route solo dopo aver rilevato che la fase di
    drag e' davvero live sul sito (state.roleConfirmActive) - qui non si
    ripete quel controllo, stessa filosofia di /api/live-draft/select."""
    body = request.json or {}
    order = body.get("order")
    response.content_type = "application/json"
    if not isinstance(order, list) or len(order) != 5 or not all(isinstance(x, str) for x in order):
        return json.dumps({"error": "Ordine ruoli non valido (servono 5 nomi campione)."})

    session = get_live_draft_session()
    return json.dumps(session.confirm_role_order(order), ensure_ascii=False)


@app.get("/api/live-draft/state")
def api_live_draft_state():
    response.content_type = "application/json"
    session = get_live_draft_session()
    return json.dumps(session.read_state(), ensure_ascii=False)


@app.post("/api/live-draft/disconnect")
def api_live_draft_disconnect():
    response.content_type = "application/json"
    session = get_live_draft_session()
    session.disconnect()
    return json.dumps({"connected": False})


@app.post("/api/live-draft/evaluate")
def api_live_draft_evaluate():
    """"Valuta la draft" per la modalita' torneo (richiesto esplicitamente
    dall'utente 2026-08-26: "penso che sia un'aggiunta importante anche per
    la modalità torneo") - stesso identico nucleo di /api/training/evaluate
    (vedi evaluate_picks in draft_evaluation.py), ma i 10 pick vengono letti
    dallo specchio della draft REALE (session.read_state(), gia' usato dal
    polling ogni 100ms) invece che da una TrainingSession.

    ourRoleOrder e' opzionale: se il frontend ha gia' un ordine ruoli VERO
    confermato sul sito (vedi /api/live-draft/confirm-role-order) lo passa
    qui per una valutazione piu' precisa; altrimenti si ricade
    sull'euristica assign_roles().

    enemyRoleOrder e' anch'esso opzionale, stesso schema - richiesto
    esplicitamente dall'utente (2026-08-26) dopo un caso reale di
    assegnazione sbagliata (Hecarim indovinato come Support invece che Top):
    a differenza del nostro lato, drafter.lol non espone in NESSUN modo la
    fase di role confirmation nemica, quindi qui e' sempre il coach stesso a
    fornirlo a mano (vedi renderTournamentEnemyRoles in app.js) se vuole
    correggere l'euristica automatica."""
    body = request.json or {}
    tier = str(body.get("tier", DEFAULT_TIER)).strip()
    our_role_order = body.get("ourRoleOrder")
    enemy_role_order = body.get("enemyRoleOrder")
    response.content_type = "application/json"
    if tier not in VALID_TIERS:
        return json.dumps({"error": "Fascia elo non valida."})
    for order in (our_role_order, enemy_role_order):
        if order is not None and (not isinstance(order, list) or not all(isinstance(x, str) for x in order)):
            return json.dumps({"error": "Ordine ruoli non valido."})

    session = get_live_draft_session()
    state = session.read_state()
    if not state.get("connected"):
        return json.dumps({"error": "Nessuna draft torneo connessa."})

    side = state.get("side")
    blue_picks = state.get("bluePicks") or []
    red_picks = state.get("redPicks") or []
    if side not in ("blue", "red") or len(blue_picks) != 5 or len(red_picks) != 5:
        return json.dumps({"error": "Stato draft non disponibile."})
    if any(p is None or p == "None" for p in blue_picks + red_picks):
        return json.dumps({"error": "La draft non e' ancora finita (mancano dei pick)."})

    our_picks, enemy_picks = (blue_picks, red_picks) if side == "blue" else (red_picks, blue_picks)

    try:
        result = evaluate_live_draft(our_picks, our_role_order, enemy_picks, enemy_role_order, tier)
    except EvaluationError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Errore durante la valutazione: {e}"})

    return json.dumps(result, ensure_ascii=False)


@app.post("/api/live-draft/role-guess")
def api_live_draft_role_guess():
    """Wrapper sottile e senza stato attorno a training_bot.assign_roles() -
    richiesto esplicitamente dall'utente (2026-08-26) per poter SEMINARE il
    pannello "Ruoli nemici" (vedi renderTournamentEnemyRoles in app.js) con
    un primo suggerimento invece di partire da zero ad ogni draft finita -
    il coach parte gia' dal miglior indovinato e corregge solo dove serve
    (es. Hecarim), invece di dover riordinare tutti e 5 i pick a mano ogni
    volta. Nessuna sessione/stato coinvolto: prende 5 nomi campione, ritorna
    l'assegnazione - usabile per QUALUNQUE 5 campioni, non solo per una
    draft torneo, ma e' l'unico chiamante per ora."""
    body = request.json or {}
    picks = body.get("picks")
    response.content_type = "application/json"
    if not isinstance(picks, list) or len(picks) != 5 or not all(isinstance(x, str) for x in picks):
        return json.dumps({"error": "Servono esattamente 5 nomi campione."})

    # Con una squadra nota l'indovinello smette di essere un indovinello dove
    # i tag lasciano pari. Caso reale, in allenamento: Ezreal e Syndra sono
    # entrambi {Bot, Mid}, quindi "Ezreal mid, Syndra adc" e il suo contrario
    # coprono cinque ruoli tutti e due e vinceva il primo trovato - sbagliato
    # meta' delle volte. Qui vale per i due pannelli del torneo: i nemici dal
    # loro op.gg, i nostri dalle tier list del roster.
    profilo = _profile_arg(body, "players", _role_counts()) or _roster_profile(
        body.get("team"), _role_counts()
    )
    return json.dumps(training_bot.assign_roles(picks, profilo), ensure_ascii=False)


def _role_counts() -> dict:
    """Le corsie viste nelle draft pro - serve a dedurre chi gioca dove.
    Lettura con cache dentro leaguepedia.load_tables, non ricarica il file."""
    return leaguepedia.load_tables().get("role_counts", {})


def _profile_arg(body: dict, key: str, role_counts: dict) -> dict | None:
    """Il profilo op.gg di un lato, ricostruito da quello che manda il client.

    Il client rimanda i giocatori cosi' come glieli abbiamo dati noi da
    /api/opgg-team (summoner, campioni con partite, corsie dichiarate) e qui
    si ricostruisce il profilo con la STESSA funzione che usa il bot di
    training, build_team_profile. Non si tiene niente in sessione apposta:
    questi due endpoint sono senza stato per scelta, e un profilo in cache
    andrebbe poi invalidato quando l'utente cambia link, ricarica o spegne il
    filtro - tre modi di sbagliare in cambio di microsecondi.

    Assente o vuoto = nessuna restrizione (None). Il client lo manda solo
    quando ha davvero una squadra caricata E il relativo chip e' acceso: qui
    non si decide niente, si prende quello che arriva.
    """
    giocatori = body.get(key)
    if not isinstance(giocatori, list) or not giocatori:
        return None
    players = []
    for g in giocatori:
        if not isinstance(g, dict):
            continue
        champs = [
            PlayerChampion(
                champion=str(c.get("champion") or ""),
                games=int(c.get("games") or 0),
                winrate=int(c.get("winrate") or 0),
            )
            for c in (g.get("champions") or [])
            if isinstance(c, dict) and c.get("champion")
        ]
        ruoli = g.get("roles")
        players.append(
            PlayerPool(
                summoner=str(g.get("summoner") or ""),
                champions=champs,
                roles={k: float(v) for k, v in ruoli.items()} if isinstance(ruoli, dict) else {},
            )
        )
    if not players:
        return None
    profile = training_bot.build_team_profile(players, role_counts)
    # Un profilo senza nemmeno un campione equivarrebbe a "nessun pick
    # giocabile" e spegnerebbe la riga: meglio nessun profilo.
    return profile if profile.get("flat") else None


def _roster_profile(nome, role_counts: dict) -> dict | None:
    """Il profilo dalle tier list di un team salvato, o None se non se ne cava
    niente. Un posto solo: lo usano sia i pick suggeriti sia l'indovinello dei
    ruoli a fine draft.

    Serve almeno UNA corsia con una tier list vera. load_profile non fallisce
    su un nome inesistente, restituisce un profilo vuoto: tutte e cinque le
    corsie ripiegherebbero sui pick meta e chi chiama si ritroverebbe un
    profilo "valido" che non dice niente di quella squadra. "Nessuna tier
    list" deve voler dire nessun profilo, non "profilo tutto meta".
    """
    if not isinstance(nome, str) or not nome.strip():
        return None
    try:
        salvato = load_profile(nome.strip())
    except Exception:
        return None
    profilo = training_bot.build_roster_profile(salvato, role_counts)
    if not any(v >= 1.0 for v in (profilo.get("confidence") or {}).values()):
        return None
    return profilo if profilo.get("flat") else None


def _comp_flags(body: dict, lato_nostro: str | None) -> tuple[bool, bool]:
    """Su quali lati si puo' ragionare per comp.

    Il coach puo' spegnere i "bordi comp": non tutti credono in quella
    tassonomia, ed e' sua. Spento significa "non guidarmi con questa roba",
    quindi si spegne sul lato SUO - non su quello avversario, dove la riga non
    e' un consiglio ma una previsione di cosa faranno loro. Il bot di training
    non passa di qui e resta sempre acceso, per la stessa ragione: lui sta
    impersonando qualcuno che le comp le pensa.

    Se non si sa quale sia il lato del coach (modalita' libera senza aver
    ancora scelto da che parte sta), non esiste nemmeno un lato "avversario":
    li' lo spegnimento vale per entrambi, che e' la lettura prudente.
    """
    if body.get("compBorders") is False:
        if lato_nostro == "blue":
            return False, True
        if lato_nostro == "red":
            return True, False
        return False, False
    return True, True


def _our_profile_arg(body: dict, role_counts: dict) -> tuple[str | None, dict | None]:
    """Il lato del coach e il profilo della SUA squadra, dalle tier list.

    Per il proprio team il coach non incolla un op.gg: sceglie il team nella
    barra in alto, e le tier list che si e' scritto a mano valgono piu' di una
    stagione di soloq - sono piu' larghe (15-25 campioni per giocatore contro
    ~10) e dicono anche quanto ci si puo' contare. Vedi build_roster_profile.

    Il LATO arriva dal client e non si indovina: in allenamento e' quello del
    trainee, in torneo quello realmente connesso, entrambi dati autorevoli.
    Fuori da li' non c'e' un lato "nostro" e la funzione si spegne da sola -
    dedurlo dall'ultimo slot cliccato e' gia' stato un bug vero (vedi
    rank_pick_suggestions sul passaggio a blu/rosso).
    """
    lato = body.get("ourSide")
    if lato not in ("blue", "red"):
        return None, None
    return lato, _roster_profile(body.get("ourTeam"), role_counts)


@app.post("/api/pick-suggestions")
def api_pick_suggestions():
    """"Pick suggeriti" FUORI dalla modalita' torneo (richiesto esplicitamente
    dall'utente 2026-08-30: "i pick suggeriti devono funzionare anche fuori
    dalla modalità torneo, sia nella modalità training che quella
    'normale'") - stesso ranking di /api/live-draft/suggestions (stessa
    euristica in training_bot.rank_pick_suggestions), ma senza stato: il
    torneo legge i pick dalla sessione live sul server perche' quella e'
    l'unica fonte autorevole li'; qui training e modalita' libera hanno GIA'
    i pick nel proprio stato client (teams/trainingState), quindi glieli si
    fa passare direttamente invece di inventare una sessione lato server che
    non serve a nient'altro. Stesso schema (senza stato, side-agnostico) gia'
    usato per /api/live-draft/role-guess.

    Dal 2026-09-06 la risposta porta DUE elenchi, "blue" e "red", uno per
    lato (vedi rank_pick_suggestions - stessa euristica, i due elenchi di
    pick scambiati). Erano "nostro" e "avversario" fino a poche ore prima,
    ma fuori da torneo/training il lato nostro era solo un'ipotesi tratta
    dall'ultimo slot cliccato: i lati invece sono un fatto. I campioni che
    compaiono in tutti e due sono i pick contesi; l'intersezione la fa la
    UI, il server non la precalcola perche' non aggiungerebbe informazione."""
    body = request.json or {}
    blue_picks = body.get("bluePicks")
    red_picks = body.get("redPicks")
    taken = body.get("taken")
    response.content_type = "application/json"
    for value in (blue_picks, red_picks, taken):
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            return json.dumps({"error": "Dati draft non validi."})

    blue_profile = _profile_arg(body, "bluePlayers", _role_counts())
    red_profile = _profile_arg(body, "redPlayers", _role_counts())

    # In ALLENAMENTO il lato del bot ha gia' un profilo, ma non passa di qui:
    # l'op.gg si scrive nel modale del training e diventa `bot_profile` della
    # sessione, mentre i pannelli laterali (che alimentano bluePlayers /
    # redPlayers) restano vuoti. Risultato, segnalato dall'utente il
    # 2026-09-07: il bot sceglieva tenendo conto della squadra vera e il
    # pannello dei pick suggeriti no - suggeriva Ezreal in Mid a un mid che
    # non lo gioca, con Caitlyn gia' presa. Due strade per lo stesso dato, e
    # una sola aggiornata.
    #
    # Il flag lo manda il client e non lo si deduce dalla sessione: `_session`
    # sopravvive alla fine dell'allenamento, e usarla senza che nessuno l'abbia
    # chiesto farebbe colare il profilo di una partita finita dentro i
    # suggerimenti della modalita' libera. Quello che il client manda per un
    # lato vince comunque: se il coach ha caricato una squadra nel pannello
    # laterale, e' una scelta esplicita e non va scavalcata.
    if body.get("useTrainingBotProfile"):
        sessione = training_bot.get_session()
        profilo = getattr(sessione, "bot_profile", None) if sessione else None
        if profilo:
            if sessione.bot_side == "team1" and blue_profile is None:
                blue_profile = profilo
            elif sessione.bot_side == "team2" and red_profile is None:
                red_profile = profilo

    # E il lato del coach prende le tier list della sua squadra, se ne ha
    # scelta una. Anche qui quello che il client manda esplicitamente vince:
    # se ha caricato un op.gg nel proprio pannello e' una scelta sua.
    lato_nostro, profilo_nostro = _our_profile_arg(body, _role_counts())
    if profilo_nostro:
        if lato_nostro == "blue" and blue_profile is None:
            blue_profile = profilo_nostro
        elif lato_nostro == "red" and red_profile is None:
            red_profile = profilo_nostro

    blue_comps, red_comps = _comp_flags(body, lato_nostro)

    try:
        ranked = training_bot.rank_pick_suggestions(
            blue_picks,
            red_picks,
            set(taken),
            blue_profile=blue_profile,
            red_profile=red_profile,
            blue_comps=blue_comps,
            red_comps=red_comps,
        )
    except ValueError as e:
        return json.dumps({"error": str(e)})

    return json.dumps(ranked, ensure_ascii=False)


@app.post("/api/live-draft/suggestions")
def api_live_draft_suggestions():
    """"Pick suggeriti" per la modalita' torneo (richiesto esplicitamente
    dall'utente 2026-08-26: "abbiamo un bot che capisce le risposte solite a
    determinati pick... implementiamo i pick suggeriti... poi sara' il coach
    a decidere cosa e' giusto prendere") - stessa euristica sinergia/counter
    gia' usata dal bot di training (vedi rank_pick_suggestions in
    training_bot.py), applicata qui ai pick REALI della draft torneo in
    corso invece che a una TrainingSession. A differenza di /evaluate, NON
    richiede la draft finita - ha senso ad ogni punto della draft (tornano
    semplicemente elenchi vuoti se non c'e' ancora nessun segnale sinergia/
    counter, es. prima ancora del primissimo pick).

    Due elenchi anche qui, come in /api/pick-suggestions: "blue" e "red".

    E' una POST pur non modificando niente: i pick li legge dalla sessione
    live, ma la pool op.gg avversaria che puo' restringere i suggerimenti
    (enemyPool, opzionale) vive solo lato client - sono un centinaio di nomi,
    che in query string starebbero stretti."""
    body = request.json or {}
    response.content_type = "application/json"
    session = get_live_draft_session()
    state = session.read_state()
    if not state.get("connected"):
        return json.dumps({"error": "Nessuna draft torneo connessa."})

    # Il lato non serve piu' a decidere quale meta' e' "nostra" (dal
    # 2026-09-06 le due righe sono blu e rosso, non noi e loro), ma resta il
    # segnale che la sessione ha davvero letto lo stato della draft room.
    if state.get("side") not in ("blue", "red"):
        return json.dumps({"error": "Stato draft non disponibile."})

    def real(values):
        return [v for v in (values or []) if v and v != "None"]

    blue_picks = real(state.get("bluePicks"))
    red_picks = real(state.get("redPicks"))
    blue_bans = real(state.get("blueBans"))
    red_bans = real(state.get("redBans"))

    taken = set(blue_picks + red_picks + blue_bans + red_bans)

    try:
        blue_profile = _profile_arg(body, "bluePlayers", _role_counts())
        red_profile = _profile_arg(body, "redPlayers", _role_counts())
        # Anche in torneo il lato del coach usa le sue tier list, vedi
        # _our_profile_arg. Qui il lato lo manda il client dallo stato della
        # draft live, che sa a quale si e' connesso davvero.
        lato_nostro, profilo_nostro = _our_profile_arg(body, _role_counts())
        if profilo_nostro:
            if lato_nostro == "blue" and blue_profile is None:
                blue_profile = profilo_nostro
            elif lato_nostro == "red" and red_profile is None:
                red_profile = profilo_nostro
        blue_comps, red_comps = _comp_flags(body, lato_nostro)
        ranked = training_bot.rank_pick_suggestions(
            blue_picks,
            red_picks,
            taken,
            blue_profile=blue_profile,
            red_profile=red_profile,
            blue_comps=blue_comps,
            red_comps=red_comps,
        )
    except ValueError as e:
        return json.dumps({"error": str(e)})

    return json.dumps(ranked, ensure_ascii=False)


@app.post("/api/detect-tierlist")
def api_detect_tierlist():
    """Rilevamento locale (Pillow+NumPy, vedi tierlist_detect.py) dei
    campioni in uno screenshot di tierlist caricato dall'utente. Risponde
    sempre 200 con {"error": "..."} sugli errori, stesso pattern di
    /api/opgg-team - il risultato va SEMPRE mostrato per revisione manuale
    nell'editor esistente, mai salvato automaticamente."""

    response.content_type = "application/json"
    upload = request.files.get("image")
    if not upload:
        return json.dumps({"error": "Nessuna immagine ricevuta."})

    try:
        image_bytes = upload.file.read()
        tiers = detect_tierlist(image_bytes)
    except Exception as e:
        return json.dumps({"error": f"Errore durante il rilevamento: {e}"})

    return json.dumps({"tiers": tiers}, ensure_ascii=False)


def _clean_player(raw: dict, valid_names: set[str]) -> dict:
    name = str(raw.get("name", "")).strip()[:60]
    riot_id = str(raw.get("riot_id", "")).strip()[:60]
    tiers_in = raw.get("tiers", {})
    tiers = {}
    for tier in TIERS:
        champs = tiers_in.get(tier, [])
        if not isinstance(champs, list):
            champs = []
        tiers[tier] = [c for c in champs if c in valid_names]
    return {"name": name, "riot_id": riot_id, "tiers": tiers}


def _clean_profile(incoming: dict) -> dict:
    valid_names = {c.name for c in load_champions()}
    cleaned = {}
    for role in ROLES:
        players_in = incoming.get(role, [])
        if not isinstance(players_in, list):
            players_in = []
        cleaned[role] = [
            _clean_player(p, valid_names) for p in players_in if isinstance(p, dict)
        ]
    return cleaned


@app.get("/api/roster-profiles")
def api_roster_profiles():
    response.content_type = "application/json"
    return json.dumps({"profiles": list_profiles()}, ensure_ascii=False)


@app.get("/api/roster-profile")
def api_roster_profile_get():
    name = request.query.name
    response.content_type = "application/json"
    return json.dumps(load_profile(name), ensure_ascii=False)


@app.post("/api/roster-profile")
def api_roster_profile_post():
    body = request.json or {}
    name = str(body.get("name", "")).strip()
    response.content_type = "application/json"
    if not name:
        return json.dumps({"error": "Il profilo deve avere un nome."})

    cleaned = _clean_profile(body.get("data", {}))
    save_profile(name, cleaned)
    return json.dumps({"profiles": list_profiles(), "data": cleaned}, ensure_ascii=False)


@app.post("/api/roster-profile-rename")
def api_roster_profile_rename():
    body = request.json or {}
    old_name = str(body.get("old_name", "")).strip()
    new_name = str(body.get("new_name", "")).strip()
    response.content_type = "application/json"
    try:
        rename_profile(old_name, new_name)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    return json.dumps({"profiles": list_profiles(), "name": new_name}, ensure_ascii=False)


@app.post("/api/roster-profile-delete")
def api_roster_profile_delete():
    body = request.json or {}
    name = str(body.get("name", "")).strip()
    delete_profile(name)
    response.content_type = "application/json"
    return json.dumps({"profiles": list_profiles()}, ensure_ascii=False)


@app.get("/api/saved-drafts")
def api_saved_drafts_list():
    """Modalita' training: 5 campioni segnati dal coach (nessun ban, nessun
    lato) da poter rivedere in seguito - vedi driftdraft/saved_drafts.py."""
    response.content_type = "application/json"
    return json.dumps({"drafts": list_saved_drafts()}, ensure_ascii=False)


@app.post("/api/saved-drafts")
def api_saved_drafts_add():
    body = request.json or {}
    name = str(body.get("name", "")).strip()
    champions_in = body.get("champions", [])
    response.content_type = "application/json"

    # Whitelist contro i nomi campione reali, stesso motivo di
    # _clean_profile/_clean_player sopra - MAI fidarsi di nomi arbitrari dal
    # client. Esattamente 5, niente draft parziali salvate per errore.
    valid_names = {c.name for c in load_champions()}
    cleaned = [str(n).strip() for n in champions_in if str(n).strip() in valid_names]
    if len(cleaned) != 5:
        return json.dumps({"error": "Servono esattamente 5 campioni validi."})

    if not name:
        name = f"Draft {len(list_saved_drafts()) + 1}"

    entry = add_saved_draft(name, cleaned)
    return json.dumps({"drafts": list_saved_drafts(), "added": entry}, ensure_ascii=False)


@app.post("/api/saved-drafts-delete")
def api_saved_drafts_delete():
    body = request.json or {}
    draft_id = str(body.get("id", "")).strip()
    delete_saved_draft(draft_id)
    response.content_type = "application/json"
    return json.dumps({"drafts": list_saved_drafts()}, ensure_ascii=False)


@app.get("/api/training/status")
def api_training_status():
    """Solo lettura locale (nessuna richiesta a Leaguepedia) - il pannello di
    setup la chiama all'apertura per mostrare subito se/quando i dati sono
    gia' stati scaricati, senza forzare un sync ad ogni volta."""
    response.content_type = "application/json"
    return json.dumps(leaguepedia.status(), ensure_ascii=False)


@app.get("/api/champion-art/status")
def api_champion_art_status():
    """Quante immagini dei campioni mancano sul disco di chi usa l'app.

    Le immagini NON viaggiano piu' dentro il pacchetto (vedi champion_art.py
    per il perche'): al primo avvio non ce n'e' nessuna e vanno scaricate.
    Questa risposta dev'essere immediata - e' solo un giro di exists() - perche'
    la UI la chiede prima di mostrare qualsiasi cosa."""
    response.content_type = "application/json"
    return json.dumps(champion_art.status(), ensure_ascii=False)


@app.post("/api/champion-art/sync")
def api_champion_art_sync():
    """Avvia lo scaricamento e torna SUBITO; l'avanzamento si legge da
    /api/champion-art/progress. Stesso schema del sync Leaguepedia: una
    richiesta che resta appesa per 21 MB non lascia alla UI nessun modo di
    dire a che punto e'."""
    response.content_type = "application/json"
    try:
        return json.dumps(champion_art.start_sync(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Impossibile avviare lo scaricamento: {e}"})


@app.get("/api/champion-art/progress")
def api_champion_art_progress():
    response.content_type = "application/json"
    return json.dumps(champion_art.sync_progress(), ensure_ascii=False)


@app.post("/api/training/sync")
def api_training_sync():
    """Avvia l'aggiornamento delle draft pro da Leaguepedia e torna SUBITO.

    Fino al 2026-09-05 questa richiesta restava appesa per tutta la durata
    del fetch (che per costruzione puo' durare parecchio: pagine da 500 con
    pause fra l'una e l'altra, piu' backoff sul limite di frequenza), e la UI
    non aveva modo di dire a che punto fosse. Ora il lavoro gira in un thread
    e l'avanzamento si legge da /api/training/sync-progress."""
    response.content_type = "application/json"
    try:
        return json.dumps(leaguepedia.start_sync(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Impossibile avviare l'aggiornamento: {e}"})


@app.get("/api/training/sync-progress")
def api_training_sync_progress():
    """Avanzamento dell'aggiornamento in corso (o esito dell'ultimo) piu' lo
    stato dei dati su disco. Sola lettura, nessuna richiesta di rete: la UI
    la interroga a intervalli mentre il sync gira."""
    response.content_type = "application/json"
    return json.dumps(leaguepedia.sync_progress(), ensure_ascii=False)


@app.get("/api/training/teams")
def api_training_teams():
    """Le squadre pro che il bot puo' impersonare, dalla piu' documentata.

    Vengono dalle tabelle, quindi si aggiornano da sole ad ogni "Aggiorna
    dati" insieme a tutto il resto - non c'e' un elenco scritto a mano da
    tenere allineato."""
    response.content_type = "application/json"
    tables = leaguepedia.load_tables()
    return json.dumps(
        {
            "teams": training_bot.list_pro_teams(tables),
            "minDrafts": (tables.get("team_pools") or {}).get("min_drafts"),
        },
        ensure_ascii=False,
    )


@app.post("/api/training/start")
def api_training_start():
    """Modalita' allenamento vs draft pro (feature 4) - avvia una nuova
    sessione (sostituisce silenziosamente una eventuale sessione precedente
    mai terminata esplicitamente, stesso spirito di connect() in
    drafter_live.py). Se il bot gioca per primo (trainee ha scelto Red), la
    sua prima mossa e' gia' inclusa nello stato ritornato qui.

    "Allena contro una squadra reale" (richiesta esplicita dell'utente
    2026-08-26): se `enemy_team_url` e' dato (un link op.gg multisearch,
    stesso formato/parsing gia' in uso per /api/opgg-team), il bot sceglie i
    suoi PICK solo fra i campioni che quella squadra ha davvero giocato -
    stesso fetch_team_pool/aggregate_pool gia' provato, nessuna nuova
    integrazione esterna.

    In modalita' "team" il profilo arriva invece dalle draft pro gia' in
    tabella (`team`, vuoto = a sorte) e ha la precedenza sull'op.gg: se il
    coach ha scelto contro chi allenarsi, e' quella squadra che deve
    giocare."""
    body = request.json or {}
    mode = str(body.get("mode", "")).strip()
    side = str(body.get("side", "")).strip()
    # Squadra pro da impersonare (modalita' "team"). Vuoto = a sorte, che e'
    # una delle due scelte offerte all'utente.
    team = str(body.get("team", "")).strip() or None
    enemy_team_url = str(body.get("enemy_team_url", "")).strip()
    response.content_type = "application/json"

    bot_profile = None
    if enemy_team_url:
        parsed = urlparse(enemy_team_url)
        if "op.gg" not in parsed.netloc:
            return json.dumps({"error": "Il link della squadra avversaria non sembra un link op.gg valido."})
        summoners_param = parse_qs(parsed.query).get("summoners", [""])[0]
        requested_summoners = [s for s in summoners_param.split(",") if s]
        if not requested_summoners:
            return json.dumps({"error": "Nessun invocatore trovato nel link della squadra avversaria."})
        try:
            players = fetch_team_pool(enemy_team_url, requested_summoners)
        except Exception as e:
            return json.dumps({"error": f"Errore durante il caricamento della squadra avversaria da op.gg: {e}"})
        # Profilo per CORSIA, non pool unica: vedi build_team_profile. Prima
        # qui si teneva `frozenset(aggregate_pool(players).keys())`, cioe' i
        # soli nomi - partite giocate e winrate venivano scaricati e buttati
        # alla riga dopo.
        # Chi e' stato chiesto ma non trovato: prima veniva scartato in
        # silenzio e la squadra arrivava incompleta senza che nessuno lo
        # dicesse (vedi _normalize_summoner in opgg.py per il caso che lo ha
        # fatto emergere). Con meno di 5 giocatori la deduzione delle corsie
        # si disattiva, quindi il coach deve saperlo.
        trovati = {p.summoner for p in players}
        mancanti = [s for s in requested_summoners if s not in trovati]
        if mancanti:
            return json.dumps({
                "error": "Non ho trovato su op.gg: " + ", ".join(mancanti)
                + ". Controlla che il nome sia scritto esattamente come sul profilo "
                "(spazi compresi) e che l'account abbia partite classificate."
            })

        bot_profile = training_bot.build_team_profile(players, leaguepedia.load_tables().get("role_counts", {}))
        if not bot_profile.get("flat"):
            return json.dumps({"error": "Nessun campione trovato per la squadra avversaria indicata."})

    try:
        session = training_bot.start_session(mode, side, bot_profile=bot_profile, team=team)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Errore durante l'avvio dell'allenamento: {e}"})

    return json.dumps(session.state(), ensure_ascii=False)


@app.get("/api/training/state")
def api_training_state():
    response.content_type = "application/json"
    session = training_bot.get_session()
    if session is None:
        return json.dumps({"active": False})
    return json.dumps(session.state(), ensure_ascii=False)


@app.post("/api/training/pick")
def api_training_pick():
    """Il trainee sceglie/banna un campione nel proprio turno - la risposta
    include GIA' l'eventuale mossa immediata del bot (nessun polling
    necessario, a differenza di "modalita' torneo": qui non c'e' un sito
    esterno con un proprio ritmo, ogni azione e' sincrona)."""
    body = request.json or {}
    champion = str(body.get("champion", "")).strip()
    response.content_type = "application/json"
    if not champion:
        return json.dumps({"error": "Nessun campione specificato."})

    try:
        session = training_bot.apply_pick(champion)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Errore durante la selezione: {e}"})

    return json.dumps(session.state(), ensure_ascii=False)


@app.post("/api/training/stop")
def api_training_stop():
    training_bot.stop_session()
    response.content_type = "application/json"
    return json.dumps({"active": False})


@app.post("/api/training/rewind")
def api_training_rewind():
    """"Ripeti da qui" (richiesta esplicita dell'utente 2026-08-26) - torna
    la draft allo stato subito prima di una delle proprie scelte passate,
    scartando tutto cio' che e' successo dopo (comprese le risposte del
    bot), cosi' il coach puo' riprovare un pick diverso dallo stesso punto."""
    body = request.json or {}
    step = body.get("step")
    response.content_type = "application/json"
    if not isinstance(step, int):
        return json.dumps({"error": "Punto di rewind non valido."})

    try:
        session = training_bot.rewind(step)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Errore durante il rewind: {e}"})

    return json.dumps(session.state(), ensure_ascii=False)


@app.post("/api/training/assign-roles")
def api_training_assign_roles():
    """Assegnazione MANUALE dei ruoli ai propri 5 pick, a fine draft -
    richiesta esplicita dell'utente (2026-08-26): decide lui quale dei suoi
    pick va in quale corsia (gli serve per un passo successivo non ancora
    specificato). A differenza del riepilogo automatico (sempre presente per
    entrambi i lati in /state, vedi assign_roles), questo tocca SOLO il lato
    del trainee ed e' una sua scelta esplicita, non un suggerimento."""
    body = request.json or {}
    order = body.get("order")
    response.content_type = "application/json"
    if not isinstance(order, list) or not all(isinstance(x, str) for x in order):
        return json.dumps({"error": "Ordine ruoli non valido."})

    try:
        session = training_bot.assign_trainee_roles(order)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Errore durante l'assegnazione ruoli: {e}"})

    return json.dumps(session.state(), ensure_ascii=False)


@app.post("/api/training/evaluate")
def api_training_evaluate():
    """"Valuta la draft" (richiesto esplicitamente dall'utente 2026-08-26,
    dopo la lunga discussione sulla curva winrate/durata-partita di
    lolalytics - vedi memoria progetto) - richiede una draft finita CON i
    ruoli del trainee gia' confermati (vedi /api/training/assign-roles).
    Lancia fino a 5 fetch veri in parallelo (uno per corsia, vedi
    draft_evaluation.py) - puo' richiedere diversi secondi, e' normale."""
    body = request.json or {}
    tier = str(body.get("tier", DEFAULT_TIER)).strip()
    response.content_type = "application/json"
    if tier not in VALID_TIERS:
        return json.dumps({"error": "Fascia elo non valida."})

    session = training_bot.get_session()
    if session is None:
        return json.dumps({"error": "Nessuna sessione di allenamento attiva."})

    try:
        result = evaluate_session(session, tier)
    except EvaluationError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Errore durante la valutazione: {e}"})

    return json.dumps(result, ensure_ascii=False)


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """WSGIRefServer di default e' single-threaded: con ~170 icone richieste
    quasi in contemporanea, le richieste si accodano e il browser abbandona
    quelle troppo lente mostrando l'icona rotta. Un thread per richiesta
    risolve il collo di bottiglia."""

    daemon_threads = True


def run_server(host="127.0.0.1", port=8721, debug=False):
    run(app, host=host, port=port, quiet=not debug, server_class=ThreadingWSGIServer)


if __name__ == "__main__":
    run_server(debug=True)
