"""Fetch + aggregazione dati draft pro da Leaguepedia (lol.fandom.com), per la
modalita' "allenamento vs draft pro" (feature 4). Vedi memoria progetto per il
design completo - qui c'e' SOLO lo strato dati (fetch, ricostruzione ordine
cronologico, aggregazione sinergia/counter, persistenza locale). La logica del
bot vive separata in training_bot.py, sopra questo strato.

Leaguepedia e' un MediaWiki con l'estensione Cargo (dati strutturati
interrogabili tipo SQL via action=cargoquery) - NON un sito da scrapare come
op.gg/lolalytics/u.gg, quindi richieste HTTP dirette (urllib, stdlib - niente
Playwright, non serve un browser vero per una vera API JSON).

Tabelle usate (verificate dal vivo via Special:CargoTables/<nome>, pagine
wiki normali NON soggette al rate limit dell'API, a differenza di
cargoquery):
- PicksAndBansS7: pick/ban/ruolo per squadra di ogni game pro (Team1/Team2 =
  SEMPRE blue/red per quella game specifica, non un'identita' di squadra
  persistente - convenzione Leaguepedia). Niente colonna data/patch diretta.
- ScoreboardGames: risultati/metadata per game, incluso DateTime_UTC e Patch.
  Collegata a PicksAndBansS7 tramite GameId (presente in entrambe).

Rate limiting: action=cargoquery e' limitato per IP (verificato: stesso
limite sia da browser che da script, quindi non aggirabile cambiando
User-Agent) - _cargo_request() ritenta con backoff esponenziale invece di
fallire subito, e' normale per qualunque API pubblica usata a raffica.
"""

import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field

from driftdraft.comps import COMP_REQUIREMENTS, MEMBER_THRESHOLD
from driftdraft.data import load_champions, slugify_champion_name
from driftdraft.paths import get_app_dir

CARGO_API_URL = "https://lol.fandom.com/api.php"

# Descrittivo con contatto, come richiesto dall'etichetta MediaWiki API (e
# stesso principio gia' seguito per gli altri User-Agent del progetto).
_USER_AGENT = "DriftDraft/1.0 (local LoL coaching tool; contact: mt57heavytankm@gmail.com)"

DRAFTS_PATH = get_app_dir() / "data" / "leaguepedia_drafts.json"
TABLES_PATH = get_app_dir() / "data" / "leaguepedia_tables.json"

# Quante draft recenti scaricare di default ad ogni sync - non ancora
# esposto in UI (nessuna decisione presa insieme all'utente su questo
# numero), scelta ragionevole propria: abbastanza dati per rendere le
# tabelle sinergia/counter dense, ordinate per data DESC quindi comunque
# sbilanciate verso il meta piu' recente senza bisogno di un filtro patch
# esplicito. Facile da alzare in futuro se servisse piu' densita'.
# Quante draft pro scaricare per un aggiornamento completo.
#
# Portato da 1500 a 3000 il 2026-09-06. Motivo: col counter direzionale e la
# soglia MIN_SUPPORT e' emerso che il limite vero non era il modo di contare
# ma la QUANTITA' di osservazioni - 88 campioni su 164 non avevano abbastanza
# dati per una risposta, e nessun accorgimento sul conteggio puo' fabbricare
# partite che non ci sono.
#
# Perche' 3000 e non di piu': queste draft sono le PIU' RECENTI, quindi il
# numero decide anche quanto indietro si va nel tempo. Misurato sulle 1500
# precedenti: 31 giorni, 3 patch (26.15/26.16/26.17), circa 48 draft al
# giorno. Quindi 3000 = circa 2 mesi e 4-5 patch, mentre 5000 sarebbero oltre
# 3 mesi e 8000 mezzo anno - con i campioni ribilanciati nel frattempo, e
# suggerimenti che verrebbero da un meta che non esiste piu'. 3000 raddoppia
# le osservazioni restando in una finestra ancora riconoscibile.
DEFAULT_FETCH_TOTAL = 3000
_CARGO_BATCH_SIZE = 500  # limite standard di una singola query Cargo

# Ordine standard del draft da torneo LoL (Ban Phase 1: 3+3, Pick Phase 1:
# 3+3, Ban Phase 2: 2+2, Pick Phase 2: 2+2) - regolamento Riot, pubblico e
# fisso, verificato dal vivo aprendo una draft board reale (vedi note di
# progetto). "team1"="blue", "team2"="red" per convenzione Leaguepedia
# (Team1 e' sempre il lato blue di QUELLA game specifica). Ogni entry e'
# (kind, side, slot_index0-based). Riusato SIA per ricostruire l'ordine
# cronologico vero di una draft storica (chronological_order sotto) SIA per
# scandire il turno di una draft simulata in training_bot.py (stesso
# identico schema - importato da li', non duplicato).
DRAFT_SEQUENCE: list[tuple[str, str, int]] = [
    ("ban", "team1", 0), ("ban", "team2", 0),
    ("ban", "team1", 1), ("ban", "team2", 1),
    ("ban", "team1", 2), ("ban", "team2", 2),
    ("pick", "team1", 0), ("pick", "team2", 0),
    ("pick", "team2", 1), ("pick", "team1", 1),
    ("pick", "team1", 2), ("pick", "team2", 2),
    ("ban", "team2", 3), ("ban", "team1", 3),
    ("ban", "team2", 4), ("ban", "team1", 4),
    ("pick", "team2", 3), ("pick", "team1", 3),
    ("pick", "team1", 4), ("pick", "team2", 4),
]


