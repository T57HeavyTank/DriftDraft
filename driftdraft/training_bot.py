"""Logica del bot per la modalita' "allenamento vs draft pro" (feature 4) -
sopra lo strato dati di leaguepedia.py. Una sessione (TrainingSession) scandisce
un draft completo a 20 azioni (DRAFT_SEQUENCE, importato da li') fra il coach
in allenamento (trainee) e il bot, che sceglie usando le tabelle sinergia/
counter aggregate dai pro game recenti.

Due modalita' (design concordato con l'utente, vedi memoria progetto):
- "freeform": il bot sceglie SOLO in base a sinergia (coi propri pick gia'
  fatti) + counter (contro i pick nemici gia' fatti), niente draft di
  riferimento.
- "team": come sopra, ma il bot IMPERSONA una squadra pro vera - pesca fra
  quello che quella squadra gioca davvero, corsia per corsia, con i campioni
  che usa di piu' in cima (vedi build_pro_team_profile).

  Ha sostituito la vecchia "anchored" (2026-09-08), che dava un bonus al
  pick che una singola draft storica fece in quella identica posizione.
  Giudizio dell'utente, condiviso: quel sistema e' fallato. Il bot ripeteva
  scelte prese CONTRO UN AVVERSARIO CHE NELLA DRAFT IN CORSO NON C'E', quindi
  appena il trainee divergeva l'ancora diventava rumore travestito da
  riferimento - "come la modalita' libera ma nerfata dal voler seguire un tot
  di pick". Una squadra ha invece abitudini che restano vere qualunque cosa
  faccia l'avversario, ed e' quello che un coach vero studia.

Nessuna sessione persistita su disco (a differenza delle draft/tabelle) - e'
stato di UNA partita di allenamento in corso, sensato solo mentre l'app resta
aperta, stesso principio di LiveDraftSession in drafter_live.py (ma qui molto
piu' semplice: nessun sito esterno, nessun thread dedicato - ogni azione e'
sincrona e istantanea, la mossa del bot e' gia' pronta nella stessa risposta
HTTP della mossa del trainee).
"""

import random
import threading
import time
from dataclasses import dataclass, field
from itertools import permutations

from driftdraft import leaguepedia
from driftdraft.comps import COMP_BEATS, COMP_REQUIREMENTS, MEMBER_THRESHOLD
from driftdraft.data import load_champions

DRAFT_SEQUENCE = leaguepedia.DRAFT_SEQUENCE

# Pausa "il bot sta pensando" prima di rivelare la sua mossa - richiesta
# esplicita dell'utente (2026-08-26) dopo aver provato la prima versione:
# la mossa del bot arrivava davvero istantanea (il calcolo e' banale), e
# senza nessun segnale questo dava la sensazione sbagliata di "sceglie senza
# pensarci" anche se il ragionamento (sinergia/counter) c'e' davvero.
# Randomizzato nel range invece di un valore fisso, stesso principio "non
# robotico" gia' usato per la scelta del campione stesso.
# Accorciata da 3-5s a 1-2s il 2026-09-06, su richiesta dell'utente dopo
# averci allenato davvero: la pausa serviva a non dare la sensazione di una
# scelta senza pensiero, ma su una draft da 20 azioni diventava attesa vera.
BOT_THINK_DELAY_MIN = 1.0
BOT_THINK_DELAY_MAX = 2.0

SYNERGY_WEIGHT = 1.0
COUNTER_WEIGHT = 1.0

# Sotto quante osservazioni un candidato NON viene proposto (2026-09-06).
#
# Serve perche' col counter direzionale certi campioni restano senza risposte
# nei dati, ed e' corretto che sia cosi': l'utente lo ha spiegato meglio di
# come lo avrebbe detto la statistica - "malphite vs sylas e' una cosa da
# evitare in qualsiasi circostanza, sylas vincera' sempre, ed e' per questo
# che i dati manco lo fanno apparire, in quanto il team che prende malphite
# si deve assicurare il ban di sylas ad ogni costo". Un campione forte ma con
# molto counterplay si gestisce con i ban, non con una risposta in draft:
# nei dati quella risposta non esiste, e mostrare comunque un top-8 costruito
# su una o due partite significa spacciare rumore per consiglio.
#
# Il valore e' MISURATO, non scelto a occhio: rigiocando 2250 stati di draft
# pro veri, il punteggio del primo suggerimento ha mediana 116 e primo
# percentile 12, mentre i casi patologici stanno tutti a 1-2 (contro Malphite
# 2,2,2,2,2,1,1,1; contro Yasuo 2,2,1,1,1,1,1,1). Fra le due fasce c'e' un
# vuoto e 5 ci sta comodamente in mezzo: toglie del tutto il rumore e lascia
# senza suggerimenti solo lo 0.1% degli stati reali.
MIN_SUPPORT = 5
# Quanta probabilita' si riserva al candidato che combacia con la mossa
# dell'ancora storica in questa esatta posizione.
#
# Era un BONUS ADDITIVO di 6.0, sostituito il 2026-09-06 da una QUOTA perche'
# un numero additivo non puo' restare tarato su una scala che cambia: 6 su
# punteggi 0-100 (sinergia/counter) era un nudge sensato, ma sui conteggi di
# popolarita' (fino a 815) e ancor piu' dopo l'elevamento a potenza della
# rosa ristretta diventava irrilevante - misurato, l'ancora usciva nel 2.5%
# dei casi invece di essere preferita. Una quota del totale invece non
# dipende ne' dalla scala dei punteggi ne' dall'esponente.
# Ogni candidato ha comunque una probabilita' minima anche a punteggio 0 -
# altrimenti il bot sceglierebbe SOLO fra campioni gia' visti nei dati
# storici, mai un pick "di chiusura" fuori pool (stesso limite di sparsita'
# dei dati gia' discusso e accettato con l'utente per le fasi avanzate).
# NOTA: dal 2026-09-06 l'epsilon vale solo per i BAN. I pick passano da una
# rosa ristretta (vedi BOT_SHORTLIST) dove il punteggio e' sempre positivo.
EPSILON = 0.2

# Quanto e' selettivo il bot nei PICK (2026-09-06). Richiesta dell'utente
# dopo averci giocato: "sembra che il bot pesca pick veramente casuali,
# vorrei diminuire drasticamente la casualita'".
#
# Il problema NON era l'epsilon, come si sarebbe potuto pensare: misurato, la
# sua massa e' l'1% del totale. Era che con dati abbondanti **136 campioni su
# 171 hanno un punteggio positivo**, e il migliore vale solo il 3.5% della
# somma - distribuire in proporzione su una coda cosi' lunga da' per forza un
# risultato piatto (il bot sceglieva il candidato migliore il 3% delle volte,
# su 146 campioni diversi).
#
# Due leve, misurate sulla stessa situazione:
#   - solo esponente 3         -> #1 nel 12% dei casi, 63 campioni diversi
#   - solo rosa top 8          -> #1 nel 15%, 8 diversi
#   - rosa top 5 + esponente 2 -> #1 nel 24%, primi 3 nel 68%, 5 diversi
# La leva vera e' la ROSA, non l'esponente. Scelto top 5 + esponente 2: il bot
# pesca sempre fra i cinque migliori e preferisce nettamente i primi, ma resta
# abbastanza vario da non ripetere la stessa draft ad ogni allenamento - che
# e' il motivo per cui non e' semplicemente "prendi il migliore".
#
# Se servisse ritoccarlo: alzare BOT_SHORTLIST allarga, abbassarlo stringe;
# 3 porterebbe il #1 al 37%.
BOT_SHORTLIST = 5
BOT_SHARPNESS = 2

# Quanto spesso il bot prende il candidato col punteggio PIU' ALTO (2026-09-06,
# secondo giro). L'utente, che gioca a questo livello: "su un gioco come League
# of Legends il miglior pick non viene preso un 27% delle volte, ma la % arriva
# piuttosto ad un 75-80%. Vorrei che la draft sia piu' prevedibile, in quanto
# di norma e' piu' prevedibile che imprevedibile".
#
# E' una QUOTA e non un esponente per un motivo misurato: i punteggi di testa
# sono quasi appaiati (in una situazione tipica 99, 97, 89, 85, 79) e nessun
# esponente ragionevole li separa - per portare il primo al 75% servirebbe la
# potenza ~50, che su punteggi piu' distanziati schiaccerebbe tutto a zero. La
# quota invece dice esattamente cio' che si vuole, indipendentemente da quanto
# sono vicini i punteggi e da BOT_SHARPNESS.
#
# BOT_SHARPNESS resta e ora fa un lavoro piu' piccolo ma sensato: distribuisce
# il 22% rimanente fra il secondo e il quinto, favorendo i migliori.
BOT_TOP_SHARE = 0.78

# Ordine ruoli standard del progetto (stesso di ROLE_COLUMNS in data.py) -
# usato per assegnare un ruolo a ciascuno dei 5 pick a fine draft (vedi
# assign_roles sotto), richiesto esplicitamente dall'utente (2026-08-26) per
# poter verificare che il bot copra davvero 5 ruoli distinti e non solo 5
# campioni "forti secondo sinergia/counter" senza badare al ruolo.
ROLE_ORDER = ["Top", "Jungle", "Mid", "Bot", "Support"]


