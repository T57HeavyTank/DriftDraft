"""Valutazione di una draft di allenamento completata (feature 4) - richiesto
esplicitamente dall'utente (2026-08-26) dopo il rework "assegnazione manuale
dei ruoli": una volta che il trainee ha finito la draft E confermato quali
dei suoi 5 pick vanno in quale corsia, questo modulo scarica le curve
winrate-per-durata-partita di ogni corsia (da lolalytics, vedi
driftdraft/lolalytics.py) e le aggrega in tre linee pensate per rispondere
alla domanda del coach: "questa draft funziona meglio se il game e' corto o
lungo, e contro QUESTO avversario specifico?".

Design concordato con l'utente (vedi memoria progetto per la discussione
completa - include due correzioni reali, entrambe emerse SOLO dopo aver
visto il risultato su dati veri, non durante la progettazione a tavolino):
prima un bug di viewport nel browser di ricerca aveva escluso per sbaglio la
curva "solista" (l'utente l'ha rimessa in discussione con degli screenshot
alla mano); poi, dopo aver usato la funzione su draft vere, l'utente ha
notato che il verde "seguiva in tutto e per tutto la curva blu, staccandosi
solo dell'esatto bonus/malus del bump" - CORRETTO (vedi sotto per il design
attuale, il precedente faceva letteralmente `green = list(blue)` e la
toccava solo quando scattava il bump a 3 corsie, ignorando le curve di
matchup in ogni altro bucket):
- BLU: media delle 5 curve SOLISTE dei nostri pick (nessun avversario
  specifico - la curva "generica" del campione, vedi
  lolalytics.fetch_winrate_curve(vs_champion=None)) - "senza considerare il
  team nemico".
- ROSSO: stessa cosa per i 5 pick del bot - fetch indipendente, NON il
  semplice complemento di BLU (le due squadre hanno le proprie tendenze
  solitarie, non e' detto sommino a 100).
- VERDE: media delle 5 curve di MATCHUP (nostro pick vs il loro, stesso
  ruolo - queste si', specifiche per l'avversario) - varia in modo continuo
  bucket per bucket in base a ENTRAMBE le squadre, non solo alla nostra (a
  differenza del vecchio design "blu +/- bump"), perche' e' letteralmente
  gia' "il nostro winrate contro QUESTI avversari specifici", non
  un'approssimazione derivata da blu.
- BUMP (annotazione, non piu' un ingrediente del calcolo di VERDE): nei
  bucket dove 3 o piu' delle 5 curve di matchup hanno uno "spike" simultaneo
  (sopra il 50% E sopra la propria media - non solo "sta vincendo", ma "sta
  vincendo PIU' del solito qui") nella stessa direzione, si segnala con una
  nota "Spingi qui"/"Attenzione qui" ed una finestra evidenziata nel
  grafico - idea originale dell'utente (piu' corsie forti insieme si
  traducono in vantaggi di squadra, roaming/obiettivi/skirmish, che una
  media semplice sottostima), preservata come segnale utile ma non piu'
  l'unico modo in cui il verde puo' scostarsi da blu.

In totale servono fino a 15 fetch veri (5 solisti nostri + 5 solisti nemici
+ 5 di matchup), paralleli con un limite (vedi _MAX_PARALLEL_FETCHES) - piu'
lento del design originale a 5 fetch, ma e' il prezzo per avere DAVVERO la
semantica "senza considerare il nemico" che l'utente aveva in mente fin
dall'inizio, non un'approssimazione.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from driftdraft.lolalytics import GAME_LENGTH_BUCKETS, NoCurveDataError, fetch_winrate_curve
from driftdraft.training_bot import ROLE_ORDER, TrainingSession, assign_roles

# Quante delle 5 corsie devono avere uno spike simultaneo nella stessa
# direzione perche' scatti il bump (ora solo un'ANNOTAZIONE, vedi
# evaluate_picks - non altera piu' il valore di VERDE, che gia' varia da
# solo in base alle curve di matchup) - idea dell'utente, non discusso se un
# valore diverso da 3 sia meglio.
BUMP_THRESHOLD = 3

# Quanti fetch lolalytics in parallelo - ognuno lancia un browser Playwright
# vero. Alzato da 3 a 4 rispetto alla primissima versione (allora erano
# solo 5 fetch totali, ora sono fino a 15 con le curve soliste ripristinate)
# per restare in un tempo totale ragionevole senza aprire troppi browser in
# contemporanea sulla macchina dell'utente.
_MAX_PARALLEL_FETCHES = 4


class EvaluationError(Exception):
    """La draft non e' in uno stato valido per la valutazione (non finita,
    ruoli non ancora confermati) - errore di stato, non di dati."""


def _fetch_curve(champion: str, role: str, vs_champion: str | None, tier: str) -> tuple[list[float], str | None]:
    """Wrapper per il ThreadPoolExecutor - non solleva MAI, ritorna sempre
    una curva completa (7 valori, curva neutra se necessario) piu' un
    messaggio di "piano B" o None.

    "Piano B" - richiesto esplicitamente dall'utente (2026-08-26) dopo aver
    visto un matchup con dati insufficienti durante il testing: invece di
    escludere la corsia dal calcolo, si usa una curva NEUTRA (50% piatto in
    ogni bucket) e si segnala il motivo al coach - piu' onesto che inventare
    una forma di curva mai osservata davvero. Bonus naturale: una curva
    piatta a 50% non e' MAI ne' sopra ne' sotto la propria media, quindi non
    puo' mai contare per il bump "3 corsie su 5" del verde (ne' a favore ne'
    contro) - corretto cosi', "nessun dato" non deve poter simulare un
    vantaggio o uno svantaggio."""
    label = champion if vs_champion is None else f"{champion} vs {vs_champion}"
    try:
        curve = fetch_winrate_curve(champion, role, vs_champion, tier)
        by_bucket = {p.bucket: p.winrate for p in curve}
        values = [by_bucket.get(b) for b in GAME_LENGTH_BUCKETS]
        if any(v is None for v in values):
            raise NoCurveDataError(f"Bucket mancanti nella curva di {label} ({role}).")
        return values, None
    except NoCurveDataError as e:
        fallback = [50.0] * len(GAME_LENGTH_BUCKETS)
        return fallback, f"{label} ({role}): dati insufficienti, trattata come neutra (50%). {e}"
    except Exception as e:
        fallback = [50.0] * len(GAME_LENGTH_BUCKETS)
        return fallback, f"{label} ({role}): errore durante il fetch, trattata come neutra (50%). {e}"


def _role_assignment_map(picks: list[str]) -> dict[str, str]:
    result = assign_roles(picks)
    return {role: entry["champion"] for role, entry in result["assignment"].items()}


def evaluate_session(session: TrainingSession, tier: str) -> dict:
    if session.current_action() is not None:
        raise EvaluationError("La draft non e' ancora finita.")
    if session.trainee_role_order is None:
        raise EvaluationError("Conferma prima l'assegnazione dei ruoli dei tuoi pick.")

    trainee_roles = dict(zip(ROLE_ORDER, session.trainee_role_order))
    bot_roles = _role_assignment_map(session.picks[session.bot_side])
    return evaluate_picks(trainee_roles, bot_roles, tier)


def evaluate_live_draft(
    our_picks: list[str],
    our_role_order: list[str] | None,
    enemy_picks: list[str],
    enemy_role_order: list[str] | None,
    tier: str,
) -> dict:
    """Stessa identica valutazione di evaluate_session, ma per "modalita'
    torneo" (richiesto esplicitamente dall'utente 2026-08-26: "è veramente
    ottima, penso sia un'aggiunta importante anche per la modalità torneo")
    - li' non esiste un `TrainingSession` (i pick vivono nello specchio
    della draft REALE su drafter.lol, vedi drafter_live.py), quindi questa
    funzione prende le liste di pick gia' estratte dal chiamante invece di
    un oggetto sessione.

    `our_role_order`: se disponibile (il coach ha gia' completato la fase di
    role confirmation VERA sul sito, vedi confirm_role_order in
    drafter_live.py), sono i 5 campioni gia' nell'ordine
    Top/Jungle/Mid/Bot/Support confermato per davvero - piu' preciso di un
    indovinato. Se None (draft finita ma non ancora, o mai, passata dalla
    fase di role confirmation - deliberatamente NON un requisito per poter
    valutare, a differenza del training: la fase di role confirmation su
    drafter.lol ha tempi/condizioni tutti suoi, legarci la valutazione la
    renderebbe fragile), si ricade su assign_roles().

    `enemy_role_order`: stesso schema di `our_role_order`, ma per il lato
    nemico - richiesto esplicitamente dall'utente (2026-08-26) dopo un caso
    REALE osservato ("mi ha immesso 'hecarim support' anche se [era] il
    toplaner"): a differenza del nostro, drafter.lol NON espone in nessun
    modo la fase di role confirmation del lato avversario (verificato nel
    codice: [data-role-confirm-lane] esiste nel DOM SOLO per il lato a cui
    siamo connessi, mai per l'altro) - l'unico modo di correggere
    un'assegnazione sbagliata (campioni flessibili tipo Hecarim, che puo'
    giocare piu' ruoli) e' lasciare che il coach la sistemi lui stesso a
    mano (vedi renderTournamentEnemyRoles in app.js), usando quello che sa
    per vie sue (comunicazioni osservate, scouting, l'ordine di pick reale)
    - se None, si ricade su assign_roles() esattamente come per il nostro."""
    if our_role_order and len(our_role_order) == 5:
        my_roles = dict(zip(ROLE_ORDER, our_role_order))
    else:
        my_roles = _role_assignment_map(our_picks)
    if enemy_role_order and len(enemy_role_order) == 5:
        enemy_roles = dict(zip(ROLE_ORDER, enemy_role_order))
    else:
        enemy_roles = _role_assignment_map(enemy_picks)
    return evaluate_picks(my_roles, enemy_roles, tier)


def evaluate_picks(trainee_roles: dict[str, str], bot_roles: dict[str, str], tier: str) -> dict:
    """Nucleo condiviso: `trainee_roles`/`bot_roles` sono gia' pronti come
    {ruolo: campione} per ciascuno dei 5 ROLE_ORDER - non sa/gli importa se
    vengono da una TrainingSession (vedi evaluate_session) o dallo specchio
    di una draft torneo reale (vedi evaluate_live_draft)."""
    # Ogni entry: chiave (kind, role) -> (campione, ruolo, avversario o None).
    # "mine"/"enemy" alimentano blu/rosso (curve soliste), "matchup" alimenta
    # solo il bump del verde (vedi sopra).
    tasks: dict[tuple[str, str], tuple[str, str, str | None]] = {}
    for role in ROLE_ORDER:
        tasks[("mine", role)] = (trainee_roles[role], role, None)
        tasks[("enemy", role)] = (bot_roles[role], role, None)
        tasks[("matchup", role)] = (trainee_roles[role], role, bot_roles[role])

    curves: dict[tuple[str, str], list[float]] = {}
    lane_errors: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=_MAX_PARALLEL_FETCHES) as pool:
        futures = {
            pool.submit(_fetch_curve, champion, role, vs_champion, tier): key
            for key, (champion, role, vs_champion) in tasks.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            values, fallback_reason = future.result()
            curves[key] = values
            if fallback_reason:
                lane_errors[f"{key[0]}:{key[1]}"] = fallback_reason

    n_buckets = len(GAME_LENGTH_BUCKETS)
    blue = [sum(curves[("mine", role)][i] for role in ROLE_ORDER) / len(ROLE_ORDER) for i in range(n_buckets)]
    red = [sum(curves[("enemy", role)][i] for role in ROLE_ORDER) / len(ROLE_ORDER) for i in range(n_buckets)]
    # VERDE = media delle 5 curve di MATCHUP, non piu' "blu +/- bump" (bug
    # reale segnalato dall'utente 2026-08-26 dopo aver usato la funzione su
    # draft vere: "sembra che segua in tutto e per tutto la curva blu... non
    # dovrebbe funzionare cosi', dovrebbe variare anche in base alla curva
    # dei nemici" - aveva ragione, il vecchio `green = list(blue)` lasciava
    # il verde IDENTICO a blu in ogni bucket senza bump, ignorando le curve
    # di matchup gia' scaricate tranne che per quel controllo). Questa media
    # e' gia' "il nostro winrate contro QUESTI avversari specifici" per
    # costruzione (ogni curva e' gia' "nostro pick vs il loro, stesso
    # ruolo") - varia da sola bucket per bucket in base ad entrambe le
    # squadre, nessuna approssimazione derivata da blu.
    green = [sum(curves[("matchup", role)][i] for role in ROLE_ORDER) / len(ROLE_ORDER) for i in range(n_buckets)]

    # Bump - ora SOLO un'annotazione (nota + finestra evidenziata nel
    # grafico), non altera piu' il valore di verde qui sopra (che gia'
    # varia da solo). Idea originale dell'utente preservata: 3+ corsie con
    # uno spike simultaneo nella stessa direzione segnalano un momento dove
    # spingere/stare attenti, un segnale che una media semplice sottostima.
    bump_notes = []
    for i, bucket in enumerate(GAME_LENGTH_BUCKETS):
        positive = 0
        negative = 0
        for role in ROLE_ORDER:
            curve = curves[("matchup", role)]
            own_avg = sum(curve) / len(curve)
            v = curve[i]
            if v > 50 and v > own_avg:
                positive += 1
            elif v < 50 and v < own_avg:
                negative += 1
        if positive >= BUMP_THRESHOLD:
            bump_notes.append({"bucket": bucket, "direction": "push", "count": positive})
        elif negative >= BUMP_THRESHOLD:
            bump_notes.append({"bucket": bucket, "direction": "danger", "count": negative})

    blue = [round(v, 2) for v in blue]
    red = [round(v, 2) for v in red]
    green = [round(v, 2) for v in green]

    return {
        "buckets": GAME_LENGTH_BUCKETS,
        "blue": blue,
        "red": red,
        "green": green,
        "bumpNotes": bump_notes,
        "laneCurves": {role: curves[("matchup", role)] for role in ROLE_ORDER},
        # Curve SOLISTE per singola corsia (richiesto esplicitamente
        # dall'utente 2026-08-26, con uno schizzo a mano: "vorrei vedere il
        # grafico face-to-face dei campioni che si scontrano nello stesso
        # ruolo") - stessi identici dati gia' scaricati per calcolare BLU/
        # ROSSO qui sopra (nessun fetch in piu'), solo non ancora mediati
        # sulle 5 corsie: un vero drill-down di cosa alimenta quelle due
        # linee, corsia per corsia invece che in aggregato.
        "myLaneCurves": {role: curves[("mine", role)] for role in ROLE_ORDER},
        "enemyLaneCurves": {role: curves[("enemy", role)] for role in ROLE_ORDER},
        "traineeRoles": trainee_roles,
        "botRoles": bot_roles,
        "laneErrors": lane_errors,
        "tier": tier,
    }