# Posizione GLOBALE di ogni pick nella draft (1..10), ricavata una volta
# sola da DRAFT_SEQUENCE invece di essere riscritta a mano: se un giorno
# quella sequenza cambiasse, questa la seguirebbe da sola.
# team1 e' il lato BLU, quello che pesca per primo: e' la convenzione della
# tabella PicksAndBansS7 di Leaguepedia, ed e' gia' quella che DRAFT_SEQUENCE
# assume qui sopra.
# Versione dello SCHEMA delle tabelle aggregate. Va alzata ogni volta che
# cambia il SIGNIFICATO di un conteggio, non quando cambiano i dati: un file
# salvato con uno schema vecchio verra' ricostruito da solo al primo utilizzo
# (vedi load_tables). Storia:
#   1 = counter simmetrico (ogni scontro contato nei due versi)
#   2 = counter direzionale "A pescato dopo B" (2026-09-06)
#   3 = + i ban di seconda fase come counter (2026-09-06)
TABLES_SCHEMA = 5

PICK_ORDER: dict[tuple[str, int], int] = {}
# Passo assoluto nella sequenza (1..20), per pick E ban: serve a sapere cosa
# era gia' successo quando una squadra ha bannato. I ban 1-3 cadono ai passi
# 1, 3, 5 - PRIMA di qualunque pick, quindi non possono essere una risposta a
# niente; i ban 4-5 ai passi 14 e 16, dopo i primi sei pick. E' il motivo per
# cui "solo gli ultimi due ban" non e' una regola da scrivere: viene da se'
# dal confronto fra i passi (vedi build_tables).
STEP_PICK: dict[tuple[str, int], int] = {}
STEP_BAN: dict[tuple[str, int], int] = {}
_pos = _step = 0
for _kind, _side, _idx in DRAFT_SEQUENCE:
    _step += 1
    if _kind == "pick":
        _pos += 1
        PICK_ORDER[(_side, _idx)] = _pos
        STEP_PICK[(_side, _idx)] = _step
    else:
        STEP_BAN[(_side, _idx)] = _step
del _pos, _step, _kind, _side, _idx


@dataclass
class ProDraft:
    game_id: str
    tournament: str
    date: str | None
    patch: str | None
    team1: str
    team2: str
    winner: int | None  # 1 o 2, None se sconosciuto
    team1_picks: list[str] = field(default_factory=list)  # ordine cronologico PickN del lato, gia' risolti a nomi DriftDraft
    team2_picks: list[str] = field(default_factory=list)
    team1_roles: list[str] = field(default_factory=list)  # stesso ordine dei picks sopra, NON un ordine per corsia
    team2_roles: list[str] = field(default_factory=list)
    team1_bans: list[str] = field(default_factory=list)
    team2_bans: list[str] = field(default_factory=list)


def chronological_picks(draft: ProDraft) -> list[dict]:
    """Espande i pick di questa draft nell'ordine cronologico VERO
    (intrecciato fra le due squadre), applicando DRAFT_SEQUENCE - usato per
    mostrare/rigiocare una draft storica in modalita' "ancorata"."""
    result = []
    for kind, side, idx in DRAFT_SEQUENCE:
        if kind != "pick":
            continue
        champs = draft.team1_picks if side == "team1" else draft.team2_picks
        roles = draft.team1_roles if side == "team1" else draft.team2_roles
        if idx >= len(champs):
            continue
        result.append({
            "side": side,
            "champion": champs[idx],
            "role": roles[idx] if idx < len(roles) else None,
        })
    return result


# --- risoluzione nomi campione: Leaguepedia usa nomi ufficiali (di solito
# identici a quelli nell'xlsx DriftDraft), ma per sicurezza si passa comunque
# per lo slug condiviso (stessa tecnica di ugg.py/opgg.py) invece di
# confrontare le stringhe cosi' come sono - assorbe differenze minori di
# maiuscole/punteggiatura senza doverle enumerare a mano. ---
_champion_name_by_slug: dict[str, str] | None = None


def _resolve_champion_name(raw: str) -> str | None:
    global _champion_name_by_slug
    if not raw:
        return None
    if _champion_name_by_slug is None:
        _champion_name_by_slug = {slugify_champion_name(c.name): c.name for c in load_champions()}
    return _champion_name_by_slug.get(slugify_champion_name(raw))


# Leaguepedia usa "Top"/"Jungle"/"Middle"/"Bottom"/"Support" o abbreviazioni
# a seconda della tabella/epoca - normalizzato al vocabolario di questo
# progetto (ROLE_COLUMNS in data.py: Top/Jungle/Mid/Bot/Support). Solo
# informativo (mostrato in modalita' "ancorata" per la draft di riferimento,
# non usato per alcuna logica di piazzamento) - un valore non riconosciuto
# passa attraverso invariato invece di scomparire.
_ROLE_NORMALIZE = {
    "top": "Top",
    "jungle": "Jungle",
    "jg": "Jungle",
    "mid": "Mid",
    "middle": "Mid",
    "bot": "Bot",
    "bottom": "Bot",
    "adc": "Bot",
    "support": "Support",
    "sup": "Support",
    "supp": "Support",
}


def _normalize_role(raw: str) -> str:
    return _ROLE_NORMALIZE.get((raw or "").strip().lower(), raw)