@dataclass
class TrainingSession:
    mode: str  # "team" | "freeform"
    trainee_side: str  # "team1" | "team2" (interno - vedi DRAFT_SEQUENCE)
    tables: dict
    # Chi il bot sta impersonando, se lo sta facendo: il nome di una squadra
    # pro (modalita' "team") oppure None. Il PROFILO vero sta in bot_profile,
    # questo serve a dirlo a schermo.
    bot_team: str | None = None
    step: int = 0
    picks: dict | None = None
    bans: dict | None = None
    last_bot_action: dict | None = None
    # Una entry per ogni azione applicata finora: {step, kind, side, idx,
    # champion, by}. Serve SOLO per il "rewind" (vedi rewind_to sotto) - lo
    # stato vero e proprio resta picks/bans/step sopra, questa e' una
    # registrazione parallela che permette di ricostruirli da zero fino a un
    # punto precedente invece di dover invertire le mosse una per una.
    history: list = field(default_factory=list)
    # I 5 pick del TRAINEE (non del bot) riordinati secondo ROLE_ORDER,
    # decisi ESPLICITAMENTE da lui a fine draft (drag&drop in UI, stesso
    # pattern gia' in uso per "modalita' torneo" dopo i 20 pick/ban) - None
    # finche' non conferma. A differenza di roleAssignment (indovinato in
    # automatico da assign_roles, sempre presente per entrambi i lati),
    # questo e' un dato scritto dal trainee stesso: richiesto esplicitamente
    # 2026-08-26 per un passo successivo (confrontare i propri pick, gia'
    # etichettati per ruolo, con altri strumenti - non ancora specificato).
    trainee_role_order: list | None = None
    # Il PROFILO della squadra che il bot impersona, da op.gg: cinque pool
    # separate una per corsia, ognuna coi campioni di QUEL giocatore e
    # quanto li gioca (vedi build_team_profile). Vale per i PICK, non per i
    # ban - richiesta esplicita dell'utente 2026-08-26. None = nessuna
    # squadra impersonata, il bot ragiona solo sul meta (comportamento
    # originale).
    #
    # Era `bot_pool: frozenset` fino al 2026-09-07: i soli NOMI, con le
    # cinque pool mescolate in un insieme unico e usate come maschera
    # acceso/spento. Si buttavano via le partite giocate - cioe' il dato che
    # distingue un cavallo di battaglia da un campione toccato una volta - e
    # il bot poteva pescare il campione del toplaner in bot lane.
    bot_profile: dict | None = None

    def __post_init__(self):
        if self.picks is None:
            self.picks = {"team1": [None] * 5, "team2": [None] * 5}
        if self.bans is None:
            self.bans = {"team1": [None] * 5, "team2": [None] * 5}

    @property
    def bot_side(self) -> str:
        return "team2" if self.trainee_side == "team1" else "team1"

    def current_action(self) -> tuple[str, str, int] | None:
        if self.step >= len(DRAFT_SEQUENCE):
            return None
        return DRAFT_SEQUENCE[self.step]

    def is_trainee_turn(self) -> bool:
        action = self.current_action()
        return action is not None and action[1] == self.trainee_side

    def all_taken(self) -> set[str]:
        taken: set[str] = set()
        for side in ("team1", "team2"):
            taken.update(c for c in self.picks[side] if c)
            taken.update(c for c in self.bans[side] if c)
        return taken

    def apply_trainee_action(self, champion: str) -> None:
        action = self.current_action()
        if not action or action[1] != self.trainee_side:
            raise ValueError("Non e' il tuo turno.")
        if champion in self.all_taken():
            raise ValueError("Campione gia' preso o bannato in questa draft.")
        valid_names = {c.name for c in load_champions()}
        if champion not in valid_names:
            raise ValueError("Campione non valido.")

        kind, side, idx = action
        arr = self.bans if kind == "ban" else self.picks
        arr[side][idx] = champion
        self.history.append(
            {"step": self.step, "kind": kind, "side": side, "idx": idx, "champion": champion, "by": "trainee"}
        )
        self.step += 1
        self.last_bot_action = None
        self._advance_bot()

        if self.last_bot_action is not None:
            # Il lock e' gia' tenuto da apply_pick() intorno a questa
            # chiamata - dormire qui dentro serializza anche eventuali altre
            # richieste nel frattempo, che va bene: non ha senso che arrivi
            # un'altra azione mentre il bot sta "pensando" alla sua.
            time.sleep(random.uniform(BOT_THINK_DELAY_MIN, BOT_THINK_DELAY_MAX))

    def _advance_bot(self) -> None:
        while self.step < len(DRAFT_SEQUENCE) and DRAFT_SEQUENCE[self.step][1] == self.bot_side:
            self._bot_act()

    def _bot_act(self) -> None:
        kind, side, idx = DRAFT_SEQUENCE[self.step]
        champion = self._choose_bot_champion(kind)
        arr = self.bans if kind == "ban" else self.picks
        arr[side][idx] = champion
        self.history.append(
            {"step": self.step, "kind": kind, "side": side, "idx": idx, "champion": champion, "by": "bot"}
        )
        self.last_bot_action = {"kind": kind, "champion": champion}
        self.step += 1

    def trainee_pick_steps(self) -> list[int | None]:
        """Per ognuno dei 5 slot PICK del trainee (non i ban - richiesta
        esplicita dell'utente, il "rewind" serve per riprovare scelte di
        campione, non ban), lo step (indice in DRAFT_SEQUENCE) in cui e'
        stato scelto - None se lo slot e' ancora vuoto. Usato dal frontend
        per il bottone "ripeti da qui" (vedi rewind_to sotto)."""
        result: list[int | None] = [None] * 5
        for h in self.history:
            if h["by"] == "trainee" and h["kind"] == "pick" and h["side"] == self.trainee_side:
                result[h["idx"]] = h["step"]
        return result

    def rewind_to(self, step: int) -> None:
        """Riporta la draft allo stato immediatamente PRIMA dell'azione fatta
        a questo step - richiesto esplicitamente dall'utente (2026-08-26) per
        poter riprovare un pick diverso dallo stesso punto e verificare che
        il bot reagisca in modo diverso (le mosse successive, comprese
        quelle del bot, vengono scartate e si rigiocano da capo). Valido
        SOLO su uno step dove e' stato il TRAINEE a scegliere - non avrebbe
        senso "rifare" una mossa del bot al posto suo."""
        if not (0 <= step < len(self.history)):
            raise ValueError("Punto di rewind non valido.")
        entry = self.history[step]
        if entry["by"] != "trainee" or entry["side"] != self.trainee_side:
            raise ValueError("Puoi ripartire solo da una tua scelta.")

        self.history = self.history[:step]
        self.picks = {"team1": [None] * 5, "team2": [None] * 5}
        self.bans = {"team1": [None] * 5, "team2": [None] * 5}
        for h in self.history:
            arr = self.bans if h["kind"] == "ban" else self.picks
            arr[h["side"]][h["idx"]] = h["champion"]
        self.step = len(self.history)
        self.last_bot_action = None
        # I 5 pick del trainee stanno per cambiare (la draft non e' piu'
        # finita) - un'assegnazione ruoli fatta per i vecchi pick non ha piu'
        # senso, va rifatta da capo una volta ricompletata.
        self.trainee_role_order = None

    def confirm_trainee_role_order(self, order: list[str]) -> None:
        """Il trainee decide esplicitamente quale dei SUOI 5 pick va in quale
        corsia (drag&drop lato UI) - richiesto esplicitamente dall'utente
        (2026-08-26) per un passo successivo non ancora specificato. Valido
        solo a draft FINITA (non ha senso assegnare ruoli a pick che possono
        ancora cambiare) e solo se `order` e' esattamente una permutazione
        dei propri 5 pick."""
        if self.current_action() is not None:
            raise ValueError("La draft non e' ancora finita.")
        own_picks = self.picks[self.trainee_side]
        if len(order) != 5 or sorted(order) != sorted(own_picks):
            raise ValueError("L'ordine deve contenere esattamente i tuoi 5 campioni, una volta ciascuno.")
        self.trainee_role_order = list(order)

    def _choose_bot_champion(self, kind: str) -> str:
        all_champs = load_champions()  # UNA sola volta per decisione, vedi nota su _can_role_match
        taken = self.all_taken()
        candidates = [c.name for c in all_champs if c.name not in taken]
        if not candidates:
            raise RuntimeError("Nessun campione disponibile per il bot.")

        synergy = self.tables.get("synergy", {})
        counter = self.tables.get("counter", {})
        pick_counts = self.tables.get("pick_counts", {})
        champs_by_name = {c.name: c for c in all_champs}
        own_picks = [c for c in self.picks[self.bot_side] if c]
        enemy_picks = [c for c in self.picks[self.trainee_side] if c]

        # Quanto la squadra impersonata gioca un dato campione, nella corsia
        # in cui potrebbe davvero schierarlo viste le scelte gia' fatte.
        profilo_per_role = (self.bot_profile or {}).get("per_role") or {}

        def affinita(nome: str) -> float:
            """0 = questa squadra non lo gioca in nessuna corsia che potrebbe
            ancora occupare, TENUTO CONTO dei pick gia' fatti.

            Il "tenuto conto" e' il punto: la corsia da cui arriva l'affinita'
            dev'essere una che il campione puo' davvero prendersi, non una
            qualsiasi ancora libera - vedi _profile_roles_for per il bug che
            l'ha resa necessaria."""
            if not self.bot_profile:
                return 1.0
            if not profilo_per_role:
                # Giocatori non esattamente cinque: le corsie non sono
                # ricavabili, si degrada alla pool unica tenendo le affinita'.
                return (self.bot_profile.get("flat") or {}).get(nome, 0.0)
            ammesse = _profile_roles_for(nome, own_picks, champs_by_name, profilo_per_role)
            if not ammesse:
                return 0.0
            return max(profilo_per_role.get(r, {}).get(nome, 0.0) for r in ammesse)

        if kind == "pick" and len(own_picks) < 5:
            # PREVIENE (non solo segnala a fine draft, vedi assign_roles) che
            # il bot si incastri in una posizione senza 5 ruoli distinti
            # possibili - richiesta esplicita dell'utente (2026-08-26): "c'e'
            # un modo per evitarlo?" dopo aver visto il warning a fine draft.
            # Ad ogni pick, un candidato e' ammesso solo se AGGIUNGENDOLO ai
            # propri pick gia' fatti esiste ancora un modo di dare a
            # ciascuno un ruolo distinto (non serve gia' sapere QUALE - i
            # pick futuri restano liberi di risolverlo, vedi
            # _can_role_match). Se il filtro svuotasse la lista (non
            # dovrebbe mai capitare con ~170 campioni disponibili, ma meglio
            # un pick "storto" che nessun pick) si ricade sulla lista intera.
            champs_by_name = {c.name: c for c in all_champs}
            role_safe = [c for c in candidates if _can_role_match(own_picks + [c], champs_by_name)]
            if role_safe:
                candidates = role_safe

            # "Allenati contro una squadra reale" - richiesta esplicita
            # dell'utente (2026-08-26): con un profilo op.gg il bot sceglie
            # SOLO fra i campioni che quella squadra gioca davvero, e da
            # 2026-09-07 solo fra quelli che gioca IL GIOCATORE della corsia
            # ancora libera (vedi _champion_affinity). Applicato DOPO il
            # filtro ruoli, non prima: la garanzia "5 ruoli distinti" e'
            # strutturale e non va rotta per rispettare il profilo - se il
            # profilo non lascia nessun candidato ancora valido per l'ultimo
            # ruolo rimasto, e' meglio un pick fuori pool che nessun pick.
            if self.bot_profile:
                giocabili = [c for c in candidates if affinita(c) > 0]
                if giocabili:
                    candidates = giocabili

        if kind == "ban":
            # Bannare non ha un equivalente "sinergia/counter" (non e' ancora
            # chiaro chi giochera' cosa) - euristica semplice: banna cio' che
            # e' piu' popolare/contestato nei dati recenti.
            weights = [float(pick_counts.get(c, 0)) + EPSILON for c in candidates]
            return random.choices(candidates, weights=weights, k=1)[0]

        # --- PICK: rosa ristretta, poi sorteggio pesato fra quei pochi -------
        scored = [(c, _pick_score(c, own_picks, enemy_picks, synergy, counter))
                  for c in candidates]

        # Nessun segnale sinergia/counter: succede al PRIMISSIMO pick (tavolo
        # vuoto: niente compagni con cui sinergizzare, niente avversari da
        # counterare) e, di rado, quando i campioni in gioco non compaiono
        # insieme nei dati. Prima qui restava solo l'epsilon, uguale per
        # tutti, e il bot pescava a caso fra 173 campioni - verificato: 170
        # campioni diversi su 600 prove. Si ricade sulla POPOLARITA', che e'
        # cio' su cui si basa davvero un primo pick pro.
        segnale = any(sc > 0 for _, sc in scored)
        if not segnale:
            scored = [(c, float(pick_counts.get(c, 0))) for c in candidates]

        # Il profilo di squadra MOLTIPLICA il punteggio, non lo sostituisce -
        # come chiesto dall'utente: "aumentare il punteggio che gia' viene
        # dato di counter/sinergia moltiplicato con il valore effettivo del
        # player". Le due domande restano separate e leggibili: "quanto e'
        # buono questo pick qui" (meta) per "quanto quel giocatore lo gioca
        # davvero" (abitudine). Un campione fortissimo che quel tizio non
        # tocca mai scende, uno mediocre che e' il suo cavallo di battaglia
        # sale - che e' come si comporta una squadra vera.
        if self.bot_profile:
            scored = [(c, sc * affinita(c)) for c, sc in scored]

        # LE COMP. Il bot non e' un ottimizzatore di sinergia: guarda dove sta
        # andando l'avversario e prova ad arrivarci contro, e intanto chiude
        # la propria comp coprendone i tag. Vale sempre per il bot, anche col
        # toggle "bordi comp" spento - quello e' una preferenza del coach su
        # come vuole essere CONSIGLIATO, non un'istruzione su come debba
        # pensare chi ha di fronte.
        direzione_nemica = None
        if len(enemy_picks) >= _comp_direction_min_picks(self.tables.get("comp_stats")):
            direzione_nemica = _comp_direction(enemy_picks, champs_by_name)
        base_comp = _comp_value(own_picks, direzione_nemica, champs_by_name)
        scored = [
            (
                c,
                sc
                * (
                    1.0
                    + COMP_WEIGHT
                    * _comp_bonus(c, own_picks, direzione_nemica, champs_by_name, base_comp)
                ),
            )
            for c, sc in scored
        ]

        scored.sort(key=lambda t: -t[1])
        rosa = scored[:BOT_SHORTLIST]

        nomi = [c for c, _ in rosa]
        pesi = [max(sc, 0.0) ** BOT_SHARPNESS for _, sc in rosa]

        # Tutti a zero (dati del tutto assenti): meglio un sorteggio uniforme
        # fra la rosa che un'eccezione da random.choices.
        if not any(pesi):
            pesi = [1.0] * len(nomi)

        # `rosa` e' ordinata per punteggio, quindi l'indice 0 e' il migliore -
        # anche quando l'ancora e' stata aggiunta in coda.
        #
        # SOLO quando un segnale c'e' davvero. Senza (primissimo pick: niente
        # compagni con cui sinergizzare, niente avversari da counterare) il
        # ripiego e' la popolarita', e li' un "migliore" cosi' netto non
        # esiste: nelle 3000 draft vere il primo pick blu si distribuisce su
        # 91 campioni, col piu' usato al 9.4%. Applicare la quota anche li'
        # faceva aprire al bot la stessa identica draft nel 79% delle
        # partite - piu' prevedibile della realta', non piu' realistico.
        # Restano comunque i 5 piu' giocati, in proporzione: e' gia' molto
        # piu' sensato del sorteggio uniforme di prima.
        if segnale:
            _give_share(pesi, 0, BOT_TOP_SHARE)
        return random.choices(nomi, weights=pesi, k=1)[0]

    def state(self) -> dict:
        def side_label(internal: str) -> str:
            return "blue" if internal == "team1" else "red"

        action = self.current_action()
        finished = action is None
        return {
            "active": True,
            "mode": self.mode,
            "traineeSide": side_label(self.trainee_side),
            "bluePicks": self.picks["team1"],
            "redPicks": self.picks["team2"],
            "blueBans": self.bans["team1"],
            "redBans": self.bans["team2"],
            "step": self.step,
            "totalSteps": len(DRAFT_SEQUENCE),
            "finished": finished,
            "isTraineeTurn": self.is_trainee_turn(),
            "currentAction": None if not action else {
                "kind": action[0],
                "side": side_label(action[1]),
            },
            "lastBotAction": self.last_bot_action,
            # Chi il bot sta impersonando. Ha sostituito il vecchio blocco
            # "anchor" (la draft storica di riferimento): quella diceva da
            # quale partita venivano i suggerimenti, questa dice CHI sta
            # giocando, che e' l'informazione utile al coach.
            "botTeam": self.bot_team,
            # Solo per gli slot PICK del trainee - step in cui e' stato
            # scelto quel campione, o None se vuoto - il frontend lo usa per
            # il bottone "ripeti da qui" (vedi rewind_to). Richiesta esplicita
            # dell'utente 2026-08-26.
            "traineePickSteps": self.trainee_pick_steps(),
            # Solo a fine draft - "in che corsia va ognuno dei 5 pick",
            # richiesta esplicita dell'utente per verificare che il bot copra
            # davvero 5 ruoli distinti (vedi assign_roles sotto).
            "roleAssignment": None if not finished else {
                # Il profilo op.gg vale per il lato del BOT: e' l'unico dei
                # due di cui sappiamo chi gioca cosa.
                "blue": assign_roles(
                    self.picks["team1"],
                    self.bot_profile if self.bot_side == "team1" else None,
                ),
                "red": assign_roles(
                    self.picks["team2"],
                    self.bot_profile if self.bot_side == "team2" else None,
                ),
            },
            # L'assegnazione ruoli DECISA dal trainee (vedi
            # confirm_trainee_role_order), non quella indovinata sopra -
            # None finche' non conferma esplicitamente in UI.
            "traineeRoleOrder": self.trainee_role_order,
            # Solo informativo per la UI ("bot limitato a un pool di N
            # campioni") - None se nessun pool nemico e' stato dato all'avvio.
            "botPoolSize": (
                len((self.bot_profile or {}).get("flat") or {}) if self.bot_profile else None
            ),
            # Chi il bot sta impersonando, corsia per corsia: e' l'unico modo
            # per il coach di accorgersi se la deduzione dei ruoli ha sbagliato.
            "botRoster": (self.bot_profile or {}).get("roster") or None,
            # Quanto e' sicura quella deduzione, corsia per corsia (0..1).
            # Sotto 1 il bot in quella corsia pesca in parte meta: vedi
            # _role_confidence. Serve alla UI per dirlo al coach, che
            # altrimenti vedrebbe solo un roster dedotto senza sapere quali
            # righe sono un'ipotesi e quali un dato.
            "botConfidence": (self.bot_profile or {}).get("confidence") or None,
        }


def _can_role_match(champion_names: list[str], champs_by_name: dict) -> bool:
    """True se esiste un modo di assegnare a QUESTI campioni (possono essere
    meno di 5) altrettanti ruoli TUTTI DISTINTI, ognuno fra quelli veri del
    campione - cioe' se un "matching che satura tutti i campioni" esiste,
    senza bisogno che copra anche gli altri ruoli restanti (quelli, se
    esistono, si presume vengano coperti da pick futuri). Usata da
    _choose_bot_champion per impedire AL BOT di incastrarsi in una
    posizione da cui, aggiungendo un dato candidato, diventerebbe poi
    impossibile finire con 5 ruoli distinti - vedi li' per il perche'.

    champs_by_name va passato gia' pronto (non richiamato qui) - questa
    funzione viene chiamata UNA VOLTA PER CANDIDATO ad ogni pick del bot
    (~170 volte), ricaricare l'xlsx da disco ad ogni chiamata l'avrebbe resa
    lentissima (trovato davvero: un test con 40 draft simulate non finiva
    piu' entro 2 minuti prima di questo fix).

    Ricerca backtracking sui campioni piu' vincolati per primi (meno ruoli
    possibili): con al massimo 5 elementi e 5 ruoli non serve un vero
    algoritmo di matching bipartito, e partire dai piu' rigidi taglia
    subito i rami morti - solitamente esce dopo aver provato 2-3 rami
    invece di tutti i 120 percorsi possibili."""
    if not champion_names:
        return True
    n = len(champion_names)
    eligible = []
    for name in champion_names:
        roles = champs_by_name[name].roles if name in champs_by_name else frozenset()
        eligible.append(roles)

    # Un campione sconosciuto resta incompatibile, come nella semantica
    # precedente: i dati non devono trasformare un nome non risolto in un jolly.
    for roles in eligible:
        if not roles:
            return False

    # Ordina per numero di ruoli possibili (meno = piu' vincolato = prima)
    indexed = sorted(range(n), key=lambda i: len(eligible[i]))

    def backtrack(k: int, used: set) -> bool:
        if k == n:
            return True
        idx = indexed[k]
        for role in eligible[idx]:
            if role not in used:
                used.add(role)
                if backtrack(k + 1, used):
                    return True
                used.remove(role)
        return False

    return backtrack(0, set())


def _profile_roles_for(
    candidate: str, own_picks: list[str], champs_by_name: dict, per_role: dict
) -> set[str]:
    """Le corsie che `candidate` potrebbe DAVVERO occupare in questa squadra.

    Nasce da un bug trovato dall'utente il 2026-09-07: il bot pescava tre ADC
    e li spargeva su tre corsie. Il filtro di prima chiedeva soltanto
    "qualcuno di questa squadra lo gioca, in una corsia ancora libera?" senza
    ricordarsi QUALE corsia rispondeva di si'. Cosi' Ezreal passava perche' lo
    gioca il loro ADC, e poi finiva contato come Mid - dove il mid non lo
    gioca per niente. Con tag di ruolo giustamente permissivi (Jhin e'
    {Bot, Jungle}, Ezreal {Bot, Mid}) l'intera pool di un giocatore si
    spalmava su tre corsie, e il controllo "5 ruoli distinti" non se ne
    accorgeva perche' quella biiezione esiste eccome.

    Qui le due domande restano legate: una corsia vale solo se il candidato
    la puo' occupare (e' fra i suoi ruoli E il giocatore di quella corsia lo
    gioca) E se i pick gia' fatti riescono a sistemarsi nelle corsie che
    restano, con lo stesso vincolo. Stessa ricerca esaustiva di
    _can_role_match - al massimo P(5,5)=120 permutazioni, per 5 elementi la
    forza bruta e' la scelta giusta.
    """

    def tag(nome: str) -> set[str]:
        return set(champs_by_name[nome].roles) if nome in champs_by_name else set()

    def sue(nome: str) -> set[str]:
        return {r for r in tag(nome) if (per_role.get(r) or {}).get(nome, 0.0) > 0}

    possibili = sue(candidate)
    if not possibili or not own_picks:
        return possibili

    # Per i campioni GIA' PRESI si ricade sui tag quando il profilo non li
    # colloca da nessuna parte. Senza questa ricaduta un solo pick fuori pool
    # - un pocket pick, o dati op.gg piu' vecchi della partita - renderebbe
    # impossibile QUALUNQUE abbinamento e spegnerebbe l'intera riga dei
    # suggerimenti invece di degradare. In allenamento non capiterebbe (i
    # pick del bot escono dal profilo per costruzione), ma in torneo le
    # squadre vere pescano quello che vogliono. Il vincolo stretto resta dove
    # serve, cioe' sul CANDIDATO: e' li' che si decide cosa consigliare.
    ammesse = set()
    altri = [sue(n) or tag(n) for n in own_picks]
    n_altri = len(altri)
    # Pre-sort altri by fewest options for faster backtracking
    indexed_altri = sorted(range(n_altri), key=lambda i: len(altri[i]))
    for r in possibili:
        def _can_assign(k: int, used: set) -> bool:
            if k == n_altri:
                return True
            idx = indexed_altri[k]
            for role in altri[idx]:
                if role in used:
                    continue
                used.add(role)
                if _can_assign(k + 1, used):
                    return True
                used.remove(role)
            return False

        if _can_assign(0, {r}):
            ammesse.add(r)
    return ammesse