def _cargo_request(params: dict, max_attempts: int = 8, on_wait=None) -> dict:
    """GET a action=cargoquery con backoff esponenziale sul rate limit
    (verificato: risposta 200 con {"error":{"code":"ratelimited"}}, non un
    codice HTTP di errore - va controllato nel corpo, non solo lo status).

    Il limite osservato empiricamente e' piu' severo di un semplice "poche
    richieste al secondo": una singola query riuscita puo' comunque far
    scattare ratelimited su quella SUBITO successiva per diversi minuti
    (verificato: un fetch di prova da 25 draft riuscito in 8s, poi un fetch
    da 1500 lanciato circa un minuto dopo ha esaurito 6 tentativi con un tetto
    di 60s ciascuno senza mai sbloccarsi). Backoff piu' paziente di quanto
    verrebbe istintivo per una API normale - accettabile qui perche' e' un
    sync in background che l'utente non deve stare a guardare (vedi
    fetch_recent_drafts/sync), non un percorso interattivo a bassa latenza.
    """
    query = dict(params)
    query["action"] = "cargoquery"
    query["format"] = "json"
    url = CARGO_API_URL + "?" + urllib.parse.urlencode(query)

    delay = 15.0
    last_error = "motivo sconosciuto"
    for attempt in range(max_attempts):
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last_error = str(e)
            # on_wait: l'attesa e' la parte piu' lunga e piu' opaca di tutto
            # il sync (fino a 120s per tentativo). Segnalarla permette alla UI
            # di dire "riprovo fra Ns" invece di restare muta - vedi
            # sync_progress() e il pannello Pick suggeriti.
            if on_wait:
                on_wait(delay, attempt + 1, max_attempts, last_error)
            time.sleep(delay)
            delay = min(delay * 2, 120.0)
            continue

        if "error" in data:
            code = data["error"].get("code")
            if code == "ratelimited":
                last_error = "limite di frequenza dell'API Leaguepedia"
                if on_wait:
                    on_wait(delay, attempt + 1, max_attempts, last_error)
                time.sleep(delay)
                delay = min(delay * 2, 120.0)
                continue
            raise RuntimeError(f"Errore API Leaguepedia: {data['error'].get('info', data['error'])}")

        return data

    raise RuntimeError(
        f"Leaguepedia non raggiungibile dopo {max_attempts} tentativi ({last_error}) - riprova piu' tardi."
    )


_PB_FIELD_NAMES = (
    ["GameId", "OverviewPage", "Winner", "Team1", "Team2"]
    + [f"Team1Pick{i}" for i in range(1, 6)]
    + [f"Team2Pick{i}" for i in range(1, 6)]
    + [f"Team1Ban{i}" for i in range(1, 6)]
    + [f"Team2Ban{i}" for i in range(1, 6)]
    + [f"Team1Role{i}" for i in range(1, 6)]
    + [f"Team2Role{i}" for i in range(1, 6)]
)
_PB_FIELDS = [f"PB.{name}=PB_{name}" for name in _PB_FIELD_NAMES] + [
    "SG.DateTime_UTC=DateTime_UTC",
    "SG.Patch=Patch",
]


def _row_to_draft(row: dict) -> ProDraft | None:
    def picks(prefix: str) -> list[str | None]:
        return [_resolve_champion_name(row.get(f"PB_{prefix}{i}", "")) for i in range(1, 6)]

    def roles(prefix: str) -> list[str]:
        return [_normalize_role(row.get(f"PB_{prefix}{i}", "")) for i in range(1, 6)]

    t1_picks, t2_picks = picks("Team1Pick"), picks("Team2Pick")
    if any(c is None for c in t1_picks + t2_picks):
        return None  # nome non risolto o slot mancante - draft scartata, non affidabile

    t1_bans = [n for n in picks("Team1Ban") if n]
    t2_bans = [n for n in picks("Team2Ban") if n]

    winner_raw = row.get("PB_Winner")
    try:
        winner = int(winner_raw) if winner_raw not in (None, "") else None
    except (TypeError, ValueError):
        winner = None

    return ProDraft(
        game_id=row.get("PB_GameId", "") or "",
        tournament=row.get("PB_OverviewPage", "") or "",
        date=row.get("DateTime_UTC") or None,
        patch=row.get("Patch") or None,
        team1=row.get("PB_Team1", "") or "",
        team2=row.get("PB_Team2", "") or "",
        winner=winner,
        team1_picks=t1_picks,
        team2_picks=t2_picks,
        team1_roles=roles("Team1Role"),
        team2_roles=roles("Team2Role"),
        team1_bans=t1_bans,
        team2_bans=t2_bans,
    )