def assign_roles(champion_names: list[str], profile: dict | None = None) -> dict:
    """Assegna i 5 ROLE_ORDER ai 5 campioni gia' scelti massimizzando quanti
    ruoli finiscono su un campione che lo ha DAVVERO fra i suoi ruoli
    nell'xlsx (frozenset Champion.roles, un campione puo' averne piu' di
    uno) - richiesto esplicitamente dall'utente (2026-08-26): il punteggio
    del bot per i pick e' PURAMENTE sinergia/counter (vedi
    _choose_bot_champion), senza alcun vincolo di ruolo durante la scelta -
    questa funzione serve a scoprire onestamente, a fine draft, se quei 5
    pick "a caso rispetto al ruolo" riescono comunque a coprire 5 posizioni
    distinte oppure no.

    Ricerca esaustiva su tutte le 5!=120 permutazioni (banale per n=5, non
    serve un vero algoritmo di matching bipartito) - ritorna la permutazione
    che massimizza il numero di assegnazioni "valide" (il ruolo e' fra
    quelli del campione), non necessariamente tutte e 5: se non e' possibile
    coprire tutti i ruoli con quei 5 campioni, `fullyCovered` e' False e le
    singole entry non valide sono marcate `confident: False` invece di
    fingere una copertura che non esiste - e' esattamente il segnale che
    l'utente vuole poter vedere."""
    champs_by_name = {c.name: c for c in load_champions()}
    eligible = [champs_by_name[n].roles if n in champs_by_name else frozenset() for n in champion_names]

    # `profile`, se c'e', fa da SPAREGGIO fra assegnazioni ugualmente valide.
    # Serve perche' i tag di ruolo da soli lasciano spesso pari: Ezreal e
    # Syndra sono entrambi {Bot, Mid}, quindi "Ezreal mid, Syndra adc" e il suo
    # contrario coprono cinque ruoli tutti e due e si vinceva a caso. Con una
    # squadra op.gg caricata la domanda ha una risposta vera - chi dei due lo
    # gioca davvero, in quale corsia - e ignorarla faceva scrivere sul
    # cartellino finale una cosa che il bot stesso non aveva pensato: i pick
    # li aveva scelti coerenti (vedi _profile_roles_for), era solo l'etichetta
    # a mentire. Segnalato dall'utente il 2026-09-07: "come mai pensa che
    # ezreal sia mid, mentre syndra adc, se i giocatori non sanno giocare i
    # rispettivi campioni dell'altro?".
    #
    # Resta uno spareggio e non un criterio: la copertura dei ruoli viene
    # prima, sempre. Senza profilo il risultato e' identico a prima.
    per_role = (profile or {}).get("per_role") or {}

    def affinita_tot(perm) -> float:
        if not per_role:
            return 0.0
        return sum(
            (per_role.get(ROLE_ORDER[i]) or {}).get(champion_names[perm[i]], 0.0)
            for i in range(5)
        )

    best_perm = tuple(range(5))
    best_score, best_aff = -1, -1.0
    for perm in permutations(range(5)):
        score = sum(1 for i in range(5) if ROLE_ORDER[i] in eligible[perm[i]])
        aff = affinita_tot(perm)
        if (score, aff) > (best_score, best_aff):
            best_score, best_aff, best_perm = score, aff, perm
            # L'uscita anticipata vale solo senza profilo: con un profilo la
            # prima assegnazione a copertura piena non e' detto sia la sua.
            if score == 5 and not per_role:
                break

    assignment = {
        ROLE_ORDER[i]: {
            "champion": champion_names[best_perm[i]],
            "confident": ROLE_ORDER[i] in eligible[best_perm[i]],
        }
        for i in range(5)
    }
    return {"assignment": assignment, "fullyCovered": best_score == 5}


def _give_share(pesi: list[float], idx: int, share: float) -> None:
    """Riscrive `pesi[idx]` perche' valga `share` del totale. Sul posto.

    E' il modo in cui questo modulo esprime "questa scelta deve uscire il N%
    delle volte", e sostituisce i bonus additivi usati prima. La differenza
    che conta: un bonus additivo va ritarato ogni volta che cambia la scala
    dei pesi (punteggi sinergia/counter 0-100, conteggi di popolarita' 0-815,
    gli uni o gli altri elevati a potenza...), e infatti si era gia'
    scalibrato una volta senza che se ne accorgesse nessuno. Una quota no:
    vale sempre quella, qualunque cosa ci sia sotto.
    """
    altri = sum(w for i, w in enumerate(pesi) if i != idx)
    if altri <= 0:
        return  # nessun concorrente: quella scelta vince comunque
    pesi[idx] = altri * share / (1.0 - share)


# ---------------------------------------------------------------------------
# PROFILO DI SQUADRA da op.gg (2026-09-07)
# ---------------------------------------------------------------------------
# Richiesta dell'utente, dopo aver constatato che il bot non somigliava a
# nessuno: "dato questo op.gg, con player A B C D E, quindi niente unione di
# pool, dai un punteggio piu' alto ai campioni piu' giocati... andando ad
# aumentare il punteggio che gia' viene dato di counter/sinergia moltiplicato
# con il valore effettivo del player... bisogna evitare assolutamente che le
# pool dei 5 player vengano mischiate".
#
# Prima il pool era `frozenset(aggregate_pool(players).keys())`: solo i NOMI,
# tutti e cinque i giocatori mescolati in un unico insieme, usato come
# maschera acceso/spento. Si buttavano via le partite giocate - cioe'
# esattamente il numero che dice quanto uno gioca davvero un campione - e si
# permetteva al bot di pescare il campione del toplaner in bot lane.
#
# Perche' la separazione conta, misurato sulle draft pro: a livello di
# SQUADRA le pool si somigliano tutte (l'80% dei pick in ~28-30 campioni, sia
# per i top team sia per quelli di categoria inferiore), ma a livello di
# CORSIA no - T1 copre l'80% con 10-13 campioni per ruolo, una squadra di
# tier basso con 5-6. Sommando le cinque corsie quella concentrazione si
# perde: l'identita' sta nel giocatore, non nella squadra.


# Quanto dev'essere netta la deduzione del ruolo perche' il bot si fidi della
# pool di quel giocatore. Misurato su 25 giocatori veri (5 squadre di
# campionato dell'utente, ruoli confermati da lui): i 21 casi giusti e sicuri
# stanno TUTTI sopra il 44% di quota, i 4 dubbi TUTTI sotto il 22%. In mezzo
# non c'e' una sfumatura, c'e' un burrone - la soglia sta li' dentro e non e'
# delicata.
ROLE_CONF_QUOTA = 0.35
# Quota op.gg che da sola basta a fidarsi, se conferma il ruolo assegnato.
ROLE_CONF_OPGG = 0.5
# Quanto le percentuali op.gg rinforzano la deduzione dai campioni.
OPGG_ROLE_BOOST = 1.0


def _meta_pool_by_role(role_counts: dict) -> dict[str, dict[str, float]]:
    """Corsia -> {campione: quanto e' meta li', 0..1}.

    Serve come pool di ripiego per una corsia in cui non si sa chi gioca cosa
    (vedi _role_confidence). Normalizzata sul campione piu' giocato di QUELLA
    corsia, cosi' sta sulla stessa scala dell'affinita' di un giocatore, dove
    1.0 e' il suo campione piu' giocato: le due si possono mescolare senza che
    una schiacci l'altra.
    """
    per_role: dict[str, dict[str, float]] = {}
    for champ, conteggi in (role_counts or {}).items():
        for ruolo, n in (conteggi or {}).items():
            # sotto MIN_SUPPORT e' rumore, non un campione da quella corsia:
            # Sion risulta 4 volte in Jungle su 278 pick, non e' un jungler
            if ruolo in ROLE_ORDER and n >= MIN_SUPPORT:
                per_role.setdefault(ruolo, {})[champ] = float(n)
    for ruolo, d in per_role.items():
        massimo = max(d.values()) or 1.0
        per_role[ruolo] = {c: n / massimo for c, n in d.items()}
    return per_role


def _role_confidence(aff: dict, ruolo: str, roles_opgg: dict | None) -> float:
    """Quanto si puo' credere che QUESTO giocatore stia in QUESTA corsia, 0..1.

    Due indizi indipendenti, e op.gg puo' solo ALZARE la fiducia, mai
    abbassarla. Il motivo e' che op.gg mostra solo le prime due corsie: una
    corsia non citata non e' allo 0%, e' ignota. Punirla farebbe danni veri e
    misurati - due support giusti su cinque squadre (blackhunterXIII, 183cm)
    non hanno il loro ruolo vero fra i due mostrati, perche' quelle
    percentuali sono di SOLOQ e non di campionato.
    """
    totale = sum(aff.values()) or 1.0
    conf = min(1.0, (aff.get(ruolo, 0.0) / totale) / ROLE_CONF_QUOTA)
    dichiarato = (roles_opgg or {}).get(ruolo, 0.0)
    if dichiarato:
        conf = max(conf, min(1.0, dichiarato / ROLE_CONF_OPGG))
    return conf


def _player_role_affinity(player, role_counts: dict) -> dict[str, float]:
    """Quanto quel giocatore "sa" di ciascun ruolo, dalle sue partite.

    op.gg non dice che ruolo gioca uno: lo si deduce dai campioni che gioca,
    usando role_counts (quante volte quel campione e' stato giocato in
    ciascuna corsia nelle draft pro). Un giocatore con molte partite su
    campioni che nei pro si vedono in Jungle e' molto probabilmente il jungler.
    """
    punteggi = {r: 0.0 for r in ROLE_ORDER}
    for c in player.champions:
        conteggi = role_counts.get(c.champion) or {}
        totale = sum(conteggi.values())
        if not totale:
            continue
        for ruolo, n in conteggi.items():
            if ruolo in punteggi:
                punteggi[ruolo] += c.games * (n / totale)
    return punteggi


def assign_players_to_roles(players: list, role_counts: dict) -> dict[str, object]:
    """Quale dei 5 giocatori sta in quale corsia.

    Stesso schema di assign_roles piu' sopra (che fa la stessa cosa per 5
    CAMPIONI): si prova ogni abbinamento possibile - sono 120 con 5 elementi,
    non serve un algoritmo di matching vero - e si tiene quello che massimizza
    l'affinita' totale. Un'assegnazione GLOBALE e non "ognuno al suo ruolo
    migliore": due giocatori potrebbero avere lo stesso ruolo preferito, e
    scegliere per ciascuno il massimo locale lascerebbe una corsia scoperta.
    """
    if len(players) != len(ROLE_ORDER):
        return {}
    aff = []
    for p in players:
        a = _player_role_affinity(p, role_counts)
        # Rinforzo op.gg: moltiplicativo e solo verso l'alto, per lo stesso
        # motivo spiegato in _role_confidence (una corsia non citata e'
        # ignota, non assente). Misurato sulle 5 squadre confermate
        # dall'utente: con un peso da 0.25 fino a 5 NON cambia nemmeno
        # un'assegnazione - dove op.gg e' sicuro i campioni sono gia'
        # d'accordo (21 casi su 25 coincidono esattamente). Serve quindi
        # come spareggio nei casi che li' non capitavano: campioni ambigui e
        # op.gg netto. Non e' quello che decide, ed e' bene che sia cosi'.
        og = getattr(p, "roles", None) or {}
        for r in ROLE_ORDER:
            a[r] = a[r] * (1.0 + OPGG_ROLE_BOOST * og.get(r, 0.0))
        aff.append(a)
    migliore, punteggio_migliore = None, -1.0
    for perm in permutations(range(len(ROLE_ORDER))):
        # perm[i] = indice del giocatore assegnato al ruolo ROLE_ORDER[i]
        tot = sum(aff[perm[i]][ROLE_ORDER[i]] for i in range(len(ROLE_ORDER)))
        if tot > punteggio_migliore:
            migliore, punteggio_migliore = perm, tot
    return {ROLE_ORDER[i]: players[migliore[i]] for i in range(len(ROLE_ORDER))}


def build_team_profile(players: list, role_counts: dict) -> dict:
    """Il profilo con cui il bot impersona una squadra reale.

    Torna {"per_role": {ruolo: {campione: affinita' 0..1}},
           "flat": {campione: affinita'},
           "roster": {ruolo: nome giocatore}}.

    L'affinita' e' le partite di QUEL giocatore su QUEL campione, divise per
    le sue partite sul campione che gioca di piu': 1.0 = il suo cavallo di
    battaglia, valori bassi = qualcosa che ha toccato appena. Normalizzata
    per giocatore e non sul totale della squadra apposta - altrimenti un
    giocatore che ha semplicemente giocato piu' partite degli altri
    schiaccerebbe i compagni, che e' un fatto sul suo tempo libero, non sulle
    abitudini di draft della squadra.

    `flat` esiste per i casi in cui i giocatori non sono esattamente cinque
    (link multisearch con sostituti: capitato davvero, vedi opgg.py) - li' la
    corrispondenza con le corsie non e' ricavabile e si degrada al
    comportamento precedente, un'unica pool, tenendo pero' le affinita'.
    """
    per_role: dict[str, dict[str, float]] = {}
    flat: dict[str, float] = {}
    roster: dict[str, str] = {}

    for p in players:
        massimo = max((c.games for c in p.champions), default=0) or 1
        for c in p.champions:
            a = c.games / massimo
            flat[c.champion] = max(flat.get(c.champion, 0.0), a)

    assegnazione = assign_players_to_roles(players, role_counts)
    meta = _meta_pool_by_role(role_counts) if assegnazione else {}
    confidence: dict[str, float] = {}
    for ruolo, p in assegnazione.items():
        massimo = max((c.games for c in p.champions), default=0) or 1
        sua = {c.champion: c.games / massimo for c in p.champions}
        conf = _role_confidence(
            _player_role_affinity(p, role_counts), ruolo, getattr(p, "roles", None)
        )
        if conf >= 1.0:
            per_role[ruolo] = sua
        else:
            # RIPIEGO META, idea dell'utente e il pezzo che risolve davvero il
            # difetto strutturale qui sotto: "un giocatore fuori ruolo giochera'
            # principalmente meta per non pesare sulla squadra, inoltre e' piu'
            # prevedibile". Mescolato e non commutato di netto proprio per quel
            # "principalmente": a fiducia 0.2 la sua pool vera pesa ancora un
            # quinto, invece di sparire per una soglia superata di un pelo.
            #
            # Il difetto: l'assegnazione e' una biiezione, quindi quando la pool
            # di un giocatore non indica nessuna corsia, quella che resta gli
            # tocca PER ESCLUSIONE. Casi veri: un toplaner schierato da sostituto
            # a mid finiva in Mid con l'1% di compatibilita', e la sua pool da
            # toplaner diventava quella del mid della squadra. Ora in quella
            # corsia il bot pesca soprattutto meta, che e' esattamente cio' che
            # fa una persona messa fuori ruolo.
            m = meta.get(ruolo, {})
            per_role[ruolo] = {
                c: conf * sua.get(c, 0.0) + (1.0 - conf) * m.get(c, 0.0)
                for c in set(sua) | set(m)
            }
        confidence[ruolo] = conf
        roster[ruolo] = p.summoner

    return {"per_role": per_role, "flat": flat, "roster": roster,
            "confidence": confidence}


# Quanto vale un campione nella tier list personale di un giocatore, sulla
# stessa scala 0..1 dell'affinita' op.gg (1.0 = il suo cavallo di battaglia).
# La semantica e' quella data dall'utente, che le tier list se le e' scritte
# lui: S "da poter prendere in qualunque occasione", A "confident, utili per
# la maggior parte degli scenari", B "OK, situazionali", C "non ok, solo come
# ultima spiaggia", D "da evitare in ogni circostanza".
#
# La spaziatura conta piu' dei valori assoluti, perche' questo numero
# MOLTIPLICA un punteggio sinergia/counter che spazia grosso modo 5x fra il
# primo e l'ultimo candidato: un B deve battere un S di ~2,2x nel punteggio
# per superarlo, un C di oltre 6x - che e' appunto "ultima spiaggia". D vale
# zero, non un epsilon: "in ogni circostanza" e' una parola sola.
#
# Un campione che nella tier list non c'e' proprio vale zero come i D: per
# quel giocatore non esiste (parole dell'utente).
TIER_AFFINITY = {"S": 1.0, "A": 0.75, "B": 0.45, "C": 0.15, "D": 0.0}


def build_roster_profile(roster_profile: dict, role_counts: dict) -> dict:
    """Il profilo della squadra del COACH, dalle tier list del roster.

    Stessa forma e stessa semantica di build_team_profile (che lo ricava da
    op.gg), quindi tutto il resto - filtro per corsia, ordinamento, ripiego
    meta - funziona identico senza sapere da dove viene il profilo.

    Due differenze rispetto a op.gg, entrambe a favore:

    1. **I ruoli non si deducono.** Nel roster il coach ha gia' messo ogni
       giocatore nella sua corsia, quindi niente assegnazione per biiezione,
       niente incertezza, niente casi limite da segnalare: la fiducia e' 1.0
       per costruzione. Sparisce di colpo tutta la parte piu' fragile.
    2. **La pool e' piu' grande e piu' vera.** op.gg da' i ~10 campioni di
       una stagione di soloq; una tier list scritta a mano ne ha 15-25 e dice
       anche QUANTO ci si puo' contare, che e' l'informazione che serve in
       draft. Motivo per cui l'utente la preferisce: "la pool del team che
       seguo e' molto piu' grande e sicura rispetto a quella presa da un
       op.gg su una singola stagione".

    Si prende il TITOLARE di ogni corsia (il primo della lista), come fa gia'
    /api/opgg-roster-team: i sub stanno nella stessa lista per convenzione,
    non in un campo separato.

    Una corsia senza tier list (non compilata, o tutta D) NON diventa "niente
    da giocare" - sarebbe un buco nero che spegne quella riga: si ricade sui
    pick meta con fiducia 0, esattamente come per un giocatore op.gg di cui
    non si capisce il ruolo.
    """
    per_role: dict[str, dict[str, float]] = {}
    flat: dict[str, float] = {}
    nomi: dict[str, str] = {}
    confidence: dict[str, float] = {}
    # Il tier di provenienza viaggia accanto all'affinita': per il coach "B" e'
    # l'informazione vera, "45%" ne e' solo la traduzione interna. La UI mostra
    # la lettera quando c'e' - vedi suggestionTitle in app.js.
    tiers: dict[str, dict[str, str]] = {}
    meta = _meta_pool_by_role(role_counts)

    for ruolo in ROLE_ORDER:
        giocatori = (roster_profile or {}).get(ruolo) or []
        titolare = giocatori[0] if giocatori else {}
        pool: dict[str, float] = {}
        etichette: dict[str, str] = {}
        for tier, campioni in (titolare.get("tiers") or {}).items():
            peso = TIER_AFFINITY.get(tier, 0.0)
            if peso <= 0:
                continue
            for c in campioni or []:
                if c and peso > pool.get(c, 0.0):
                    pool[c] = peso
                    etichette[c] = tier

        if pool:
            per_role[ruolo] = pool
            tiers[ruolo] = etichette
            confidence[ruolo] = 1.0
        else:
            per_role[ruolo] = dict(meta.get(ruolo, {}))
            confidence[ruolo] = 0.0
        nomi[ruolo] = str(titolare.get("name") or "").strip() or ruolo
        for c, a in per_role[ruolo].items():
            flat[c] = max(flat.get(c, 0.0), a)

    return {"per_role": per_role, "flat": flat, "roster": nomi,
            "confidence": confidence, "tiers": tiers}


# --- COMP: la parte "umana" del ragionamento -------------------------------
#
# Un drafter vero non sceglie solo il pick con la sinergia migliore: guarda
# dove sta andando l'avversario e prova ad arrivarci contro, e intanto cerca
# di chiudere la propria comp coprendone i tag. Queste due cose sono separate
# apposta, perche' rispondono a domande diverse e una puo' valere senza
# l'altra (i tag si chiudono anche senza sapere niente del nemico).
#
# Quanto la comp puo' spostare il punteggio sinergia/counter. MOLTIPLICATIVO
# e non additivo, come tutto il resto qui dentro: un bonus additivo va
# ritarato ogni volta che cambia la scala sotto, ed e' gia' successo una
# volta senza che nessuno se ne accorgesse (vedi _give_share).
# MISURATO, non scelto a occhio. Su 120 draft simulate per valore, contro un
# avversario che pesca il miglior punteggio sinergia/counter:
#
#   peso   comp in vantaggio   sinergia conservata
#   0.0          47%  (= caso)        94.9%
#   0.6          73%                  94.1%
#   1.0          77%                  93.7%
#   1.5          89%                  93.1%
#
# Due cose che quei numeri dicono. Primo: SENZA comp il bot sta al 47% contro
# un caso puro del 50% - cioe' finiva sistematicamente contro-draftato, ed e'
# il buco che questa modifica chiude. Secondo: il prezzo e' quasi piatto, e la
# MEDIANA resta 100% a ogni peso - la maggior parte dei pick e' comunque il
# migliore disponibile, a cambiare e' solo la coda.
#
# Non c'e' un ginocchio, quindi il valore e' una scelta di gusto fatta
# prudente: 1.5 comprerebbe altri 12 punti di vantaggio per mezzo punto di
# sinergia, ma un bot che vince il confronto di comp quasi sempre diventa
# prevedibile, che e' l'opposto di "umano".
COMP_WEIGHT = 1.0
# Quanto vale in piu' puntare a una comp che BATTE quella del nemico. E' il
# moltiplicatore del guadagno, non un secondo termine: anticipare conta solo
# se quel pick fa comunque avanzare una comp.
COMP_COUNTER_BONUS = 1.0
# Da quanto la direzione del nemico e' abbastanza affidabile per anticiparla.
# La soglia e' sull'ACCURATEZZA misurata nei dati, non sul numero di pick:
# il numero di pick lo ricava build_comp_stats e cambia col meta. Stesso
# principio di MIN_SUPPORT - meglio non anticipare che anticipare a caso.
COMP_DIRECTION_MIN_ACCURACY = 0.80


def _comp_direction_min_picks(comp_stats: dict | None) -> int:
    """Dopo quanti pick avversari ci si puo' fidare della loro direzione.

    Letto dalle tabelle, che si rigenerano ad ogni "Aggiorna dati": se il meta
    si sposta e le comp diventano leggibili prima (o dopo), questo numero si
    sposta da solo. Senza dati si torna 6, cioe' "mai": si preferisce non
    anticipare piuttosto che anticipare alla cieca.
    """
    acc = (comp_stats or {}).get("direction_accuracy") or {}
    for k in range(1, 6):
        try:
            if float(acc.get(str(k), 0.0)) >= COMP_DIRECTION_MIN_ACCURACY:
                return k
        except (TypeError, ValueError):
            continue
    return 6