def fetch_recent_drafts(
    total: int = DEFAULT_FETCH_TOTAL,
    patch_prefix: str | None = None,
    on_progress=None,
) -> list[ProDraft]:
    """Scarica le `total` draft pro complete piu' recenti (paginato a blocchi
    da 500, il massimo di una singola query Cargo), unendo PicksAndBansS7 a
    ScoreboardGames su GameId per avere data/patch. Una draft e' scartata (non
    solo saltata a meta') se anche un solo pick non risolve a un nome
    campione DriftDraft valido - meglio poche draft affidabili che tabelle
    sinergia/counter sporcate da entry rotte.

    Se una pagina SUCCESSIVA alla prima esaurisce tutti i tentativi (rate
    limit persistente, vedi _cargo_request), non butta via cio' che le pagine
    precedenti avevano gia' scaricato - ritorna quello che ha, invece di
    sollevare e perdere tutto. Solleva solo se la PRIMISSIMA pagina fallisce
    (zero draft totali, niente di utile da salvare comunque)."""
    where = "PB.IsComplete=1 AND PB.Winner IS NOT NULL"
    if patch_prefix:
        escaped = patch_prefix.replace('"', '')
        where += f' AND SG.Patch LIKE "{escaped}%"'

    drafts: list[ProDraft] = []
    offset = 0
    first_batch = True
    page = 0

    def report(phase: str, **extra) -> None:
        if on_progress:
            on_progress({"phase": phase, "drafts": len(drafts), "target": total, **extra})

    while len(drafts) < total:
        page += 1
        if not first_batch:
            # Pausa deliberata fra due query RIUSCITE consecutive (non solo
            # nei retry falliti, vedi _cargo_request) - il limite osservato
            # sembra scattare anche subito dopo un successo, questa pausa
            # riduce quanto spesso serve poi il backoff completo.
            report("pausa", seconds=10, page=page)
            time.sleep(10)

        report("scarico", page=page)
        batch_limit = min(_CARGO_BATCH_SIZE, total - len(drafts) + 50)  # margine per compensare draft scartate
        params = {
            "tables": "PicksAndBansS7=PB,ScoreboardGames=SG",
            "join_on": "PB.GameId=SG.GameId",
            "fields": ",".join(_PB_FIELDS),
            "where": where,
            "order_by": "SG.DateTime_UTC DESC",
            "limit": str(batch_limit),
            "offset": str(offset),
        }
        try:
            data = _cargo_request(
                params,
                on_wait=lambda secs, att, maxatt, why: report(
                    "attesa", seconds=round(secs), attempt=att, maxAttempts=maxatt, reason=why, page=page
                ),
            )
        except RuntimeError:
            if first_batch:
                raise
            break  # abbiamo gia' qualcosa di utile dalle pagine precedenti, meglio di niente

        first_batch = False
        rows = [entry.get("title", entry) for entry in data.get("cargoquery", [])]
        if not rows:
            break

        for row in rows:
            draft = _row_to_draft(row)
            if draft:
                drafts.append(draft)

        offset += len(rows)
        report("scarico", page=page)
        if len(rows) < batch_limit:
            # Non e' un errore: Leaguepedia non ha altre draft complete oltre
            # queste. La UI lo distingue da "finito perche' ho raggiunto il
            # totale" mostrando "non c'e' altro da importare".
            report("esaurito", page=page)
            break

    return drafts[:total] if len(drafts) > total else drafts


# Quante draft servono a una squadra perche' la sua pool voglia dire qualcosa.
# A 15 restano 197 squadre che coprono l'80% dei lati; a 20 sarebbero 114
# (57%), a 10 sarebbero 261 (93%) ma con pool troppo sottili per distinguere
# l'abitudine dal caso.
TEAM_POOL_MIN_DRAFTS = 15

# I pick recenti pesano di piu', ma i vecchi non spariscono. Parole
# dell'utente: "piu' e' recente piu' e' attuale col meta, ma fino ad un certo
# punto - non togliere completamente i pick vecchi, i campioni viabili in
# proplay restano abbastanza simili in 4-5 patch". Da qui la mezza vita a 4
# patch e un pavimento sotto cui non si scende.
#
# Misurato sulle 197 squadre: cambia il campione piu' giocato di una corsia
# nel 9.4% dei casi e i primi tre nel 15.3% - rinfresca senza riscrivere
# l'identita' della squadra. Con mezza vita 2 salirebbe a 16% e 28.5%, troppo
# per quel "fino ad un certo punto".
#
# Il pavimento oggi quasi non morde (i dati coprono 8 patch, e 0.5^(7/4) vale
# gia' 0.30): serve fra un anno, quando la finestra sara' piu' lunga.
TEAM_POOL_HALF_LIFE = 4.0
TEAM_POOL_FLOOR = 0.35


def _patch_number(patch: str | None) -> int | None:
    """"26.14" -> 2614, per poter dire quanto dista una patch da un'altra."""
    try:
        maggiore, minore = str(patch).split(".")[:2]
        return int(maggiore) * 100 + int(minore)
    except (AttributeError, ValueError):
        return None


def build_team_pools(drafts: list[ProDraft]) -> dict:
    """Cosa gioca ciascuna squadra pro, corsia per corsia.

    E' il materiale con cui il bot impersona una squadra vera invece di
    inseguire una singola draft storica (la vecchia "modalita' ancorata", che
    l'utente ha giudicato fallata: ripeteva i pick che quella squadra fece
    contro un avversario che nella draft in corso non c'e').

    **Il vantaggio rispetto a op.gg e alle tier list: qui il ruolo di ogni
    pick e' REGISTRATO.** Niente deduzione, niente assegnazione per biiezione,
    niente incertezza da segnalare - la parte piu' fragile del sistema qui non
    esiste proprio.

    I conteggi sono pesati per recency (vedi le costanti sopra) e restano
    conteggi grezzi: la normalizzazione a 0..1 la fa chi costruisce il profilo,
    perche' e' li' che serve la convenzione "1.0 = il loro cavallo di
    battaglia", la stessa delle altre due sorgenti.

    Escluse le squadre sotto TEAM_POOL_MIN_DRAFTS: con quattro partite la
    "pool" e' solo l'elenco di cosa hanno pescato quelle volte.
    """
    numeri = [n for d in drafts if (n := _patch_number(d.patch)) is not None]
    ultima = max(numeri) if numeri else 0

    def peso(patch: str | None) -> float:
        n = _patch_number(patch)
        if n is None:
            return TEAM_POOL_FLOOR
        distanza = max(0, ultima - n)
        return max(TEAM_POOL_FLOOR, 0.5 ** (distanza / TEAM_POOL_HALF_LIFE))

    pools: dict[str, dict[str, dict[str, float]]] = {}
    conteggio: dict[str, int] = {}
    for d in drafts:
        w = peso(d.patch)
        for team, picks, roles in ((d.team1, d.team1_picks, d.team1_roles),
                                   (d.team2, d.team2_picks, d.team2_roles)):
            if not team:
                continue
            coppie = [(c, r) for c, r in zip(picks, roles) if c and r]
            if len(coppie) != 5:
                continue  # draft incompleta: non dice niente sulle abitudini
            conteggio[team] = conteggio.get(team, 0) + 1
            per_ruolo = pools.setdefault(team, {})
            for champ, ruolo in coppie:
                corsia = per_ruolo.setdefault(ruolo, {})
                corsia[champ] = corsia.get(champ, 0.0) + w

    return {
        "min_drafts": TEAM_POOL_MIN_DRAFTS,
        "teams": {
            t: {"drafts": conteggio[t], "per_role": pools[t]}
            for t in pools
            if conteggio.get(t, 0) >= TEAM_POOL_MIN_DRAFTS
        },
    }