def _comp_progress(comp: str, picks: list[str], champs_by_name: dict) -> float:
    """Quanto quella comp e' avviata con questi pick, 0..1.

    Meta' dai MEMBRI (chi appartiene alla comp) e meta' dai TAG obbligatori
    coperti. Le due meta' esistono perche' contano cose diverse e l'utente le
    tiene distinte da sempre: cinque campioni della comp che pero' non
    coprono i tag non sono quella comp, e viceversa. E' la stessa coppia di
    criteri che gia' mostra il pannello "Comp rilevate" (membri per dire
    "rilevata", tag come sotto-quest).
    """
    reqs = COMP_REQUIREMENTS.get(comp) or {}
    obbligatori = reqs.get("mandatory") or []
    membri = 0
    tag: set[str] = set()
    for n in picks:
        c = champs_by_name.get(n)
        if not c:
            continue
        if comp in c.comps:
            membri += 1
        tag |= set(c.tags)
    # Membri su CINQUE, non su MEMBER_THRESHOLD: una comp con tutti e cinque
    # dentro e' piu' di una che arriva appena alla soglia di "rilevata". Con
    # la soglia al denominatore il valore saturava a 1.0 al terzo pick e da
    # li' in poi la comp che stavamo costruendo smetteva di valere niente -
    # cioe' il segnale spariva esattamente quando eravamo impegnati.
    quota_membri = membri / 5.0
    coperti = sum(1 for t in obbligatori if t in tag)
    quota_tag = (coperti / len(obbligatori)) if obbligatori else 1.0
    return 0.5 * quota_membri + 0.5 * quota_tag


def _comp_direction(picks: list[str], champs_by_name: dict) -> str | None:
    """Verso che comp sta andando questo lato, o None se e' in parita'.

    In parita' si torna None e basta: a fine draft il 36% delle squadre pro
    non ha una comp dominante, quindi "nessuna direzione" e' una risposta
    frequente e legittima, non un caso limite da forzare.
    """
    conteggi = []
    for comp in COMP_REQUIREMENTS:
        n = sum(1 for p in picks if p in champs_by_name and comp in champs_by_name[p].comps)
        conteggi.append((n, comp))
    conteggi.sort(reverse=True)
    if not conteggi or conteggi[0][0] == 0:
        return None
    if len(conteggi) > 1 and conteggi[0][0] == conteggi[1][0]:
        return None
    return conteggi[0][1]


def _comp_value(
    picks: list[str], enemy_direction: str | None, champs_by_name: dict
) -> float:
    """Il valore della migliore comp raggiungibile con questi pick.

    Il vantaggio di comp e' un PESO su questo valore, non un termine a parte:
    una comp che batte quella del nemico vale di piu' a parita' di
    avanzamento, quindi puo' scavalcare quella in testa quando il distacco e'
    ancora piccolo - presto, che e' quando serve - ma non quando ormai siamo
    impegnati da un'altra parte.
    """
    migliore = 0.0
    for comp in COMP_REQUIREMENTS:
        v = _comp_progress(comp, picks, champs_by_name)
        if enemy_direction and enemy_direction in COMP_BEATS.get(comp, frozenset()):
            v *= 1.0 + COMP_COUNTER_BONUS
        migliore = max(migliore, v)
    return migliore


def _comp_bonus(
    candidate: str,
    own_picks: list[str],
    enemy_direction: str | None,
    champs_by_name: dict,
    base: float | None = None,
) -> float:
    """Quanto questo candidato aiuta, dal punto di vista delle comp.

    Si misura di quanto sale la MIGLIORE comp raggiungibile, non il guadagno
    piu' grande su una comp qualsiasi. La differenza e' tutta qui, e la prima
    versione sbagliava proprio questo: premiando il guadagno maggiore, il pick
    che faceva scattare in avanti una comp appena abbozzata batteva quello che
    portava avanti la comp in cui eravamo gia' dentro - cioe' spingeva a
    disperdersi invece che a chiudere, l'opposto del "creare una comp con
    tutti i suoi inside-tag".

    Guardando invece il massimo, avanzare la comp in testa e' quello che alza
    davvero il tetto, e le altre contano solo quando riescono a superarla.

    Il vantaggio di comp entra come PESO sul valore, non come termine a parte:
    una comp che batte quella verso cui va il nemico vale di piu' a parita' di
    avanzamento, quindi puo' scavalcare la comp in testa quando il distacco e'
    ancora piccolo - presto, che e' quando serve - ma non quando siamo ormai
    impegnati altrove. E' il ragionamento descritto dall'utente: capire in
    anticipo dove vanno e arrivarci contro.
    """

    if base is None:
        base = _comp_value(own_picks, enemy_direction, champs_by_name)
    return max(0.0, _comp_value(own_picks + [candidate], enemy_direction, champs_by_name) - base)


def build_pro_team_profile(team: str, tables: dict) -> dict:
    """Il profilo di una squadra PRO, dalle sue draft su Leaguepedia.

    Terza sorgente con la stessa forma delle altre due (build_team_profile da
    op.gg, build_roster_profile dalle tier list): per_role / flat / roster /
    confidence. Da qui in giu' non cambia niente - filtro coerente per corsia,
    ordinamento, ripiego meta e ragionamento per comp funzionano identici
    senza sapere da dove arriva il profilo.

    **Qui i ruoli sono REGISTRATI, non dedotti.** Leaguepedia salva la corsia
    di ogni pick, quindi niente assegnazione per biiezione, niente casi
    ambigui, niente incertezza: la fiducia e' 1.0 per costruzione e la parte
    piu' fragile del sistema semplicemente non esiste. E' il motivo per cui
    questa sorgente e' la piu' solida delle tre.

    I conteggi arrivano gia' pesati per recency da build_team_pools; qui si
    normalizzano per corsia sul campione piu' giocato, cosi' 1.0 significa "il
    loro cavallo di battaglia in quella corsia" - stessa convenzione delle
    altre due sorgenti.
    """
    squadre = ((tables.get("team_pools") or {}).get("teams") or {})
    voce = squadre.get(team)
    if not voce:
        return {}

    per_role: dict[str, dict[str, float]] = {}
    flat: dict[str, float] = {}
    confidence: dict[str, float] = {}
    for ruolo, conteggi in (voce.get("per_role") or {}).items():
        if ruolo not in ROLE_ORDER or not conteggi:
            continue
        massimo = max(conteggi.values()) or 1.0
        pool = {c: n / massimo for c, n in conteggi.items()}
        per_role[ruolo] = pool
        confidence[ruolo] = 1.0
        for c, a in pool.items():
            flat[c] = max(flat.get(c, 0.0), a)

    if not flat:
        return {}
    # `roster` altrove porta i nomi dei giocatori; qui i dati non li hanno, e
    # ripetere il nome della squadra su cinque righe non direbbe niente. Chi
    # sta giocando lo dice botTeam nello stato.
    return {"per_role": per_role, "flat": flat, "roster": {}, "confidence": confidence}


def list_pro_teams(tables: dict) -> list[dict]:
    """Le squadre impersonabili, dalla piu' documentata alla meno."""
    squadre = ((tables.get("team_pools") or {}).get("teams") or {})
    return sorted(
        ({"name": t, "drafts": v.get("drafts", 0)} for t, v in squadre.items()),
        key=lambda x: (-x["drafts"], x["name"]),
    )


def _pick_score(
    champion: str, own_picks: list[str], enemy_picks: list[str], synergy: dict, counter: dict
) -> float:
    """Punteggio sinergia/counter di UN candidato pick - stessa formula usata
    sia dalla scelta ponderata-casuale del bot (_choose_bot_champion) sia dai
    "pick suggeriti" in modalita' torneo (vedi rank_pick_suggestions sotto,
    richiesto esplicitamente dall'utente 2026-08-26) - estratta a livello di
    modulo (non un metodo di TrainingSession) apposta: la modalita' torneo
    non ha nessuna TrainingSession, solo la draft REALE specchiata, ma deve
    usare la STESSA identica euristica, non una riscritta a parte che
    rischierebbe di scostarsi nel tempo."""
    syn = synergy.get(champion, {})
    cnt = counter.get(champion, {})
    w = sum(syn.get(p, 0) for p in own_picks) * SYNERGY_WEIGHT
    w += sum(cnt.get(p, 0) for p in enemy_picks) * COUNTER_WEIGHT
    return w


def _support(score: float) -> float:
    """Quante osservazioni ci sono dietro un punteggio.

    Oggi i pesi valgono 1.0 entrambi, quindi il punteggio coincide col numero
    di partite osservate; passare da qui rende la cosa esplicita invece che
    accidentale, ed e' l'unico punto da correggere se un giorno i pesi
    cambiassero."""
    peso = max(SYNERGY_WEIGHT, COUNTER_WEIGHT)
    return score / peso if peso else score


def _can_cover(role_sets: list[set[str]]) -> bool:
    """C'e' un modo di dare a ciascun campione un ruolo DISTINTO fra i suoi?

    Backtracking sui campioni piu' vincolati per primi (meno ruoli
    possibili): con al massimo 6 elementi e 5 ruoli non serve un vero
    algoritmo di matching bipartito, e partire dai piu' rigidi taglia
    subito i rami morti.
    """
    n = len(role_sets)
    if n == 0:
        return True
    # Ordina per numero di ruoli possibili (meno = piu' vincolato = prima)
    indexed = sorted(range(n), key=lambda i: len(role_sets[i]))

    def go(k: int, used: set[str]) -> bool:
        if k == n:
            return True
        idx = indexed[k]
        for role in role_sets[idx] - used:
            used.add(role)
            if go(k + 1, used):
                return True
            used.remove(role)
        return False

    return go(0, set())


def _blocked_roles(picks: list[str], champs_by_name: dict) -> set[str]:
    """Ruoli in cui NON ha piu' senso suggerire un pick, per UNA squadra.

    Richiesta dell'utente 2026-09-05: "gnar può essere giocato solo top, non
    ha senso suggerirmi altri pick per la top; in caso di poppy, invece, che
    può essere giocata top o support, allora ha senso continuare a suggerire
    pick, ma nel momento in cui si sceglie un top, allora poppy è per forza
    support e quindi si bloccano entrambi i suggerimenti delle corsie".

    Non basta quindi segnare come occupati i ruoli dei pick fatti: un
    campione flex occupa un ruolo solo QUANDO il resto della squadra non gli
    lascia alternative. E' un problema di vincoli, non di conteggio.

    Formulato al contrario, diventa una domanda sola e facile: per ogni
    ruolo, "se aggiungessi ORA un campione in questo ruolo, i pick gia' fatti
    troverebbero ancora tutti posto?" Se no, quel ruolo e' di fatto gia'
    speso. Cinque verifiche in tutto, indipendenti dal numero di candidati -
    per questo si calcola una volta sola e non per ogni campione.

    Sull'esempio dell'utente:
      - Poppy da sola {Top,Jungle,Support}: nessun ruolo bloccato (per ogni
        ruolo r, Poppy puo' spostarsi su un altro dei suoi).
      - Poppy + Ornn {Top}: Ornn e' obbligato in Top, quindi un nuovo Top non
        entrerebbe; e se il nuovo prendesse Support, Poppy dovrebbe andare in
        Top - occupata da Ornn. Restano bloccati sia Top sia Support, che e'
        esattamente cio' che l'utente descrive.

    I ruoli sono quelli di champions.xlsx (Champion.roles), la stessa fonte
    gia' usata da assign_roles: un solo modello di ruoli in tutto il
    progetto. Un campione senza ruoli nell'xlsx vale come jolly (puo' stare
    ovunque) invece di rendere impossibile qualunque copertura.

    champs_by_name arriva da FUORI (non si ricarica qui): dal 2026-09-06 il
    ranking gira due volte per ogni aggiornamento, una per squadra, e
    load_champions() rilegge l'xlsx da zero ad ogni chiamata - vedi la nota
    sulle letture condivise in rank_pick_suggestions.
    """
    all_roles = set(ROLE_ORDER)

    own_sets: list[set[str]] = []
    for name in picks:
        champ = champs_by_name.get(name)
        roles = set(champ.roles) if champ and champ.roles else set(all_roles)
        own_sets.append(roles & all_roles or set(all_roles))

    if len(own_sets) >= len(ROLE_ORDER):
        return set(all_roles)

    return {r for r in ROLE_ORDER if not _can_cover(own_sets + [{r}])}