def build_comp_stats(drafts: list[ProDraft]) -> dict:
    """Come si comportano le comp nei dati che abbiamo ADESSO.

    Sono numeri che il bot usa per calibrarsi, e vivono qui e non come
    costanti scritte a mano per una ragione precisa, dettata dall'utente: il
    meta si sposta. Se una patch buffa gli enchanter e "Proteggi il
    presidente" torna giocabile, quelle frequenze cambiano - e devono
    cambiare da sole al prossimo "Aggiorna dati", non alla prossima volta che
    qualcuno si ricorda di riscrivere una costante. Per questo stanno nelle
    tabelle, che si rigenerano insieme al resto.

    Due cose:

    `rates` - quanto spesso ciascuna comp risulta soddisfatta su un lato.
    E' il bersaglio di calibrazione: il bot dovrebbe produrre draft che
    somigliano a queste frequenze, non a un'idea di comp che ho in testa io.

    `direction_accuracy` - dopo k pick, quanto la comp piu' avanti di un lato
    predice quella che risultera' a fine draft. Dice DA QUANDO ha senso
    anticipare l'avversario: prima e' indovinare, ed e' lo stesso principio
    di MIN_SUPPORT (meglio non dire niente che dire a caso).

    Se i dati dei campioni non sono leggibili si torna un dizionario vuoto:
    sono statistiche di supporto, non devono impedire la costruzione del
    resto delle tabelle.
    """
    try:
        champs = {c.name: c for c in load_champions()}
    except Exception:
        return {}
    if not champs:
        return {}

    comps = list(COMP_REQUIREMENTS)

    def membri(picks) -> dict:
        return {
            c: sum(1 for p in picks if p in champs and c in champs[p].comps)
            for c in comps
        }

    def direzione(conteggi):
        """La comp verso cui quel lato sta andando, o None se e' in parita'."""
        ordinati = sorted(conteggi.items(), key=lambda kv: -kv[1])
        if not ordinati or ordinati[0][1] == 0:
            return None
        if len(ordinati) > 1 and ordinati[0][1] == ordinati[1][1]:
            return None
        return ordinati[0][0]

    lati = 0
    soddisfatte = {c: 0 for c in comps}
    leggibili = {k: 0 for k in range(1, 6)}
    azzeccate = {k: 0 for k in range(1, 6)}

    for d in drafts:
        for picks in (d.team1_picks, d.team2_picks):
            p = [x for x in picks if x]
            if len(p) != 5:
                continue
            lati += 1
            conteggi = membri(p)
            for c in comps:
                if conteggi[c] >= MEMBER_THRESHOLD:
                    soddisfatte[c] += 1
            finale = direzione(conteggi)
            if finale is None:
                continue
            for k in range(1, 6):
                ora = direzione(membri(p[:k]))
                if ora is None:
                    continue
                leggibili[k] += 1
                if ora == finale:
                    azzeccate[k] += 1

    if not lati:
        return {}
    return {
        "sides": lati,
        "rates": {c: soddisfatte[c] / lati for c in comps},
        "direction_accuracy": {
            str(k): (azzeccate[k] / leggibili[k]) if leggibili[k] else 0.0
            for k in range(1, 6)
        },
    }