def _profile_affinity(
    name: str, profile: dict | None, picks: list[str], champs_by_name: dict
) -> float:
    """Quanto quella squadra gioca `name`, in una corsia che potrebbe davvero
    dargli viste le scelte gia' fatte.

    E' identica alla domanda che si fa il bot in _choose_bot_champion
    (l'helper `affinita` li' dentro), riusata qui per i pick suggeriti: e' il
    seguito chiesto dall'utente - "una volta finito il sistema, i pick
    suggeriti potrebbero usarlo". Stesso profilo, stessa semantica, quindi il
    pannello consiglia con lo stesso criterio con cui il bot sceglie - bug
    compresi: la corsia da cui arriva l'affinita' dev'essere una che il
    campione puo' davvero occupare, vedi _profile_roles_for.

    Senza profilo torna 1.0, cioe' neutro: il punteggio resta quello che era.
    """
    if not profile:
        return 1.0
    per_role = profile.get("per_role") or {}
    if not per_role:
        # Giocatori non esattamente cinque (link con sostituti): le corsie non
        # sono ricavabili, si degrada alla pool unica tenendo le affinita'.
        return (profile.get("flat") or {}).get(name, 0.0)
    ammesse = _profile_roles_for(name, picks, champs_by_name, per_role)
    if not ammesse:
        return 0.0
    return max(per_role.get(r, {}).get(name, 0.0) for r in ammesse)


def _rank_one_side(
    picks: list[str],
    opponents: list[str],
    taken: set[str],
    all_champs: list,
    champs_by_name: dict,
    synergy: dict,
    counter: dict,
    role_counts: dict,
    top_n: int,
    profile: dict | None = None,
    comps_enabled: bool = True,
    comp_stats: dict | None = None,
) -> list[dict]:
    """Il ranking vero e proprio, per UNA squadra sola.

    `picks` sono i campioni gia' presi da quella squadra (con cui il
    candidato deve avere SINERGIA), `opponents` quelli della squadra di
    fronte (che il candidato deve COUNTERARE). Non c'e' niente in questa
    funzione che sappia quale delle due sia "noi": e' esattamente cio' che
    permette di ottenere i suggerimenti avversari passando gli stessi due
    elenchi scambiati - vedi rank_pick_suggestions.

    `profile`, se dato, e' il profilo op.gg di quella squadra (vedi
    build_team_profile): non piu' un elenco chiuso di nomi ma "quanto ciascun
    giocatore gioca ciascun campione, nella sua corsia". Fa due cose - esclude
    chi quella squadra non gioca in nessuna corsia ancora libera, e ORDINA il
    resto pesando il punteggio con quanto lo gioca davvero.

    La differenza pratica rispetto alla vecchia pool di soli nomi: in una
    corsia di cui non si sa chi la occupi il profilo contiene anche i pick
    meta (vedi _role_confidence), quindi li' i suggerimenti non restano
    imprigionati nella pool soloq di un giocatore assegnato per esclusione.

    Torna `{"suggestions": [...], "thin": bool}`. `thin` e' vero quando dei
    candidati c'erano, ma tutti sotto MIN_SUPPORT: e' la differenza fra "non
    c'e' niente da dire" e "non ho abbastanza dati per dirlo", e la UI la
    mostra invece di lasciare una riga vuota.
    """
    blocked = _blocked_roles(picks, champs_by_name)
    all_roles = set(ROLE_ORDER)

    def open_roles(champ) -> set[str]:
        roles = set(champ.roles) & all_roles if champ.roles else set(all_roles)
        return (roles or all_roles) - blocked

    scored = [
        (c.name, _pick_score(c.name, picks, opponents, synergy, counter), open_roles(c))
        for c in all_champs
        if c.name not in taken
    ]
    # Fuori chi ha punteggio nullo E chi non ha piu' nessuna corsia libera.
    scored = [(name, score, free) for name, score, free in scored if score > 0 and free]
    # ...e, se c'e' un profilo, chi quella squadra non gioca da nessuna parte.
    affinita = {
        name: _profile_affinity(name, profile, picks, champs_by_name)
        for name, _, _ in scored
    }
    if profile:
        scored = [t for t in scored if affinita[t[0]] > 0]
    # ...e fuori anche chi si regge su troppe poche partite: vedi MIN_SUPPORT.
    # Coi pesi a 1.0 il punteggio E' il numero di osservazioni; il confronto
    # resta scritto su quel numero e non sul punteggio pesato, cosi' cambiare
    # un peso domani non sposta silenziosamente la soglia.
    solidi = [t for t in scored if _support(t[1]) >= MIN_SUPPORT]
    thin = bool(scored) and not solidi
    # Si FILTRA sul punteggio grezzo e si ORDINA su quello pesato. Sono due
    # domande diverse e vanno tenute separate: "quante volte l'ho visto nei
    # dati" e' una proprieta' delle draft pro e non cambia perche' una certa
    # squadra gioca poco un campione - pesare prima della soglia farebbe
    # sparire come "pochi dati" cose su cui i dati ci sono eccome.
    # Il fattore comp entra nell'ORDINE come l'affinita', e per lo stesso
    # motivo non tocca il punteggio mostrato: quello resta il sinergia/counter
    # grezzo, che e' come lo chiama il tooltip. `comps_enabled` e' spento sul
    # lato del coach quando lui ha spento i bordi comp - chi non crede in
    # questo sistema non vuole esserci guidato - ma resta acceso sull'altro
    # lato, che non e' un consiglio: e' una previsione di cosa faranno loro.
    fattore_comp = {name: 1.0 for name, _, _ in solidi}
    if comps_enabled and solidi:
        direzione_nemica = None
        if len(opponents) >= _comp_direction_min_picks(comp_stats):
            direzione_nemica = _comp_direction(opponents, champs_by_name)
        base_comp = _comp_value(picks, direzione_nemica, champs_by_name)
        for name, _, _ in solidi:
            fattore_comp[name] = 1.0 + COMP_WEIGHT * _comp_bonus(
                name, picks, direzione_nemica, champs_by_name, base_comp
            )
    solidi.sort(key=lambda t: t[1] * affinita[t[0]] * fattore_comp[t[0]], reverse=True)
    top = solidi[:top_n]

    # La corsia mostrata sulla card deve essere una che quella squadra puo'
    # davvero coprire con quel campione, non una qualunque compatibile coi
    # tag - stessa incoerenza appena corretta in assign_roles.
    allowed = {
        name: (
            _profile_roles_for(name, picks, champs_by_name, profile["per_role"])
            if profile and profile.get("per_role")
            else free
        )
        for name, _, free in top
    }
    roles = _suggest_roles([name for name, _, _ in top], opponents, role_counts, allowed)
    return {
        "suggestions": [
            {
                "champion": name,
                # Resta il punteggio GREZZO sinergia/counter, che e' come lo
                # chiama il tooltip: se ci moltiplicassi dentro l'affinita'
                # quell'etichetta direbbe una cosa falsa. Il peso viaggia a
                # parte, cosi' la UI puo' spiegare perche' l'ordine non segue
                # il numero.
                "score": round(score, 2),
                "role": roles.get(name),
                "affinity": round(affinita[name], 3) if profile else None,
                # Presente solo per un profilo che nasce da tier list scritte a
                # mano (vedi build_roster_profile): li' la lettera e' il dato
                # vero e la percentuale una traduzione. Da op.gg non esiste.
                "tier": ((profile or {}).get("tiers") or {})
                .get(roles.get(name) or "", {})
                .get(name),
            }
            for name, score, _ in top
        ],
        "thin": thin,
    }