def build_tables(drafts: list[ProDraft]) -> dict:
    """Tabelle coppia-per-coppia, conteggi di co-occorrenza puri (nessun
    esito vittoria/sconfitta, vedi note di progetto sul perche').

    SINERGIA: stessa squadra, simmetrica - due campioni giocati insieme lo
    sono per entrambi, l'ordine non vuol dire niente.

    COUNTER: squadre opposte, **DIREZIONALE dal 2026-09-06**.
    `counter[A][B]` = quante volte A e' stato pescato DOPO B, a squadre
    opposte: quante volte A e' stato una RISPOSTA a B.

    Prima era simmetrica (ogni coppia avversaria incrementava entrambi i
    versi) ed era un errore di modello, segnalato dall'utente con un caso
    concreto: "se io prendo Yasuo, ai nemici suggerisce Gnar. Yasuo viene
    preso IN RISPOSTA a Gnar, non il contrario". Un conteggio simmetrico non
    puo' distinguere le due cose: vede solo "Yasuo e Gnar si sono affrontati
    N volte" e risponde N in entrambe le direzioni. Il danno e' peggiore per
    un coach poco esperto, che si fida: "i nemici hanno preso Yasuo, mi
    propone Gnar, sara' una buona risposta" - quando Gnar e' proprio il pick
    che Yasuo puniva.

    L'ordine si ricava da PICK_ORDER (vedi sopra): non serve nessun dato
    nuovo, era gia' tutto in ProDraft, semplicemente non veniva guardato.

    ONESTA' SUI LIMITI, misurato sui 1500 draft dell'utente PRIMA di fare la
    modifica (script in scratchpad, vedi memoria di progetto):
      - l'ordine porta segnale vero: sulle coppie con almeno 10 scontri la
        direzione dominante vale in media il 73% (50% sarebbe rumore puro);
      - ma l'87% di quell'asimmetria e' spiegato da QUANDO un campione si
        pesca di solito, non da una relazione specifica fra i due. In
        pratica questa tabella dice soprattutto "i counter-pick rispondono
        ai blind-pick" (Nocturne/Vi/Orianna stanno intorno alla posizione
        2.5-2.9, Malphite/Dr. Mundo/Vayne intorno alla 8.5-8.9). E' comunque
        cio' che serve: e' esattamente il motivo per cui non ha senso
        proporre un blind-pick come risposta a un counter-pick;
      - il totale dei conteggi si dimezza (75000 -> 37500 sui 1500 draft),
        perche' prima ogni scontro veniva contato due volte. I candidati
        BUONI perdono poco - i loro scontri erano gia' quasi tutti nel verso
        "dopo" - a sparire e' il verso sbagliato. Per questo
        SYNERGY_WEIGHT/COUNTER_WEIGHT non sono stati ritoccati.

    **I BAN DI SECONDA FASE contano come counter, dal 2026-09-06.** Idea
    dell'utente: "potremmo ricavare i ban presi come 'questi campioni ci
    ostacolano' e quindi inserirli effettivamente come punteggio counter?
    Normalmente parliamo degli ultimi 2 ban, i primi 3 sono fatti per evitare
    gli stessi meta-pick, mentre gli ultimi 2 sono fatti apposta per dire
    'questi campioni, per la draft che stiamo creando, danno fastidio'".

    Cattura una cosa che i pick per definizione non possono catturare: i
    matchup che non avvengono MAI perche' vengono impediti. L'esempio suo:
    "malphite vs sylas e' una cosa da evitare in qualsiasi circostanza, sylas
    vincera' sempre, ed e' per questo che i dati manco lo fanno apparire, in
    quanto il team che prende malphite si deve assicurare il ban di sylas ad
    ogni costo".

    Quindi: per ogni ban di una squadra, per ogni suo pick GIA' fatto in quel
    momento, counter[bannato][pick] += 1 - "il bannato e' una risposta a quel
    pick". La distinzione fra primi tre e ultimi due ban non e' scritta da
    nessuna parte: viene fuori da sola dal confronto fra i passi, perche' i
    primi tre cadono prima di ogni pick e non hanno nulla a cui riferirsi.
    La direzione resta coerente col counter direzionale: il ban avviene DOPO
    i pick a cui risponde.

    Squadre con meno di 5 ban vengono saltate (1.3% dei casi): _row_to_draft
    compatta la lista scartando i ban vuoti, quindi li' l'indice non
    corrisponde piu' allo slot e non si puo' sapere a che passo sia avvenuto.

    Peso PIENO, come un pick, dopo averlo misurato: il timore era che i
    campioni bannati contro tutto (Vayne da sola e' il 4.5% dei ban di
    seconda fase) diventassero una risposta universale. Misurato invece che
    supposto - il campione piu' "universale" passa dal 26.8% al 26.2% degli
    scenari, cioe' la concentrazione non peggiora - mentre una variante piu'
    prudente (solo le coppie con lift >= 1.5) recuperava meno della meta' dei
    campioni. Aggiunge 17772 osservazioni sulle 37500 da soli pick (+47%).

    Un pick_counts terzo, popolarita' grezza per campione - usato
    da training_bot.py come euristica per i ban del bot (nessuna sinergia/
    counter ha senso per "cosa bannare", solo "cosa e' forte/contestato").

    Un quarto role_counts (dal 2026-09-05): campione -> quante volte e' stato
    giocato in ciascuna corsia in queste draft. Serve ai "pick suggeriti",
    che mostrano la corsia accanto ad ogni suggerimento - richiesta esplicita
    dell'utente: "alcuni campioni possono essere giocati in diverse corsie
    rispetto alla loro principale, ed alcune risposte sono specifiche (vedesi
    poppy support contro specifici campioni)". La fonte giusta e' proprio
    questa e non i ruoli di champions.xlsx: li' c'e' il ruolo "di scheda" del
    campione, qui c'e' quello che i pro giocano DAVVERO nella patch corrente
    - se Poppy in questo meta si vede a support, sono questi numeri a dirlo.
    I ruoli arrivano allineati posizionalmente ai pick (team1_roles[i] e' la
    corsia di team1_picks[i], vedi _row_to_draft)."""
    synergy: dict[str, dict[str, int]] = {}
    counter: dict[str, dict[str, int]] = {}
    pick_counts: dict[str, int] = {}
    role_counts: dict[str, dict[str, int]] = {}

    def bump(table: dict[str, dict[str, int]], a: str, b: str) -> None:
        if a == b:
            return
        table.setdefault(a, {})
        table[a][b] = table[a].get(b, 0) + 1

    for d in drafts:
        for name in d.team1_picks + d.team2_picks:
            pick_counts[name] = pick_counts.get(name, 0) + 1

        # zip() si ferma al piu' corto dei due: se una draft avesse i ruoli
        # incompleti (capita su righe Leaguepedia parziali) i pick restanti
        # vengono semplicemente saltati qui, senza disallineare nulla.
        for picks, roles in ((d.team1_picks, d.team1_roles), (d.team2_picks, d.team2_roles)):
            for name, role in zip(picks, roles):
                if not name or not role:
                    continue
                role_counts.setdefault(name, {})
                role_counts[name][role] = role_counts[name].get(role, 0) + 1

        for team_picks in (d.team1_picks, d.team2_picks):
            for i in range(len(team_picks)):
                for j in range(i + 1, len(team_picks)):
                    bump(synergy, team_picks[i], team_picks[j])
                    bump(synergy, team_picks[j], team_picks[i])

        # Counter DIREZIONALE (vedi docstring): ogni coppia avversaria viene
        # contata UNA volta sola, nel verso di chi ha pescato dopo. Le due
        # meta' restano separate perche' le coppie di squadra sono sinergia,
        # gia' contate qui sopra. PICK_ORDER.get(): una draft con piu' di 5
        # pick per lato non dovrebbe esistere (_row_to_draft le scarta), ma
        # un file salvato a mano non deve far esplodere l'aggregazione.
        blu = [(PICK_ORDER.get(("team1", i)), n) for i, n in enumerate(d.team1_picks) if n]
        rosso = [(PICK_ORDER.get(("team2", i)), n) for i, n in enumerate(d.team2_picks) if n]
        for pos_a, a in blu:
            for pos_b, b in rosso:
                if pos_a is None or pos_b is None:
                    continue
                if pos_a > pos_b:
                    bump(counter, a, b)
                else:
                    bump(counter, b, a)

        # I ban come counter (vedi docstring). Nessun filtro sul numero del
        # ban: si confrontano i passi, e i primi tre si escludono da soli
        # perche' avvengono prima di ogni pick.
        for lato, bans, picks in (("team1", d.team1_bans, d.team1_picks),
                                  ("team2", d.team2_bans, d.team2_picks)):
            if len(bans) != len(STEP_BAN) // 2:
                continue  # lista compattata: gli indici non sono affidabili
            for idx, bannato in enumerate(bans):
                passo_ban = STEP_BAN.get((lato, idx))
                if not bannato or passo_ban is None:
                    continue
                for i, pick in enumerate(picks):
                    passo_pick = STEP_PICK.get((lato, i))
                    if pick and passo_pick is not None and passo_pick < passo_ban:
                        bump(counter, bannato, pick)

    return {
        "schema": TABLES_SCHEMA,
        "synergy": synergy,
        "counter": counter,
        "pick_counts": pick_counts,
        "role_counts": role_counts,
        # Ricalcolate ad ogni ricostruzione: e' cosi' che il bot segue il meta
        # invece di inseguirlo. Vedi build_comp_stats.
        "comp_stats": build_comp_stats(drafts),
        # Chi gioca cosa, squadra per squadra: rigenerato ad ogni
        # ricostruzione come le statistiche comp, cosi' un "Aggiorna dati"
        # porta anche le abitudini aggiornate. Vedi build_team_pools.
        "team_pools": build_team_pools(drafts),
    }


def save_drafts(drafts: list[ProDraft], path=DRAFTS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": time.time(), "drafts": [asdict(d) for d in drafts]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# Cache di load_drafts, con chiave (percorso, mtime, dimensione). Il file e'
# ~1MB di JSON e da settembre 2026 viene letto anche dai "pick suggeriti"
# (per capire in che corsia i pro giocano un campione CONTRO certi
# avversari, vedi _suggest_roles in training_bot.py) - cioe' ad ogni pick
# della draft, non piu' solo all'avvio di un allenamento. Rileggerlo e
# ricostruire 1000 dataclass ogni volta costava ~45ms misurati.
# La chiave include mtime e dimensione, quindi un "Aggiorna dati" che
# riscrive il file invalida la cache da solo: nessuna invalidazione manuale
# da ricordare altrove.
_drafts_cache: tuple | None = None
_drafts_cache_key: tuple | None = None


def load_drafts(path=DRAFTS_PATH) -> list[ProDraft]:
    global _drafts_cache, _drafts_cache_key
    if not path.exists():
        return []

    st = path.stat()
    key = (str(path), st.st_mtime_ns, st.st_size)
    if _drafts_cache_key == key and _drafts_cache is not None:
        # Lista nuova ad ogni chiamata: i ProDraft sono condivisi (e nessuno
        # li muta), ma un chiamante che ordinasse/filtrasse la lista in place
        # non deve poter corrompere la cache.
        return list(_drafts_cache)

    raw = json.loads(path.read_text(encoding="utf-8"))
    drafts = [ProDraft(**d) for d in raw.get("drafts", [])]
    _drafts_cache = tuple(drafts)
    _drafts_cache_key = key
    return drafts


def save_tables(tables: dict, path=TABLES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tables, ensure_ascii=False), encoding="utf-8")


# Una ricostruzione alla volta: due richieste HTTP quasi simultanee dopo un
# aggiornamento dell'app troverebbero entrambe lo schema vecchio e
# rifarebbero lo stesso lavoro. Il risultato sarebbe comunque corretto (e'
# idempotente), ma e' inutile farlo due volte su 1500 draft.
_rebuild_lock = threading.Lock()