def rank_pick_suggestions(
    blue_picks: list[str],
    red_picks: list[str],
    taken: set[str],
    top_n: int = 8,
    blue_profile: dict | None = None,
    red_profile: dict | None = None,
    blue_comps: bool = True,
    red_comps: bool = True,
) -> dict:
    """"Pick suggeriti" per le due squadre: {"blue": {...}, "red": {...}}.

    **Ragiona per LATI, non per "noi"/"loro" (2026-09-06).** Prima le due
    meta' erano "la nostra" e "quella avversaria", e fuori da torneo/training
    il lato nostro veniva DEDOTTO dall'ultimo slot cliccato: un dettaglio
    invisibile che scambiava il significato delle due righe. L'utente ci si
    e' imbattuto con Ambessa: "una nota risposta di Ambessa e' Renekton,
    tuttavia il tool non sa effettivamente chi e' per noi e per loro...
    propongo di immettere al posto di per noi e per loro -> blueside e
    redside". Aveva ragione: il calcolo era corretto, era l'etichetta a
    mentire. Blu e rosso invece non sono un'ipotesi, sono dove stanno i
    campioni.

    Richiesto per la nostra meta' dall'utente il 2026-08-26 ("dato che
    abbiamo un bot che capisce le risposte 'solite' a determinati pick...
    implementiamo i pick suggeriti... poi sara' il coach, in base a cosa
    gioca il suo team, cosa gioca il team avversario ed altri parametri, a
    decidere cosa e' giusto prendere") - quindi SOLO un elenco ordinato con
    un punteggio trasparente, mai una scelta automatica: stessa euristica
    sinergia/counter del bot (vedi _pick_score), applicata qui come un
    RANKING deterministico su tutti i campioni disponibili invece che come
    una scelta ponderata-casuale di uno solo.

    La seconda meta' e' stata aggiunta il 2026-09-06, su richiesta
    dell'utente: "sfruttando gli stessi dati possiamo individuare sia i pick
    che vanno a nostro vantaggio, ma non quelli che vanno a vantaggio del
    team nemico... in modo da anticipare ed individuare eventuali pick
    contesi con lo stesso sistema".

    Non serve nessuna euristica nuova per ottenerla: "buono per un lato" e'
    definito come sinergia coi pick di QUEL lato piu' counter contro quelli
    dell'altro, e la domanda per l'altro lato e' la stessa formula coi due
    elenchi scambiati. _rank_one_side e' quindi scritta senza alcun concetto
    di lato, e viene chiamata due volte con gli argomenti invertiti. Questo
    vale anche per i due ragionamenti piu' delicati che ci stanno sotto, che
    seguono lo scambio da soli:
      - i ruoli gia' spesi (_blocked_roles) vengono calcolati sui pick del
        lato per cui si sta suggerendo;
      - la corsia mostrata (_suggest_roles) e' quella piu' frequente CONTRO
        i campioni dell'altro lato.
    Un campione che compare in ENTRAMBI gli elenchi e' un pick conteso; chi
    chiama non deve fare altro che intersecarli (lo fa la UI, vedi
    renderSuggestionsPanel in app.js).

    Niente EPSILON/ancora qui (a differenza di _choose_bot_champion):
    l'epsilon esiste solo per dare al BOT una scelta di chiusura anche senza
    dati, irrilevante per un elenco che il coach legge lui stesso; l'ancora
    e' un concetto specifico della modalita' training (una singola draft pro
    scelta a caso all'avvio), che il torneo non ha.

    Solo candidati con punteggio STRETTAMENTE positivo vengono ritornati - a
    inizio draft (blue_picks e red_picks entrambi vuoti) OGNI candidato
    avrebbe punteggio 0, ed evidenziare un "top N" arbitrario a quel punto
    sarebbe fuorviante (sembrerebbe un consiglio vero, ma non c'e' nessun
    segnale nei dati) - meglio non suggerire nulla che suggerire a caso.
    Ne segue che a draft appena iniziata i due elenchi sono vuoti entrambi, e
    che dopo il primo ban/pick di solito uno solo dei due si popola.

    `blue_profile`/`red_profile` (opzionali) legano ciascun lato alla squadra
    vera che lo gioca, dal suo op.gg - "in modo da poter selezionare i pick
    suggeriti e renderli ancora di meno, in base proprio a cosa il team
    nemico puo' giocare" (utente, 2026-09-06). Un profilo per lato e non una
    sola pool "avversaria": col passaggio a blu/rosso non esiste piu' un lato
    avversario a priori, e il vincolo naturale di un lato e' la sua stessa
    squadra. Restringere DENTRO il ranking e non dopo e' l'unico modo di avere
    comunque i primi N candidati fra quelli giocabili: filtrare gli otto gia'
    scelti ne lascerebbe due o tre, quasi a caso.

    Dal 2026-09-07 non e' piu' un elenco di nomi ma lo STESSO profilo che usa
    il bot di training (build_team_profile), su richiesta dell'utente: quindi
    non solo esclude, ma ordina in base a quanto quella squadra gioca davvero
    ciascun campione - e nelle corsie di cui non si sa chi le occupi lascia
    passare i pick meta invece di imprigionare il consiglio nella pool soloq
    di un giocatore assegnato per esclusione.

    Le letture da disco (xlsx dei campioni, tabelle Leaguepedia) si fanno UNA
    volta sola qui e si passano alle due chiamate: load_champions() non ha
    cache e riapre il file ogni volta, e questa funzione gira ad ogni cambio
    di stato della draft - in torneo anche piu' volte di seguito.
    """
    all_champs = load_champions()
    champs_by_name = {c.name: c for c in all_champs}
    tables = leaguepedia.load_tables()
    synergy = tables.get("synergy", {})
    counter = tables.get("counter", {})
    role_counts = tables.get("role_counts", {})
    if not tables.get("pick_counts"):
        raise ValueError(
            "Nessun dato Leaguepedia disponibile - premi prima \"Aggiorna dati\" per scaricare le draft pro."
        )

    comp_stats = tables.get("comp_stats") or {}

    def side(picks, opponents, profile=None, comps=True):
        return _rank_one_side(
            picks, opponents, taken, all_champs, champs_by_name,
            synergy, counter, role_counts, top_n, profile, comps, comp_stats,
        )

    return {
        "blue": side(blue_picks, red_picks, blue_profile, blue_comps),
        "red": side(red_picks, blue_picks, red_profile, red_comps),
    }


def _suggest_roles(
    names: list[str],
    enemy_picks: list[str],
    role_counts: dict,
    allowed: dict[str, set[str]] | None = None,
) -> dict[str, str | None]:
    """Per ognuno dei campioni suggeriti, in che CORSIA lo si sta suggerendo.

    Richiesta dell'utente 2026-09-05: "alcuni campioni possono essere giocati
    in diverse corsie rispetto alla loro principale, ed alcune risposte sono
    specifiche (vedesi poppy support contro specifici campioni)".

    Due livelli, in quest'ordine:

    1. CONTESTUALE - fra le draft pro in cui quel campione ha affrontato
       almeno uno dei nemici gia' pescati, qual e' la corsia piu' frequente.
       E' questo che cattura il caso "Poppy support CONTRO tizio": nei dati
       Poppy e' complessivamente piu' jungle (32) che support (25), quindi il
       solo conteggio globale mostrerebbe la corsia sbagliata proprio nei casi
       che interessano al coach.
    2. GLOBALE - la corsia piu' giocata in assoluto nei dati pro, usata
       quando il contesto non ha abbastanza osservazioni (soglia sotto).

    Il fallback serve perche' il contesto e' per sua natura sparso: con pochi
    nemici pescati, o con avversari rari, le draft che combaciano possono
    essere due o tre - un numero su cui non vale la pena ribaltare la corsia
    mostrata. Sotto soglia si preferisce il dato solido a quello specifico.

    Nota sui dati usati: i ruoli vengono dalle draft pro (role_counts, vedi
    leaguepedia.build_tables), NON dai ruoli di champions.xlsx - li' c'e' il
    ruolo "di scheda", qui quello che i pro giocano davvero in questa patch.
    """
    # Quante osservazioni servono perche' il contesto batta il dato globale.
    MIN_CONTEXT = 3

    def best(counts: dict[str, int], only: set[str] | None) -> str | None:
        # `only` = le corsie ancora libere per questo campione (vedi
        # _blocked_roles). Filtrare QUI, e non dopo, evita di mostrare una
        # corsia che la squadra non puo' piu' coprire: senza, un Poppy
        # suggerito con la top gia' spesa continuerebbe a mostrare "Top"
        # solo perche' e' la piu' frequente nei dati.
        if only is not None:
            counts = {r: n for r, n in counts.items() if r in only}
        if not counts:
            # Nessun dato pro utile: se resta una sola corsia libera e'
            # comunque l'informazione giusta da dare.
            if only and len(only) == 1:
                return next(iter(only))
            return None
        # A parita' di conteggio vince il ruolo alfabeticamente primo: senza
        # un criterio esplicito l'ordine dipenderebbe da come e' stato
        # costruito il dizionario, e la corsia mostrata potrebbe cambiare da
        # un aggiornamento dati all'altro senza motivo visibile.
        return max(sorted(counts), key=lambda r: counts[r])

    def only_for(name: str) -> set[str] | None:
        return allowed.get(name) if allowed else None

    globali = {name: best(role_counts.get(name, {}), only_for(name)) for name in names}

    enemies = {e for e in enemy_picks if e}
    if not enemies:
        return globali

    drafts = leaguepedia.load_drafts()
    if not drafts:
        return globali

    wanted = set(names)
    ctx: dict[str, dict[str, int]] = {}
    for d in drafts:
        for picks, picks_roles, opponents in (
            (d.team1_picks, d.team1_roles, d.team2_picks),
            (d.team2_picks, d.team2_roles, d.team1_picks),
        ):
            # Ci interessano solo le draft in cui questa squadra ha davvero
            # affrontato almeno uno dei campioni nemici gia' pescati ora.
            if not enemies.intersection(opponents):
                continue
            for name, role in zip(picks, picks_roles):
                if name in wanted and role:
                    ctx.setdefault(name, {})
                    ctx[name][role] = ctx[name].get(role, 0) + 1

    out = {}
    for name in names:
        counts = ctx.get(name, {})
        only = only_for(name)
        if only is not None:
            counts = {r: n for r, n in counts.items() if r in only}
        out[name] = best(counts, only) if sum(counts.values()) >= MIN_CONTEXT else globali[name]
    return out


_session: TrainingSession | None = None
# Il server Bottle di questo progetto e' threaded (un thread nuovo per ogni
# richiesta HTTP, vedi ThreadingWSGIServer in server.py) - senza questo lock,
# due richieste /api/training/pick quasi simultanee (doppio click veloce, o
# un retry di rete) potrebbero leggere ENTRAMBE lo stesso self.step prima che
# la prima abbia scritto la propria mossa, scrivendo sullo stesso slot e
# incrementando self.step due volte per una sola azione reale - trovato
# davvero durante un test automatizzato con click rapidissimi in sequenza
# (uno slot restava None nonostante step avesse gia' raggiunto 20/20). Un
# lock semplice invece della coda dedicata di drafter_live.py: qui non c'e'
# un browser esterno da possedere per tutta la sessione, solo un oggetto in
# memoria - basta serializzare le mutazioni.
_lock = threading.Lock()


def start_session(
    mode: str,
    side: str,
    bot_profile: dict | None = None,
    team: str | None = None,
) -> TrainingSession:
    """`team`: in modalita' "team", quale squadra pro impersonare. None = a
    sorte fra quelle disponibili, che e' una delle due scelte offerte
    dall'utente ("casuale" oppure "scelgo io")."""
    global _session
    if mode not in ("team", "freeform"):
        raise ValueError("Modalita' non valida.")
    if side not in ("blue", "red"):
        raise ValueError("Lato non valido.")

    tables = leaguepedia.load_tables()
    if not tables.get("pick_counts"):
        raise ValueError(
            "Nessun dato Leaguepedia disponibile - premi prima \"Aggiorna dati\" per scaricare le draft pro."
        )

    bot_team = None
    if mode == "team":
        disponibili = list_pro_teams(tables)
        if not disponibili:
            raise ValueError(
                "Nessuna squadra con abbastanza draft - premi \"Aggiorna dati\" per scaricarne altre."
            )
        if team:
            if not any(x["name"] == team for x in disponibili):
                raise ValueError(f'Squadra non disponibile: "{team}".')
            bot_team = team
        else:
            bot_team = random.choice(disponibili)["name"]
        profilo = build_pro_team_profile(bot_team, tables)
        if not profilo:
            raise ValueError(f'Nessun dato utilizzabile per "{bot_team}".')
        # Il profilo della squadra pro vince su un eventuale op.gg: se il
        # coach ha scelto di allenarsi contro una squadra precisa, e' quella
        # che deve giocare.
        bot_profile = profilo

    trainee_side = "team1" if side == "blue" else "team2"
    session = TrainingSession(
        mode=mode,
        trainee_side=trainee_side,
        tables=tables,
        bot_team=bot_team,
        bot_profile=bot_profile,
    )
    with _lock:
        session._advance_bot()  # se il bot e' team1 (blue), agisce per primo nel Ban Phase 1
        _session = session
    return session


def get_session() -> TrainingSession | None:
    return _session


def stop_session() -> None:
    global _session
    with _lock:
        _session = None


def apply_pick(champion: str) -> TrainingSession:
    with _lock:
        if _session is None:
            raise ValueError("Nessuna sessione di allenamento attiva.")
        _session.apply_trainee_action(champion)
        return _session


def rewind(step: int) -> TrainingSession:
    with _lock:
        if _session is None:
            raise ValueError("Nessuna sessione di allenamento attiva.")
        _session.rewind_to(step)
        return _session


def assign_trainee_roles(order: list[str]) -> TrainingSession:
    with _lock:
        if _session is None:
            raise ValueError("Nessuna sessione di allenamento attiva.")
        _session.confirm_trainee_role_order(order)
        return _session