def load_tables(path=TABLES_PATH) -> dict:
    if not path.exists():
        return {"synergy": {}, "counter": {}, "pick_counts": {}, "role_counts": {}}
    tables = json.loads(path.read_text(encoding="utf-8"))

    # Schema vecchio: si RICOSTRUISCE dalle draft gia' su disco, senza
    # ripassare da Leaguepedia. E' la differenza fra due secondi di calcolo e
    # un riscaricamento che, col limite di frequenza di quella API, puo'
    # durare minuti (e che l'utente non ha chiesto). Le draft grezze non
    # cambiano mai di schema: sono il dato, le tabelle solo un'aggregazione.
    if tables.get("schema") != TABLES_SCHEMA:
        with _rebuild_lock:
            # Ricontrollato dentro il lock: chi era in coda trova gia' fatto.
            current = json.loads(path.read_text(encoding="utf-8"))
            if current.get("schema") == TABLES_SCHEMA:
                current.setdefault("role_counts", {})
                return current
            drafts = load_drafts()
            if drafts:
                tables = build_tables(drafts)
                save_tables(tables)

    # role_counts e' arrivato dopo (2026-09-05): un file salvato prima non ce
    # l'ha, e senza questo default ogni lettura andrebbe protetta a mano.
    tables.setdefault("role_counts", {})
    return tables


def sync(total: int = DEFAULT_FETCH_TOTAL, on_progress=None) -> dict:
    """Fetch + aggregazione + persistenza in un colpo solo.

    Chiamata in modo SINCRONO resta bloccante quanto prima; il percorso usato
    dalla UI passa pero' da start_sync()/sync_progress() qui sotto, che la
    fanno girare in un thread e ne raccontano l'avanzamento."""
    drafts = fetch_recent_drafts(total=total, on_progress=on_progress)
    if not drafts:
        raise RuntimeError("Nessuna draft valida scaricata da Leaguepedia.")

    # Un fetch che si ferma a meta' (limite di frequenza persistente su una
    # pagina successiva alla prima) ritorna cio' che ha invece di sollevare -
    # vedi fetch_recent_drafts. Senza questo controllo un aggiornamento
    # sfortunato SOSTITUIREBBE una raccolta buona con una piu' piccola, e le
    # draft gia' scaricate costano minuti di rete: si tiene la piu' ricca. Il
    # confronto e' col target oltre che con cio' che c'e', altrimenti
    # abbassare di proposito `total` diventerebbe impossibile.
    esistenti = load_drafts()
    if len(drafts) < len(esistenti) and len(drafts) < total:
        raise RuntimeError(
            f"Scaricate solo {len(drafts)} draft su {total} richieste, meno delle "
            f"{len(esistenti)} gia' presenti: i dati esistenti NON sono stati "
            "toccati. Riprova piu' tardi (Leaguepedia limita le richieste)."
        )

    if on_progress:
        on_progress({"phase": "elaboro", "drafts": len(drafts), "target": total})
    save_drafts(drafts)
    tables = build_tables(drafts)
    save_tables(tables)
    return status()


# Stato del sync in corso, condiviso fra il thread che scarica e le richieste
# HTTP che lo interrogano. Un lock semplice basta: le scritture sono piccole e
# rare (una per pagina/attesa), le letture sono un poll leggero dalla UI.
#
# Perche' async (2026-09-05): prima il bottone "Aggiorna dati" teneva appesa
# la richiesta HTTP per tutta la durata, e l'utente restava davanti a un
# pannello muto - "non c'e' scritto quanto tempo ci vuole ancora, se ha
# fatto, se non ha fatto, o se semplicemente non c'e' altro da importare".
# Il fetch puo' durare parecchio per costruzione (pagine da 500 con 10s di
# pausa fra una e l'altra, piu' un backoff fino a 120s per tentativo sul
# limite di frequenza), quindi il problema non era la lentezza ma il silenzio.
_sync_lock = threading.Lock()
_sync_state: dict = {"running": False}


def _set_sync_state(**fields) -> None:
    with _sync_lock:
        _sync_state.update(fields)


def sync_progress() -> dict:
    """Stato dell'aggiornamento in corso (o dell'ultimo concluso), piu' lo
    stato dei dati gia' su disco. Sola lettura, nessuna richiesta di rete."""
    with _sync_lock:
        state = dict(_sync_state)
    state["data"] = status()
    return state


def start_sync(total: int = DEFAULT_FETCH_TOTAL) -> dict:
    """Avvia l'aggiornamento in un thread e torna SUBITO. Se ce n'e' gia' uno
    in corso non ne lancia un secondo: due fetch paralleli si darebbero
    fastidio a vicenda sul limite di frequenza, e l'ultimo a finire
    sovrascriverebbe comunque il primo."""
    with _sync_lock:
        if _sync_state.get("running"):
            return {"alreadyRunning": True}
        _sync_state.clear()
        _sync_state.update(
            {"running": True, "phase": "avvio", "drafts": 0, "target": total, "startedAt": time.time()}
        )

    def worker() -> None:
        try:
            sync(total=total, on_progress=lambda p: _set_sync_state(**p))
        except Exception as e:
            _set_sync_state(running=False, phase="errore", error=str(e), finishedAt=time.time())
            return
        _set_sync_state(running=False, phase="fatto", error=None, finishedAt=time.time())

    threading.Thread(target=worker, daemon=True).start()
    return {"started": True}


def status() -> dict:
    """Solo lettura locale, nessuna richiesta di rete - per mostrare subito
    lo stato dell'ultimo sync (se c'e') quando si apre il pannello training,
    senza forzare un fetch ad ogni apertura."""
    if not DRAFTS_PATH.exists():
        return {"synced": False}
    raw = json.loads(DRAFTS_PATH.read_text(encoding="utf-8"))
    drafts = raw.get("drafts", [])
    patches = sorted({d.get("patch") for d in drafts if d.get("patch")}, reverse=True)
    return {
        "synced": True,
        "draftsCount": len(drafts),
        "fetchedAt": raw.get("fetched_at"),
        "recentPatches": patches[:5],
    }


