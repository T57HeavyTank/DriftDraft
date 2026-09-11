const backend = window.pywebview
  ? {
      getChampions: () => window.pywebview.api.get_champions(),
      getCompMeta: () => window.pywebview.api.get_comp_meta(),
      championArtStatus: () => window.pywebview.api.champion_art_status(),
      championArtSync: () => window.pywebview.api.champion_art_sync(),
      championArtProgress: () => window.pywebview.api.champion_art_progress(),
      saveChampionTags: (champion, comps, tags, roles) =>
        window.pywebview.api.save_champion_tags(champion, comps, tags, roles),
      resetChampionTags: (champion) => window.pywebview.api.reset_champion_tags(champion),
      detect: (picked) => window.pywebview.api.detect(picked),
      fetchOpggTeam: (url) => window.pywebview.api.fetch_opgg_team(url),
      fetchOpggRosterTeam: (teamName) => window.pywebview.api.fetch_opgg_roster_team(teamName),
      listRosterProfiles: () => window.pywebview.api.list_roster_profiles(),
      getRosterProfile: (name) => window.pywebview.api.get_roster_profile(name),
      saveRosterProfile: (name, data) => window.pywebview.api.save_roster_profile(name, data),
      deleteRosterProfile: (name) => window.pywebview.api.delete_roster_profile(name),
      renameRosterProfile: (oldName, newName) =>
        window.pywebview.api.rename_roster_profile(oldName, newName),
      connectLiveDraft: (url) => window.pywebview.api.connect_live_draft(url),
      liveDraftJoinOptions: (team) => window.pywebview.api.live_draft_join_options(team),
      liveDraftJoin: (team, side) => window.pywebview.api.live_draft_join(team, side),
      getLiveDraftState: () => window.pywebview.api.get_live_draft_state(),
      readyLiveDraft: () => window.pywebview.api.ready_live_draft(),
      disconnectLiveDraft: () => window.pywebview.api.disconnect_live_draft(),
      selectLiveDraft: (champion) => window.pywebview.api.select_live_draft(champion),
      confirmLiveDraft: (side, kind, index) => window.pywebview.api.confirm_live_draft(side, kind, index),
      confirmRoleOrder: (order) => window.pywebview.api.confirm_role_order(order),
      liveDraftEvaluate: (tier, ourRoleOrder, enemyRoleOrder) =>
        window.pywebview.api.live_draft_evaluate(tier, ourRoleOrder, enemyRoleOrder),
      liveDraftSuggestions: (bluePlayers, redPlayers, ourTeam, ourSide, compBorders) =>
        window.pywebview.api.live_draft_suggestions(
          bluePlayers, redPlayers, ourTeam, ourSide, compBorders),
      liveDraftRoleGuess: (picks, players, team) =>
        window.pywebview.api.live_draft_role_guess(picks, players, team),
      pickSuggestions: (bluePicks, redPicks, taken, bluePlayers, redPlayers,
                       useTrainingBotProfile, ourTeam, ourSide, compBorders) =>
        window.pywebview.api.pick_suggestions(
          bluePicks, redPicks, taken, bluePlayers, redPlayers,
          useTrainingBotProfile, ourTeam, ourSide, compBorders),
      listSavedDrafts: () => window.pywebview.api.list_saved_drafts(),
      addSavedDraft: (name, champions) => window.pywebview.api.add_saved_draft(name, champions),
      deleteSavedDraft: (id) => window.pywebview.api.delete_saved_draft(id),
      trainingStatus: () => window.pywebview.api.training_status(),
      trainingSync: () => window.pywebview.api.training_sync(),
      trainingSyncProgress: () => window.pywebview.api.training_sync_progress(),
      trainingStart: (mode, side, enemyTeamUrl, team) =>
        window.pywebview.api.training_start(mode, side, enemyTeamUrl, team),
      trainingTeams: () => window.pywebview.api.training_teams(),
      trainingPick: (champion) => window.pywebview.api.training_pick(champion),
      trainingState: () => window.pywebview.api.training_state(),
      trainingStop: () => window.pywebview.api.training_stop(),
      trainingRewind: (step) => window.pywebview.api.training_rewind(step),
      trainingAssignRoles: (order) => window.pywebview.api.training_assign_roles(order),
      trainingEvaluate: (tier) => window.pywebview.api.training_evaluate(tier),
    }
  : {
      getChampions: () => fetch("/api/champions").then((r) => r.json()),
      getCompMeta: () => fetch("/api/comp-meta").then((r) => r.json()),
      championArtStatus: () => fetch("/api/champion-art/status").then((r) => r.json()),
      championArtSync: () =>
        fetch("/api/champion-art/sync", { method: "POST" }).then((r) => r.json()),
      championArtProgress: () => fetch("/api/champion-art/progress").then((r) => r.json()),
      saveChampionTags: (champion, comps, tags, roles) =>
        fetch("/api/champion-tags", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ champion, comps, tags, roles }),
        }).then((r) => r.json()),
      resetChampionTags: (champion) =>
        fetch("/api/champion-tags/reset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ champion }),
        }).then((r) => r.json()),
      detect: (picked) =>
        fetch("/api/detect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(picked),
        }).then((r) => r.json()),
      fetchOpggTeam: (url) =>
        fetch("/api/opgg-team", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        }).then((r) => r.json()),
      fetchOpggRosterTeam: (teamName) =>
        fetch("/api/opgg-roster-team", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ team_name: teamName }),
        }).then((r) => r.json()),
      listRosterProfiles: () => fetch("/api/roster-profiles").then((r) => r.json()),
      getRosterProfile: (name) =>
        fetch(`/api/roster-profile?name=${encodeURIComponent(name)}`).then((r) => r.json()),
      saveRosterProfile: (name, data) =>
        fetch("/api/roster-profile", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, data }),
        }).then((r) => r.json()),
      deleteRosterProfile: (name) =>
        fetch("/api/roster-profile-delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name }),
        }).then((r) => r.json()),
      renameRosterProfile: (oldName, newName) =>
        fetch("/api/roster-profile-rename", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ old_name: oldName, new_name: newName }),
        }).then((r) => r.json()),
      connectLiveDraft: (url) =>
        fetch("/api/live-draft/connect", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        }).then((r) => r.json()),
      liveDraftJoinOptions: (team) =>
        fetch("/api/live-draft/join-options", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ team }),
        }).then((r) => r.json()),
      liveDraftJoin: (team, side) =>
        fetch("/api/live-draft/join", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ team, side }),
        }).then((r) => r.json()),
      getLiveDraftState: () => fetch("/api/live-draft/state").then((r) => r.json()),
      readyLiveDraft: () => fetch("/api/live-draft/ready", { method: "POST" }).then((r) => r.json()),
      disconnectLiveDraft: () =>
        fetch("/api/live-draft/disconnect", { method: "POST" }).then((r) => r.json()),
      selectLiveDraft: (champion) =>
        fetch("/api/live-draft/select", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ champion }),
        }).then((r) => r.json()),
      confirmLiveDraft: (side, kind, index) =>
        fetch("/api/live-draft/confirm", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ side, kind, index }),
        }).then((r) => r.json()),
      confirmRoleOrder: (order) =>
        fetch("/api/live-draft/confirm-role-order", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ order }),
        }).then((r) => r.json()),
      liveDraftEvaluate: (tier, ourRoleOrder, enemyRoleOrder) =>
        fetch("/api/live-draft/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tier, ourRoleOrder, enemyRoleOrder }),
        }).then((r) => r.json()),
      liveDraftSuggestions: (bluePlayers, redPlayers, ourTeam, ourSide, compBorders) =>
        fetch("/api/live-draft/suggestions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ bluePlayers, redPlayers, ourTeam, ourSide, compBorders }),
        }).then((r) => r.json()),
      liveDraftRoleGuess: (picks, players, team) =>
        fetch("/api/live-draft/role-guess", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ picks, players, team }),
        }).then((r) => r.json()),
      pickSuggestions: (bluePicks, redPicks, taken, bluePlayers, redPlayers,
                       useTrainingBotProfile, ourTeam, ourSide, compBorders) =>
        fetch("/api/pick-suggestions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            bluePicks, redPicks, taken, bluePlayers, redPlayers,
            useTrainingBotProfile, ourTeam, ourSide, compBorders,
          }),
        }).then((r) => r.json()),
      listSavedDrafts: () => fetch("/api/saved-drafts").then((r) => r.json()),
      addSavedDraft: (name, champions) =>
        fetch("/api/saved-drafts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, champions }),
        }).then((r) => r.json()),
      deleteSavedDraft: (id) =>
        fetch("/api/saved-drafts-delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id }),
        }).then((r) => r.json()),
      trainingStatus: () => fetch("/api/training/status").then((r) => r.json()),
      trainingSync: () => fetch("/api/training/sync", { method: "POST" }).then((r) => r.json()),
      trainingSyncProgress: () => fetch("/api/training/sync-progress").then((r) => r.json()),
      trainingTeams: () => fetch("/api/training/teams").then((r) => r.json()),
      trainingStart: (mode, side, enemyTeamUrl, team) =>
        fetch("/api/training/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode, side, enemy_team_url: enemyTeamUrl, team }),
        }).then((r) => r.json()),
      trainingPick: (champion) =>
        fetch("/api/training/pick", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ champion }),
        }).then((r) => r.json()),
      trainingState: () => fetch("/api/training/state").then((r) => r.json()),
      trainingStop: () => fetch("/api/training/stop", { method: "POST" }).then((r) => r.json()),
      trainingRewind: (step) =>
        fetch("/api/training/rewind", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ step }),
        }).then((r) => r.json()),
      trainingAssignRoles: (order) =>
        fetch("/api/training/assign-roles", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ order }),
        }).then((r) => r.json()),
      trainingEvaluate: (tier) =>
        fetch("/api/training/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tier }),
        }).then((r) => r.json()),
    };

const ROLE_ICONS = [
  ["Top", "Top Icon.svg"],
  ["Jungle", "Jungle Icon.svg"],
  ["Mid", "Mid Icon.svg"],
  ["Bot", "Bot Icon.svg"],
  ["Support", "Support Icon.svg"],
];

// Fasce elo per la ricerca counter (lolalytics) - valore/etichetta/icona,
// stesso ordine mostrato nel selettore. Valori = parametro "tier" del sito.
const RANK_TIERS = [
  ["emerald_plus", "Emerald+", "emerald.png"],
  ["diamond_plus", "Diamond+", "diamond.png"],
  ["master_plus", "Master+", "master.png"],
];

// Un colore per slot giocatore (1-5), stesso ordine di teamPools[team].players -
// cosi' le righe statistiche nella griglia si distinguono a colpo d'occhio
// senza dover leggere il tooltip ogni volta ("credevo lo giocasse lui...").
// Sfumatura fra i 3 blu gia' stabiliti nella palette (--sky-light/--sky-mid/
// --blue-dark) invece di 5 colori arbitrari a rotazione - richiesta
// esplicita dell'utente (2026-08-18) dopo aver alzato il limite giocatori a
// 10: con soli 5 colori, il 6* giocatore avrebbe ripetuto lo stesso colore
// del 1* (modulo), confondibili. Una sfumatura invece distribuisce N
// giocatori in proporzione lungo lo stesso gradiente, qualunque sia N (da 2
// a 10) - mai una ripetizione, e resta comunque riconoscibile "a occhio"
// grazie anche al nuovo filtro per singolo giocatore (non serve piu'
// distinguerli tutti a colpo d'occhio, solo isolare quello che serve).
const PLAYER_GRADIENT_STOPS = [
  [208, 225, 245], // --sky-light
  [174, 188, 232], // --sky-mid
  [67, 76, 146], // --blue-dark
];

function playerColorForFraction(t) {
  const seg = t <= 0.5 ? 0 : 1;
  const localT = t <= 0.5 ? t / 0.5 : (t - 0.5) / 0.5;
  const [r1, g1, b1] = PLAYER_GRADIENT_STOPS[seg];
  const [r2, g2, b2] = PLAYER_GRADIENT_STOPS[seg + 1];
  const r = Math.round(r1 + (r2 - r1) * localT);
  const g = Math.round(g1 + (g2 - g1) * localT);
  const b = Math.round(b1 + (b2 - b1) * localT);
  return `rgb(${r}, ${g}, ${b})`;
}

let champions = [];
let compMeta = {};

// Bordo colorato disegnato via CODICE invece che incorporato nei pixel
// dell'icona (richiesto esplicitamente dall'utente 2026-08-27, insieme al
// passaggio a icone "pulite" di Data Dragon - vedi scripts/sync_ddragon_icons.py
// e la nota su Champion.icon in data.py): un campione con tag/comp modificati
// in app (vedi il pannello "Modifica tag") deve aggiornare SUBITO il colore
// del bordo, cosa impossibile quando il colore era fisso nel file immagine.
//
// Stesso ordine/colori di COMP_COLORS in server.py (servito via
// /api/comp-meta, gia' caricato in compMeta) - un campione puo' appartenere
// a piu' comp contemporaneamente (Champion.comps e' un frozenset): questo
// ordine di priorita' decide quale colore mostrare quando il bordo puo'
// mostrarne uno solo. Nessuna richiesta esplicita su come risolvere i casi
// multipli - scelta ragionevole propria, facile da cambiare in futuro.
const COMP_BORDER_PRIORITY = [
  "TeamFight \\ WomboCombo",
  "Split",
  "Pick",
  "Poke \\ Siege",
  "Proteggi il presidente",
];

// Stesso identico elenco/ordine di TAG_COLUMNS in driftdraft/data.py -
// duplicato qui deliberatamente (stesso principio gia' in uso per
// TRAINING_ROLE_ORDER/ROLE_ORDER): questa e' una tassonomia fissa che
// cambia pochissimo, un secondo endpoint solo per esporla non varrebbe la
// complessita' - usato dall'editor tag (vedi renderTagEditorPanel) per
// mostrare le checkbox nello stesso ordine gia' familiare dall'xlsx.
const TAG_ORDER = [
  "Danno burst singolo",
  "Danno DPS singolo",
  "Danno burst AoE",
  "Danno DPS AoE",
  "Hard Engage singolo",
  "Hard Engage AoE",
  "Hard CC Singolo",
  "Hard CC AoE",
  "Mobilità",
  "Disingaggio",
  "Protezione \\ peeling",
  "Utility generica",
  "Long Range",
  "Waveclear",
  "Side forte",
];

// Tutti i colori delle comp a cui il campione appartiene (non solo il
// primo) - richiesto esplicitamente dall'utente (2026-08-27). Ordine =
// COMP_BORDER_PRIORITY - un campione in 1 sola comp ha un bordo di un
// colore solo, esattamente come prima.
function champCompBorderColors(champ) {
  if (!champ || !champ.comps) return [];
  return COMP_BORDER_PRIORITY.filter((comp) => champ.comps.includes(comp)).map(
    (comp) => compMeta[comp]?.color
  ).filter(Boolean);
}

const COMP_BORDER_WIDTH = 3;

// Un vero bordo (border-width/border-image), non piu' un box-shadow ad
// anelli concentrici - la primissima versione multi-comp (anelli
// concentrici) e' stata bocciata dall'utente subito dopo averla vista:
// "non si capisce praticamente niente in questo modo... vorrei che segui lo
// stile di come le avevo fatte io" - lo stile originale (icone bordate a
// mano, vedi assets/icons_bordered_backup_2026-08-27/) non impilava un
// colore sopra l'altro: divideva il PERIMETRO in spicchi, uno per comp
// (verificato aprendo Aatrox.png del backup: 3 comp -> bordo diviso in 3
// archi di ~120° ciascuno, non 3 anelli). conic-gradient() sul bordo
// replica esattamente questo - un solo colore = bordo pieno normale
// (border-color, niente sfumatura, piu' pulito per il caso piu' comune),
// 2+ colori = border-image con un conic-gradient a spicchi uguali.
// Ritorna le 3 custom property come oggetto - riusato sia per gli elementi
// DOM (applyCompBorderVar sotto) sia per la stringa inline di
// buildLaneFaceoffSection (che costruisce HTML via template literal, non
// elementi DOM, quindi non puo' chiamare .style.setProperty direttamente).
function champCompBorderVars(champ) {
  const colors = champCompBorderColors(champ);
  if (colors.length === 0) {
    return { width: "0px", color: "transparent", image: "none" };
  }
  if (colors.length === 1) {
    // "image" e' un colore solido espresso come gradient degenere (non
    // "none") apposta - richiesto esplicitamente dall'utente (2026-08-31,
    // screenshot di confronto): con "none" qui, .champion-card/
    // .team-slot.filled dovevano trattare mono/multi-comp con DUE tecniche
    // diverse (border-color nudo vs sfondo a 2 layer, vedi style.css),
    // finendo con spessori dell'anello diversi (il gap di padding proprio
    // della card restava scoperto solo nel caso multi). Un solo colore
    // "ripetuto" come gradient permette alla STESSA regola CSS di
    // gestire entrambi i casi in modo identico, spessore garantito
    // uguale per costruzione invece che per coincidenza.
    return { width: `${COMP_BORDER_WIDTH}px`, color: colors[0], image: `linear-gradient(${colors[0]}, ${colors[0]})` };
  }
  const step = 100 / colors.length;
  const stops = colors
    .map((color, i) => `${color} ${(i * step).toFixed(2)}% ${((i + 1) * step).toFixed(2)}%`)
    .join(", ");
  return { width: `${COMP_BORDER_WIDTH}px`, color: colors[0], image: `conic-gradient(${stops})` };
}

function applyCompBorderVar(el, champ) {
  const vars = champCompBorderVars(champ);
  el.style.setProperty("--comp-border-width", vars.width);
  el.style.setProperty("--comp-border-color", vars.color);
  el.style.setProperty("--comp-border-image", vars.image);
}
let activeFilters = new Set(); // condiviso tra le due squadre, filtra l'unica griglia
let teams = { left: [null, null, null, null, null], right: [null, null, null, null, null] };
let bans = { left: [null, null, null, null, null], right: [null, null, null, null, null] };
// In sospeso secondo il sito stesso (classe CSS pulse-animation-*, vedi
// drafter_live.py) - a differenza di tournamentPendingSlot (solo le NOSTRE
// azioni appena inviate), questo copre ANCHE le selezioni dell'avversario
// non ancora confermate, aggiornato ad ogni poll.
let picksPending = { left: [false, false, false, false, false], right: [false, false, false, false, false] };
let bansPending = { left: [false, false, false, false, false], right: [false, false, false, false, false] };
let activeSlot = null; // { team: "left"|"right", index: 0-4, kind: "pick"|"ban" } - dove finisce il prossimo click/drop
let searchText = "";
let expandedComps = { left: new Set(), right: new Set() }; // per squadra: comp aperte manualmente
let activeTagFilters = new Set(); // condiviso, come activeFilters
let activeRoleFilters = new Set(); // ruoli cliccati in alto a destra
let teamPools = { left: null, right: null }; // risultato di /api/opgg-team, null finche' non si preme "Aggiorna"
let activePoolFilters = new Set(); // "left"/"right" - quali pool INTERE squadra sono attive come filtro griglia
// Filtro per SINGOLO giocatore (uno alla volta per lato, come
// contextPlayerKey sotto - stessa ragione: durante una draft si guarda
// sempre la pool di UN giocatore preciso per UNO slot preciso, non l'unione
// di piu' pool). Richiesta esplicita dell'utente (2026-08-18): la pool
// intera squadra serve per scovare flex pick, ma serve ANCHE poter isolare
// un giocatore solo, per sapere con certezza "chi gioca cosa" in fase di
// ban/pick. Mutuamente esclusivo con activePoolFilters PER LATO (selezionare
// un giocatore disattiva "pool squadra" per quel lato e viceversa - averli
// entrambi attivi sarebbe ridondante, il giocatore e' gia' incluso nella
// pool intera, e mostrerebbe le sue righe statistiche due volte).
let activePlayerFilters = { left: null, right: null };

// Contesto draft: quale team salvato (roster) sta giocando questa partita, e
// quale suo giocatore e' attivo come filtro (tramite la SUA tierlist
// importata/manuale) - indipendente dal profilo aperto nel modale roster,
// che riguarda l'EDITING, non il filtro in griglia.
let contextTeamName = "";
let contextTeamData = null; // profilo completo {Top:[player,...], ...} del team selezionato
let contextPlayerKey = null; // "Ruolo|indice" del giocatore attivo, null = nessun filtro
// Risposta grezza di /api/opgg-roster-team per il team di contesto (stessa
// forma di /api/opgg-team: {pool, players}) - NON alimenta teamPools/pool-chip
// (quella e' un'altra funzione, il multisearch a mano sui pannelli Blue/Red
// Side): resta qui finche' non si clicca il tag di un giocatore specifico,
// che ne mostra SOLO i suoi dati (vedi contextPlayerOpggStats). Richiesta
// esplicita dell'utente (2026-08-19) dopo che la prima versione li mandava
// erroneamente sul pannello laterale.
let contextTeamOpggData = null;
// Soglia tier cumulativa (S=migliore...D=peggiore) sul giocatore di contesto
// attivo - null = nessuna soglia, tutte le tier incluse (comportamento
// originale). Vedi contextPlayerChampionSet.
let contextTierThreshold = null;
// "blue"/"red" scelto a mano per la MODALITA' LIBERA, null se non ancora
// deciso. Serve solo li': in allenamento il lato e' quello del trainee, in
// torneo quello connesso, e in entrambi i casi e' un dato autorevole che non
// va chiesto ne' indovinato. Si azzera ad ogni cambio di team - una scelta
// fatta per una squadra non vuol dire niente per un'altra.
let contextTeamSide = null;

// Ricerca counter: un campione di riferimento gia' in uno slot + un ruolo,
// contro cui confrontare ogni campione in griglia. Stato globale unico (non
// un Set) - una nuova ricerca sostituisce la precedente ("fino a prossima
// analisi", richiesta esplicita dell'utente).
//
// ENTRAMBE le fonti (winrate lolalytics + GD15 u.gg) vengono caricate
// INSIEME a ogni ricerca, non una sola in base al toggle - richiesta
// esplicita dell'utente 2026-08-24: il toggle "Counter corsia" deve solo
// CAMBIARE QUALE dei due dataset gia' scaricati viene mostrato (istantaneo,
// nessuna nuova richiesta di rete), non innescare un nuovo caricamento -
// "evitare fastidiosi caricamenti multipli ad ogni opzione". Due dataset
// separati invece di uno solo "attivo" perche' entrambi vanno tenuti vivi
// in memoria contemporaneamente (altrimenti il toggle richiederebbe comunque
// un fetch al cambio). Vedi activeCounterData()/activeCounterError() per il
// punto unico da cui si legge "quale dei due mostrare ora".
let counterModeChampion = null;
let counterModeRole = null;
let counterModeDataWinrate = null; // {nomeCampione: {champion, winrate, games}} - null finche' non arriva la risposta (o se lolalytics fallisce)
let counterModeDataGd15 = null; // {nomeCampione: {champion, gd15, games}} - null finche' non arriva la risposta (o se u.gg fallisce)
let counterModeErrorWinrate = null; // messaggio d'errore SOLO per il dataset winrate, null se andato a buon fine
let counterModeErrorGd15 = null; // messaggio d'errore SOLO per il dataset gd15, null se andato a buon fine
let counterModeSearchedTier = null; // fascia elo USATA per la ricerca ATTIVA (condivisa da entrambi i dataset) - vedi counterModeTier sotto
let counterSearchLoading = null; // {champion, role} della ricerca in corso, null se nessuna

// Fascia elo per la ricerca counter - impostazione persistente (sopravvive
// a un riavvio, come showCounterDiagram), NON resettata da resetAllFilters:
// e' una preferenza del coach su quale dato guardare, non un filtro sulla
// draft corrente. Si applica alla PROSSIMA ricerca, non a caldo su una
// ricerca gia' in corso - per questo e' distinta da counterModeSearchedTier
// sopra (quella e' la fascia con cui e' stata fatta la ricerca ATTIVA, puo'
// differire da questa se il coach la cambia senza rilanciare la ricerca).
let counterModeTier = localStorage.getItem("counterTier") || "emerald_plus";

// Counter di CORSIA (differenza oro a 15', fonte u.gg) invece del winrate
// generale (fonte lolalytics) - stessa natura di counterModeTier: preferenza
// persistente del coach, non un filtro sulla draft corrente. Richiesta
// esplicita dell'utente 2026-08-24 dopo aver trovato lui stesso la sezione
// "Best Lane Counters" su u.gg (non presente su lolalytics). Cambiare
// questo toggle NON fa piu' una nuova richiesta (vedi runCounterSearch) -
// sceglie solo quale dei due dataset gia' scaricati leggere qui sotto.
let laneCounterMode = localStorage.getItem("laneCounterMode") === "true";

// "Bordi comp" (richiesto esplicitamente dall'utente 2026-08-27: "alcuni
// coach semplicemente non usano questo sistema, e non vogliono
// confusione... aggiungere un'opzione con cui vedere/non vedere i bordi")
// - default ON (comportamento gia' visto prima di questo toggle). Applicata
// come classe su <body> (vedi setupCompBordersToggle) invece che ri-
// renderizzando ogni card: le custom property --comp-border-* restano
// impostate su ogni elemento a prescindere, questa preferenza ne nasconde
// solo la resa visiva via CSS.
let compBordersEnabled = localStorage.getItem("compBordersEnabled") !== "false";

// Punto UNICO da cui leggere "quale dataset/errore mostrare ora" - tutto il
// resto del codice (rendering griglia, ordinamento, tooltip) passa da qui
// invece di controllare laneCounterMode ripetutamente.
function activeCounterData() {
  return laneCounterMode ? counterModeDataGd15 : counterModeDataWinrate;
}
function activeCounterError() {
  return laneCounterMode ? counterModeErrorGd15 : counterModeErrorWinrate;
}

// Modalita' torneo: specchio in tempo reale di una draft VERA su drafter.lol
// (vedi drafter_live.py - sessione Playwright che resta connessa), PIU'
// l'invio delle nostre scelte come azioni vere (Fase 2). Quando connessi, un
// click in griglia durante il turno del nostro lato invia la selezione al
// sito vero (visibile all'avversario, non ancora bloccata) - il bottone
// "Conferma" blocca davvero, oppure ci pensa da solo il timeout del sito.
let tournamentModeSelectedSide = null; // "blue"/"red" scelto nel modale di connessione, prima di Connetti
let tournamentUrl = null; // ultimo URL usato per connettersi - serve a calcolare l'URL della game successiva (fearless draft, vedi advanceToNextGame)
// Fearless draft: {side, game, champion}[] cosi' come letto dal sito
// ("Used Champions This Series", funzione nuova di drafter.lol) - vuoto
// finche' non si e' connessi, azzerato alla disconnessione. side = lato di
// QUELLA game specifica (non un'identita' di squadra persistente), game =
// numero 1-based.
let fearlessPicks = [];
let tournamentConnected = false;
let tournamentPollTimer = null;
let tournamentLastPickSignature = ""; // per non ri-renderizzare la squadra ad ogni poll se nulla e' cambiato
let tournamentPendingSlot = null; // {team, index, kind, sentAt} appena inviato - mostra il lampeggio finche' non arriva conferma esplicita o scade il timeout di sicurezza
let tournamentConfirmInFlight = false; // true mentre una richiesta di conferma e' gia' in volo - evita di accodarne altre su piu' click
let tournamentSide = null; // "blue"/"red" del lato REALMENTE connesso (da state.side, autorevole)
let tournamentLastStep = ""; // testo fase piu' recente (es. "Blue ban 1"), aggiornato ad ogni poll
let tournamentIsReadyPhase = false; // state.buttonText del sito contiene "ready" - decide sia l'etichetta che dove instrada il click
let tournamentButtonDisabledReal = true; // rispecchia DIRETTAMENTE state.buttonDisabled del sito - unica fonte di verita' per abilitare/disabilitare il nostro bottone, in ogni fase
let tournamentButtonTextRaw = ""; // state.buttonText grezzo del sito (es. "Ready", "Ban", "Pick") - tradotto per l'etichetta del nostro bottone, mostrato cosi' com'e' se non riconosciuto

// "Valuta la draft" per la modalita' torneo (richiesto esplicitamente
// dall'utente 2026-08-26, stessa funzione gia' costruita per il training -
// vedi evaluateTrainingDraft/evaluateTournamentDraft). tournamentEvaluation
// azzerata alla disconnessione e ad ogni nuova game (fearless draft) - una
// valutazione vecchia non ha piu' senso per 10 pick diversi.
let tournamentEvaluation = null;
let tournamentEvaluateBusy = false;

// "Pick suggeriti" (richiesto esplicitamente dall'utente 2026-08-26 per la
// modalita' torneo: "dato che abbiamo un bot che capisce le risposte solite
// a determinati pick... implementiamo i pick suggeriti... si illuminano un
// pochino... poi sara' il coach a decidere cosa e' giusto prendere", poi
// ESTESO 2026-08-30 a training e modalita' normale: "devono funzionare
// anche fuori dalla modalità torneo") - stessa euristica sinergia/counter
// del bot di training, qui come un elenco/evidenziazione invece di una
// scelta automatica, UNA SOLA implementazione condivisa dalle 3 modalita'
// (stesso toggle, stessa evidenziazione in renderGrid - vedi
// refreshSuggestions per come cambia solo LA FONTE dei pick in base alla
// modalita' attiva). Persistito in localStorage (stesso principio di
// laneCounterMode) - se il coach lo attiva una volta, resta attivo sempre.
let suggestionsEnabled = localStorage.getItem("suggestionsEnabled") === "true";
// Un elenco per LATO (2026-09-06): gli stessi dati letti dalle due parti del
// tavolo - "possiamo individuare sia i pick che vanno a nostro vantaggio, ma
// non quelli che vanno a vantaggio del team nemico... in modo da anticipare
// ed individuare eventuali pick contesi". Arrivano gia' ordinati per
// punteggio decrescente dal server, che li calcola con la STESSA funzione
// chiamata due volte a parti invertite (vedi rank_pick_suggestions).
//
// BLU e ROSSO, non "noi" e "loro": fuori da torneo/training il lato nostro
// veniva indovinato dall'ultimo slot cliccato, e le due righe si scambiavano
// di significato senza dirlo. I lati invece si vedono. Un campione presente
// in tutti e due gli elenchi e' un pick CONTESO: l'intersezione la facciamo
// qui, vedi suggestionState.
// Filtro "solo pool op.gg" (2026-09-06): quando per un lato e' stata
// caricata la pool op.gg, la riga di quel lato mostra soltanto campioni che
// quel team gioca davvero - "in modo da poter selezionare i pick suggeriti e
// renderli ancora di meno, in base proprio a cosa il team nemico puo'
// giocare". Vale per LATO da quando le righe sono blu/rosso: non esiste piu'
// un lato "avversario" a priori, e il vincolo naturale di un lato e' la sua
// stessa pool. Acceso di default: chi si prende la briga di caricare una
// pool lo fa proprio per questo. Persistito come tutte le altre preferenze;
// il chip che lo comanda esiste solo quando almeno una pool c'e' davvero
// (vedi renderSuggestionsPanel).
let poolFilterEnabled = localStorage.getItem("poolFilterEnabled") !== "false";
let blueSuggestions = []; // [{champion, score, role}] buoni per il Blue Side
let redSuggestions = []; //  [{champion, score, role}] buoni per il Red Side
// "Dei candidati c'erano, ma tutti troppo poco osservati per dire qualcosa"
// (vedi MIN_SUPPORT lato Python). E' diverso da un elenco vuoto e basta:
// li' non c'e' proprio niente da dire, qui c'e' da dire che non si sa.
let blueThin = false;
let redThin = false;
let blueNames = new Set(); // stessi nomi, come Set - solo per un lookup rapido dentro renderGrid
let redNames = new Set();
// Numero di sequenza incrementato ad ogni fetch avviato: una risposta che
// arriva quando non e' piu' la piu' recente (es. due fetch quasi
// consecutivi per due cambi di stato ravvicinati, la prima risponde DOPO la
// seconda) va scartata invece di sovrascrivere un risultato piu' fresco -
// stesso principio di "ultima risposta vince, non ultima richiesta
// inviata" gia' visto altrove nel progetto per evitare race condition.
let suggestionsFetchSeq = 0;
let suggestionsDebounceTimer = null;

// Ruoli NEMICI - richiesto esplicitamente dall'utente (2026-08-26, dopo un
// caso reale osservato: "mi ha immesso Hecarim support anche se era il
// toplaner"), poi esteso ("viene usata in automatico, ma sempre dando la
// possibilità al coach di aggiustare... in modo da coprire entrambi i
// casi"): tournamentEnemyRoleOrder e' il valore VERO usato ad ogni
// "Valuta la draft" (5 nomi campione in ordine ROLE_ORDER), aggiornato con
// una priorita' a 3 livelli in updateTournamentEnemyRolesPanel - (1) il tag
// REALE del sito una volta che entrambi i lati passano la fase di conferma
// ruoli (vedi tournamentEnemyRoleTags sotto, e la nota su
// blueRoleTags/redRoleTags in drafter_live.py - trovato con un'indagine dal
// vivo apposta), (2) altrimenti l'indovinato assign_roles() via
// /api/live-draft/role-guess, (3) l'ordine di pick grezzo come seed
// immediato prima che (1)/(2) arrivino. tournamentEnemyRoleSource traccia
// da quale livello viene il valore CORRENTE - none finche' non seminato,
// "manual" appena il coach trascina UNA VOLTA, e a quel punto resta cosi'
// per sempre (nessun auto-aggiornamento successivo lo sovrascrive piu',
// nemmeno se il sito conferma qualcosa di diverso dopo - la correzione del
// coach vince sempre, e' esattamente il "sempre dando la possibilita' di
// aggiustare" richiesto).
let tournamentEnemyRoleOrder = null;
let tournamentEnemyRoleSource = null; // null | "raw" | "guess" | "site" | "manual"
// Ultimo blueRoleTags/redRoleTags letto dal poll (vedi pollTournamentState) -
// 5 etichette ("Top"/"Jungle"/.../null se non ancora confermato), nell'ORDINE
// DI PICK del lato nemico (NON gia' riordinate per ROLE_ORDER) - cache
// dell'ultimo dato fresco, stesso principio gia' usato per
// tournamentButtonTextRaw/tournamentRoleConfirmLive.
let tournamentEnemyRoleTags = null;

// Ruoli NOSTRI - richiesto esplicitamente dall'utente (2026-08-30: "sto
// notando che diversi team non selezionano, dopo la modalità torneo, i pick
// nell'ordine giusto, quindi voglio poterli impostare io personalmente...
// i pick per entrambe le squadre"). Fino ad ora SOLO tournamentConfirmedRoleOrder
// esisteva per il nostro lato (vedi confirmRoleOrder), popolato SOLO se la
// fase di role confirmation VERA del sito viene affrontata dal vivo durante
// la draft - stesso punto debole gia' visto e risolto per il lato nemico
// (assign_roles() da solo non e' affidabile). tournamentOwnRoleOrder/
// tournamentOwnRoleSource/tournamentOwnRoleTags sono lo STESSO identico
// meccanismo a priorita' gia' costruito per tournamentEnemyRoleOrder qui
// sopra (site tag passivo -> guess -> raw -> manual assorbente), applicato
// simmetricamente al nostro lato invece che al nemico - vedi
// updateTournamentOwnRolesPanel/renderTournamentOwnRoles. A differenza del
// nemico, qui c'e' ANCHE tournamentConfirmedRoleOrder come fonte
// aggiuntiva: quando presente (la conferma vera e' avvenuta) resta la fonte
// piu' autorevole di tutte tranne una correzione manuale esplicita - vedi
// evaluateTournamentDraft per come le due fonti si combinano.
let tournamentOwnRoleOrder = null;
let tournamentOwnRoleSource = null; // null | "raw" | "guess" | "site" | "manual"
let tournamentOwnRoleTags = null;

// Role confirmation (dopo i 20 pick/ban - vedi sezione dedicata nelle note
// di progetto): il coach riordina localmente i 5 pick del nostro lato in
// DriftDraft (nessuna fretta, e' tutto locale finche' non si preme
// "Conferma ruoli"), poi la replica sul sito vero avviene in un colpo solo.
let tournamentRoleConfirmLive = false; // state.roleConfirmActive dell'ultimo poll - true SOLO quando la fase di drag e' davvero apparsa sul sito (serve anche l'avversario pronto, non solo noi)
let roleConfirmOriginalOrder = null; // ordine pick del nostro lato al momento in cui e' apparsa la fase - mai piu' toccato, e' la base per calcolare le mosse da replicare
let roleConfirmOrder = null; // copia locale modificabile via drag, null finche' la fase non e' rilevata in questa connessione
let roleConfirmInFlight = false;
// Ultimo ordine ruoli confermato con successo SUL SITO VERO (vedi
// confirmRoleOrder) - a differenza di roleConfirmOriginalOrder (la bozza
// PRIMA del drag, mai toccata) o roleConfirmOrder (azzerato non appena la
// fase finisce, vedi updateRoleConfirmPanel), questo sopravvive fino alla
// prossima connessione/game: e' quello che evaluateTournamentDraft passa al
// server per sapere davvero quale pick va in quale corsia, invece di
// affidarsi all'indovinato assign_roles() lato server.
let tournamentConfirmedRoleOrder = null;
const ROLE_CONFIRM_LANES = ["Top", "Jungle", "Mid", "Bottom", "Support"]; // stesso ordine/nomi delle corsie data-role-confirm-lane sul sito

// Modalita' training (feature 4): allenamento vs un bot che sceglie in base
// a tabelle sinergia/counter aggregate da draft pro recenti (Leaguepedia,
// vedi driftdraft/leaguepedia.py e training_bot.py). A differenza di
// "modalita' torneo" non c'e' nessun sito esterno con un proprio ritmo -
// ogni mossa e' sincrona: la risposta di /api/training/pick include GIA'
// l'eventuale mossa immediata del bot, niente polling.
let trainingConnected = false;
let trainingState = null; // ultima risposta di /api/training/(start|pick|state|rewind)
let trainingModeSelected = null; // "team" | "freeform" scelto nel modale, prima di iniziare
// Contro chi allenarsi: "" = a sorte (la tira il server, che sa quali squadre
// ha), oppure il nome di una squadra. Le due possibilita' volute dall'utente -
// a sorte per allenarsi contro qualcosa di imprevisto, scelta per prepararsi a
// un avversario preciso - stanno in un solo controllo, con "Casuale" come
// prima voce dell'elenco.
let trainingTeamSelected = "";
let trainingTeamsCache = null; // elenco da /api/training/teams, caricato una volta
let trainingSideSelected = null; // "blue" | "red" scelto nel modale
// Campione cliccato in griglia ma non ancora confermato (vedi
// selectTrainingPending/confirmTrainingPick) - richiesta esplicita
// dell'utente 2026-08-26: un click non deve piu' bannare/pickare subito,
// solo selezionare, per evitare errori da click involontario.
let trainingPendingChampion = null;
// true mentre una richiesta (conferma pick, o rewind) e' in volo - copre
// anche il ritardo deliberato "il bot sta pensando" lato server (vedi
// BOT_THINK_DELAY_MIN/MAX in training_bot.py), la richiesta resta aperta per
// tutta quella durata. Blocca nuove selezioni/conferme/rewind nel frattempo.
let trainingBusy = false;
// Ordine (Top/Jungle/Mid/Bot/Support) dei 5 pick del TRAINEE, SOLO a draft
// finita - bozza locale trascinabile, seminata dal suggerimento automatico
// del server la prima volta che si vede "finished", poi lasciata alle
// modifiche dell'utente finche' non la conferma (vedi
// confirmTrainingRoleOrder). null fuori dalla fase finale o dopo un rewind
// (che azzera anche quella salvata server-side, vedi rewind_to). Richiesta
// esplicita dell'utente 2026-08-26: vuole decidere lui quali dei suoi
// campioni vanno dove, per un passo successivo non ancora specificato.
let trainingRoleOrder = null;
const TRAINING_ROLE_ORDER = ["Top", "Jungle", "Mid", "Bot", "Support"]; // stesso ordine di ROLE_ORDER in training_bot.py

// Risultato di /api/training/evaluate (vedi evaluateTrainingDraft) - null
// finche' non si preme "Valuta la draft" (bottone #training-confirm
// riusato a draft finita, vedi updateTrainingConfirmButton). Richiesta
// esplicita dell'utente 2026-08-26: curve winrate/durata-partita per
// corsia, aggregate in blu/rosso/verde - vedi driftdraft/draft_evaluation.py
// per il design completo.
let trainingEvaluation = null;

const TIER_LABELS = ["S", "A", "B", "C", "D"];
let rosterProfiles = []; // nomi dei profili-team salvati
let rosterCurrentProfileName = null; // profilo aperto ora nel modale (null = non ancora salvato)
let rosterDraftName = ""; // nome mostrato/editabile nel campo di testo, salvato solo al click su Salva
let rosterDraft = null; // { Top: [player,...], Jungle: [...], ... } - copia locale, scartata se si chiude senza salvare
// Fotografia della bozza com'era all'ultimo salvataggio (o all'apertura di
// un profilo): serve solo a sapere se c'e' qualcosa da perdere prima di
// buttarla via. Confronto per stringa JSON invece che campo per campo -
// un roster e' piccolo (5 ruoli, pochi giocatori, cinque tier di nomi) e
// una struttura ricorsiva da confrontare a mano si dimentica sempre di un
// ramo quando il modello cresce.
let rosterSavedSnapshot = null;
let rosterActiveRole = "Top";
let rosterActivePlayerIndex = -1; // indice in rosterDraft[rosterActiveRole], -1 = nessun giocatore selezionato
let rosterActiveTier = "S";
let rosterSearchText = "";
let rosterRoleFilterOn = true;

function allPickedNames() {
  return [...teams.left, ...teams.right].filter(Boolean);
}

function allBannedNames() {
  return [...bans.left, ...bans.right].filter(Boolean);
}

// Quanti "Aggiorna" op.gg sono in corso adesso. Serve a bloccare lo scambio
// Blue/Red mentre uno scraping e' ancora aperto: il risultato si salva sul
// lato catturato al momento del click, quindi scambiare a meta' caricamento
// metterebbe il link da una parte e la sua pool dall'altra. Lo scraping dura
// diversi secondi (Playwright), quindi non e' un caso teorico.
let poolLoadsInFlight = 0;

function setupPoolImport(team) {
  const input = document.getElementById(`pool-url-${team}`);
  const btn = document.getElementById(`pool-refresh-${team}`);

  btn.addEventListener("click", async () => {
    const url = input.value.trim();
    if (!url) return;

    btn.disabled = true;
    btn.textContent = "...";
    poolLoadsInFlight++;
    updatePoolSwapButtons();
    let result;
    try {
      result = await backend.fetchOpggTeam(url);
    } finally {
      // finally e non dopo l'await: se la richiesta lancia, il contatore deve
      // scendere lo stesso, altrimenti lo scambio resterebbe bloccato per
      // sempre. Stessa cosa per il bottone, che prima restava su "...".
      poolLoadsInFlight--;
      updatePoolSwapButtons();
      btn.disabled = false;
      btn.textContent = "Aggiorna";
    }

    if (result.error) {
      teamPools[team] = null;
      activePoolFilters.delete(team);
      renderPoolChip(team, result.error);
    } else {
      teamPools[team] = result;
      renderPoolChip(team);
    }
    renderGrid();
    // Se e' la pool della squadra di FRONTE, i suggerimenti avversari ora
    // possono restringersi a quello che quel team gioca davvero.
    refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
  });
}

// Scambia gli op.gg fra Blue e Red Side - richiesta esplicita dell'utente
// (2026-09-11): per simulare la stessa sfida dall'altro lato senza ricopiare
// i due link a mano. Scambia anche le pool GIA' CARICATE e i filtri attivi,
// non solo il testo dei campi: altrimenti servirebbero due "Aggiorna", cioe'
// due scraping op.gg da diversi secondi l'uno, per ritrovarsi con gli stessi
// dati di prima.
//
// Il bottone c'e' su entrambi i pannelli e fa la stessa cosa: il layout e'
// speculare ovunque (vedi il tema su Blue e lo slider su Red), e chi prepara
// una draft guarda il lato su cui sta lavorando, non l'altro.
function swapPoolSides() {
  if (poolLoadsInFlight > 0) return; // vedi poolLoadsInFlight

  const inputLeft = document.getElementById("pool-url-left");
  const inputRight = document.getElementById("pool-url-right");
  [inputLeft.value, inputRight.value] = [inputRight.value, inputLeft.value];

  // Un errore di caricamento non vive nello stato ma solo nella sua chip:
  // lo si legge da li' e lo si riscrive dall'altra parte, insieme al link
  // che l'ha causato. Senza, il link sbagliato cambierebbe lato e l'errore
  // sparirebbe, facendolo sembrare buono.
  const erroreDi = (team) =>
    document.querySelector(`#pool-chip-${team} .pool-chip.error`)?.textContent || null;
  const erroreLeft = erroreDi("left");
  const erroreRight = erroreDi("right");

  [teamPools.left, teamPools.right] = [teamPools.right, teamPools.left];
  [activePlayerFilters.left, activePlayerFilters.right] = [
    activePlayerFilters.right,
    activePlayerFilters.left,
  ];
  const squadraLeftAttiva = activePoolFilters.has("left");
  const squadraRightAttiva = activePoolFilters.has("right");
  activePoolFilters.delete("left");
  activePoolFilters.delete("right");
  if (squadraRightAttiva) activePoolFilters.add("left");
  if (squadraLeftAttiva) activePoolFilters.add("right");

  renderPoolChip("left", erroreRight);
  renderPoolChip("right", erroreLeft);
  renderGrid();
  refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
}

function updatePoolSwapButtons() {
  for (const team of ["left", "right"]) {
    document.getElementById(`pool-swap-${team}`).disabled = poolLoadsInFlight > 0;
  }
}

function setupPoolSwap() {
  for (const team of ["left", "right"]) {
    document.getElementById(`pool-swap-${team}`).addEventListener("click", swapPoolSides);
  }
}

function renderPoolChip(team, errorMessage) {
  const el = document.getElementById(`pool-chip-${team}`);
  el.innerHTML = "";

  if (errorMessage) {
    const chip = document.createElement("span");
    chip.className = "pool-chip error";
    chip.textContent = errorMessage;
    el.appendChild(chip);
    return;
  }

  const data = teamPools[team];
  if (!data) return;

  const chip = document.createElement("span");
  chip.className = "pool-chip" + (activePoolFilters.has(team) ? " active" : "");
  chip.textContent = `Pool squadra (${Object.keys(data.pool).length})`;
  chip.title = data.players.map((p) => p.summoner).join(", ");
  chip.addEventListener("click", () => {
    if (activePoolFilters.has(team)) {
      activePoolFilters.delete(team);
    } else {
      activePoolFilters.add(team);
      activePlayerFilters[team] = null; // mutuamente esclusivo, vedi nota sopra sulla dichiarazione
    }
    renderPoolChip(team);
    renderGrid();
  });
  el.appendChild(chip);

  // Sotto-chip per singolo giocatore - stesso pattern visivo/interattivo
  // dei tag funzionali dentro una comp-card (richiesto esplicitamente
  // dall'utente come riferimento). Mostra solo il nome (senza #TAG, gia'
  // disponibile per intero nel tooltip) per restare compatto.
  const playersEl = document.createElement("div");
  playersEl.className = "player-chips";
  for (const player of data.players) {
    const pChip = document.createElement("span");
    pChip.className =
      "player-chip" + (activePlayerFilters[team] === player.summoner ? " active" : "");
    pChip.textContent = player.summoner.split("#")[0];
    pChip.title = player.summoner;
    // Stesso colore stabile per giocatore gia' usato in .pool-stats-row -
    // qui come bordo (non sfondo pieno, la chip resta piccola e va letta
    // anche da spenta) cosi' si riconosce a colpo d'occhio quale giocatore
    // e' quale, coerente col resto della UI.
    pChip.style.borderColor = playerColor(team, player.summoner);
    pChip.addEventListener("click", () => {
      if (activePlayerFilters[team] === player.summoner) {
        activePlayerFilters[team] = null;
      } else {
        activePlayerFilters[team] = player.summoner;
        activePoolFilters.delete(team); // mutuamente esclusivo
      }
      renderPoolChip(team);
      renderGrid();
    });
    playersEl.appendChild(pChip);
  }
  el.appendChild(playersEl);
}

function anyPoolFilterActive() {
  return activePoolFilters.size > 0 || !!activePlayerFilters.left || !!activePlayerFilters.right;
}

function emptyRosterDraft() {
  return { Top: [], Jungle: [], Mid: [], Bot: [], Support: [] };
}

function currentPlayer() {
  const list = rosterDraft[rosterActiveRole];
  return rosterActivePlayerIndex >= 0 && rosterActivePlayerIndex < list.length
    ? list[rosterActivePlayerIndex]
    : null;
}

function rosterSnapshot() {
  return JSON.stringify({ name: rosterDraftName, draft: rosterDraft });
}

// C'e' del lavoro non salvato? Falso anche quando non c'e' nessuna bozza
// aperta (modale mai aperto), cosi' chi chiama non deve controllarlo.
function rosterIsDirty() {
  return rosterDraft !== null && rosterSavedSnapshot !== null && rosterSnapshot() !== rosterSavedSnapshot;
}

async function loadRosterProfile(name) {
  rosterDraft = await backend.getRosterProfile(name);
  rosterCurrentProfileName = name;
  rosterDraftName = name;
  rosterActiveRole = "Top";
  rosterActivePlayerIndex = rosterDraft.Top.length > 0 ? 0 : -1;
  rosterSavedSnapshot = rosterSnapshot();
  rosterActiveTier = "S";
}

function startBlankRosterDraft() {
  rosterCurrentProfileName = null;
  rosterDraftName = "";
  rosterDraft = emptyRosterDraft();
  rosterActiveRole = "Top";
  rosterActivePlayerIndex = -1;
  rosterActiveTier = "S";
  rosterSavedSnapshot = rosterSnapshot();
}

async function openRosterModal() {
  rosterProfiles = (await backend.listRosterProfiles()).profiles;
  if (rosterProfiles.length > 0) {
    await loadRosterProfile(rosterProfiles[0]);
  } else {
    startBlankRosterDraft();
  }
  rosterSearchText = "";
  document.getElementById("roster-search").value = "";
  document.getElementById("roster-modal").classList.remove("hidden");
  renderRosterModal();
}

// Salva la bozza corrente. Torna true se e' andata: chi chiama (il bottone
// "Salva", ma anche "Salva ed esci" dell'avviso) deve poter distinguere un
// salvataggio riuscito da uno rifiutato, per non chiudere il modale sopra un
// errore.
async function saveRosterDraft() {
  const newName = rosterDraftName.trim();
  if (!newName) {
    alert("Assegna un nome al team prima di salvare (scrivilo nel campo in alto).");
    return false;
  }

  // se il nome e' cambiato rispetto a un profilo gia' salvato, rinomina prima di salvare
  if (rosterCurrentProfileName && newName !== rosterCurrentProfileName) {
    const renameResult = await backend.renameRosterProfile(rosterCurrentProfileName, newName);
    if (renameResult.error) {
      alert(renameResult.error);
      return false;
    }
  }

  const result = await backend.saveRosterProfile(newName, rosterDraft);
  if (result.error) {
    alert(result.error);
    return false;
  }
  rosterProfiles = result.profiles;
  rosterCurrentProfileName = newName;
  rosterDraftName = newName;
  rosterSavedSnapshot = rosterSnapshot();
  renderRosterProfileSelect();
  return true;
}

// Mostra l'avviso e aspetta la scelta: "save" | "discard" | "cancel".
// Promessa invece di confirm() perche' le scelte sono TRE - "vuoi uscire
// oppure salvare i dati?" ha bisogno anche di un "ho sbagliato a cliccare",
// e un confirm nativo ne offre solo due.
function askRosterUnsaved() {
  const veil = document.getElementById("roster-unsaved");
  const text = document.getElementById("roster-unsaved-text");
  const name = rosterDraftName.trim();
  text.textContent = name
    ? `Le modifiche a "${name}" non sono salvate. Vuoi salvarle prima di uscire?`
    : "Le modifiche a questo team non sono salvate. Vuoi salvarle prima di uscire?";
  veil.classList.remove("hidden");

  return new Promise((resolve) => {
    const buttons = [
      ["roster-unsaved-save", "save"],
      ["roster-unsaved-discard", "discard"],
      ["roster-unsaved-cancel", "cancel"],
    ];
    const handlers = [];
    const finish = (choice) => {
      for (const [el, fn] of handlers) el.removeEventListener("click", fn);
      veil.classList.add("hidden");
      resolve(choice);
    };
    for (const [id, choice] of buttons) {
      const el = document.getElementById(id);
      const fn = () => finish(choice);
      el.addEventListener("click", fn);
      handlers.push([el, fn]);
    }
  });
}

// Da chiamare PRIMA di qualunque cosa butti via la bozza corrente (chiudere
// il modale, cambiare team, iniziarne uno nuovo): torna false se l'utente ha
// annullato, o se il salvataggio che ha chiesto non e' riuscito.
// Richiesta dell'utente (2026-09-06): "sarebbe il caso di aggiungere una
// sottospecie di notifica se si esce dalla schermata senza salvare i dati".
// Il cambio team e "Nuovo" sono la stessa perdita da un'altra porta: la
// bozza spariva li' esattamente come chiudendo, e senza dire niente.
async function confirmRosterDiscard() {
  if (!rosterIsDirty()) return true;
  const choice = await askRosterUnsaved();
  if (choice === "cancel") return false;
  if (choice === "save") return await saveRosterDraft();
  return true;
}

async function closeRosterModal() {
  if (!(await confirmRosterDiscard())) return;
  closeRosterCombos();
  document.getElementById("roster-modal").classList.add("hidden");
  rosterDraft = null; // le modifiche non salvate vengono scartate
  rosterSavedSnapshot = null;
  refreshContextTeamOptions();
}

function renderRosterModal() {
  // Cambia cio' che gli elenchi stanno mostrando: lasciarli aperti sopra
  // dati vecchi e' peggio che richiuderli.
  closeRosterCombos();
  renderRosterProfileSelect();
  renderRosterRoleTabs();
  renderRosterPlayerSelect();
  renderRosterTierRows();
  renderRosterGrid();
}

function renderRosterProfileSelect() {
  // Un solo campo al posto di <select>+campo di testo separato che
  // mostravano lo stesso nome due volte - richiesta esplicita dell'utente
  // (2026-08-18): "perche' la nostra deve avere due sezioni con lo stesso
  // dato che appesantiscono solo la GUI?". Il campo resta uno solo, ma dal
  // 2026-09-06 fa un mestiere solo: mostra e RINOMINA il team aperto. Per
  // sceglierne un altro c'e' la freccia (vedi setupCombo).
  document.getElementById("roster-profile-combo").value = rosterDraftName;
}

function renderRosterRoleTabs() {
  const el = document.getElementById("roster-role-tabs");
  el.innerHTML = "";
  for (const [role, iconFile] of ROLE_ICONS) {
    const tab = document.createElement("div");
    tab.className = "roster-role-tab" + (role === rosterActiveRole ? " active" : "");
    const img = document.createElement("img");
    img.src = `/assets/role_icons/${encodeURIComponent(iconFile)}`;
    tab.appendChild(img);
    const label = document.createElement("span");
    const count = rosterDraft[role].length;
    label.textContent = role + (count > 0 ? ` (${count})` : "");
    tab.appendChild(label);
    tab.addEventListener("click", () => {
      closeRosterCombos(); // l'elenco giocatori e' per ruolo: quello aperto non vale piu'
      rosterActiveRole = role;
      rosterActivePlayerIndex = rosterDraft[role].length > 0 ? 0 : -1;
      rosterActiveTier = "S";
      renderRosterPlayerSelect();
      renderRosterTierRows();
      renderRosterGrid();
      renderRosterRoleTabs();
    });
    el.appendChild(tab);
  }
}

function renderRosterPlayerSelect() {
  // Stesso campo unico di renderRosterProfileSelect sopra, stessa ragione e
  // stessa divisione dei compiti: qui si rinomina il giocatore aperto, con
  // la freccia se ne sceglie un altro.
  //
  // L'elenco lo costruisce setupCombo al momento dell'apertura, e a
  // differenza della vecchia datalist NON salta i giocatori senza nome:
  // erano irraggiungibili: contavano nel totale del ruolo ("Mid (2)") ma
  // non comparivano da nessuna parte, quindi non si potevano ne' aprire ne'
  // cancellare. Segnalato dall'utente proprio cosi'.
  const comboInput = document.getElementById("roster-player-combo");
  const player = currentPlayer();
  comboInput.value = player ? player.name : "";
  comboInput.disabled = !player;

  const riotIdInput = document.getElementById("roster-player-riotid");
  riotIdInput.value = player ? player.riot_id || "" : "";
  riotIdInput.disabled = !player;
}

// Toglie il campione da qualunque tier ce l'avesse e lo mette in quella
// indicata - usata sia dal click che dal drag&drop, cosi' trascinare
// un'icona GIA' piazzata in un altro tier la sposta invece di duplicarla.
function assignChampToTier(player, champName, tier) {
  for (const t of TIER_LABELS) {
    player.tiers[t] = player.tiers[t].filter((n) => n !== champName);
  }
  player.tiers[tier].push(champName);
}

function renderRosterTierRows() {
  const el = document.getElementById("roster-tier-rows");
  el.innerHTML = "";
  const player = currentPlayer();

  for (const tier of TIER_LABELS) {
    const row = document.createElement("div");
    row.className = "tier-row" + (tier === rosterActiveTier ? " active" : "");

    const label = document.createElement("div");
    label.className = "tier-label";
    label.textContent = tier;
    row.appendChild(label);

    const champsEl = document.createElement("div");
    champsEl.className = "tier-champs";
    if (player) {
      for (const name of player.tiers[tier]) {
        const champ = champions.find((c) => c.name === name);
        if (!champ) continue;

        // Avvolta in un div draggable (stesso pattern di .champion-card in
        // renderRosterGrid, che GIA' funziona) invece di rendere l'img
        // stessa draggable - richiesta esplicita dell'utente (2026-08-19):
        // trascinare un campione GIA' piazzato da una tier all'altra non
        // funzionava, a differenza di trascinarlo qui da nuovo dalla
        // griglia sotto. Causa: l'img aveva ENTRAMBI draggable=true E
        // -webkit-user-drag:none sullo STESSO elemento - la proprieta'
        // sopprime il drag nativo del browser, ma a quanto pare anche
        // quello custom quando e' la STESSA immagine a doverlo avviare
        // (mai un problema per .champion-card, dove draggable vive sul div
        // contenitore e -webkit-user-drag:none solo sull'img figlia).
        const wrap = document.createElement("div");
        wrap.className = "tier-champ-wrap";
        wrap.title = `${name} - clicca per rimuovere, trascina per spostare`;
        wrap.draggable = true;
        applyCompBorderVar(wrap, champ);

        const img = document.createElement("img");
        img.className = "tier-champ";
        img.src = champ.icon;
        wrap.appendChild(img);

        wrap.addEventListener("dragstart", (e) => {
          e.dataTransfer.setData("text/plain", name);
        });
        wrap.addEventListener("click", (e) => {
          e.stopPropagation();
          player.tiers[tier] = player.tiers[tier].filter((n) => n !== name);
          renderRosterTierRows();
          renderRosterGrid();
        });
        champsEl.appendChild(wrap);
      }
    }
    row.appendChild(champsEl);

    row.addEventListener("click", () => {
      rosterActiveTier = tier;
      renderRosterTierRows();
    });

    row.addEventListener("dragover", (e) => {
      e.preventDefault();
      row.classList.add("drag-over");
    });
    row.addEventListener("dragleave", () => {
      row.classList.remove("drag-over");
    });
    row.addEventListener("drop", (e) => {
      e.preventDefault();
      row.classList.remove("drag-over");
      if (!player) return;
      const champName = e.dataTransfer.getData("text/plain");
      if (!champions.some((c) => c.name === champName)) return;
      rosterActiveTier = tier;
      assignChampToTier(player, champName, tier);
      renderRosterTierRows();
      renderRosterGrid();
    });

    el.appendChild(row);
  }
}

function renderRosterGrid() {
  const grid = document.getElementById("roster-champion-grid");
  grid.innerHTML = "";

  const player = currentPlayer();
  const assigned = player ? new Set(Object.values(player.tiers).flat()) : new Set();

  const filtered = champions.filter((c) => {
    if (rosterSearchText && !c.name.toLowerCase().includes(rosterSearchText)) return false;
    if (rosterRoleFilterOn && !c.roles.includes(rosterActiveRole)) return false;
    return true;
  });

  for (const champ of filtered) {
    const card = document.createElement("div");
    card.className = "champion-card" + (assigned.has(champ.name) ? " assigned" : "");
    card.title = champ.name;
    card.draggable = true;
    applyCompBorderVar(card, champ);

    const img = document.createElement("img");
    img.src = champ.icon;
    img.alt = champ.name;
    img.loading = "lazy";
    card.appendChild(img);

    card.addEventListener("click", () => {
      if (!player) return; // nessun giocatore selezionato per questo ruolo
      assignChampToTier(player, champ.name, rosterActiveTier);
      renderRosterTierRows();
      renderRosterGrid();
    });

    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", champ.name);
    });

    grid.appendChild(card);
  }
}

// Combobox costruito a mano, usato dai due menu del modale roster (team e
// giocatori). Sostituisce <input list=datalist> (2026-09-06).
//
// Il datalist nativo e' un AUTOCOMPLETE, non un menu: filtra sempre le voci
// sul testo gia' presente nel campo. Con un nome scritto dentro - che e' la
// norma, il campo mostra sempre il team/giocatore aperto - l'elenco si
// riduceva ai soli nomi che gli somigliavano, ed era esattamente la
// discrepanza segnalata dall'utente: "se si preme al centro appaiono solo
// nomi gia' immessi, invece se si preme alla freccia appaiono tutti". La
// freccia mostrava tutto solo perche' un giro precedente aveva aggiunto uno
// svuotamento del campo prima di aprire il picker, apposta per aggirare quel
// filtro. Due gesti, due risultati diversi, nessuno dei due spiegabile.
//
// Il vero problema sotto pero' era un altro: lo stesso campo faceva DUE
// mestieri. Scrivere un nome che combaciava esattamente con un altro
// elemento non lo rinominava, ci SALTAVA SOPRA - quindi non si poteva ne'
// capire in che modalita' si stesse (suggerimenti o roba gia' immessa, come
// ha notato l'utente) ne' rinominare qualcosa dandogli un nome esistente.
//
// Qui i due gesti sono separati e non si sovrappongono:
//   - il CAMPO rinomina cio' che e' selezionato, e non cambia mai selezione;
//   - la FRECCIA apre l'elenco COMPLETO, sempre lo stesso, mai filtrato.
//
// getOptions() viene richiamata ad ogni apertura (non una volta sola alla
// costruzione): l'elenco dei giocatori cambia col ruolo attivo, e quello dei
// team ad ogni salvataggio.
function setupCombo(rootId, getOptions, onPick, opzioni = {}) {
  // `opzioni.filtra`: scrivere nel campo FILTRA l'elenco invece di chiuderlo.
  // I due combobox del roster non lo vogliono - li' scrivere e' rinominare, e
  // un elenco aperto sopra darebbe solo fastidio - mentre quello delle
  // squadre pro sceglie fra 197 voci, dove senza ricerca l'elenco e' inutile.
  const filtra = !!opzioni.filtra;
  const root = document.getElementById(rootId);
  const input = root.querySelector("input[type='text']");
  const arrow = root.querySelector(".combo-arrow");
  const list = root.querySelector(".combo-list");

  const isOpen = () => !list.classList.contains("hidden");

  // mousedown in cattura, non click: cosi' l'elenco si chiude anche quando
  // il click finisce su qualcosa che ferma la propagazione o che sparisce
  // sotto il puntatore prima del click vero.
  const onAway = (e) => {
    if (!root.contains(e.target)) close();
  };

  function close() {
    list.classList.add("hidden");
    document.removeEventListener("mousedown", onAway, true);
  }

  function open() {
    list.innerHTML = "";
    const options = getOptions(filtra ? input.value.trim() : "");
    if (options.length === 0) {
      const empty = document.createElement("div");
      empty.className = "combo-empty";
      empty.textContent = "Niente da scegliere";
      list.appendChild(empty);
    }
    for (const opt of options) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "combo-option" + (opt.current ? " current" : "");

      const name = document.createElement("span");
      name.className = "combo-option-name" + (opt.label ? "" : " empty");
      name.textContent = opt.label || "(senza nome)";
      btn.appendChild(name);

      // Riga secondaria: e' cio' che rende distinguibili due omonimi, che
      // col solo nome erano la stessa identica voce.
      if (opt.sub) {
        const sub = document.createElement("span");
        sub.className = "combo-option-sub";
        sub.textContent = opt.sub;
        btn.appendChild(sub);
      }

      btn.addEventListener("click", () => {
        close();
        onPick(opt.key);
      });
      list.appendChild(btn);
    }
    list.classList.remove("hidden");
    document.addEventListener("mousedown", onAway, true);
  }

  arrow.addEventListener("click", () => (isOpen() ? close() : open()));
  // Escape sulla RADICE, non sul solo campo di testo: dopo un click sulla
  // freccia il fuoco resta sul bottone, e li' un listener sull'input non
  // vedrebbe mai il tasto - cioe' proprio nel percorso normale (si apre
  // l'elenco con la freccia). Trovato provandolo: col fuoco nel campo
  // funzionava, dalla freccia no.
  root.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isOpen()) {
      e.stopPropagation();
      close();
    }
  });
  // Scrivere nel campo e' una rinomina: l'elenco aperto sopra darebbe solo
  // fastidio (e non si aggiorna, non essendo un filtro). Dove invece il campo
  // e' una ricerca, scrivere riapre l'elenco gia' filtrato.
  input.addEventListener("input", () => (filtra ? open() : close()));

  root.closeComboList = close;
}

// Chiude entrambi gli elenchi del modale: serve quando cambia sotto di loro
// cio' che stanno mostrando (cambio ruolo, cambio profilo, salvataggio).
function closeRosterCombos() {
  for (const id of ["roster-profile-picker", "roster-player-picker"]) {
    document.getElementById(id).closeComboList?.();
  }
}

// Editor tag in-app (richiesto esplicitamente dall'utente 2026-08-27: "non
// tutti hanno excel sul proprio pc... vorrei introdurre un modo per dare
// modo ai coach di poter modificare i tag direttamente in app") - salva via
// /api/champion-tags in un file JSON separato da champions.xlsx (vedi
// driftdraft/champion_overrides.py per il perche'), MAI una scrittura
// diretta nell'xlsx. Nessuno stato "bozza non salvata" qui a differenza di
// altri editor in questo file (roster, ruoli torneo): ogni Salva/Ripristina
// e' immediato, non c'e' un "Annulla" - stessa filosofia di una semplice
// pagina di impostazioni, non di una draft in corso dove un errore costa
// una scelta reale.
let tagEditorSelectedChampion = null;

async function openTagEditorModal() {
  document.getElementById("tag-editor-search").value = "";
  tagEditorSelectedChampion = null;
  document.getElementById("tag-editor-panel").classList.add("hidden");
  renderTagEditorChampList();
  document.getElementById("tag-editor-modal").classList.remove("hidden");
}

function closeTagEditorModal() {
  document.getElementById("tag-editor-modal").classList.add("hidden");
}

function renderTagEditorChampList() {
  const listEl = document.getElementById("tag-editor-champ-list");
  listEl.innerHTML = "";
  const search = document.getElementById("tag-editor-search").value.trim().toLowerCase();
  const filtered = champions.filter((c) => !search || c.name.toLowerCase().includes(search));
  for (const champ of filtered) {
    const row = document.createElement("div");
    row.className = "tag-editor-champ-row" + (champ.name === tagEditorSelectedChampion ? " active" : "");
    const img = document.createElement("img");
    img.src = champ.icon;
    img.alt = champ.name;
    applyCompBorderVar(img, champ);
    row.appendChild(img);
    const label = document.createElement("span");
    label.textContent = champ.name;
    row.appendChild(label);
    row.addEventListener("click", () => selectTagEditorChampion(champ.name));
    listEl.appendChild(row);
  }
}

function renderTagEditorChecks(containerId, allValues, currentValues) {
  const el = document.getElementById(containerId);
  el.innerHTML = "";
  for (const value of allValues) {
    const label = document.createElement("label");
    label.className = "tag-editor-check";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = value;
    input.checked = currentValues.includes(value);
    label.appendChild(input);
    label.append(value);
    el.appendChild(label);
  }
}

function collectTagEditorChecks(containerId) {
  return [...document.getElementById(containerId).querySelectorAll("input:checked")].map((i) => i.value);
}

function selectTagEditorChampion(name) {
  tagEditorSelectedChampion = name;
  renderTagEditorChampList(); // solo per aggiornare l'evidenziazione "active" nella lista
  const champ = champions.find((c) => c.name === name);
  if (!champ) return;

  document.getElementById("tag-editor-panel").classList.remove("hidden");
  document.getElementById("tag-editor-champ-name").textContent = champ.name;
  document.getElementById("tag-editor-champ-icon").src = champ.icon;
  setTagEditorStatus("");

  renderTagEditorChecks("tag-editor-comps", COMP_BORDER_PRIORITY, champ.comps);
  renderTagEditorChecks("tag-editor-roles", TRAINING_ROLE_ORDER, champ.roles);
  renderTagEditorChecks("tag-editor-tags", TAG_ORDER, champ.tags);
}

// Ricarica /api/champions dopo un salvataggio/reset e ri-renderizza tutto
// cio' che dipende dall'elenco campioni - un tag modificato deve
// aggiornarsi SUBITO ovunque (griglia, slot pick/ban, comp rilevate, bordo
// colorato...), non solo al prossimo riavvio dell'app. Non tocca la
// modalita' torneo/training (i loro pick gia' fatti restano quelli che
// sono, solo l'aspetto/i dati dei campioni ancora in griglia cambiano).
async function refreshChampionsAfterTagEdit() {
  champions = await backend.getChampions();
  renderGrid();
  renderTeam("left");
  renderTeam("right");
  refreshDetection("left");
  refreshDetection("right");
}

function setTagEditorStatus(text, kind) {
  const statusEl = document.getElementById("tag-editor-status");
  statusEl.textContent = text;
  statusEl.className = kind || "";
}

async function saveTagEditorChampion() {
  if (!tagEditorSelectedChampion) return;
  setTagEditorStatus("Salvo...");
  const result = await backend.saveChampionTags(
    tagEditorSelectedChampion,
    collectTagEditorChecks("tag-editor-comps"),
    collectTagEditorChecks("tag-editor-tags"),
    collectTagEditorChecks("tag-editor-roles")
  );
  if (result.error) {
    setTagEditorStatus(`Errore: ${result.error}`, "error");
    return;
  }
  await refreshChampionsAfterTagEdit();
  selectTagEditorChampion(tagEditorSelectedChampion); // ri-legge i dati aggiornati nello stesso pannello
  setTagEditorStatus("✓ Salvato.", "success");
}

async function resetTagEditorChampion() {
  if (!tagEditorSelectedChampion) return;
  setTagEditorStatus("Ripristino...");
  const result = await backend.resetChampionTags(tagEditorSelectedChampion);
  if (result.error) {
    setTagEditorStatus(`Errore: ${result.error}`, "error");
    return;
  }
  await refreshChampionsAfterTagEdit();
  selectTagEditorChampion(tagEditorSelectedChampion);
  setTagEditorStatus("✓ Ripristinato ai valori di Excel.", "success");
}

function setupTagEditorModal() {
  document.getElementById("edit-tags-open").addEventListener("click", openTagEditorModal);
  document.getElementById("tag-editor-close").addEventListener("click", closeTagEditorModal);
  document.getElementById("tag-editor-search").addEventListener("input", renderTagEditorChampList);
  document.getElementById("tag-editor-save").addEventListener("click", saveTagEditorChampion);
  document.getElementById("tag-editor-reset").addEventListener("click", resetTagEditorChampion);
}

function setupRosterModal() {
  document.getElementById("roster-open").addEventListener("click", openRosterModal);
  document.getElementById("roster-close").addEventListener("click", closeRosterModal);
  // Elenco dei team: sempre completo, con quello aperto marcato.
  setupCombo(
    "roster-profile-picker",
    () =>
      rosterProfiles.map((name) => ({
        key: name,
        label: name,
        current: name === rosterCurrentProfileName,
      })),
    async (name) => {
      if (name === rosterCurrentProfileName) return;
      // Cambiare team butta via la bozza corrente tanto quanto chiudere.
      if (!(await confirmRosterDiscard())) return;
      await loadRosterProfile(name);
      renderRosterModal();
    }
  );

  // Elenco dei giocatori del ruolo attivo. La chiave e' l'INDICE, non il
  // nome: e' cio' che rende raggiungibili sia i giocatori senza nome sia
  // due omonimi (che per la vecchia datalist erano la stessa voce). Il Riot
  // ID va in seconda riga proprio per distinguerli.
  setupCombo(
    "roster-player-picker",
    () =>
      rosterDraft[rosterActiveRole].map((p, i) => ({
        key: i,
        label: p.name,
        sub: p.riot_id || "(nessun Riot ID)",
        current: i === rosterActivePlayerIndex,
      })),
    (index) => {
      rosterActivePlayerIndex = index;
      rosterActiveTier = "S";
      renderRosterPlayerSelect();
      renderRosterTierRows();
      renderRosterGrid();
    }
  );

  document.getElementById("roster-search").addEventListener("input", (e) => {
    rosterSearchText = e.target.value.toLowerCase();
    renderRosterGrid();
  });

  document.getElementById("roster-role-filter-toggle").addEventListener("change", (e) => {
    rosterRoleFilterOn = e.target.checked;
    renderRosterGrid();
  });

  // --- profilo (team) ---
  // Scrivere qui e' SOLO una rinomina in bozza del team aperto (o il nome
  // di uno nuovo). Fino al 2026-09-06 scrivere un nome che combaciava
  // esattamente con un altro team ci saltava sopra invece di rinominare -
  // serviva perche' scegliere dalla datalist arrivava qui sotto forma di
  // "input", indistinguibile dal digitare. Ora la scelta ha il suo canale
  // (setupCombo sopra) e questo puo' fare una cosa sola.
  document.getElementById("roster-profile-combo").addEventListener("input", (e) => {
    rosterDraftName = e.target.value;
  });

  document.getElementById("roster-profile-new").addEventListener("click", async () => {
    if (!(await confirmRosterDiscard())) return;
    startBlankRosterDraft();
    renderRosterModal();
    document.getElementById("roster-profile-combo").focus();
  });

  document.getElementById("roster-profile-save").addEventListener("click", saveRosterDraft);

  document.getElementById("roster-profile-delete").addEventListener("click", async () => {
    if (!rosterCurrentProfileName) return;
    if (!confirm(`Eliminare il profilo "${rosterCurrentProfileName}"?`)) return;
    const result = await backend.deleteRosterProfile(rosterCurrentProfileName);
    rosterProfiles = result.profiles;
    if (rosterProfiles.length > 0) {
      await loadRosterProfile(rosterProfiles[0]);
    } else {
      startBlankRosterDraft();
    }
    renderRosterModal();
  });

  // --- giocatore (nel ruolo corrente) ---
  // Come per il team: qui si rinomina e basta. Prima scrivere il nome di un
  // altro giocatore dello stesso ruolo ci saltava sopra, il che rendeva
  // impossibile dare a due giocatori lo stesso nome... e allo stesso tempo
  // era proprio cosi' che due omonimi finivano indistinguibili. I giocatori
  // non hanno un passo "rinomina" via API come i profili: il nome si salva
  // insieme al resto quando si preme Salva.
  document.getElementById("roster-player-combo").addEventListener("input", (e) => {
    const player = currentPlayer();
    if (player) player.name = e.target.value;
  });

  document.getElementById("roster-player-new").addEventListener("click", () => {
    rosterDraft[rosterActiveRole].push({
      name: "",
      riot_id: "",
      tiers: { S: [], A: [], B: [], C: [], D: [] },
    });
    rosterActivePlayerIndex = rosterDraft[rosterActiveRole].length - 1;
    rosterActiveTier = "S";
    renderRosterRoleTabs();
    renderRosterPlayerSelect();
    renderRosterTierRows();
    renderRosterGrid();
    document.getElementById("roster-player-combo").focus();
  });

  document.getElementById("roster-player-delete").addEventListener("click", () => {
    if (rosterActivePlayerIndex < 0) return;
    rosterDraft[rosterActiveRole].splice(rosterActivePlayerIndex, 1);
    rosterActivePlayerIndex = rosterDraft[rosterActiveRole].length > 0 ? 0 : -1;
    renderRosterRoleTabs();
    renderRosterPlayerSelect();
    renderRosterTierRows();
    renderRosterGrid();
  });

  document.getElementById("roster-player-riotid").addEventListener("input", (e) => {
    const player = currentPlayer();
    if (player) player.riot_id = e.target.value;
  });

  // --- importa tierlist da screenshot (rilevamento locale, vedi
  // tierlist_detect.py) - sostituisce le tier del giocatore corrente col
  // risultato, ma SOLO nel draft locale: va sempre rivisto/corretto a mano
  // nell'editor sotto prima di premere Salva, mai fidarsi ciecamente. ---
  document.getElementById("roster-tierlist-import").addEventListener("click", () => {
    if (!currentPlayer()) {
      alert("Seleziona prima un giocatore (o creane uno nuovo).");
      return;
    }
    document.getElementById("roster-tierlist-file").click();
  });

  document.getElementById("roster-tierlist-file").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const preview = document.getElementById("roster-tierlist-preview");
    preview.src = URL.createObjectURL(file);
    preview.classList.add("visible");

    const status = document.getElementById("roster-tierlist-status");
    status.textContent = "Rilevamento in corso...";

    const player = currentPlayer();
    if (!player) return;

    const formData = new FormData();
    formData.append("image", file);

    let result;
    try {
      result = await fetch("/api/detect-tierlist", { method: "POST", body: formData }).then((r) =>
        r.json()
      );
    } catch (err) {
      status.textContent = "Errore di rete durante il rilevamento.";
      return;
    }

    if (result.error) {
      status.textContent = result.error;
      return;
    }

    let total = 0;
    for (const tier of TIER_LABELS) {
      player.tiers[tier] = result.tiers[tier] || [];
      total += player.tiers[tier].length;
    }
    status.textContent = `${total} campioni rilevati - controlla e correggi sotto prima di Salvare.`;

    renderRosterTierRows();
    renderRosterGrid();
  });
}

// Azzera tutti i filtri/ricerche attivi sulla griglia campioni per poterne
// avviare una pulita - NON tocca i campioni gia' piazzati in squadra (quello
// e' un annullamento della draft, non della ricerca) ne' i dati gia'
// scaricati (pool op.gg, team di contesto), solo lo stato attivo dei filtri.
function resetAllFilters() {
  searchText = "";
  document.getElementById("search").value = "";

  activeFilters.clear();
  activeTagFilters.clear();
  activeRoleFilters.clear();
  activePoolFilters.clear();
  activePlayerFilters = { left: null, right: null };
  contextPlayerKey = null;
  contextTierThreshold = null;
  counterModeChampion = null;
  counterModeRole = null;
  counterModeDataWinrate = null;
  counterModeDataGd15 = null;
  counterModeErrorWinrate = null;
  counterModeErrorGd15 = null;
  counterModeSearchedTier = null;
  counterSearchLoading = null;
  closeCounterPopover();

  renderRoleFilters();
  renderPoolChip("left");
  renderPoolChip("right");
  renderContextPlayerFilters();
  renderContextTierFilters();
  renderTeam("left");
  renderTeam("right");
  refreshDetection("left");
  refreshDetection("right");
  renderGrid();
}

// Prima configurazione: le immagini dei campioni non stanno piu' nel
// pacchetto (vedi driftdraft/champion_art.py), quindi al primo avvio non ce
// n'e' nessuna. Si scaricano qui, prima di disegnare qualunque cosa: la
// griglia senza icone sembrerebbe un'app rotta, non un'attesa.
//
// Torna sempre, anche in caso di errore: senza immagini l'app e' brutta ma
// funziona (tag, comp, suggerimenti e bot non dipendono dalle icone), quindi
// un CDN irraggiungibile non deve impedire di lavorare.
async function ensureChampionArt() {
  const overlay = document.getElementById("art-setup");
  const fill = document.getElementById("art-setup-fill");
  const count = document.getElementById("art-setup-count");
  const text = document.getElementById("art-setup-text");
  const retry = document.getElementById("art-setup-retry");

  let stato;
  try {
    stato = await backend.championArtStatus();
  } catch (e) {
    return; // se non risponde nemmeno questo, il resto dell'avvio lo dira'
  }
  if (!stato || !stato.missing) return;

  overlay.classList.remove("hidden");

  return new Promise((resolve) => {
    let finito = false;
    const chiudi = () => {
      if (finito) return;
      finito = true;
      overlay.classList.add("hidden");
      resolve();
    };

    const mostraErrore = (messaggio) => {
      text.innerHTML = messaggio;
      retry.classList.remove("hidden");
    };

    const avvia = async () => {
      retry.classList.add("hidden");
      text.innerHTML =
        "Scarico le immagini dei campioni da Data Dragon.<br>" +
        "Si fa una volta sola: restano sul tuo computer.";
      count.textContent = "";
      fill.style.width = "0%";
      const r = await backend.championArtSync();
      if (r && r.error) {
        mostraErrore("Non sono riuscito ad avviare lo scaricamento.<br>" + r.error);
        return;
      }
      sonda();
    };

    const sonda = async () => {
      if (finito) return;
      let p;
      try {
        p = await backend.championArtProgress();
      } catch (e) {
        setTimeout(sonda, 600);
        return;
      }
      if (p.total) {
        // `done` e' quante ne ha FINITE; il nome mostrato e' quella in corso.
        fill.style.width = `${Math.round((p.done / p.total) * 100)}%`;
        count.textContent = `${p.done} / ${p.total}${p.champion ? " — " + p.champion : ""}`;
      }
      if (p.phase === "fatto") {
        const falliti = (p.failed || []).length;
        if (falliti) {
          // Qualcuna non e' arrivata: si va avanti lo stesso, ma va detto -
          // un campione senza icona altrimenti sembra un bug dell'app.
          mostraErrore(
            `${falliti} immagini non sono state scaricate. ` +
              "Puoi riprovare ora oppure continuare: si riscaricano al prossimo avvio."
          );
          return;
        }
        chiudi();
        return;
      }
      if (p.phase === "errore") {
        mostraErrore("Scaricamento non riuscito.<br>" + (p.error || ""));
        return;
      }
      setTimeout(sonda, 400);
    };

    retry.addEventListener("click", avvia);
    document.getElementById("art-setup-skip").addEventListener("click", chiudi);
    avvia();
  });
}

async function init() {
  await ensureChampionArt();
  [champions, compMeta] = await Promise.all([
    backend.getChampions(),
    backend.getCompMeta(),
  ]);
  renderRoleFilters();
  renderCounterTierToggle();
  renderGrid();
  renderTeam("left");
  renderTeam("right");
  setupRosterModal();
  setupTagEditorModal();
  setupPoolImport("left");
  setupPoolImport("right");
  setupPoolSwap();
  await setupContextBar();
  await Promise.all([refreshDetection("left"), refreshDetection("right")]);

  document.getElementById("search").addEventListener("input", (e) => {
    searchText = e.target.value.toLowerCase();
    renderGrid();
  });

  document.addEventListener("click", (e) => {
    if (e.target.closest(".slot-counter-btn") || e.target.closest(".counter-role-popover")) return;
    closeCounterPopover();
  });

  document.getElementById("reset-filters").addEventListener("click", resetAllFilters);
  setupSuggestionsToggle();
  setupTournamentMode();
  setupTrainingMode();
  setupIconSizeSlider();
  setupSidebarSizeSlider();
  setupThemeToggle();
  setupCounterDiagramToggle();
  setupLaneCounterToggle();
  setupCompBordersToggle();
  setupSaveDraftPopovers();
  setupSavedDraftsViewer();

  renderCounterDiagram();
}

// Dimensione icone griglia (1x-2x) - preferenza puramente personale, non
// "giusta/sbagliata" (richiesta esplicita dell'utente), quindi persistita
// per utente/macchina via localStorage invece che fissata nel CSS.
function setupIconSizeSlider() {
  const slider = document.getElementById("icon-size-slider");
  const saved = parseFloat(localStorage.getItem("iconScale"));
  const initial = Number.isFinite(saved) ? Math.min(2, Math.max(1, saved)) : 2;
  slider.value = initial;
  document.documentElement.style.setProperty("--icon-scale", initial);
  slider.addEventListener("input", () => {
    document.documentElement.style.setProperty("--icon-scale", slider.value);
    localStorage.setItem("iconScale", slider.value);
  });
}

// Larghezza pannelli laterali (1x-2x, default 1.2 = "leggermente piu'
// larghi" richiesto dall'utente) - stessa logica/pattern di
// setupIconSizeSlider sopra, stessa ragione (preferenza personale, non
// "giusta/sbagliata"). I due lati restano sempre identici fra loro: un solo
// slider/variabile controlla entrambe le colonne in #app.
function setupSidebarSizeSlider() {
  const slider = document.getElementById("sidebar-size-slider");
  const saved = parseFloat(localStorage.getItem("sidebarScale"));
  const initial = Number.isFinite(saved) ? Math.min(2, Math.max(1, saved)) : 1.2;
  slider.value = initial;
  document.documentElement.style.setProperty("--sidebar-scale", initial);
  slider.addEventListener("input", () => {
    document.documentElement.style.setProperty("--sidebar-scale", slider.value);
    localStorage.setItem("sidebarScale", slider.value);
  });
}

// Tema chiaro/scuro (richiesto dall'utente 2026-09-05: "in modo che ognuno
// può immettere la sua preferenza"). Lo SCURO resta il default - e' il tema
// per cui la UI e' stata disegnata e quello che l'utente stessa preferisce:
// il chiaro si ottiene aggiungendo la classe `theme-light` su <body>, che in
// style.css ridefinisce i token di colore (vedi il blocco in fondo a quel
// file). Nessuna regola sparsa da tenere allineata: qui si tocca solo la
// classe.
//
// Persistito in localStorage come ogni altra preferenza di aspetto (icone,
// larghezza pannelli, bordi comp): la finestra dell'app gira con
// private_mode=False apposta perche' sopravvivano ai riavvii - vedi main.py.
//
// L'icona mostra la DESTINAZIONE, non lo stato corrente (col tema scuro
// attivo si vede il sole, cioe' "portami alla luce"): e' la convenzione piu'
// diffusa e la piu' leggibile su un bottone che sta da solo, senza etichetta.
function applyTheme(light) {
  // La classe va su <html>, NON su <body>: --text/--text-dim e le ombre
  // --nm-out/--nm-in sono dichiarate su :root come alias di altre
  // variabili, e una custom property che ne contiene un'altra viene
  // risolta sull'elemento dove e' DICHIARATA, poi ereditata gia'
  // calcolata. Con la classe su <body> quelle derivate restavano
  // ferme ai valori del tema scuro (testo azzurro chiaro su fondo
  // chiaro, illeggibile - bug visto dal vivo). Sullo stesso elemento
  // di :root, invece, la cascata le ricalcola tutte.
  document.documentElement.classList.toggle("theme-light", light);
  const btn = document.getElementById("theme-toggle");
  btn.textContent = light ? "\u{1F319}" : "\u{2600}\u{FE0F}";
  btn.title = light ? "Passa al tema scuro" : "Passa al tema chiaro";
}

function setupThemeToggle() {
  let light = localStorage.getItem("themeLight") === "true";
  applyTheme(light);
  document.getElementById("theme-toggle").addEventListener("click", () => {
    light = !light;
    localStorage.setItem("themeLight", light);
    applyTheme(light);
  });
}

// Mostra/nascondi il diagramma "Counter naturali" - solo un aiuto per
// neofiti secondo l'utente, quindi opzionale. Nasconde solo il corpo
// (#counter-diagram-body), MAI il titolo/interruttore stesso - altrimenti
// non ci sarebbe piu' modo di riaccenderlo.
function setupCounterDiagramToggle() {
  const toggle = document.getElementById("counter-diagram-toggle");
  const body = document.getElementById("counter-diagram-body");
  const saved = localStorage.getItem("showCounterDiagram");
  const initial = saved === null ? true : saved === "true";
  toggle.checked = initial;
  body.classList.toggle("hidden", !initial);
  toggle.addEventListener("change", () => {
    body.classList.toggle("hidden", !toggle.checked);
    localStorage.setItem("showCounterDiagram", toggle.checked);
  });
}

// "Counter corsia" (u.gg) vs winrate generale (lolalytics) - stesso
// interruttore mobile gia' usato per "Counter naturali" sopra, valore
// iniziale da laneCounterMode (gia' letto da localStorage all'avvio, vedi
// dichiarazione della variabile). NON rilancia una ricerca - richiesta
// esplicita dell'utente 2026-08-24: entrambi i dataset sono gia' stati
// scaricati insieme dall'ultima ricerca (vedi runCounterSearch), il toggle
// si limita a cambiare quale dei due leggere (activeCounterData()) e a
// ridisegnare. Se il dataset appena scelto e' vuoto per un errore avuto in
// quella singola fonte (l'altra puo' essere andata a buon fine), avvisa qui
// - non al momento della ricerca, altrimenti interromperebbe il coach con
// un popup per un errore su una fonte che magari non stava nemmeno
// guardando in quel momento.
// Applica subito lo stato corrente di compBordersEnabled alla classe su
// <body> - chiamata sia da setupCompBordersToggle() (al change) sia da
// init() (per partire gia' nello stato giusto, senza aspettare un click).
function applyCompBordersPreference() {
  document.body.classList.toggle("comp-borders-off", !compBordersEnabled);
}

function setupCompBordersToggle() {
  const toggle = document.getElementById("comp-borders-toggle");
  toggle.checked = compBordersEnabled;
  applyCompBordersPreference();
  toggle.addEventListener("change", () => {
    compBordersEnabled = toggle.checked;
    localStorage.setItem("compBordersEnabled", compBordersEnabled);
    applyCompBordersPreference();
    // Da quando questa preferenza spegne anche il ragionamento per comp nei
    // pick suggeriti (vedi _comp_flags lato server), il pannello va rifatto
    // subito: altrimenti si preme e non cambia niente fino al pick dopo.
    refreshSuggestions();
  });
}

function setupLaneCounterToggle() {
  // Chip, non piu' <input type=checkbox>: lo stato acceso e' la classe
  // .active (premuta), come per ogni altro filtro della toolbar.
  const toggle = document.getElementById("lane-counter-toggle");
  toggle.classList.toggle("active", laneCounterMode);
  toggle.addEventListener("click", () => {
    laneCounterMode = !laneCounterMode;
    toggle.classList.toggle("active", laneCounterMode);
    localStorage.setItem("laneCounterMode", laneCounterMode);
    renderTeam("left");
    renderTeam("right");
    renderGrid();
    if (counterModeChampion && !activeCounterData() && activeCounterError()) {
      alert(activeCounterError());
    }
  });
}

// I counter naturali fra le comp NON stanno piu' qui: vivono in
// driftdraft/comps.py (COMP_INNER_CYCLE/COMP_OUTER_CYCLE) e arrivano dentro
// compMeta via /api/comp-meta. Il motivo del trasloco: da quando anche il
// BOT ragiona per comp, la stessa relazione serve a Python, e due copie che
// col tempo divergono sono un modo garantito di far dire al diagramma una
// cosa e al bot un'altra. Le frecce restano colorate come il nodo di
// PARTENZA, cioe' chi counter-a.
function compCycles() {
  const inner = [];
  const outer = [];
  for (const [comp, meta] of Object.entries(compMeta)) {
    if (meta.innerBeats) inner.push([comp, meta.innerBeats]);
    if (meta.outerBeats) outer.push([comp, meta.outerBeats]);
  }
  return { inner, outer };
}

function renderCounterDiagram() {
  const el = document.getElementById("counter-diagram");
  const size = 240;
  const cx = size / 2;
  const cy = size / 2;
  const r = 92;

  // ordine in senso orario a partire dall'alto, stesso layout del riferimento
  const order = [
    "TeamFight \\ WomboCombo",
    "Pick",
    "Proteggi il presidente",
    "Poke \\ Siege",
    "Split",
  ];
  const shortLabel = {
    "TeamFight \\ WomboCombo": "Teamfight",
    "Pick": "Pick",
    "Proteggi il presidente": "Protect",
    "Poke \\ Siege": "Poke/Siege",
    "Split": "Split",
  };

  const boxH = 24;
  const gap = 5; // piccolo spazio in piu' tra la punta della freccia e il bordo

  const pos = {};
  order.forEach((comp, i) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
    const label = shortLabel[comp];
    const w = Math.max(58, label.length * 7 + 16);
    pos[comp] = {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
      halfW: w / 2 + gap,
      halfH: boxH / 2 + gap,
    };
  });

  // Punto in cui una retta uscente dal centro del rettangolo (cx,cy, halfW,
  // halfH) in direzione (dx,dy) esce dal suo bordo - cosi' ogni freccia si
  // ferma esattamente al bordo della scatola, qualunque sia la sua larghezza
  // e l'angolo di arrivo, invece di un accorciamento fisso che andava bene
  // solo per alcune combinazioni.
  function edgePoint(box, dx, dy) {
    if (dx === 0 && dy === 0) return { x: box.x, y: box.y };
    const scaleX = dx !== 0 ? box.halfW / Math.abs(dx) : Infinity;
    const scaleY = dy !== 0 ? box.halfH / Math.abs(dy) : Infinity;
    const scale = Math.min(scaleX, scaleY);
    return { x: box.x + dx * scale, y: box.y + dy * scale };
  }

  let arrows = "";
  const { inner, outer } = compCycles();
  for (const [from, to] of [...inner, ...outer]) {
    const a = pos[from];
    const b = pos[to];
    const color = compMeta[from]?.color || "#888";
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const start = edgePoint(a, dx, dy);
    const end = edgePoint(b, -dx, -dy);
    arrows += `<line x1="${start.x}" y1="${start.y}" x2="${end.x}" y2="${end.y}" stroke="${color}" stroke-width="2" marker-end="url(#arrow-${color.slice(1)})" />`;
  }

  const defs = order
    .map((comp) => {
      const color = compMeta[comp]?.color || "#888";
      const id = `arrow-${color.slice(1)}`;
      return `<marker id="${id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${color}" /></marker>`;
    })
    .join("");

  let boxes = "";
  for (const comp of order) {
    const { x, y, halfW } = pos[comp];
    const color = compMeta[comp]?.color || "#888";
    const label = shortLabel[comp];
    const w = (halfW - gap) * 2;
    boxes += `
      <rect x="${x - w / 2}" y="${y - 12}" width="${w}" height="24" rx="5" fill="var(--nm-surface)" stroke="${color}" stroke-width="1.5" />
      <text x="${x}" y="${y + 4}" text-anchor="middle" font-size="10" fill="var(--text)">${label}</text>
    `;
  }

  el.innerHTML = `
    <svg viewBox="0 0 ${size} ${size}" width="100%">
      <defs>${defs}</defs>
      ${arrows}
      ${boxes}
    </svg>
  `;
}

function renderRoleFilters() {
  const el = document.getElementById("role-filters");
  el.innerHTML = "";
  for (const [role, iconFile] of ROLE_ICONS) {
    const btn = document.createElement("div");
    btn.className = "role-filter" + (activeRoleFilters.has(role) ? " active" : "");
    btn.title = role;

    const img = document.createElement("img");
    img.src = `/assets/role_icons/${encodeURIComponent(iconFile)}`;
    img.alt = role;
    btn.appendChild(img);

    btn.addEventListener("click", () => {
      if (activeRoleFilters.has(role)) {
        activeRoleFilters.delete(role);
      } else {
        activeRoleFilters.add(role);
      }
      renderRoleFilters();
      renderGrid();
    });
    el.appendChild(btn);
  }
}

// Fascia elo per la ricerca counter - toggle SEMPRE visibile in toolbar,
// affianco ai filtri ruolo (non dentro il popover "cerca counter": un coach
// la sceglie una volta in base al livello del team che sta allenando, non
// ad ogni singola ricerca - richiesta esplicita dell'utente 2026-08-24,
// prima versione la metteva nel popover e serviva un click di troppo).
// Selezione singola (radio-like), non un Set multiplo come activeRoleFilters:
// una ricerca ha sempre e solo UNA fascia elo.
function renderCounterTierToggle() {
  const el = document.getElementById("counter-tier-toggle");
  el.innerHTML = "";
  for (const [tierValue, tierLabel, iconFile] of RANK_TIERS) {
    const btn = document.createElement("div");
    btn.className = "role-filter" + (counterModeTier === tierValue ? " active" : "");
    btn.title = tierLabel;

    const img = document.createElement("img");
    img.src = `/assets/rank_icons/${encodeURIComponent(iconFile)}`;
    img.alt = tierLabel;
    btn.appendChild(img);

    btn.addEventListener("click", () => {
      counterModeTier = tierValue;
      localStorage.setItem("counterTier", tierValue);
      renderCounterTierToggle();
    });
    el.appendChild(btn);
  }
}

// Rilegge l'elenco team salvati e ripopola il menu, preservando la
// selezione corrente se il team esiste ancora (es. dopo aver creato/salvato
// un ALTRO team nel modale roster - un rename/eliminazione del team che era
// selezionato qui azzera invece la selezione, comportamento sicuro di
// default piuttosto che inseguire il nuovo nome).
async function refreshContextTeamOptions() {
  const profiles = (await backend.listRosterProfiles()).profiles;
  const sel = document.getElementById("context-team-select");
  const current = sel.value;

  sel.innerHTML = '<option value="">Nessun team selezionato</option>';
  for (const name of profiles) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    sel.appendChild(opt);
  }

  if (profiles.includes(current)) {
    sel.value = current;
  } else {
    contextTeamName = "";
    contextTeamData = null;
    contextPlayerKey = null;
    contextTierThreshold = null;
    contextTeamSide = null;
    contextTeamOpggData = null;
    document.getElementById("context-team-opgg-status").textContent = "";
    renderContextPlayerFilters();
    renderContextTierFilters();
    renderGrid();
  }
}

async function setupContextBar() {
  await refreshContextTeamOptions();

  document.getElementById("context-team-select").addEventListener("change", async (e) => {
    contextTeamName = e.target.value;
    contextPlayerKey = null;
    contextTierThreshold = null;
    contextTeamOpggData = null;
    contextTeamSide = null;
    document.getElementById("context-team-opgg-status").textContent = "";
    contextTeamData = contextTeamName ? await backend.getRosterProfile(contextTeamName) : null;
    renderContextPlayerFilters();
    renderContextTierFilters();
    renderContextSideChip();
    renderGrid();
    refreshSuggestions();
    if (contextTeamName) {
      // Il lato si chiede SUBITO, e il caricamento op.gg parte in parallelo.
      // Prima la domanda aspettava la fine del caricamento, e in quei secondi
      // il promemoria nella barra era gia' li': si poteva rispondere e poi
      // vedersi arrivare il dialogo lo stesso. Le tier list, che sono l'unica
      // cosa a cui il lato serve, non c'entrano niente con op.gg - quello
      // alimenta le statistiche per giocatore sulla griglia, un'altra cosa.
      // Chiedere prima toglie l'attesa e la doppia domanda insieme.
      const caricamento = refreshContextTeamOpgg();
      await chiediLatoSeServe(contextTeamName);
      await caricamento;
    }
  });

  document.getElementById("context-side-chip").addEventListener("click", async () => {
    if (!contextTeamName) return;
    const scelta = await askContextSide(contextTeamName);
    contextTeamSide = scelta;
    renderContextSideChip();
    refreshSuggestions();
  });

  document
    .getElementById("context-team-opgg-refresh")
    .addEventListener("click", refreshContextTeamOpgg);
}

// Scarica la pool op.gg (storico completo, un fetch per titolare - vedi
// fetch_player_champions in opgg.py) dei 5 titolari del team di contesto.
// NON alimenta teamPools/pool-chip (quella e' un'altra funzione, il
// multisearch a mano sui pannelli Blue/Red Side, rimasta invariata) - i
// dati restano in contextTeamOpggData finche' non si clicca il tag di un
// giocatore specifico accanto al menu team (vedi contextPlayerOpggStats),
// che ne mostra SOLO i suoi campioni/winrate sulla griglia. Richiamata sia
// al cambio team sia dal pulsante di refresh manuale.
// Il team ha almeno una tier list vera? Se non ne ha nessuna, chiedere il
// lato non servirebbe a niente: il profilo non verrebbe usato comunque (la
// stessa guardia sta lato server in _our_profile_arg, qui e' solo per non
// fare una domanda inutile). I campioni in D non contano: valgono zero.
function teamHasTierLists() {
  if (!contextTeamData) return false;
  return Object.values(contextTeamData).some((players) => {
    const t = players && players[0] && players[0].tiers;
    return t && ["S", "A", "B", "C"].some((k) => (t[k] || []).length);
  });
}

// Chiede da che lato si gioca. Promise come askRosterUnsaved, stesso schema:
// i listener si rimuovono tutti all'uscita, altrimenti si accumulano ad ogni
// apertura e al terzo giro un click risolve tre promesse.
function askContextSide(teamName) {
  const veil = document.getElementById("side-picker");
  document.getElementById("side-picker-text").textContent =
    `Da che lato giochi con "${teamName}"?`;
  veil.classList.remove("hidden");

  return new Promise((resolve) => {
    const scelte = [
      ["side-picker-blue", "blue"],
      ["side-picker-red", "red"],
      ["side-picker-skip", null],
    ];
    const handlers = [];
    const finish = (scelta) => {
      for (const [el, fn] of handlers) el.removeEventListener("click", fn);
      document.removeEventListener("keydown", onKey);
      veil.classList.add("hidden");
      resolve(scelta);
    };
    // Escape sul DOCUMENTO e non sul velo: il velo non ha il fuoco appena
    // aperto, e un listener attaccato a lui non riceverebbe niente finche'
    // non ci si clicca sopra (errore gia' fatto sui menu del roster).
    const onKey = (e) => {
      if (e.key === "Escape") finish(null);
    };
    document.addEventListener("keydown", onKey);
    for (const [id, scelta] of scelte) {
      const el = document.getElementById(id);
      const fn = () => finish(scelta);
      el.addEventListener("click", fn);
      handlers.push([el, fn]);
    }
  });
}

// Il promemoria nella barra. Compare SOLO in modalita' libera con un team che
// ha delle tier list: altrove il lato lo sa gia' l'app e mostrarlo darebbe
// l'idea che sia una cosa da decidere.
function renderContextSideChip() {
  const chip = document.getElementById("context-side-chip");
  if (!chip) return;
  const serve = !tournamentConnected && !trainingConnected && teamHasTierLists();
  chip.classList.toggle("hidden", !serve);
  if (!serve) return;
  const etichette = { blue: "Blue Side", red: "Red Side" };
  chip.textContent = contextTeamSide ? etichette[contextTeamSide] : "Da che lato?";
  chip.className =
    "context-side-chip " +
    (contextTeamSide ? "side-" + contextTeamSide : "side-none");
  chip.title = contextTeamSide
    ? "Clicca per cambiare lato"
    : "Scegli da che lato giochi, per avere i pick suggeriti dalle tue tier list";
}

// Chiede il lato dopo che il team e' stato caricato del tutto. Il guardiano
// sul nome serve perche' fra la selezione e la fine del caricamento op.gg
// passano diversi secondi: se nel frattempo si e' cambiato team di nuovo,
// questa domanda e' vecchia e va buttata, non mostrata sopra l'altra.
async function chiediLatoSeServe(teamAtteso) {
  if (contextTeamName !== teamAtteso) return;
  if (tournamentConnected || trainingConnected) return;
  if (!teamHasTierLists()) return;
  // Gia' risposto: non si richiede. Non e' teorico - finche' la domanda
  // aspettava la fine del caricamento op.gg, il promemoria nella barra era
  // gia' cliccabile e chi rispondeva li' si vedeva comunque arrivare il
  // dialogo qualche secondo dopo (segnalato dall'utente). La domanda ora
  // parte subito e quella finestra non esiste piu', ma la guardia resta:
  // chiude la CLASSE di problema, non solo il caso che l'ha fatto emergere.
  if (contextTeamSide) return;
  const scelta = await askContextSide(teamAtteso);
  if (contextTeamName !== teamAtteso) return; // cambiato mentre era aperto
  contextTeamSide = scelta;
  renderContextSideChip();
  refreshSuggestions();
}

async function refreshContextTeamOpgg() {
  if (!contextTeamName) return;
  const btn = document.getElementById("context-team-opgg-refresh");
  const status = document.getElementById("context-team-opgg-status");
  // Il fetch reale (un lancio Playwright per titolare) impiega diversi
  // secondi - senza un segnale visibile l'utente non capisce se il click e'
  // stato registrato e tende a ripremere piu' volte (osservato dall'utente
  // stesso, 2026-08-19). Il bottone e' gia' disabilitato durante il fetch
  // (i re-click non fanno nulla), ma qui serve renderlo VISIBILE.
  btn.disabled = true;
  status.textContent = "Aggiornamento…";

  const result = await backend.fetchOpggRosterTeam(contextTeamName);
  btn.disabled = false;

  if (result.error) {
    contextTeamOpggData = null;
    status.textContent = "";
    alert(result.error);
  } else {
    contextTeamOpggData = result;
    status.textContent = "Aggiornata";
    if (result.warning) alert(result.warning);
  }
  renderGrid();
}

function renderContextPlayerFilters() {
  const el = document.getElementById("context-player-filters");
  el.innerHTML = "";
  if (!contextTeamData) return;

  for (const [role, iconFile] of ROLE_ICONS) {
    contextTeamData[role].forEach((player, i) => {
      if (!player.name) return;
      const key = `${role}|${i}`;

      const chip = document.createElement("div");
      chip.className = "context-player-chip" + (contextPlayerKey === key ? " active" : "");
      chip.title = role;

      const img = document.createElement("img");
      img.src = `/assets/role_icons/${encodeURIComponent(iconFile)}`;
      img.alt = role;
      chip.appendChild(img);

      const label = document.createElement("span");
      label.textContent = player.name;
      chip.appendChild(label);

      chip.addEventListener("click", () => {
        contextPlayerKey = contextPlayerKey === key ? null : key;
        contextTierThreshold = null;
        renderContextPlayerFilters();
        renderContextTierFilters();
        renderGrid();
      });

      el.appendChild(chip);
    });
  }
}

// Unione di tutte le tier (S-D) del giocatore attivo nel contesto draft -
// null se non c'e' nessun giocatore selezionato (nessun filtro da applicare).
function contextPlayerChampionSet() {
  if (!contextTeamData || !contextPlayerKey) return null;
  const [role, idxStr] = contextPlayerKey.split("|");
  const player = contextTeamData[role][Number(idxStr)];
  if (!player) return null;

  // Soglia cumulativa (richiesta esplicita dell'utente, 2026-08-19): S e'
  // la tier migliore, D la peggiore - selezionarne una mostra quella E
  // tutte le migliori (es. "A" -> S+A, "C" -> S+A+B+C). Nessuna soglia
  // attiva = comportamento originale, tutte le tier incluse.
  const maxIdx = contextTierThreshold ? TIER_LABELS.indexOf(contextTierThreshold) : TIER_LABELS.length - 1;
  const set = new Set();
  for (let i = 0; i <= maxIdx; i++) {
    for (const champ of player.tiers[TIER_LABELS[i]]) set.add(champ);
  }
  return set;
}

// Statistiche op.gg (games/winrate) del giocatore di contesto attivo, per
// nome campione - null se non c'e' un giocatore attivo, non ha un riot_id,
// o i dati non sono ancora stati scaricati (vedi refreshContextTeamOpgg).
function contextPlayerOpggStats() {
  if (!contextTeamOpggData || !contextTeamData || !contextPlayerKey) return null;
  const [role, idxStr] = contextPlayerKey.split("|");
  const player = contextTeamData[role][Number(idxStr)];
  if (!player || !player.riot_id) return null;

  const entry = contextTeamOpggData.players.find((p) => p.summoner === player.riot_id);
  if (!entry) return null;

  const map = {};
  for (const c of entry.champions) map[c.champion] = c;
  return map;
}

// Chip S/A/B/C/D per soglia tier, visibili solo quando un giocatore di
// contesto e' selezionato (senza un giocatore attivo la soglia non ha nulla
// su cui applicarsi). Vedi contextPlayerChampionSet per la logica cumulativa.
function renderContextTierFilters() {
  const container = document.getElementById("context-tier-filters");
  container.innerHTML = "";
  if (!contextPlayerKey) {
    container.classList.add("hidden");
    return;
  }
  container.classList.remove("hidden");

  const label = document.createElement("span");
  label.className = "context-tier-filters-label";
  label.textContent = "Soglia tier:";
  container.appendChild(label);

  for (const tier of TIER_LABELS) {
    const chip = document.createElement("span");
    chip.className = "player-chip" + (contextTierThreshold === tier ? " active" : "");
    chip.textContent = tier;
    chip.title = `Mostra solo ${tier} e le tier migliori`;
    chip.addEventListener("click", () => {
      contextTierThreshold = contextTierThreshold === tier ? null : tier;
      renderContextTierFilters();
      renderGrid();
    });
    container.appendChild(chip);
  }
}

// Righe pool (una per giocatore, MAI fuse) per un campione, raccolte dalle
// pool squadra attualmente attive come filtro - richiesta esplicita
// dell'utente: se piu' giocatori hanno lo stesso campione, righe separate.
function poolRowsFor(name) {
  const rows = [];
  for (const team of activePoolFilters) {
    const entries = teamPools[team]?.pool[name];
    if (entries) {
      for (const e of entries) rows.push({ ...e, team });
    }
  }
  for (const team of ["left", "right"]) {
    const summoner = activePlayerFilters[team];
    if (!summoner) continue;
    const entry = teamPools[team]?.pool[name]?.find((e) => e.summoner === summoner);
    if (entry) rows.push({ ...entry, team });
  }
  return rows;
}

// Colore stabile per giocatore, in base alla sua posizione fra i 5 di quella
// squadra (stesso ordine restituito da /api/opgg-team).
function playerColor(team, summoner) {
  const players = teamPools[team]?.players || [];
  const idx = players.findIndex((p) => p.summoner === summoner);
  if (idx === -1 || players.length === 0) return "#555";
  const t = players.length === 1 ? 0 : idx / (players.length - 1);
  return playerColorForFraction(t);
}

function poolTotalGames(name) {
  return poolRowsFor(name).reduce((sum, r) => sum + r.games, 0);
}

function renderGrid() {
  const grid = document.getElementById("champion-grid");
  grid.innerHTML = "";

  const playerSet = contextPlayerChampionSet();
  const contextStats = contextPlayerOpggStats();
  const bannedSet = new Set(allBannedNames());
  // Fearless draft: campioni gia' presi in una game precedente della stessa
  // serie - vuoto fuori dalla modalita' torneo (fearlessPicks si popola solo
  // dal poll live). Stesso trattamento visivo di ban/pick (oscurato, non
  // selezionabile) - il divieto e' GLOBALE, richiesta esplicita dell'utente:
  // conta chi l'ha preso in una game qualunque, non solo "il nostro lato".
  const fearlessSet = new Set(fearlessPicks.map((p) => p.champion));

  const filtered = champions.filter((c) => {
    if (searchText && !c.name.toLowerCase().includes(searchText)) return false;
    if (activeFilters.size > 0 && !c.comps.some((cc) => activeFilters.has(cc)))
      return false;
    if (activeTagFilters.size > 0 && ![...activeTagFilters].every((t) => c.tags.includes(t)))
      return false;
    if (activeRoleFilters.size > 0 && ![...activeRoleFilters].every((r) => c.roles.includes(r)))
      return false;
    if (anyPoolFilterActive() && poolRowsFor(c.name).length === 0) return false;
    if (playerSet && !playerSet.has(c.name)) return false;
    if (activeCounterData() && !activeCounterData()[c.name]) return false;
    return true;
  });

  if (anyPoolFilterActive()) {
    filtered.sort((a, b) => poolTotalGames(b.name) - poolTotalGames(a.name));
  }
  const activeData = activeCounterData();
  if (activeData) {
    const metricKey = laneCounterMode ? "gd15" : "winrate";
    filtered.sort((a, b) => activeData[b.name][metricKey] - activeData[a.name][metricKey]);
  }

  const already = allPickedNames();

  for (const champ of filtered) {
    // Bannato o gia' pickato: stesso trattamento visivo (oscurato, non
    // selezionabile/trascinabile) - richiesta esplicita dell'utente
    // (2026-08-17): un ban deve restare visibile "come se fosse gia'
    // preso", non sparire del tutto dalla griglia.
    const isUnavailable =
      already.includes(champ.name) || bannedSet.has(champ.name) || fearlessSet.has(champ.name);
    const card = document.createElement("div");
    // "Pick suggeriti" (tutte e 3 le modalita') - vedi refreshSuggestions.
    // !isUnavailable e' una guardia difensiva in piu' (il server esclude gia'
    // i campioni presi/bannati dall'elenco): il fetch e' asincrono e non
    // bloccante, uno stato leggermente superato non deve mai far
    // "illuminare" una card gia' grigia.
    const suggestClass =
      suggestionsEnabled && !isUnavailable ? suggestionState(champ.name) : "";
    card.className =
      "champion-card" +
      (isUnavailable ? " picked" : "") +
      (trainingConnected && champ.name === trainingPendingChampion ? " training-pending" : "") +
      (suggestClass ? " " + suggestClass : "");
    card.title = suggestClass ? suggestionTitle(champ.name) : champ.name;
    card.draggable = !isUnavailable;
    applyCompBorderVar(card, champ);

    const img = document.createElement("img");
    img.src = champ.icon;
    img.alt = champ.name;
    img.loading = "lazy";
    card.appendChild(img);

    if (anyPoolFilterActive()) {
      const rows = poolRowsFor(champ.name);
      if (rows.length > 0) {
        const stats = document.createElement("div");
        stats.className = "pool-stats";
        for (const r of rows) {
          const rowEl = document.createElement("div");
          rowEl.className = "pool-stats-row";
          rowEl.style.borderColor = playerColor(r.team, r.summoner);
          rowEl.textContent = `${r.games} · ${r.winrate}%`;
          rowEl.title = `${r.summoner}: ${r.games} partite, ${r.winrate}% vittorie`;
          stats.appendChild(rowEl);
        }
        card.appendChild(stats);
      }
    }

    if (activeCounterData() && activeCounterData()[champ.name]) {
      const entry = activeCounterData()[champ.name];
      const stats = document.createElement("div");
      stats.className = "pool-stats";
      const rowEl = document.createElement("div");
      rowEl.className = "pool-stats-row";
      const tierLabel = RANK_TIERS.find(([value]) => value === counterModeSearchedTier)?.[1] ?? counterModeSearchedTier;
      if (laneCounterMode) {
        // Counter di corsia (u.gg): gd15 e' un DELTA (puo' essere negativo),
        // non una percentuale - soglia a 0, non a 50 come il winrate.
        rowEl.style.background = entry.gd15 >= 0 ? "#1e8449" : "#8e2f2f";
        rowEl.textContent = `${entry.gd15 >= 0 ? "+" : ""}${entry.gd15} GD15 · ${entry.games}p`;
        rowEl.title = `${champ.name} vs ${counterModeChampion} (${counterModeRole}, ${tierLabel}): ${entry.gd15 >= 0 ? "+" : ""}${entry.gd15} differenza oro a 15' su ${entry.games} partite (corsia, u.gg)`;
      } else {
        rowEl.style.background = entry.winrate >= 50 ? "#1e8449" : "#8e2f2f";
        rowEl.textContent = `${entry.winrate}% · ${entry.games}p`;
        rowEl.title = `${champ.name} vs ${counterModeChampion} (${counterModeRole}, ${tierLabel}): ${entry.winrate}% winrate su ${entry.games} partite`;
      }
      stats.appendChild(rowEl);
      card.appendChild(stats);
    }

    if (contextStats && contextStats[champ.name]) {
      const entry = contextStats[champ.name];
      const stats = document.createElement("div");
      stats.className = "pool-stats";
      const rowEl = document.createElement("div");
      rowEl.className = "pool-stats-row";
      rowEl.textContent = `${entry.games} · ${entry.winrate}%`;
      rowEl.title = `${entry.games} partite, ${entry.winrate}% vittorie (op.gg)`;
      stats.appendChild(rowEl);
      card.appendChild(stats);
    }

    card.addEventListener("click", () => placeChampion(champ.name));
    card.addEventListener("dragstart", (e) => {
      if (isUnavailable) {
        e.preventDefault();
        return;
      }
      e.dataTransfer.setData("text/plain", champ.name);
    });
    grid.appendChild(card);
  }
}

// Riempie lo slot attivo (scelto cliccando uno slot, pick O ban) con questo
// campione; se nessuno slot e' attivo, si comporta come prima: primo slot
// pick libero della squadra sinistra. Un campione gia' scelto o bannato non
// si puo' riselezionare dalla griglia (per i pick va prima rimosso
// cliccando il suo slot; i bannati non compaiono proprio in griglia, questo
// controllo e' solo un'assicurazione in piu').
function placeChampion(name) {
  if (allPickedNames().includes(name) || allBannedNames().includes(name)) return;

  // Modalita' torneo connessa: un click in griglia non tocca mai lo stato
  // locale direttamente - invia (o ignora, se non e' il nostro turno) la
  // selezione alla draft vera, che poi torna indietro tramite il polling.
  if (tournamentConnected) {
    sendTournamentSelection(name);
    return;
  }
  if (trainingConnected) {
    selectTrainingPending(name);
    return;
  }

  let target = activeSlot;
  if (!target) {
    const idx = teams.left.indexOf(null);
    if (idx === -1) return;
    target = { team: "left", index: idx, kind: "pick" };
  }

  const arr = target.kind === "ban" ? bans : teams;
  arr[target.team][target.index] = name;
  const nextEmpty = arr[target.team].indexOf(null);
  activeSlot = nextEmpty === -1 ? null : { team: target.team, index: nextEmpty, kind: target.kind };

  renderTeam("left");
  renderTeam("right");
  renderGrid();
  refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
  if (target.kind === "pick") refreshDetection(target.team);
}

function closeCounterPopover() {
  const existing = document.querySelector(".counter-role-popover");
  if (existing) existing.remove();
}

async function runCounterSearch(champion, role) {
  closeCounterPopover();

  if (counterModeChampion === champion && counterModeRole === role) {
    // richiedere di nuovo la STESSA ricerca gia' attiva la annulla
    counterModeChampion = null;
    counterModeRole = null;
    counterModeDataWinrate = null;
    counterModeDataGd15 = null;
    counterModeErrorWinrate = null;
    counterModeErrorGd15 = null;
    counterModeSearchedTier = null;
    renderTeam("left");
    renderTeam("right");
    renderGrid();
    return;
  }

  counterSearchLoading = { champion, role };
  renderTeam("left");
  renderTeam("right");

  // Richiesta esplicita dell'utente 2026-08-24: caricare ENTRAMBE le fonti
  // insieme (in parallelo, stessa fascia elo) invece di una sola in base al
  // toggle - dopo, cambiare "Counter corsia" e' istantaneo (nessuna nuova
  // richiesta, vedi setupLaneCounterToggle/activeCounterData), evitando
  // "fastidiosi caricamenti multipli ad ogni opzione".
  const body = JSON.stringify({ champion, role, tier: counterModeTier });
  const [winrateResult, gd15Result] = await Promise.all([
    fetch("/api/counters", { method: "POST", headers: { "Content-Type": "application/json" }, body }).then((r) =>
      r.json()
    ),
    fetch("/api/lane-counters", { method: "POST", headers: { "Content-Type": "application/json" }, body }).then(
      (r) => r.json()
    ),
  ]);

  // se nel frattempo e' partita un'altra ricerca, queste risposte sono scadute
  if (!counterSearchLoading || counterSearchLoading.champion !== champion || counterSearchLoading.role !== role) {
    return;
  }
  counterSearchLoading = null;

  if (winrateResult.error && gd15Result.error) {
    alert(winrateResult.error === gd15Result.error ? winrateResult.error : `${winrateResult.error}\n${gd15Result.error}`);
    renderTeam("left");
    renderTeam("right");
    return;
  }

  counterModeChampion = champion;
  counterModeRole = role;
  counterModeSearchedTier = counterModeTier;

  counterModeErrorWinrate = winrateResult.error || null;
  counterModeDataWinrate = null;
  if (!winrateResult.error) {
    counterModeDataWinrate = {};
    for (const c of winrateResult.counters) counterModeDataWinrate[c.champion] = c;
  }

  counterModeErrorGd15 = gd15Result.error || null;
  counterModeDataGd15 = null;
  if (!gd15Result.error) {
    counterModeDataGd15 = {};
    for (const c of gd15Result.laneCounters) counterModeDataGd15[c.champion] = c;
  }

  renderTeam("left");
  renderTeam("right");
  renderGrid();

  // La fonte ATTIVA (quella mostrata adesso) e' fallita ma l'altra no -
  // avvisa subito invece di lasciare la griglia senza colori senza
  // spiegazione. Se invece fallisce la fonte NON attiva in questo momento,
  // l'avviso e' rimandato a quando/se il coach ci fa toggle sopra (vedi
  // setupLaneCounterToggle), per non interromperlo per un errore che in
  // quel momento non lo riguarda.
  if (!activeCounterData() && activeCounterError()) {
    alert(activeCounterError());
  }
}

function renderCounterButton(slot, champ) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "slot-counter-btn";
  btn.title = "Cerca counter";

  const isLoading = counterSearchLoading && counterSearchLoading.champion === champ.name;
  const isActive = counterModeChampion === champ.name;
  btn.textContent = isLoading ? "…" : "🔍";
  btn.disabled = !!isLoading;
  if (isActive) btn.classList.add("active");

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const alreadyOpenForThis = document.querySelector(
      `.counter-role-popover[data-for="${CSS.escape(champ.name)}"]`
    );
    closeCounterPopover();
    if (alreadyOpenForThis) return;

    const popover = document.createElement("div");
    popover.className = "counter-role-popover";
    popover.dataset.for = champ.name;
    popover.addEventListener("click", (e2) => e2.stopPropagation());

    for (const [role, iconFile] of ROLE_ICONS) {
      if (!champ.roles.includes(role)) continue;
      const roleBtn = document.createElement("button");
      roleBtn.type = "button";
      roleBtn.className =
        "counter-role-btn" +
        (counterModeChampion === champ.name && counterModeRole === role ? " active" : "");
      roleBtn.title = role;
      const img = document.createElement("img");
      img.src = `/assets/role_icons/${encodeURIComponent(iconFile)}`;
      img.alt = role;
      roleBtn.appendChild(img);
      roleBtn.addEventListener("click", (e2) => {
        e2.stopPropagation();
        runCounterSearch(champ.name, role);
      });
      popover.appendChild(roleBtn);
    }

    // Appeso al BODY, non allo slot: `.team-slot.filled` ha overflow:hidden
    // (serve alla splash art ritagliata) e faceva sparire il popover, che si
    // apre appena sotto lo slot - vedi il commento esteso su
    // .counter-role-popover in style.css. Va appeso PRIMA di posizionarlo:
    // fuori dal DOM la sua altezza misurata sarebbe 0, e openCounterPopover
    // ha bisogno di quella vera per decidere se aprirsi sopra o sotto.
    document.body.appendChild(popover);
    openCounterPopover(slot, popover);
  });

  slot.appendChild(btn);
}

// Posiziona il popover della corsia (position:fixed, quindi in coordinate
// viewport) sotto lo slot che l'ha aperto, o sopra se sotto non ci sta -
// stessa logica, e stesse ragioni, di openSaveDraftPopover() qui sotto.
// Allineato al bordo DESTRO dello slot, che e' dove stava con il vecchio
// `right: 0` da discendente assoluto: il bottone 🔍 e' nell'angolo in alto a
// destra, e da li' il popover si estende verso sinistra restando dentro il
// pannello su entrambi i lati.
function openCounterPopover(slot, popover) {
  const rect = slot.getBoundingClientRect();
  const popoverHeight = popover.getBoundingClientRect().height;
  if (rect.bottom + 4 + popoverHeight <= window.innerHeight) {
    popover.style.top = `${rect.bottom + 4}px`;
    popover.style.bottom = "auto";
  } else {
    popover.style.bottom = `${window.innerHeight - rect.top + 4}px`;
    popover.style.top = "auto";
  }
  popover.style.right = `${window.innerWidth - rect.right}px`;
  popover.style.left = "auto";
}

// Il bottone "Modalita' training" ora implementa DAVVERO la feature 4
// (allenamento vs bot da dati pro Leaguepedia - vedi setupTrainingMode()
// piu' sotto). La primissima idea per questo bottone (un modal con
// griglia/slot isolati per salvare una comp) era tutt'altra cosa ed e' stata
// scartata dall'utente 2026-08-26: duplicava la griglia principale (comp/
// tag/pool/counter gia' tutti li') per un risultato meno utile della griglia
// vera - vedi saveDraftFromTeam() sotto, che salva direttamente lo stato
// GIA' piazzato in teams.left/right (funzione separata, non il bot).

// Bottone "salva questa comp" (icona libro) accanto ai ban - abilitato solo
// a selezione COMPLETA (5/5), stesso significato di "draft salvata" gia'
// avuto con la modalita' training scartata: sempre 5 campioni, mai parziali.
function updateSaveDraftButton(team) {
  const btn = document.getElementById(team === "left" ? "save-draft-open-left" : "save-draft-open-right");
  const full = !teams[team].includes(null);
  btn.disabled = !full;
  btn.title = full
    ? "Salva questa comp come draft"
    : "Servono 5 campioni piazzati per salvare questa comp";
}

function closeSaveDraftPopovers() {
  document.getElementById("save-draft-popover-left").classList.add("hidden");
  document.getElementById("save-draft-popover-right").classList.add("hidden");
}

// Il popover e' position:fixed e vive fuori da #sidebar/#sidebar-right (vedi
// nota nell'HTML e in style.css sul perche') - quindi la sua posizione non
// e' piu' "gratis" via CSS relativo a un genitore, va calcolata qui dalla
// posizione REALE del bottone cliccato. Lato blue: popover appeso al bordo
// sinistro del bottone, si apre verso destra (spazio libero, griglia
// campioni). Lato red: appeso al bordo DESTRO del bottone (usando "right"
// invece di "left"), si apre verso sinistra - il bottone e' vicino al
// margine destro dello schermo, aprirsi verso destra lo farebbe uscire
// dalla viewport.
function openSaveDraftPopover(team, openBtn, popover) {
  const rect = openBtn.getBoundingClientRect();
  // Il chiamante ha gia' tolto "hidden" prima di questa chiamata apposta -
  // serve un'altezza VERA (non 0) per decidere se aprirsi sotto o sopra il
  // bottone. Bug reale trovato testando su un viewport basso (il popover si
  // apriva sempre verso il basso, finiva fuori schermo se il bottone era
  // vicino al bordo inferiore - dopo aver spostato il bottone sotto la riga
  // ban invece che affiancato, capita piu' spesso).
  const popoverHeight = popover.getBoundingClientRect().height;
  const opensBelow = rect.bottom + 4 + popoverHeight <= window.innerHeight;
  if (opensBelow) {
    popover.style.top = `${rect.bottom + 4}px`;
    popover.style.bottom = "auto";
  } else {
    popover.style.bottom = `${window.innerHeight - rect.top + 4}px`;
    popover.style.top = "auto";
  }
  if (team === "left") {
    popover.style.left = `${rect.left}px`;
    popover.style.right = "auto";
  } else {
    popover.style.right = `${window.innerWidth - rect.right}px`;
    popover.style.left = "auto";
  }
}

function setupSaveDraftPopovers() {
  for (const team of ["left", "right"]) {
    const openBtn = document.getElementById(team === "left" ? "save-draft-open-left" : "save-draft-open-right");
    const popover = document.getElementById(team === "left" ? "save-draft-popover-left" : "save-draft-popover-right");
    const nameInput = document.getElementById(team === "left" ? "save-draft-name-left" : "save-draft-name-right");
    const confirmBtn = document.getElementById(
      team === "left" ? "save-draft-confirm-left" : "save-draft-confirm-right"
    );

    openBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const wasHidden = popover.classList.contains("hidden");
      closeSaveDraftPopovers();
      if (wasHidden) {
        // Va reso visibile PRIMA di calcolare la posizione: da nascosto la
        // sua altezza misurata sarebbe 0, e openSaveDraftPopover() ha
        // bisogno dell'altezza vera per decidere se aprirsi sopra o sotto
        // il bottone senza uscire dallo schermo.
        popover.classList.remove("hidden");
        openSaveDraftPopover(team, openBtn, popover);
      }
    });
    popover.addEventListener("click", (e) => e.stopPropagation());

    confirmBtn.addEventListener("click", async () => {
      const name = nameInput.value.trim();
      const result = await backend.addSavedDraft(name, teams[team]);
      if (result.error) {
        alert(result.error);
        return;
      }
      nameInput.value = "";
      popover.classList.add("hidden");
    });
  }

  // Stesso pattern gia' in uso per .counter-role-popover: un click fuori
  // dal popover/bottone lo richiude.
  document.addEventListener("click", (e) => {
    if (e.target.closest(".save-draft-open") || e.target.closest(".save-draft-popover")) return;
    closeSaveDraftPopovers();
  });
}

// Elenco delle draft salvate (letto da /api/saved-drafts ad ogni apertura,
// non tenuto in cache - costo trascurabile, evita di disallinearsi se la
// stessa lista viene modificata altrove).
async function renderSavedDraftsList() {
  const el = document.getElementById("saved-drafts-list");
  el.innerHTML = "";
  const result = await backend.listSavedDrafts();
  const drafts = result.drafts || [];

  if (drafts.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-label";
    empty.textContent = "Nessuna draft salvata.";
    el.appendChild(empty);
    return;
  }

  for (const draft of drafts) {
    const row = document.createElement("div");
    row.className = "saved-draft-entry";

    const icons = document.createElement("div");
    icons.className = "saved-draft-icons";
    for (const champName of draft.champions) {
      const champ = champions.find((c) => c.name === champName);
      const img = document.createElement("img");
      img.className = "saved-draft-icon";
      img.src = champ ? champ.icon : "";
      img.alt = champName;
      img.title = champName;
      if (champ) applyCompBorderVar(img, champ);
      icons.appendChild(img);
    }
    row.appendChild(icons);

    const name = document.createElement("span");
    name.className = "saved-draft-name";
    name.textContent = draft.name;
    row.appendChild(name);

    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "icon-btn";
    deleteBtn.title = "Elimina questa draft salvata";
    deleteBtn.textContent = "🗑";
    deleteBtn.addEventListener("click", async () => {
      if (!confirm(`Eliminare la draft "${draft.name}"?`)) return;
      await backend.deleteSavedDraft(draft.id);
      renderSavedDraftsList();
    });
    row.appendChild(deleteBtn);

    el.appendChild(row);
  }
}

function setupSavedDraftsViewer() {
  document.getElementById("saved-drafts-open").addEventListener("click", () => {
    renderSavedDraftsList();
    document.getElementById("saved-drafts-modal").classList.remove("hidden");
  });

  document.getElementById("saved-drafts-close").addEventListener("click", () => {
    document.getElementById("saved-drafts-modal").classList.add("hidden");
  });
}

// Analizza il testo di fase mostrato dal sito (es. "Blue ban 1", "Red pick
// 3") per capire lato e tipo azione - non serve corrispondenza esatta col
// formato, basta che il testo contenga "blue"/"red" e "ban"/"pick" da
// qualche parte (piu' robusto di un parsing rigido, il sito decide comunque
// lui stesso quale azione eseguire in base alla propria fase).
function parseTournamentPhase(step) {
  if (!step) return null;
  const s = step.toLowerCase();
  const side = s.includes("blue") ? "blue" : s.includes("red") ? "red" : null;
  const kind = s.includes("ban") ? "ban" : s.includes("pick") ? "pick" : null;
  if (!side || !kind) return null;
  return { side, kind };
}

// null se non e' il nostro turno (o la fase non e' riconoscibile), altrimenti
// "ban"/"pick" - unico punto in cui si decide se un click in griglia deve
// diventare un'azione vera sulla draft live.
function currentTournamentTurn() {
  if (!tournamentConnected || !tournamentSide) return null;
  const phase = parseTournamentPhase(tournamentLastStep);
  if (!phase || phase.side !== tournamentSide) return null;
  return phase.kind;
}

// Traduce il testo grezzo del bottone del sito in un'etichetta italiana per
// i casi noti - per qualunque altro testo (stati non ancora visti, es. "in
// attesa dell'avversario") mostra il testo del sito cosi' com'e' invece di
// indovinare una traduzione, cosi' il nostro bottone non mostra mai
// un'etichetta sbagliata o stantia.
function translateDraftButtonText(raw) {
  if (!raw) return "Conferma selezione";
  const lower = raw.toLowerCase();
  if (lower.includes("ready")) return "Pronto";
  if (lower.includes("ban")) return "Conferma ban";
  if (lower.includes("pick")) return "Conferma pick";
  return raw;
}

// "Collegato" al bottone vero del sito (richiesta esplicita dell'utente,
// 2026-08-17, dopo aver notato che molti dei problemi visti finora
// nascevano proprio dal mantenere uno stato locale parallelo che poteva
// disallinearsi dal sito): l'abilitazione usa SEMPRE e SOLO
// tournamentButtonDisabledReal (lo stato disabled vero del bottone,
// aggiornato ad ogni poll), mai una previsione locale - e l'etichetta segue
// il testo vero del sito. Questo e' diventato sicuro da fare solo ora che
// confirmTournamentSelection VERIFICA che ogni conferma sia andata davvero
// a segno (vedi sotto e confirm_selection in drafter_live.py) - prima un
// click "riuscito" secondo Playwright ma finito sul bersaglio sbagliato
// avrebbe lasciato il bottone vero bloccato senza che ce ne accorgessimo.
// Bottone "Valuta la draft" - indipendente da #tournament-confirm (vedi
// commento li' sopra sul perche' non e' stato riusato quel bottone):
// nessuna azione sul sito vero, solo un calcolo nostro via lolalytics, quindi
// una condizione di visibilita' tutta sua invece di seguire lo stato del
// bottone del sito. Visibile appena tutti i 10 pick sono presenti, A
// PRESCINDERE dalla fase di role confirmation (quella riguarda solo
// #tournament-confirm/#role-confirm-panel) - il coach potrebbe voler vedere
// la valutazione anche mentre sta ancora sistemando l'ordine ruoli sul sito.
// Chiamata da dentro updateTournamentConfirmButton() cosi' da ereditarne
// automaticamente TUTTI e 9 i punti di chiamata nel file (stessa lezione
// gia' imparata li': la guardia deve stare dentro la funzione stessa, non
// inseguita ad ogni chiamante) invece di duplicarli qui.
function updateTournamentEvaluateButton() {
  const row = document.getElementById("tournament-evaluate-row");
  const btn = document.getElementById("tournament-evaluate");
  const draftComplete =
    tournamentConnected && teams.left.every((c) => c !== null) && teams.right.every((c) => c !== null);
  if (!draftComplete) {
    row.classList.add("hidden");
    return;
  }
  row.classList.remove("hidden");
  btn.textContent = tournamentEvaluation ? "Rivaluta la draft" : "Valuta la draft";
  btn.disabled = tournamentEvaluateBusy;
}

// "Ruoli nemici" (richiesto esplicitamente dall'utente 2026-08-26, dopo un
// caso reale: "mi ha immesso Hecarim support anche se era il toplaner", poi
// esteso: "viene usata in automatico, ma sempre dando la possibilità al
// coach di aggiustare... in modo da coprire entrambi i casi") - stessa
// condizione di visibilita' di updateTournamentEvaluateButton (draft
// completa), chiamata dallo stesso punto per lo stesso motivo (la guardia
// deve stare dentro la funzione, non inseguita ad ogni chiamante).
//
// Priorita' a 3 livelli per tournamentEnemyRoleOrder (vedi
// tournamentEnemyRoleSource per quale e' attivo ORA):
// 1. "site" - il tag REALE confermato sul sito (tournamentEnemyRoleTags,
//    fresco ad ogni poll - vedi drafter_live.py per come viene letto), non
//    appena disponibile per tutti e 5 i pick. Il PIU' affidabile perche' e'
//    quello che le squadre hanno davvero confermato - ma anche questo puo'
//    essere sbagliato (es. confermato per timeout col default invece che
//    sistemato attivamente, verificato dal vivo durante l'indagine) - non
//    e' un sostituto del controllo del coach, solo il miglior punto di
//    partenza possibile.
// 2. "guess" - l'euristica assign_roles() via /api/live-draft/role-guess,
//    usata finche' (1) non e' ancora disponibile (la fase di conferma ruoli
//    sul sito arriva DOPO tutti e 10 i pick, non e' detto sia gia' iniziata
//    quando questo pannello compare).
// 3. "raw" - l'ordine di pick grezzo, seed SINCRONO immediato prima ancora
//    che (1)/(2) rispondano (nessun flash vuoto).
//
// "manual" e' uno stato ASSORBENTE: appena il coach trascina anche una sola
// volta (vedi renderTournamentEnemyRoles), questa funzione smette per
// sempre di toccare l'ordine - nessun aggiornamento automatico successivo
// (nemmeno se il sito conferma qualcosa dopo) puo' piu' sovrascriverlo. E'
// esattamente il "sempre dando la possibilita' di aggiustare" richiesto: la
// correzione del coach e' definitiva finche' non si resetta la draft.
function updateTournamentEnemyRolesPanel() {
  const panel = document.getElementById("tournament-enemy-roles");
  const draftComplete =
    tournamentConnected && teams.left.every((c) => c !== null) && teams.right.every((c) => c !== null);
  if (!draftComplete) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");

  if (tournamentEnemyRoleSource === "manual") {
    renderTournamentEnemyRoles();
    return;
  }

  const enemyTeam = tournamentSide === "blue" ? "right" : "left";
  const enemyPicks = teams[enemyTeam].slice();

  const siteTags = tournamentEnemyRoleTags;
  const siteConfirmed = siteTags && TRAINING_ROLE_ORDER.every((role) => siteTags.includes(role));
  if (siteConfirmed) {
    if (tournamentEnemyRoleSource !== "site") {
      tournamentEnemyRoleOrder = TRAINING_ROLE_ORDER.map((role) => enemyPicks[siteTags.indexOf(role)]);
      tournamentEnemyRoleSource = "site";
    }
    renderTournamentEnemyRoles();
    return;
  }

  if (tournamentEnemyRoleSource) {
    renderTournamentEnemyRoles(); // gia' seminato ("raw" o "guess"), aspetta il sito o il coach
    return;
  }

  tournamentEnemyRoleOrder = enemyPicks;
  tournamentEnemyRoleSource = "raw";
  renderTournamentEnemyRoles();

  // La squadra avversaria, se il coach ne ha caricato l'op.gg nel suo
  // pannello: con quella l'assegnazione smette di tirare a sorte fra due
  // permutazioni ugualmente valide per i tag. Vedi api_live_draft_role_guess.
  const enemySide = tournamentSide === "blue" ? "red" : "blue";
  backend.liveDraftRoleGuess(enemyPicks, teamPlayers(enemySide), null).then((result) => {
    if (result.error || tournamentEnemyRoleSource !== "raw") return; // superato nel frattempo dal sito o dal coach
    tournamentEnemyRoleOrder = TRAINING_ROLE_ORDER.map((role) => result.assignment[role].champion);
    tournamentEnemyRoleSource = "guess";
    renderTournamentEnemyRoles();
  });
}

// Da dove viene l'ordine ATTUALMENTE mostrato - richiesto implicitamente
// dall'utente ("coprire entrambi i casi"): il coach deve poter vedere a
// colpo d'occhio se sta guardando un tag confermato dal sito o solo un
// indovinato, prima di fidarsene per una decisione - stesso principio di
// trasparenza gia' usato per i laneErrors della valutazione ("piano B").
// Niente hint per "raw" (stato transitorio, sostituito da "guess" quasi
// subito) ne' per null (pannello non ancora seminato). Condiviso fra
// pannello nemico e nostro (2026-08-30) - il testo non menziona mai "nemico"
// esplicitamente, quindi vale identico per entrambi.
const ROLE_SOURCE_LABELS = {
  guess: "Indovinato automaticamente (sinergia/counter) - correggi se serve",
  site: "Confermato dal sito (drafter.lol) - correggi se serve",
  manual: "Corretto da te",
};

// Drag&drop per riordinare i ruoli nemici - stesso identico meccanismo
// (arrayMove via DataTransfer) di renderTrainingRoleEditable, qui pero'
// senza bottone "conferma"/hint "salvato": non c'e' nulla da persistere
// lato server, l'ordine locale viene passato direttamente ad ogni click su
// "Valuta la draft" (vedi evaluateTournamentDraft).
function renderTournamentEnemyRoles() {
  const panel = document.getElementById("tournament-enemy-roles");
  const rowsEl = panel.querySelector(".training-role-rows");
  rowsEl.innerHTML = "";

  tournamentEnemyRoleOrder.forEach((champName, i) => {
    const role = TRAINING_ROLE_ORDER[i];
    const row = document.createElement("div");
    row.className = "training-role-row training-role-row-editable";
    row.draggable = true;
    row.appendChild(buildTrainingRoleIcon(role));
    const champImg = buildTrainingChampIcon(champName);
    if (champImg) row.appendChild(champImg);
    const label = document.createElement("span");
    label.textContent = champName;
    row.appendChild(label);

    row.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(i));
      e.dataTransfer.effectAllowed = "move";
    });
    row.addEventListener("dragover", (e) => {
      e.preventDefault();
      row.classList.add("drag-over");
    });
    row.addEventListener("dragleave", () => row.classList.remove("drag-over"));
    row.addEventListener("drop", (e) => {
      e.preventDefault();
      row.classList.remove("drag-over");
      const fromIndex = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (Number.isNaN(fromIndex) || fromIndex === i) return;
      const [item] = tournamentEnemyRoleOrder.splice(fromIndex, 1);
      tournamentEnemyRoleOrder.splice(i, 0, item);
      tournamentEnemyRoleSource = "manual"; // assorbente - vedi updateTournamentEnemyRolesPanel
      renderTournamentEnemyRoles();
    });

    rowsEl.appendChild(row);
  });

  const team = panel.querySelector(".training-role-team");
  let hint = team.querySelector(".training-role-source-hint");
  const label = ROLE_SOURCE_LABELS[tournamentEnemyRoleSource];
  if (label) {
    if (!hint) {
      hint = document.createElement("div");
      hint.className = "training-role-source-hint";
      team.appendChild(hint);
    }
    hint.textContent = label;
  } else if (hint) {
    hint.remove();
  }
}

// Ruoli NOSTRI - vedi la nota su tournamentOwnRoleOrder piu' in alto.
// Stessa identica logica di updateTournamentEnemyRolesPanel/
// renderTournamentEnemyRoles qui sopra, applicata al nostro lato invece che
// al nemico - duplicata invece che parametrizzata deliberatamente: la
// versione nemico e' un meccanismo gia' verificato dal vivo con una storia
// di bug reali dietro (Hecarim), stessa cautela di non ritoccare codice che
// funziona gia' bene solo per generalizzarlo.
function updateTournamentOwnRolesPanel() {
  const panel = document.getElementById("tournament-own-roles");
  const draftComplete =
    tournamentConnected && teams.left.every((c) => c !== null) && teams.right.every((c) => c !== null);
  if (!draftComplete) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");

  if (tournamentOwnRoleSource === "manual") {
    renderTournamentOwnRoles();
    return;
  }

  const ownTeam = tournamentSide === "blue" ? "left" : "right";
  const ownPicks = teams[ownTeam].slice();

  const siteTags = tournamentOwnRoleTags;
  const siteConfirmed = siteTags && TRAINING_ROLE_ORDER.every((role) => siteTags.includes(role));
  if (siteConfirmed) {
    if (tournamentOwnRoleSource !== "site") {
      tournamentOwnRoleOrder = TRAINING_ROLE_ORDER.map((role) => ownPicks[siteTags.indexOf(role)]);
      tournamentOwnRoleSource = "site";
    }
    renderTournamentOwnRoles();
    return;
  }

  if (tournamentOwnRoleSource) {
    renderTournamentOwnRoles(); // gia' seminato ("raw" o "guess"), aspetta il sito o il coach
    return;
  }

  tournamentOwnRoleOrder = ownPicks;
  tournamentOwnRoleSource = "raw";
  renderTournamentOwnRoles();

  // Per noi la fonte migliore sono le tier list del roster (i ruoli li' non si
  // deducono, li ha assegnati il coach); se manca il team si ricade sull'op.gg
  // del nostro pannello, e se manca anche quello sui soli tag come prima.
  backend
    .liveDraftRoleGuess(ownPicks, teamPlayers(tournamentSide), contextTeamName || null)
    .then((result) => {
    if (result.error || tournamentOwnRoleSource !== "raw") return; // superato nel frattempo dal sito o dal coach
    tournamentOwnRoleOrder = TRAINING_ROLE_ORDER.map((role) => result.assignment[role].champion);
    tournamentOwnRoleSource = "guess";
    renderTournamentOwnRoles();
  });
}

// Drag&drop per riordinare i ruoli nostri - vedi renderTournamentEnemyRoles
// qui sopra, stesso meccanismo identico.
function renderTournamentOwnRoles() {
  const panel = document.getElementById("tournament-own-roles");
  const rowsEl = panel.querySelector(".training-role-rows");
  rowsEl.innerHTML = "";

  tournamentOwnRoleOrder.forEach((champName, i) => {
    const role = TRAINING_ROLE_ORDER[i];
    const row = document.createElement("div");
    row.className = "training-role-row training-role-row-editable";
    row.draggable = true;
    row.appendChild(buildTrainingRoleIcon(role));
    const champImg = buildTrainingChampIcon(champName);
    if (champImg) row.appendChild(champImg);
    const label = document.createElement("span");
    label.textContent = champName;
    row.appendChild(label);

    row.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(i));
      e.dataTransfer.effectAllowed = "move";
    });
    row.addEventListener("dragover", (e) => {
      e.preventDefault();
      row.classList.add("drag-over");
    });
    row.addEventListener("dragleave", () => row.classList.remove("drag-over"));
    row.addEventListener("drop", (e) => {
      e.preventDefault();
      row.classList.remove("drag-over");
      const fromIndex = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (Number.isNaN(fromIndex) || fromIndex === i) return;
      const [item] = tournamentOwnRoleOrder.splice(fromIndex, 1);
      tournamentOwnRoleOrder.splice(i, 0, item);
      tournamentOwnRoleSource = "manual"; // assorbente - vedi updateTournamentOwnRolesPanel
      renderTournamentOwnRoles();
    });

    rowsEl.appendChild(row);
  });

  const team = panel.querySelector(".training-role-team");
  let hint = team.querySelector(".training-role-source-hint");
  const label = ROLE_SOURCE_LABELS[tournamentOwnRoleSource];
  if (label) {
    if (!hint) {
      hint = document.createElement("div");
      hint.className = "training-role-source-hint";
      team.appendChild(hint);
    }
    hint.textContent = label;
  } else if (hint) {
    hint.remove();
  }
}

function updateTournamentConfirmButton() {
  updateTournamentEvaluateButton();
  updateTournamentEnemyRolesPanel();
  updateTournamentOwnRolesPanel();
  const row = document.getElementById("tournament-confirm-row");
  const btn = document.getElementById("tournament-confirm");
  // Il pannello dedicato "Conferma ruoli" prende il posto di questo bottone
  // per tutta la fase di role confirmation (roleConfirmOrder non-null =
  // pannello attivo, vedi updateRoleConfirmPanel) - va tenuto nascosto
  // anche qui, non solo li'. BUG REALE TROVATO da un test dell'utente
  // (2026-08-20, quarto giro): nascondere la riga SOLO dentro
  // updateRoleConfirmPanel() non bastava, perche' pollTournamentState()
  // chiama ANCHE questa funzione (la stessa!) una seconda volta subito
  // dopo, nello stesso identico ciclio di poll - quella seconda chiamata
  // ri-mostrava la riga prima ancora che il browser disegnasse il frame,
  // quindi il risultato visibile restava sempre "entrambi i bottoni". La
  // guardia va messa QUI, alla fonte, per essere valida a prescindere da
  // quante volte o da dove questa funzione viene richiamata (9 punti
  // diversi nel file) - non ha piu' senso inseguire ogni singolo
  // chiamante.
  if (!tournamentConnected || roleConfirmOrder) {
    row.classList.add("hidden");
    return;
  }
  row.classList.remove("hidden");
  btn.textContent = translateDraftButtonText(tournamentButtonTextRaw);
  btn.disabled = tournamentConfirmInFlight || tournamentButtonDisabledReal;
}

// Invia (senza confermare) la selezione di un campione alla draft VERA -
// unica azione a rischio reale di questo progetto. Scrive prima in locale in
// modo ottimistico (cosi' la UI reagisce subito, non fra 0.1s al prossimo
// poll), poi il prossimo poll sovrascrive comunque tutto con lo stato vero
// (autorevole) - se l'invio fallisce o il sito fa qualcosa di diverso da
// quanto ipotizzato qui, si autocorregge da solo entro un ciclo di poll.
async function sendTournamentSelection(name) {
  // NIENTE piu' guardia "una selezione gia' in sospeso blocca il resto" -
  // rimossa dopo un test reale (2026-08-17): impediva di cambiare idea su
  // un campione non ancora confermato, un flusso che l'utente usa
  // deliberatamente ("la selezione iniziale non serve a confermare
  // sicuramente il campione ma ad aspettare di selezionare quello giusto").
  // Il crash che aveva motivato quella guardia (2026-08-16) e' stato
  // rintracciato altrove nel frattempo (il watchdog che rimuoveva popup
  // dal DOM invece di nasconderli, corretto separatamente) - ricliccare un
  // campione diverso prima di confermare e' safe di per se'.
  const kind = currentTournamentTurn();
  if (!kind) return; // non e' il nostro turno, o fase non riconosciuta: click ignorato

  const team = tournamentSide === "blue" ? "left" : "right";
  const arr = kind === "ban" ? bans : teams;

  // Se stiamo gia' cambiando idea su una selezione in sospeso (stesso
  // team+kind), riusa LO STESSO slot - altrimenti indexOf(null)
  // troverebbe il prossimo slot libero (quello vecchio non e' piu' null,
  // ha gia' il campione precedente) e piazzerebbe la nuova scelta altrove
  // invece di sostituire quella di prima.
  const reuseSlot =
    tournamentPendingSlot && tournamentPendingSlot.team === team && tournamentPendingSlot.kind === kind;
  const index = reuseSlot ? tournamentPendingSlot.index : arr[team].indexOf(null);
  if (index === -1) return; // nessuno slot libero, non dovrebbe succedere

  const previousValue = arr[team][index]; // per ripristinare se l'invio fallisce davvero
  arr[team][index] = name;
  tournamentPendingSlot = { team, index, kind, sentAt: Date.now() };
  renderTeam("left");
  renderTeam("right");
  renderGrid();
  updateTournamentConfirmButton();

  const result = await backend.selectLiveDraft(name);
  if (result.error) {
    // Il click non e' arrivato a segno sul sito vero (visto in un test
    // reale, 2026-08-17: "dal browser fallback non appare nessun pick") -
    // annullare anche qui la scrittura ottimistica, altrimenti DriftDraft
    // continua a mostrare una selezione che sul sito non esiste davvero.
    arr[team][index] = previousValue;
    tournamentPendingSlot = null;
    renderTeam("left");
    renderTeam("right");
    renderGrid();
    updateTournamentConfirmButton();
    alert(`Errore inviando la selezione a drafter.lol: ${result.error}`);
  }
}

async function confirmTournamentSelection() {
  // Un secondo click mentre la richiesta precedente e' ancora in volo (es.
  // perche' sembra non rispondere) accodava un'altra conferma sullo stesso
  // worker, sovrapponendosi - trovato in un test reale (2026-08-16, 2
  // tentativi falliti in due modi diversi dopo un solo click percepito).
  if (tournamentConfirmInFlight) return;

  const kind = currentTournamentTurn();
  if (!kind || !tournamentSide) return;
  const team = tournamentSide === "blue" ? "left" : "right";

  // Preferisce tournamentPendingSlot (piu' immediato, valorizzato appena
  // inviamo NOI una selezione), ma se non corrisponde si affida al dato
  // vero del poll (bansPending/picksPending) - copre il caso in cui il
  // bottone risulti comunque abilitato (il sito mostra davvero qualcosa in
  // sospeso) senza che il nostro tracciamento locale l'abbia registrato.
  const pendingArr = kind === "ban" ? bansPending : picksPending;
  const index =
    tournamentPendingSlot && tournamentPendingSlot.team === team && tournamentPendingSlot.kind === kind
      ? tournamentPendingSlot.index
      : pendingArr[team].indexOf(true);
  if (index === -1) return; // niente risulta davvero in sospeso, non c'e' nulla da confermare

  tournamentConfirmInFlight = true;
  document.getElementById("tournament-confirm").disabled = true;

  const result = await backend.confirmLiveDraft(tournamentSide, kind, index);

  tournamentConfirmInFlight = false;
  if (!result.error) {
    tournamentPendingSlot = null;
    // BUG trovato in un test reale (2026-08-17): senza ridisegnare qui, lo
    // slot restava visivamente "lampeggiante" (classe .pending applicata
    // all'ultimo render, quando tournamentPendingSlot era ancora valorizzato)
    // finche' non capitava un ALTRO evento a caso (es. la mossa del nemico)
    // che ridisegnasse tutto per un motivo indipendente - da qui anche la
    // "fatica" percepita nel selezionare il pick successivo: lo stato
    // visivamente stantio confondeva quale slot fosse davvero libero.
    renderTeam("left");
    renderTeam("right");
    renderGrid();
  }
  updateTournamentConfirmButton();
  if (result.error) {
    alert(`Errore confermando la selezione su drafter.lol: ${result.error}`);
  }
}

// FASE 2 estesa (2026-08-17): il "Ready" iniziale della draft passa dallo
// stesso bottone di "Conferma selezione" (stessa posizione del sito vero,
// dove #draft-button mostra "Ready" prima e "Ban"/"Pick" poi) invece di
// dover per forza usare la finestra di riserva. Il backend esiste gia' dalla
// Fase 1 (session.click_ready(), azione a basso rischio: non sceglie/invia
// nulla, segnala solo "pronto").
async function sendTournamentReady() {
  if (tournamentConfirmInFlight) return;
  tournamentConfirmInFlight = true;
  document.getElementById("tournament-confirm").disabled = true;

  const result = await backend.readyLiveDraft();

  tournamentConfirmInFlight = false;
  updateTournamentConfirmButton();
  if (result.error) {
    alert(`Errore inviando "pronto" a drafter.lol: ${result.error}`);
  }
}

// Router del click sull'unico bottone condiviso - decide se siamo ancora
// nella fase "Ready" (state.buttonText del sito lo dice) o gia' in una fase
// di ban/pick.
function handleTournamentConfirmClick() {
  if (tournamentIsReadyPhase) {
    sendTournamentReady();
  } else {
    confirmTournamentSelection();
  }
}

function openTournamentModal() {
  document.getElementById("tournament-modal").classList.remove("hidden");
}

function closeTournamentModal() {
  document.getElementById("tournament-modal").classList.add("hidden");
}

// --- Connessione in due tempi alla draft room (2026-09-05) ---------------
// Prima si incolla SOLO il link: la sessione apre la room e si ferma sul
// dialogo "Join the Draft", da cui leggiamo i team veri e i lati liberi
// (vedi _JOIN_OPTIONS_JS in drafter_live.py). Poi si sceglie qui, cliccando,
// invece di digitare a memoria il nome esatto del team come si doveva fare
// prima. Bonus preso in prestito dal sito: se l'altro team ha gia' occupato
// un lato, quel lato arriva gia' marcato non disponibile e non lo si puo'
// scegliere per sbaglio.
let tournamentJoinTeams = [];
let tournamentJoinTeamSelected = null;
let tournamentJoinSides = { blue: false, red: false };

function renderTournamentJoinChoices() {
  const box = document.getElementById("tournament-join-choices");
  const teamRow = document.getElementById("tournament-team-choices");
  const sideRow = document.getElementById("tournament-side-choices");
  box.classList.toggle("hidden", tournamentJoinTeams.length === 0);

  teamRow.innerHTML = "";
  for (const team of tournamentJoinTeams) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tournament-side-btn";
    btn.textContent = team;
    btn.classList.toggle("active", team === tournamentJoinTeamSelected);
    btn.addEventListener("click", () => selectTournamentTeam(team));
    teamRow.appendChild(btn);
  }

  sideRow.innerHTML = "";
  for (const [side, label] of [["blue", "Blue Side"], ["red", "Red Side"]]) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tournament-side-btn";
    btn.textContent = label;
    // Senza un team scelto il sito tiene disabilitati ENTRAMBI i lati:
    // rispecchiamo la stessa regola invece di lasciar cliccare a vuoto.
    const usable = !!tournamentJoinTeamSelected && tournamentJoinSides[side];
    btn.disabled = !usable;
    if (!usable && tournamentJoinTeamSelected) {
      btn.title = "Lato gia' occupato in questa draft room";
    }
    btn.classList.toggle("active", side === tournamentModeSelectedSide);
    btn.addEventListener("click", () => selectTournamentSide(side));
    sideRow.appendChild(btn);
  }
}

async function selectTournamentTeam(team) {
  const statusEl = document.getElementById("tournament-connect-status");
  tournamentJoinTeamSelected = team;
  tournamentModeSelectedSide = null; // i lati liberi dipendono dal team
  renderTournamentJoinChoices();

  statusEl.style.color = "";
  statusEl.textContent = "Controllo i lati disponibili...";
  const result = await backend.liveDraftJoinOptions(team);
  if (result.error) {
    statusEl.textContent = result.error;
    return;
  }
  tournamentJoinSides = result.sides || { blue: false, red: false };
  statusEl.textContent = "";
  renderTournamentJoinChoices();

  if (!tournamentJoinSides.blue && !tournamentJoinSides.red) {
    statusEl.textContent =
      "Nessun lato libero per questo team: potrebbe averlo gia' preso qualcuno del tuo team.";
  }
}

function selectTournamentSide(side) {
  tournamentModeSelectedSide = side;
  renderTournamentJoinChoices();
}

function resetTournamentJoinChoices() {
  tournamentJoinTeams = [];
  tournamentJoinTeamSelected = null;
  tournamentModeSelectedSide = null;
  tournamentJoinSides = { blue: false, red: false };
  renderTournamentJoinChoices();
  document.getElementById("tournament-connect").textContent = "Connetti";
}

// Il bottone del modale fa DUE lavori diversi a seconda della fase: apre la
// room ("Connetti") oppure entra davvero con le scelte fatte ("Entra nella
// draft"). Un solo bottone invece di due perche' le due azioni non sono mai
// disponibili insieme.
async function connectTournament() {
  const statusEl = document.getElementById("tournament-connect-status");
  const connectBtn = document.getElementById("tournament-connect");

  // Fase 2: abbiamo gia' le opzioni a video, si entra.
  if (tournamentJoinTeams.length > 0) {
    if (!tournamentJoinTeamSelected) {
      statusEl.textContent = "Scegli il tuo team.";
      return;
    }
    if (!tournamentModeSelectedSide) {
      statusEl.textContent = "Scegli il lato.";
      return;
    }
    statusEl.style.color = "";
    statusEl.textContent = "Ingresso nella draft...";
    const joined = await backend.liveDraftJoin(
      tournamentJoinTeamSelected,
      tournamentModeSelectedSide
    );
    if (joined.error) {
      statusEl.textContent = joined.error;
      return;
    }
    finalizeTournamentConnection(document.getElementById("tournament-url").value.trim());
    return;
  }

  // Fase 1: solo il link.
  const url = document.getElementById("tournament-url").value.trim();
  if (!url) {
    statusEl.textContent = "Incolla prima il link della draft room.";
    return;
  }

  statusEl.style.color = "";
  statusEl.textContent = "Apertura della draft room... (può richiedere qualche secondo)";
  const result = await backend.connectLiveDraft(url);
  if (result.error) {
    statusEl.textContent = result.error;
    return;
  }

  tournamentJoinTeams = (result.teams || []).map((t) => t.name);
  tournamentJoinSides = result.sides || { blue: false, red: false };
  tournamentJoinTeamSelected = null;
  tournamentModeSelectedSide = null;
  renderTournamentJoinChoices();

  if (tournamentJoinTeams.length === 0) {
    statusEl.textContent = "Nessun team trovato in questa draft room.";
    return;
  }
  statusEl.textContent = "Scegli il tuo team, poi il lato.";
  connectBtn.textContent = "Entra nella draft";
}

// Parte comune a fine connessione: accende la modalita' torneo nella UI.
// Estratta perche' la usa anche "Prossima draft" della stessa serie.
function finalizeTournamentConnection(url) {
  tournamentConnected = true;
  tournamentSide = tournamentModeSelectedSide;
  tournamentUrl = url;
  tournamentPendingSlot = null;
  activeSlot = null; // uno slot attivo da prima di connettersi non ha piu' senso in torneo
  closeTournamentModal();
  resetTournamentJoinChoices();
  document.getElementById("tournament-mode-open").classList.add("connected");
  document.getElementById("tournament-status").classList.remove("hidden");
  document.getElementById("training-mode-open").disabled = true; // mutuamente esclusiva con la modalita' training
  updateTournamentConfirmButton();
  startTournamentPolling();
}

// Tornando in modalita' pianificazione i dati della draft appena specchiata
// non hanno piu' senso restare a video (richiesta esplicita dell'utente,
// 2026-08-17: "quando si passa da modalita' torneo a modalita' di planning,
// i dati devono essere resettati, da entrambi i lati") - simmetrico a come
// planning->torneo "resetta" gia' di fatto (la connessione sovrascrive
// tutto col primo poll, quindi non serviva farlo esplicitamente lì).
function resetDraftForPlanningMode() {
  activeSlot = null;
  teams = { left: [null, null, null, null, null], right: [null, null, null, null, null] };
  bans = { left: [null, null, null, null, null], right: [null, null, null, null, null] };
  picksPending = { left: [false, false, false, false, false], right: [false, false, false, false, false] };
  bansPending = { left: [false, false, false, false, false], right: [false, false, false, false, false] };
  fearlessPicks = [];
  tournamentRoleConfirmLive = false;
  roleConfirmOriginalOrder = null;
  roleConfirmOrder = null;
  roleConfirmPhaseSeen = false;
  tournamentConfirmedRoleOrder = null;
  tournamentEvaluation = null;
  // suggestionsEnabled (la preferenza del toggle) NON va azzerata qui -
  // persiste tra una connessione e l'altra e tra una modalita' e l'altra
  // (stesso principio di laneCounterMode) - solo i DATI gia' scaricati,
  // ormai riferiti a una draft che non c'e' piu', vanno buttati.
  blueSuggestions = [];
  redSuggestions = [];
  blueNames = new Set();
  redNames = new Set();
  blueThin = false;
  redThin = false;
  tournamentOwnRoleOrder = null;
  tournamentOwnRoleSource = null;
  tournamentOwnRoleTags = null;
  tournamentEnemyRoleOrder = null;
  tournamentEnemyRoleSource = null;
  tournamentEnemyRoleTags = null;
  document.getElementById("role-confirm-panel").classList.add("hidden");
  document.getElementById("tournament-confirm-row").classList.remove("hidden");
  document.getElementById("tournament-own-roles").classList.add("hidden");
  document.getElementById("tournament-enemy-roles").classList.add("hidden");
  document.getElementById("tournament-evaluation").classList.add("hidden");
  document.getElementById("tournament-evaluation").innerHTML = "";
  renderTeam("left");
  renderTeam("right");
  renderFearlessPanel();
  renderGrid();
  refreshDetection("left");
  refreshDetection("right");
}

async function disconnectTournament() {
  stopTournamentPolling();
  tournamentConnected = false;
  tournamentPendingSlot = null;
  tournamentUrl = null;
  document.getElementById("tournament-mode-open").classList.remove("connected");
  document.getElementById("tournament-status").classList.add("hidden");
  document.getElementById("training-mode-open").disabled = false;
  updateTournamentConfirmButton();
  await backend.disconnectLiveDraft();
  resetDraftForPlanningMode();
}

// Fearless draft: "prossima draft" e' una riconnessione guidata, non una
// funzione nuova - il sito stesso richiede un "Join the Draft" completo ad
// ogni game (inclusa la riscelta del lato, perche' e' la squadra che perde
// a decidere se cambiarlo, informazione che non possiamo dedurre da soli).
// Disconnette, precompila URL (stesso room ID, ?game= incrementato) e nome
// team nel modale gia' esistente, e lascia che sia il coach a confermare
// lato + Connetti come al primo collegamento. Nessun controllo nostro su
// "la draft precedente e' davvero finita" - se e' troppo presto, e' il
// sito stesso a rifiutare la connessione (stesso path di errore gia'
// gestito da connectTournament).
function computeNextGameUrl(currentUrl) {
  try {
    const u = new URL(currentUrl);
    const current = parseInt(u.searchParams.get("game") || "1", 10);
    u.searchParams.set("game", String(current + 1));
    return u.toString();
  } catch (err) {
    return currentUrl;
  }
}

async function advanceToNextGame() {
  if (!tournamentUrl) return;
  const nextUrl = computeNextGameUrl(tournamentUrl);
  await disconnectTournament();

  document.getElementById("tournament-url").value = nextUrl;
  // La game successiva e' una room a se': team e lati vanno riletti da capo
  // (il sito puo' anche aver invertito i lati fra una game e l'altra).
  resetTournamentJoinChoices();
  document.getElementById("tournament-connect-status").textContent = "";
  openTournamentModal();
}

// Pannello "Usati in serie" vicino ai ban di ciascun lato - mostra le
// entry lette dal sito raggruppate per LATO DI QUELLA GAME (stessa
// organizzazione del sito stesso: non segue un'identita' di squadra
// persistente attraverso i cambi di lato fra una game e l'altra).
function renderFearlessPanel() {
  for (const side of ["left", "right"]) {
    const sideKey = side === "left" ? "blue" : "red";
    const container = document.getElementById(`fearless-pool-${side}`);
    const iconsEl = container.querySelector(".fearless-pool-icons");
    const entries = fearlessPicks.filter((p) => p.side === sideKey);

    container.classList.toggle("hidden", entries.length === 0);
    iconsEl.innerHTML = "";
    for (const entry of entries) {
      const champ = champions.find((c) => c.name === entry.champion);
      if (!champ) continue;
      const img = document.createElement("img");
      img.className = "fearless-pool-icon";
      img.src = champ.icon;
      img.title = `${entry.champion} - Game ${entry.game}`;
      applyCompBorderVar(img, champ);
      iconsEl.appendChild(img);
    }
  }
}

// Role confirmation - vedi dichiarazione di roleConfirmOrder piu' sopra.
// state.buttonText e' gia' la fonte di verita' usata ovunque nel resto di
// questa integrazione (translateDraftButtonText, tournamentIsReadyPhase) -
// stesso principio qui: NON serve un flag nuovo dal backend per sapere "sono
// in questa fase", basta guardare il testo del bottone reale.
//
// BUG REALE TROVATO da un test dell'utente (2026-08-20): il testo passa per
// uno stato intermedio "Waiting for red"/"Waiting for blue" (sul NOSTRO
// bottone) appena clicchiamo pronto, PRIMA che anche l'avversario lo faccia -
// ne' "role confirmation" ne' "confirm roles" lo intercettavano, quindi
// updateRoleConfirmPanel() credeva la fase gia' finita, nascondeva il
// pannello e AZZERAVA roleConfirmOrder - al ricomparire (avversario pronto,
// "Confirm roles") ripartiva da capo dall'ordine di default, cancellando
// quanto il coach aveva gia' sistemato. Fix: un flag "sticky"
// (roleConfirmPhaseSeen) che una volta diventato true per un segnale
// INEQUIVOCABILE (solo "role confirmation"/"confirm roles"/lane live -
// stringhe che non ricorrono altrove nel draft) resta true anche durante un
// "waiting" successivo - il ready-up INIZIALE della draft (prima di
// ban/pick) non puo' mai essere scambiato per questo, perche' fra i due c'e'
// sempre l'intero ban/pick e roleConfirmPhaseSeen viene azzerato ad ogni
// uscita vera dalla fase.
let roleConfirmPhaseSeen = false;

function tournamentRolePhaseSignal() {
  return /role confirmation|confirm roles/i.test(tournamentButtonTextRaw) || tournamentRoleConfirmLive;
}

// Chiamata ad OGNI poll (100ms), non solo quando ban/pick cambiano - deve
// accorgersi il prima possibile della transizione in/fuori da questa fase.
// Edge-triggered: inizializza/renderizza SOLO al primo rilevamento, poi si
// fa da parte e lascia che sia il drag locale a gestire i re-render (ri-
// disegnare ad ogni tick da qui cancellerebbe un drag a meta').
// La visibilita' di #tournament-confirm-row (il bottone generico) e'
// governata SOLO da updateTournamentConfirmButton(), non da qui - quella
// funzione controlla direttamente roleConfirmOrder (non-null = questo
// pannello e' attivo) e si nasconde da sola di conseguenza. BUG REALE
// TROVATO da due test dal vivo consecutivi (2026-08-20, terzo e quarto
// giro): nascondere quella riga QUI dentro non bastava in nessuna delle due
// forme provate (solo alla prima rilevazione: veniva ri-mostrata dal tick
// di poll successivo; riaffermata ad ogni tick ma PRIMA della seconda
// chiamata a updateTournamentConfirmButton() nello stesso identico ciclo di
// poll: quella chiamata la ri-mostrava comunque subito dopo, stesso frame).
// L'unico posto davvero robusto - a prescindere da quante volte o da dove
// updateTournamentConfirmButton() viene richiamata (9 punti nel file) - e'
// dentro la funzione stessa. Vedi li' per il dettaglio.
function updateRoleConfirmPanel() {
  const panel = document.getElementById("role-confirm-panel");

  if (tournamentRolePhaseSignal()) {
    roleConfirmPhaseSeen = true;
  }
  const stillInPhase =
    tournamentConnected &&
    roleConfirmPhaseSeen &&
    (tournamentRolePhaseSignal() || tournamentButtonTextRaw.toLowerCase().includes("waiting"));

  if (!stillInPhase) {
    if (roleConfirmOrder) {
      panel.classList.add("hidden");
      roleConfirmOriginalOrder = null;
      roleConfirmOrder = null;
    }
    roleConfirmPhaseSeen = false;
    return;
  }

  panel.classList.remove("hidden");

  if (roleConfirmOrder) return; // gia' inizializzato per questa fase, il resto (creare gli slot) non va ripetuto

  const team = tournamentSide === "blue" ? "left" : "right";
  roleConfirmOriginalOrder = teams[team].slice();
  roleConfirmOrder = teams[team].slice();
  document.getElementById("role-confirm-status").textContent = "";
  renderRoleConfirmSlots();
}

function renderRoleConfirmSlots() {
  const el = document.getElementById("role-confirm-slots");
  el.innerHTML = "";

  roleConfirmOrder.forEach((name, i) => {
    const slot = document.createElement("div");
    slot.className = "role-confirm-slot";
    slot.draggable = true;

    const label = document.createElement("div");
    label.className = "role-confirm-lane-label";
    label.textContent = ROLE_CONFIRM_LANES[i];
    slot.appendChild(label);

    const champ = champions.find((c) => c.name === name);
    if (champ) {
      const img = document.createElement("img");
      img.className = "role-confirm-champ-icon";
      img.src = champ.icon;
      applyCompBorderVar(img, champ);
      // Stesso gotcha gia' noto (drag&drop nell'app buildata, vedi Fix 3
      // nelle note di progetto): senza questo, Chromium/WebView2 prova ad
      // avviare un drag NATIVO dell'immagine invece di lasciar gestire il
      // drag&drop custom qui sotto.
      img.style.webkitUserDrag = "none";
      slot.appendChild(img);
      const nameLabel = document.createElement("span");
      nameLabel.className = "role-confirm-champ-name";
      nameLabel.textContent = name;
      slot.appendChild(nameLabel);
    }

    slot.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(i));
      e.dataTransfer.effectAllowed = "move";
    });
    slot.addEventListener("dragover", (e) => {
      e.preventDefault();
      slot.classList.add("drag-over");
    });
    slot.addEventListener("dragleave", () => slot.classList.remove("drag-over"));
    slot.addEventListener("drop", (e) => {
      e.preventDefault();
      slot.classList.remove("drag-over");
      const fromIndex = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (Number.isNaN(fromIndex) || fromIndex === i) return;
      // Stesso meccanismo del sito (arrayMove: estrai e reinserisci, mai
      // uno scambio a coppia) - l'anteprima locale deve comportarsi
      // identica a quello che poi verra' davvero replicato.
      const [item] = roleConfirmOrder.splice(fromIndex, 1);
      roleConfirmOrder.splice(i, 0, item);
      renderRoleConfirmSlots();
    });

    el.appendChild(slot);
  });
}

// Al click: (1) se non abbiamo ancora segnalato pronto per questa fase sul
// sito, lo fa; (2) aspetta che state.roleConfirmActive diventi vero (serve
// anche l'avversario pronto, fuori dal nostro controllo - il polling da
// 100ms gia' in corso aggiorna tournamentRoleConfirmLive da solo, qui ci si
// limita ad aspettarlo); (3) calcola e invia l'ordine desiderato, che il
// backend traduce in mosse di drag e replica sul sito. Se qualunque passo
// fallisce o l'avversario non risulta mai pronto in tempo, non si tocca
// nulla sul sito - il suo stesso countdown blocchera' comunque l'ordine di
// default, rete di sicurezza gia' concordata in fase di design.
async function confirmRoleOrder() {
  if (roleConfirmInFlight || !roleConfirmOrder) return;
  roleConfirmInFlight = true;
  const btn = document.getElementById("role-confirm-button");
  const status = document.getElementById("role-confirm-status");
  btn.disabled = true;

  if (tournamentIsReadyPhase) {
    status.textContent = "Segnalo pronto sul sito...";
    const readyResult = await backend.readyLiveDraft();
    if (readyResult.error) {
      status.textContent = `Errore: ${readyResult.error}`;
      roleConfirmInFlight = false;
      btn.disabled = false;
      return;
    }
  }

  if (!tournamentRoleConfirmLive) {
    status.textContent = "In attesa che anche l'avversario sia pronto...";
    const deadline = Date.now() + 27000; // margine sotto i ~29s reali del sito (vedi note di progetto)
    while (!tournamentRoleConfirmLive && Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 200));
    }
  }

  if (!tournamentRoleConfirmLive) {
    status.textContent =
      "L'avversario non è mai risultato pronto in tempo - non ho toccato nulla, il sito confermerà da solo l'ordine di default.";
    roleConfirmInFlight = false;
    btn.disabled = false;
    return;
  }

  status.textContent = "Replico l'ordine sul sito...";
  const orderSent = roleConfirmOrder.slice();
  const result = await backend.confirmRoleOrder(orderSent);
  roleConfirmInFlight = false;
  // Diagnostico per il prossimo giro se dovesse ripresentarsi un problema -
  // stampa cosa abbiamo davvero inviato e cosa ha risposto il backend
  // (mosse calcolate, ordine effettivamente letto sul sito dopo il drag),
  // cosi' non serve ripartire da zero per capire dove si e' rotto.
  console.log("[DriftDraft role-confirm] inviato:", orderSent, "risposta:", result);

  if (result.error) {
    status.textContent = `Errore: ${result.error}`;
    btn.disabled = false;
  } else {
    status.textContent = "Ruoli confermati sul sito.";
    tournamentConfirmedRoleOrder = orderSent;
    // Non serve nascondere il pannello qui: il prossimo poll rileva che
    // buttonText e' uscito da questa fase e updateRoleConfirmPanel() lo fa
    // da solo (stesso meccanismo edge-triggered dell'ingresso in fase).
  }
}

// --- Barra del timer (modalita' torneo, 2026-09-05) ---------------------
// Richiesta dell'utente: il timer numerico "e' piccolino e si nota veramente
// poco". Ora l'INTERA barra di stato fa da indicatore: una striscia piena
// che si svuota col passare dei secondi, verde -> giallo -> rosso con
// passaggio continuo ("il colore non è uno stacco netto ma preferisco un
// cambiamento dinamico"), e lampeggiante sotto i 5 secondi.
//
// Il MASSIMO non e' fissato a 30: drafter.lol puo' usare durate diverse (e
// le fasi di ban e pick non sono per forza uguali). Si ricava osservando il
// timer stesso - quando RISALE vuol dire che e' iniziato un turno nuovo, e
// quel valore diventa il nuovo massimo da cui calcolare la percentuale.
let tournamentTimerMax = 0;
let tournamentTimerPrev = null;

// Verde finche' c'e' tempo, giallo verso i 15s, rosso verso i 10s.
// Interpolazione sulla TINTA (hue) invece di tre colori fissi: e' cio' che
// rende il passaggio continuo invece che a scatti.
function tournamentTimerHue(sec, max) {
  if (sec >= 15 && max > 15) {
    // da 15s (giallo, hue 55) al massimo del turno (verde, hue 130)
    const t = Math.min(1, (sec - 15) / (max - 15));
    return 55 + t * 75;
  }
  if (sec >= 10) {
    // da 10s (rosso, hue 0) a 15s (giallo, hue 55)
    return ((sec - 10) / 5) * 55;
  }
  return 0; // sotto i 10 secondi: rosso pieno
}

function updateTournamentTimerBar(rawTimer) {
  const bar = document.getElementById("tournament-timer-bar");
  const sec = parseInt(rawTimer, 10);

  // Nessun timer attivo (fasi di attesa, draft finita): barra spenta.
  if (!Number.isFinite(sec) || sec <= 0) {
    bar.style.width = "0%";
    bar.classList.remove("critical");
    tournamentTimerMax = 0;
    tournamentTimerPrev = null;
    return;
  }

  if (tournamentTimerPrev === null || sec > tournamentTimerPrev) {
    tournamentTimerMax = sec; // primo valore letto, oppure turno nuovo
  }
  tournamentTimerPrev = sec;
  const max = Math.max(tournamentTimerMax, sec, 1);

  bar.style.width = `${Math.max(0, Math.min(100, (sec / max) * 100))}%`;
  bar.style.backgroundColor = `hsl(${tournamentTimerHue(sec, max)} 72% 45% / 0.42)`;
  bar.classList.toggle("critical", sec <= 5);
}

function startTournamentPolling() {
  stopTournamentPolling();
  pollTournamentState();
  tournamentPollTimer = setInterval(pollTournamentState, 100);
}

function stopTournamentPolling() {
  if (tournamentPollTimer) {
    clearInterval(tournamentPollTimer);
    tournamentPollTimer = null;
  }
}

async function pollTournamentState() {
  const state = await backend.getLiveDraftState();

  if (!state.connected) {
    // la sessione lato server si e' interrotta (es. la finestra automatica
    // e' stata chiusa) - non insistere a oltranza, ferma il poll e avvisa.
    stopTournamentPolling();
    tournamentConnected = false;
    tournamentPendingSlot = null;
    document.getElementById("tournament-mode-open").classList.remove("connected");
    document.getElementById("tournament-step").textContent = "Disconnesso";
    document.getElementById("tournament-timer").textContent = state.error || "";
    updateTournamentTimerBar(null);
    updateTournamentConfirmButton();
    resetDraftForPlanningMode();
    return;
  }

  // Aggiornati ad OGNI tick, non solo quando cambiano ban/pick: servono
  // sempre freschi a currentTournamentTurn() per decidere se un click in
  // griglia in questo preciso momento deve diventare un'azione vera.
  tournamentSide = state.side;
  tournamentLastStep = state.step || "";
  tournamentButtonTextRaw = state.buttonText || "";
  tournamentIsReadyPhase = tournamentButtonTextRaw.toLowerCase().includes("ready");
  tournamentButtonDisabledReal = !!state.buttonDisabled;
  document.getElementById("tournament-step").textContent = state.step || "";
  document.getElementById("tournament-timer").textContent = state.timer ? `${state.timer}s` : "";
  updateTournamentTimerBar(state.timer);

  // Come sopra, fresco ad OGNI tick: confirmRoleOrder() aspetta esattamente
  // questo segnale (window di drag apparsa sul sito, serve anche
  // l'avversario pronto) tramite questa stessa variabile aggiornata dal
  // poll gia' in corso, invece di un polling separato duplicato.
  tournamentRoleConfirmLive = !!state.roleConfirmActive;
  updateRoleConfirmPanel();

  // Tag ruolo REALE di entrambi i lati (vedi drafter_live.py per come viene
  // letto dal sito) - fresco ad ogni poll come sopra, letto poi da
  // updateTournamentEnemyRolesPanel/updateTournamentOwnRolesPanel per
  // l'auto-aggiornamento dei due pannelli "Ruoli nemici"/"Ruoli nostri".
  tournamentEnemyRoleTags = tournamentSide === "blue" ? state.redRoleTags : state.blueRoleTags;
  tournamentOwnRoleTags = tournamentSide === "blue" ? state.blueRoleTags : state.redRoleTags;

  // Rete di sicurezza finale per il pending: se per qualunque motivo il
  // segnale preciso qui sotto (pulse-animation-*) non arrivasse mai a
  // liberarlo, un'azione dura comunque solo ~25s (verificato navigando il
  // sito) - oltre quel margine non ha piu' senso tenerlo comunque. Ridisegna
  // anche qui (stesso bug del re-render mancante gia' corretto in
  // confirmTournamentSelection): pulire solo la variabile senza ridisegnare
  // lascerebbe lo slot lampeggiante a video finche' non capita altro.
  if (tournamentPendingSlot && Date.now() - tournamentPendingSlot.sentAt > 28000) {
    tournamentPendingSlot = null;
    renderTeam("left");
    renderTeam("right");
    renderGrid();
  }
  updateTournamentConfirmButton();

  const signature = JSON.stringify([
    state.bluePicks,
    state.redPicks,
    state.blueBans,
    state.redBans,
    state.bluePicksPending,
    state.redPicksPending,
    state.blueBansPending,
    state.redBansPending,
    state.fearlessPicks,
  ]);
  if (signature === tournamentLastPickSignature) return;
  tournamentLastPickSignature = signature;

  // Segnale preciso di "confermato" per la NOSTRA selezione in sospeso: lo
  // stesso pulse-animation-* che permette di specchiare il lampeggio
  // dell'avversario (sotto) ci dice anche, per il nostro slot specifico,
  // quando il sito lo considera davvero bloccato - piu' rapido e piu'
  // affidabile del fallback a tempo sopra (che resta solo come ultima
  // rete). Provato e scartato in due test reali precedenti (2026-08-17):
  // dedurre "confermato" dal cambiamento del nome/ID scattava troppo
  // presto (il sito mostra la scelta in sospeso nello stesso punto di
  // quella bloccata); dedurlo da state.buttonDisabled restava bloccato per
  // sempre fra due turni consecutivi dello stesso lato (es. Blue pick 2 ->
  // Blue pick 3, ordine reale 1-2-2-1 dei pick).
  if (tournamentPendingSlot) {
    const side = tournamentPendingSlot.team === "left" ? "blue" : "red";
    const key = tournamentPendingSlot.kind === "ban" ? `${side}BansPending` : `${side}PicksPending`;
    if (state[key] && state[key][tournamentPendingSlot.index] === false) {
      tournamentPendingSlot = null;
      updateTournamentConfirmButton();
    }
  }

  const toSlotValue = (name) => (name && name !== "None" ? name : null);
  teams.left = state.bluePicks.map(toSlotValue);
  teams.right = state.redPicks.map(toSlotValue);
  bans.left = state.blueBans.map(toSlotValue);
  bans.right = state.redBans.map(toSlotValue);
  picksPending.left = state.bluePicksPending;
  picksPending.right = state.redPicksPending;
  bansPending.left = state.blueBansPending;
  bansPending.right = state.redBansPending;
  fearlessPicks = state.fearlessPicks || [];

  renderTeam("left");
  renderTeam("right");
  renderFearlessPanel();
  renderGrid();
  refreshDetection("left");
  refreshDetection("right");
  refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
}

// Toggle "Pick suggeriti" - vive nel toolbar sempre visibile (non piu'
// dentro #tournament-status) da quando la feature e' stata estesa a tutte e
// 3 le modalita' (2026-08-30), quindi va cablato una volta sola qui invece
// che dentro setupTournamentMode.
function setupSuggestionsToggle() {
  const suggestionsToggle = document.getElementById("suggestions-toggle");
  document.getElementById("suggestions-sync").addEventListener("click", startDataSync);
  refreshSuggestionsDataInfo();
  suggestionsToggle.checked = suggestionsEnabled;
  // Le due righe partono NASCOSTE quando non c'e' niente da mostrare (di
  // norma all'avvio: interruttore spento, o acceso ma draft ancora vuota).
  // Serve una chiamata esplicita qui: fino al 2026-09-06 una riga vuota era
  // letteralmente invisibile (un contenitore flex senza figli), da quando
  // c'e' l'etichetta "Blue Side"/"Red Side" invece resterebbe a video da sola.
  renderSuggestionsPanel();
  suggestionsToggle.addEventListener("change", () => {
    suggestionsEnabled = suggestionsToggle.checked;
    localStorage.setItem("suggestionsEnabled", suggestionsEnabled);
    refreshSuggestions();
  });
  document.getElementById("pool-filter").addEventListener("click", () => {
    poolFilterEnabled = !poolFilterEnabled;
    localStorage.setItem("poolFilterEnabled", poolFilterEnabled);
    refreshSuggestions(); // ridisegna anche il chip, vedi renderSuggestionsPanel
  });
}

function setupTournamentMode() {
  document.getElementById("tournament-mode-open").addEventListener("click", openTournamentModal);
  document.getElementById("tournament-close").addEventListener("click", closeTournamentModal);
  // I bottoni Blue/Red non sono piu' fissi nell'HTML: vengono creati (con i
  // team) da renderTournamentJoinChoices dopo l'apertura del link, ognuno
  // col proprio listener - vedi la connessione in due tempi piu' sopra.
  document.getElementById("tournament-connect").addEventListener("click", connectTournament);
  document.getElementById("tournament-disconnect").addEventListener("click", disconnectTournament);
  document.getElementById("tournament-next-game").addEventListener("click", advanceToNextGame);
  document.getElementById("tournament-confirm").addEventListener("click", handleTournamentConfirmClick);
  document.getElementById("tournament-evaluate").addEventListener("click", evaluateTournamentDraft);
  document.getElementById("role-confirm-button").addEventListener("click", confirmRoleOrder);
}

// Modalita' training (feature 4) - a differenza di "modalita' torneo" non
// c'e' un sito esterno da specchiare: ogni azione e' un'unica richiesta
// sincrona (POST /api/training/pick) la cui risposta include GIA' l'
// eventuale mossa immediata del bot, quindi niente polling/timer qui.
// Riusa lo stesso "prende in mano tutta la GUI principale" di torneo:
// stessi team-slots/ban-slots/champion-grid, stesso gating (niente editing
// manuale mentre connessi, solo click in griglia nel proprio turno).

function openTrainingModal() {
  document.getElementById("training-modal").classList.remove("hidden");
  document.getElementById("training-start-status").textContent = "";
}

function closeTrainingModal() {
  document.getElementById("training-modal").classList.add("hidden");
}

function selectTrainingMode(mode) {
  trainingModeSelected = mode;
  document.getElementById("training-mode-team").classList.toggle("active", mode === "team");
  document.getElementById("training-mode-freeform").classList.toggle("active", mode === "freeform");
  // Le opzioni della squadra compaiono solo dove servono; l'op.gg avversario
  // sparisce li', perche' riempirebbe lo stesso posto (chi impersona il bot)
  // e due sorgenti per lo stesso slot sono solo un modo di contraddirsi.
  document.getElementById("training-team-pick").classList.toggle("hidden", mode !== "team");
  document
    .getElementById("training-enemy-pool-row")
    .classList.toggle("hidden", mode === "team");
  document.getElementById("training-enemy-pool-hint").classList.toggle("hidden", mode === "team");
  if (mode === "team") loadTrainingTeams();
}

function selectTrainingSide(side) {
  trainingSideSelected = side;
  document.getElementById("training-side-blue").classList.toggle("active", side === "blue");
  document.getElementById("training-side-red").classList.toggle("active", side === "red");
}

// Bot: {kind, champion} dell'ultima mossa, o null - Ancora: torneo/team/patch
// della draft pro di riferimento in modalita' "ancorata", null in "libera".
function updateTrainingStatusBar() {
  if (!trainingState) return;
  const stepEl = document.getElementById("training-step");
  const infoEl = document.getElementById("training-info");

  if (trainingState.finished) {
    stepEl.textContent = "Draft completata";
  } else if (trainingBusy) {
    // Ritardo deliberato prima di rivelare la mossa del bot (vedi
    // BOT_THINK_DELAY_MIN/MAX in training_bot.py) - richiesta esplicita
    // dell'utente 2026-08-26: senza un segnale esplicito la mossa del bot
    // sembrava istantanea "senza pensarci".
    stepEl.textContent = "Il bot sta pensando...";
  } else if (trainingState.isTraineeTurn) {
    stepEl.textContent = trainingPendingChampion
      ? `Hai selezionato ${trainingPendingChampion} - premi Conferma`
      : trainingState.currentAction.kind === "ban"
      ? "Tocca a te: banna"
      : "Tocca a te: scegli";
  } else {
    stepEl.textContent = "Turno del bot";
  }

  const parts = [];
  if (trainingState.lastBotAction) {
    const a = trainingState.lastBotAction;
    parts.push(`Bot: ${a.kind === "ban" ? "ha bannato" : "ha scelto"} ${a.champion}`);
  }

  // Prima qui c'era anche "Riferimento: X vs Y (patch Z)", cioe' da quale
  // partita storica venivano i suggerimenti. Ora conta CHI sta giocando: una
  // squadra ha abitudini vere, quella partita era contro un avversario che
  // nella draft in corso non c'e'.
  //
  // Le due provenienze del profilo si escludono e vanno dette per quello che
  // sono: scritto "da op.gg" con un profilo che arriva da Leaguepedia sarebbe
  // un'etichetta che mente, ed e' il difetto che abbiamo appena finito di
  // togliere da tre altri punti.
  if (trainingState.botPoolSize) {
    // Le corsie incerte finiscono nella riga visibile e non solo nel title:
    // e' l'unico punto in cui il coach puo' accorgersi che li' il bot sta
    // tirando a indovinare, e un title si vede solo se ci passi sopra.
    const conf = trainingState.botConfidence || {};
    const incerte = Object.values(conf).filter((v) => v < 1).length;
    const nota = incerte
      ? `, ${incerte} ${incerte === 1 ? "corsia incerta" : "corsie incerte"}`
      : "";
    const provenienza = trainingState.botTeam
      ? `gioca come ${trainingState.botTeam}`
      : "squadra avversaria da op.gg";
    parts.push(`Bot: ${provenienza} (${trainingState.botPoolSize} campioni${nota})`);
  }
  infoEl.textContent = parts.join(" · ");

  // Chi il bot pensa giochi quale corsia. La deduzione viene dai campioni
  // giocati (op.gg non dice il ruolo, vedi assign_players_to_roles lato
  // Python) e puo' sbagliare: senza mostrarla, un errore resterebbe
  // invisibile e il coach vedrebbe solo un bot che pesca cose strane. Sta
  // nel title e non a schermo per non allungare la riga di stato.
  const roster = trainingState.botRoster;
  const conf = trainingState.botConfidence || {};
  infoEl.title = roster
    ? "Ruoli dedotti da campioni giocati e op.gg:\n" +
      Object.entries(roster)
        .map(([r, nome]) => {
          // Sotto 1 quella corsia e' un'ipotesi e il bot ci mescola pick
          // meta: dirlo, invece di mostrare un roster che sembra tutto
          // ugualmente certo.
          const c = conf[r];
          return c !== undefined && c < 1
            ? `${r}: ${nome} - incerto, gioca ${Math.round((1 - c) * 100)}% meta`
            : `${r}: ${nome}`;
        })
        .join("\n")
    : "";
}

// Bottone "Conferma selezione" della griglia (vedi selectTrainingPending) -
// stesso pattern di updateTournamentConfirmButton, ma qui abilitato da una
// selezione LOCALE non ancora inviata (non da qualcosa che il sito esterno
// mostra gia' in sospeso, non c'e' nessun sito esterno qui).
// Le squadre impersonabili arrivano dalle tabelle (si aggiornano da sole ad
// ogni "Aggiorna dati"), quindi si chiedono al server invece di tenerne una
// lista scritta qui che invecchierebbe in silenzio.
async function loadTrainingTeams() {
  if (trainingTeamsCache) return;
  const r = await backend.trainingTeams();
  if (r.error) return;
  trainingTeamsCache = r.teams || [];
  const hint = document.getElementById("training-team-hint");
  hint.textContent = trainingTeamsCache.length
    ? `${trainingTeamsCache.length} squadre con almeno ${r.minDrafts} draft.`
    : "Nessuna squadra disponibile: aggiorna prima i dati.";
}

// Le voci del combobox: "Casuale" sempre in cima, poi le squadre che
// combaciano con quel che si sta scrivendo. La ricerca e' su sottostringa
// senza distinzione di maiuscole - i nomi veri sono cose come "Hanwha Life
// Esports", cercarli per parola intera sarebbe scomodo.
function trainingTeamOptions(query) {
  const q = (query || "").toLowerCase();
  const voci = [
    { key: "", label: "Casuale", sub: "una squadra a sorte", current: !trainingTeamSelected },
  ];
  for (const t of trainingTeamsCache || []) {
    if (q && !t.name.toLowerCase().includes(q)) continue;
    voci.push({
      key: t.name,
      label: t.name,
      sub: `${t.drafts} draft`,
      current: t.name === trainingTeamSelected,
    });
  }
  return voci;
}

function pickTrainingTeam(name) {
  trainingTeamSelected = name || "";
  // Il campo mostra la scelta; vuoto significa "Casuale", che e' anche il
  // testo del segnaposto - cosi' non c'e' uno stato in cui il campo e' vuoto
  // e non si capisce cosa succedera'.
  document.getElementById("training-team-combo").value = trainingTeamSelected;
  document.getElementById("training-start-status").textContent = "";
}

function updateTrainingConfirmButton() {
  const row = document.getElementById("training-confirm-row");
  const btn = document.getElementById("training-confirm");
  if (!trainingConnected || !trainingState) {
    row.classList.add("hidden");
    return;
  }

  if (trainingState.finished) {
    // A draft finita questo STESSO bottone diventa "Valuta la draft"
    // (richiesto esplicitamente dall'utente 2026-08-26: riusare il
    // bottone gia' familiare invece di aggiungerne uno nuovo) - abilitato
    // solo dopo che il trainee ha confermato l'assegnazione ruoli (vedi
    // confirmTrainingRoleOrder), la valutazione ha bisogno di sapere quale
    // pick va in quale corsia.
    row.classList.remove("hidden");
    btn.textContent = trainingEvaluation ? "Rivaluta la draft" : "Valuta la draft";
    btn.disabled = trainingBusy || !trainingState.traineeRoleOrder;
    btn.title = trainingState.traineeRoleOrder
      ? ""
      : "Conferma prima l'assegnazione dei ruoli qui sopra";
    return;
  }

  row.classList.remove("hidden");
  btn.textContent = trainingPendingChampion ? `Conferma: ${trainingPendingChampion}` : "Conferma selezione";
  btn.disabled = trainingBusy || !trainingState.isTraineeTurn || !trainingPendingChampion;
  btn.title = "";
}

// Click in griglia durante il training: SELEZIONA soltanto (non invia
// ancora) - richiesta esplicita dell'utente (2026-08-26), stesso principio
// di drafter.lol: un click sinistro sbagliato non deve poter bannare/pickare
// per errore, serve una conferma esplicita (vedi confirmTrainingPick sotto).
// Ricliccare lo STESSO campione gia' selezionato lo deseleziona.
function selectTrainingPending(name) {
  if (!trainingState || !trainingState.isTraineeTurn || trainingState.finished || trainingBusy) return;
  trainingPendingChampion = trainingPendingChampion === name ? null : name;
  renderGrid();
  updateTrainingConfirmButton();
  updateTrainingStatusBar();
}

function applyTrainingState(state) {
  trainingState = state;
  trainingPendingChampion = null;
  teams.left = state.bluePicks;
  teams.right = state.redPicks;
  bans.left = state.blueBans;
  bans.right = state.redBans;

  if (!state.finished) {
    // La draft puo' "tornare non finita" con un rewind - un ordine ruoli o
    // una valutazione gia' fatti per i vecchi 5 pick non hanno piu' senso
    // (il server azzera trainee_role_order anche lato suo, vedi rewind_to).
    trainingRoleOrder = null;
    trainingEvaluation = null;
  } else if (state.traineeRoleOrder) {
    // Gia' confermato server-side (es. dopo un refresh/riapertura pannello) -
    // quello e' autorevole.
    trainingRoleOrder = state.traineeRoleOrder.slice();
  } else if (!trainingRoleOrder) {
    // Prima volta che vediamo la draft finita con questi 5 pick - semina la
    // bozza dal suggerimento automatico (assign_roles), poi l'utente la
    // trascina a piacere. Se trainingRoleOrder e' GIA' valorizzato (bozza
    // locale non ancora confermata) non lo si tocca qui - stesso principio
    // "edge-triggered" gia' usato per roleConfirmOrder in modalita' torneo.
    const guess = state.roleAssignment[state.traineeSide];
    trainingRoleOrder = TRAINING_ROLE_ORDER.map((role) => guess.assignment[role].champion);
  }

  renderTeam("left");
  renderTeam("right");
  renderGrid();
  refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
  refreshDetection("left");
  refreshDetection("right");
  updateTrainingStatusBar();
  updateTrainingConfirmButton();
  renderTrainingRoleSummary();
  renderTrainingEvaluation();
}

// Invio VERO al server - solo dal bottone Conferma (vedi
// selectTrainingPending sopra) o dal rewind (vedi rewindTraining). Piazza
// subito il nostro pick in locale (ottimistico: reattivo al click anche se
// la risposta e' volutamente ritardata per la mossa del bot, vedi
// trainingBusy/"Il bot sta pensando" sopra) - se il server rifiuta,
// ripristina l'ultimo stato autorevole invece di lasciare un piazzamento
// fasullo a video.
async function confirmTrainingPick() {
  if (!trainingPendingChampion || !trainingState || !trainingState.isTraineeTurn || trainingBusy) return;
  const name = trainingPendingChampion;
  trainingPendingChampion = null;

  const action = trainingState.currentAction;
  const arr = action.kind === "ban" ? bans : teams;
  const team = action.side === "blue" ? "left" : "right";
  const idx = arr[team].indexOf(null);
  if (idx !== -1) {
    arr[team][idx] = name;
    renderTeam("left");
    renderTeam("right");
  }
  renderGrid();
  trainingBusy = true;
  updateTrainingConfirmButton();
  updateTrainingStatusBar();

  const result = await backend.trainingPick(name);
  trainingBusy = false;

  if (result.error) {
    alert(result.error);
    const fresh = await backend.trainingState();
    if (fresh.active) applyTrainingState(fresh);
    return;
  }
  applyTrainingState(result);
}

// "Ripeti da qui" (rewind) - richiesta esplicita dell'utente (2026-08-26)
// per poter riprovare un pick diverso dallo stesso punto e verificare che il
// bot reagisca in modo diverso (conferma anche che il bot ragiona DAVVERO
// sui pick del trainee, non solo sull'ancora storica). Scarta tutte le mosse
// successive, comprese quelle del bot.
async function rewindTraining(step) {
  if (trainingBusy) return;
  if (!confirm("Ripartire da qui? Le scelte successive (tue e del bot) verranno annullate.")) return;
  trainingBusy = true;
  updateTrainingConfirmButton();

  const result = await backend.trainingRewind(step);
  trainingBusy = false;

  if (result.error) {
    alert(result.error);
    updateTrainingConfirmButton();
    return;
  }
  applyTrainingState(result);
}

const ROLE_ICON_FILE = Object.fromEntries(ROLE_ICONS); // "Top" -> "Top Icon.svg", ecc - riusato per il riepilogo ruoli

function buildTrainingRoleIcon(role) {
  const roleImg = document.createElement("img");
  roleImg.className = "training-role-icon";
  roleImg.src = `/assets/role_icons/${encodeURIComponent(ROLE_ICON_FILE[role])}`;
  return roleImg;
}

function buildTrainingChampIcon(champName) {
  const champ = champions.find((c) => c.name === champName);
  if (!champ) return null;
  const champImg = document.createElement("img");
  champImg.className = "training-role-champ-icon";
  champImg.src = champ.icon;
  champImg.style.webkitUserDrag = "none"; // stesso gotcha gia' noto (drag&drop nell'app buildata)
  applyCompBorderVar(champImg, champ);
  return champImg;
}

// Riepilogo per il lato BOT (o per il trainee finche' non ha ancora
// trascinato nulla di suo) - SOLO lettura, dal suggerimento automatico di
// assign_roles lato server. Segnala onestamente quando un ruolo non e'
// coperto da nessun vero specialista (nessun vincolo di ruolo durante la
// scelta del bot per i ban - vedi training_bot.py - ma i PICK ora sono gia'
// protetti da _can_role_match, quindi per il bot questo warning non
// dovrebbe piu' comparire davvero; resta per il lato trainee, dove nessun
// vincolo e' mai stato imposto, giustamente).
function renderTrainingRoleReadonly(container, data) {
  const rowsEl = container.querySelector(".training-role-rows");
  rowsEl.innerHTML = "";

  for (const role of TRAINING_ROLE_ORDER) {
    const entry = data.assignment[role];
    const row = document.createElement("div");
    row.className = "training-role-row";
    row.appendChild(buildTrainingRoleIcon(role));
    const champImg = buildTrainingChampIcon(entry.champion);
    if (champImg) row.appendChild(champImg);
    const label = document.createElement("span");
    label.textContent = entry.champion;
    row.appendChild(label);
    if (!entry.confident) {
      const warn = document.createElement("span");
      warn.className = "training-role-warning";
      warn.textContent = "⚠ non è il suo ruolo naturale";
      row.appendChild(warn);
    }
    rowsEl.appendChild(row);
  }

  let notCoveredEl = container.querySelector(".training-role-not-covered");
  if (!data.fullyCovered) {
    if (!notCoveredEl) {
      notCoveredEl = document.createElement("div");
      notCoveredEl.className = "training-role-not-covered";
      container.appendChild(notCoveredEl);
    }
    notCoveredEl.textContent = "⚠ questi 5 pick non coprono davvero 5 ruoli distinti.";
  } else if (notCoveredEl) {
    notCoveredEl.remove();
  }
}

// Riepilogo TRASCINABILE per il lato del TRAINEE - richiesto esplicitamente
// dall'utente (2026-08-26): "voglio poter decidere io quali dei miei
// campioni vanno dove" (gli serve per un passo successivo, confrontarli con
// altri strumenti). trainingRoleOrder e' la bozza locale (seminata dal
// suggerimento automatico la prima volta, vedi applyTrainingState) -
// trascinare riordina SOLO in locale, "Conferma assegnazione ruoli" la
// invia davvero al server (stesso schema two-step di renderRoleConfirmSlots
// in modalita' torneo: drag libero, un bottone esplicito per confermare).
function renderTrainingRoleEditable(container) {
  const rowsEl = container.querySelector(".training-role-rows");
  rowsEl.innerHTML = "";
  const oldNotCovered = container.querySelector(".training-role-not-covered");
  if (oldNotCovered) oldNotCovered.remove(); // qui non ha senso, e' l'utente stesso a decidere

  trainingRoleOrder.forEach((champName, i) => {
    const role = TRAINING_ROLE_ORDER[i];
    const row = document.createElement("div");
    row.className = "training-role-row training-role-row-editable";
    row.draggable = true;
    row.appendChild(buildTrainingRoleIcon(role));
    const champImg = buildTrainingChampIcon(champName);
    if (champImg) row.appendChild(champImg);
    const label = document.createElement("span");
    label.textContent = champName;
    row.appendChild(label);

    row.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", String(i));
      e.dataTransfer.effectAllowed = "move";
    });
    row.addEventListener("dragover", (e) => {
      e.preventDefault();
      row.classList.add("drag-over");
    });
    row.addEventListener("dragleave", () => row.classList.remove("drag-over"));
    row.addEventListener("drop", (e) => {
      e.preventDefault();
      row.classList.remove("drag-over");
      const fromIndex = parseInt(e.dataTransfer.getData("text/plain"), 10);
      if (Number.isNaN(fromIndex) || fromIndex === i) return;
      const [item] = trainingRoleOrder.splice(fromIndex, 1);
      trainingRoleOrder.splice(i, 0, item);
      renderTrainingRoleEditable(container);
    });

    rowsEl.appendChild(row);
  });

  let confirmBtn = container.querySelector(".training-role-confirm-btn");
  if (!confirmBtn) {
    confirmBtn = document.createElement("button");
    confirmBtn.type = "button";
    confirmBtn.className = "training-role-confirm-btn";
    confirmBtn.textContent = "Conferma assegnazione ruoli";
    confirmBtn.addEventListener("click", confirmTrainingRoleOrder);
    container.appendChild(confirmBtn);
  }

  let savedHint = container.querySelector(".training-role-saved-hint");
  const isSaved =
    trainingState.traineeRoleOrder &&
    trainingState.traineeRoleOrder.every((n, i) => n === trainingRoleOrder[i]);
  if (isSaved) {
    if (!savedHint) {
      savedHint = document.createElement("div");
      savedHint.className = "training-role-saved-hint";
      container.appendChild(savedHint);
    }
    savedHint.textContent = "✓ Assegnazione salvata";
  } else if (savedHint) {
    savedHint.remove();
  }
}

// Riepilogo ruoli a fine draft ("in che corsia va ognuno dei 5 pick") -
// richiesto esplicitamente dall'utente (2026-08-26): il bot sceglie i pick
// SOLO per sinergia/counter (vedi training_bot.py), nessun vincolo di ruolo
// durante la scelta - questo mostra onestamente se i 5 campioni ottenuti
// riescono comunque a coprire 5 posizioni distinte (assign_roles lato
// server) o no. Lato TRAINEE e' trascinabile (vedi renderTrainingRoleEditable
// sopra), lato bot resta di sola lettura (non e' una sua scelta da
// correggere - e comunque, dopo il fix del 2026-08-26, e' sempre gia'
// fullyCovered per costruzione).
function renderTrainingRoleSummary() {
  const panel = document.getElementById("training-role-summary");
  if (!trainingConnected || !trainingState || !trainingState.roleAssignment) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");

  for (const [side, elId] of [["blue", "training-role-blue"], ["red", "training-role-red"]]) {
    const container = document.getElementById(elId);
    if (side === trainingState.traineeSide) {
      renderTrainingRoleEditable(container);
    } else {
      renderTrainingRoleReadonly(container, trainingState.roleAssignment[side]);
    }
  }
}

async function confirmTrainingRoleOrder() {
  if (!trainingRoleOrder || trainingBusy) return;
  const result = await backend.trainingAssignRoles(trainingRoleOrder);
  if (result.error) {
    alert(result.error);
    return;
  }
  applyTrainingState(result);
}

// "Valuta la draft" - richiesto esplicitamente dall'utente (2026-08-26):
// scarica le curve winrate/durata-partita delle 5 corsie da lolalytics (fino
// a 5 fetch VERI in parallelo lato server, vedi driftdraft/draft_evaluation.py)
// e le aggrega in blu/rosso/verde. Usa la fascia elo gia' scelta dal coach
// nel toolbar (counterModeTier, la stessa gia' usata per la ricerca counter -
// "il tag del tier pre-selezionato dal coach", richiesta esplicita). Puo'
// richiedere diversi secondi (rete reale, non un ritardo finto) - il
// pannello stesso mostra un messaggio di attesa invece della sola barra di
// stato, dato il tempo potenzialmente lungo.
async function evaluateTrainingDraft() {
  if (trainingBusy || !trainingState || !trainingState.traineeRoleOrder) return;
  trainingBusy = true;
  updateTrainingConfirmButton();

  const panel = document.getElementById("training-evaluation");
  panel.classList.remove("hidden");
  panel.innerHTML =
    '<div class="training-eval-loading">Valutazione in corso... scarico dati reali da lolalytics (curve solista e di matchup per le 5 corsie, può richiedere fino a 40 secondi).</div>';

  const result = await backend.trainingEvaluate(counterModeTier);
  trainingBusy = false;
  updateTrainingConfirmButton();

  if (result.error) {
    alert(result.error);
    renderTrainingEvaluation();
    return;
  }
  trainingEvaluation = result;
  renderTrainingEvaluation();
}

// Equivalente di evaluateTrainingDraft per la modalita' torneo (richiesto
// esplicitamente dall'utente 2026-08-26). ourRoleOrder inviato al server e'
// il MIGLIOR ordine disponibile fra due fonti indipendenti, in ordine di
// fiducia: (1) una correzione manuale del coach nel pannello "Ruoli nostri"
// (tournamentOwnRoleSource === "manual", vedi updateTournamentOwnRolesPanel
// - se il coach ha corretto a mano, quella e' definitiva, stessa priorita'
// assoluta gia' data alla correzione manuale nemica), (2) altrimenti
// tournamentConfirmedRoleOrder se la fase di role confirmation VERA sul
// sito e' stata affrontata dal vivo (vedi confirmRoleOrder - quando c'e',
// resta la fonte piu' autorevole delle due perche' e' la conferma reale
// della squadra), (3) altrimenti il pannello "Ruoli nostri" stesso nella
// sua variante auto-calcolata (tag sito passivo -> euristica -> ordine
// grezzo - richiesto esplicitamente dall'utente 2026-08-30 dopo aver
// notato che "diversi team non selezionano... i pick nell'ordine giusto",
// quindi (2) da solo non bastava piu' come UNICA fonte per il nostro
// lato). Se nemmeno (3) e' ancora disponibile (draft non ancora finita) il
// server ricade da solo sull'euristica assign_roles() (vedi
// evaluate_live_draft in draft_evaluation.py) - deliberatamente NON un
// requisito bloccante qui, a differenza del training.
async function evaluateTournamentDraft() {
  if (tournamentEvaluateBusy || !tournamentConnected) return;
  tournamentEvaluateBusy = true;
  updateTournamentEvaluateButton();

  const panel = document.getElementById("tournament-evaluation");
  panel.classList.remove("hidden");
  panel.innerHTML =
    '<div class="training-eval-loading">Valutazione in corso... scarico dati reali da lolalytics (curve solista e di matchup per le 5 corsie, può richiedere fino a 40 secondi).</div>';

  const ourRoleOrder =
    tournamentOwnRoleSource === "manual"
      ? tournamentOwnRoleOrder
      : tournamentConfirmedRoleOrder || tournamentOwnRoleOrder;
  const result = await backend.liveDraftEvaluate(counterModeTier, ourRoleOrder, tournamentEnemyRoleOrder);
  tournamentEvaluateBusy = false;
  updateTournamentEvaluateButton();

  if (result.error) {
    alert(result.error);
    renderTournamentEvaluation();
    return;
  }
  tournamentEvaluation = result;
  renderTournamentEvaluation();
}

// "Pick suggeriti" (richiesto esplicitamente dall'utente 2026-08-26 per il
// torneo, ESTESO 2026-08-30 a training e modalita' normale) - a differenza
// di evaluateTournamentDraft/evaluateTrainingDraft (bottone, esplicito, una
// tantum), questo va richiamato automaticamente ogni volta che i pick/ban
// cambiano E il toggle e' attivo (vedi i punti di chiamata: dentro
// pollTournamentState per il torneo, applyTrainingState per il training,
// dentro placeChampion/i click\drop sugli slot per la modalita' normale) -
// NON await-ato li' dentro apposta: in torneo il poll gira ogni 100ms e deve
// restare veloce per specchiare bene il sito vero, un fetch di suggerimenti
// (query verso le tabelle locali, comunque rapido ma non istantaneo) non
// deve mai rallentare nessuno di quei punti di chiamata. Il rendering della
// griglia con l'evidenziazione aggiornata arriva quindi con un frame di
// ritardo rispetto al resto (picchi/ban), mai bloccante.
//
// La FONTE dei pick e' l'unica cosa che cambia in base alla modalita': il
// torneo ha gia' un endpoint dedicato che legge la sessione live autorevole
// lato server (nessun pick da passare); training e modalita' normale non
// hanno una sessione server equivalente, quindi passano i pick GIA' noti
// lato client (teams.left/right) al nuovo endpoint stateless
// /api/pick-suggestions (stesso principio side-agnostico gia' usato per
// /api/live-draft/role-guess).
// Pannello "Pick suggeriti" sotto la griglia (2026-09-05). Richiesto
// dall'utente al posto della sola evidenziazione in griglia:
// "l'ultima implementazione, che dorava il campione e' una buona idea,
// tuttavia ritengo che sia la scelta sbagliata... c'e' un sistema migliore".
// L'evidenziazione in griglia resta comunque (ridotta al solo alone attorno
// alla card, vedi .suggest-blue/.suggest-red nel css): serve a ritrovare i
// campioni elencati qui.
//
// Tre differenze sostanziali rispetto alla sola evidenziazione:
//  - ordine per PUNTEGGIO sinergia/counter, non alfabetico come la griglia
//    (l'elenco arriva gia' ordinato da rank_pick_suggestions);
//  - NON risente dei filtri della toolbar: un suggerimento resta leggibile
//    anche mentre la griglia e' filtrata per comp/ruolo/pool/ricerca, che era
//    il limite vero della sola evidenziazione in griglia;
//  - corsia mostrata per ogni suggerimento (vedi _suggest_roles lato Python).
//
// DUE RIGHE dal 2026-09-06, una per LATO: "Blue Side" e "Red Side". Ognuna
// usa gli stessi dati letti dalla sua parte del tavolo (vedi
// rank_pick_suggestions lato Python, che chiama la stessa funzione a parti
// invertite) e insieme rispondono a una domanda che prima l'app non poteva
// porre: non solo "cosa conviene prendere a me" ma anche "cosa vorra'
// l'altro lato" - quindi cosa bannare, e soprattutto quali campioni
// piacciono a tutti e due (i pick CONTESI, che compaiono in entrambe le
// righe con la cornice mezza blu e mezza rossa).
//
// Erano "Per noi"/"Per loro" fino a poche ore prima, ma fuori da
// torneo/training il lato nostro era dedotto dall'ultimo slot cliccato: le
// due righe si scambiavano di significato in silenzio, e l'utente ci si e'
// imbattuto con Ambessa (Renekton, la risposta giusta, gli compariva nella
// riga sbagliata). I lati non sono un'ipotesi.
// --- Stato dei dati Leaguepedia, condiviso da pannello e modale training ---
// Prima l'unico posto da cui aggiornare i dati era il modale "Modalita'
// training", e la richiesta restava appesa senza dire nulla fino alla fine.
// L'utente (2026-09-05): "non c'e' scritto quanto tempo ci vuole ancora, se
// ha fatto, se non ha fatto, o se semplicemente non c'e' altro da importare".
// Ora il sync gira lato server in un thread (leaguepedia.start_sync) e qui si
// interroga il suo avanzamento, con un solo motore che alimenta entrambe le
// scritte: quella del pannello Pick suggeriti e quella del modale.
let suggestionsSyncPollTimer = null;

function formatSyncMessage(progress) {
  const d = progress.data || {};
  if (progress.running) {
    const done = progress.drafts || 0;
    const target = progress.target || 0;
    switch (progress.phase) {
      case "attesa":
        // La parte piu' lunga e prima del tutto invisibile: l'API ha un
        // limite di frequenza severo e il backoff arriva a 120s.
        return `${progress.reason || "In attesa"} - riprovo fra ${progress.seconds}s (tentativo ${progress.attempt}/${progress.maxAttempts})...`;
      case "pausa":
        return `Pausa di ${progress.seconds}s fra una pagina e l'altra (${done}/${target} draft)...`;
      case "elaboro":
        return `Elaboro le tabelle su ${done} draft...`;
      case "esaurito":
        return `Non c'e' altro da importare: Leaguepedia non ha altre draft complete (${done} scaricate).`;
      default:
        return `Scarico da Leaguepedia... ${done}/${target} draft`;
    }
  }
  if (progress.phase === "errore") return progress.error || "Aggiornamento non riuscito.";
  if (!d.synced) return "Dati non ancora scaricati - premi \"Aggiorna dati\".";

  const when = d.fetchedAt ? new Date(d.fetchedAt * 1000).toLocaleString("it-IT") : "?";
  const patches = (d.recentPatches || []).join(", ");
  return `${d.draftsCount} draft${patches ? ` (patch ${patches})` : ""} - aggiornate il ${when}`;
}

async function refreshSuggestionsDataInfo() {
  const progress = await backend.trainingSyncProgress();
  const text = formatSyncMessage(progress);

  const info = document.getElementById("suggestions-data-info");
  if (info) info.textContent = text;

  // Un sync in corso spegne il bottone: il server rifiuta comunque un
  // secondo avvio (vedi start_sync), ma un bottone che resta cliccabile e
  // non fa nulla e' peggio di uno spento.
  const btn = document.getElementById("suggestions-sync");
  if (btn) btn.disabled = !!progress.running;

  if (progress.running && !suggestionsSyncPollTimer) {
    // 2s: il sync dura minuti e cambia stato di rado (una volta per pagina o
    // per tentativo), non serve un poll fitto.
    suggestionsSyncPollTimer = setInterval(refreshSuggestionsDataInfo, 2000);
  } else if (!progress.running && suggestionsSyncPollTimer) {
    clearInterval(suggestionsSyncPollTimer);
    suggestionsSyncPollTimer = null;
    // Dati nuovi su disco: i suggerimenti a video sono calcolati su quelli
    // vecchi finche' non si rifanno.
    if (progress.phase === "fatto") refreshSuggestions();
  }
}

async function startDataSync() {
  const info = document.getElementById("suggestions-data-info");
  if (info) info.textContent = "Avvio aggiornamento...";
  const result = await backend.trainingSync();
  if (result.error) {
    if (info) info.textContent = result.error;
    return;
  }
  refreshSuggestionsDataInfo();
}

// In quale dei tre stati sta un campione, dal punto di vista dei due elenchi
// di suggerimenti. E' l'unico posto in cui si decide "conteso": ovunque
// serva la classe CSS (griglia e card del pannello) si passa di qui, cosi'
// griglia e pannello non possono divergere.
function suggestionState(name) {
  const blu = blueNames.has(name);
  const rosso = redNames.has(name);
  if (blu && rosso) return "suggest-contested";
  if (blu) return "suggest-blue";
  if (rosso) return "suggest-red";
  return "";
}

// Il testo del tooltip, sia in griglia sia nel pannello. Su un pick conteso
// mostra ENTRAMBI i punteggi: sono due letture diverse degli stessi dati
// (quanto conviene a noi / quanto a loro) e possono essere molto diverse fra
// loro - il fatto che sia conteso non dice ancora chi lo vuole di piu'.
function suggestionTitle(name) {
  const blu = blueSuggestions.find((s) => s.champion === name);
  const rosso = redSuggestions.find((s) => s.champion === name);
  const lane = (blu || rosso).role;
  const where = lane ? ` in ${lane}` : "";
  // Quanto quella squadra lo gioca davvero, se per quel lato c'e' un op.gg
  // caricato. Va detto: e' il peso che ha deciso l'ORDINE dell'elenco, e
  // senza mostrarlo la riga sembrerebbe ordinata male rispetto al punteggio.
  // Con le tier list della propria squadra la lettera E' il dato ("B" dice
  // molto piu' di "45%", che ne e' solo la traduzione interna); da op.gg la
  // lettera non esiste e resta la percentuale di quanto lo giocano.
  const quanto = (s) => {
    if (!s || s.affinity == null) return "";
    if (s.tier) return `, tier ${s.tier}`;
    return `, quanto lo giocano: ${Math.round(s.affinity * 100)}%`;
  };
  if (blu && rosso) {
    return `${name} — CONTESO${where}: conviene al Blue Side (${blu.score}${quanto(blu)}) e al Red Side (${rosso.score}${quanto(rosso)})`;
  }
  if (blu)
    return `${name} — per il Blue Side${where} (punteggio sinergia/counter: ${blu.score}${quanto(blu)})`;
  return `${name} — per il Red Side${where} (punteggio sinergia/counter: ${rosso.score}${quanto(rosso)})`;
}

// Una card del pannello, identica per le due righe: cambia solo la cornice,
// che dipende dallo stato del campione e non dalla riga in cui si trova - e'
// cosi' che un pick conteso appare mezzo dorato e mezzo rosso in ENTRAMBE.
function buildSuggestionCard(entry) {
  const champ = champions.find((c) => c.name === entry.champion);
  if (!champ) return null;

  const card = document.createElement("div");
  const state = suggestionState(entry.champion);
  card.className = "suggestion-card" + (state ? " " + state : "");
  card.title = suggestionTitle(entry.champion);
  // Cliccabile e trascinabile esattamente come una card della griglia:
  // stesso placeChampion, quindi in torneo un click qui e' un'azione VERA
  // sulla draft, come lo e' in griglia. Nessuna scorciatoia diversa. Vale
  // anche per la riga avversaria: cliccarci sopra mette il campione nello
  // slot attivo (che durante un nostro turno e' un nostro slot) - il gesto
  // giusto per "me lo prendo prima io", che e' il senso di quella riga.
  card.addEventListener("click", () => placeChampion(entry.champion));
  card.draggable = true;
  card.addEventListener("dragstart", (e) => {
    e.dataTransfer.setData("text/plain", entry.champion);
  });


  // Corsia sopra l'icona. entry.role puo' mancare (campione mai visto
  // nelle draft pro scaricate): in quel caso si lascia la riga vuota
  // invece di inventare un ruolo, cosi' le card restano allineate fra loro.
  const roleRow = document.createElement("div");
  roleRow.className = "suggestion-role";
  const roleFile = (ROLE_ICONS.find(([r]) => r === entry.role) || [])[1];
  if (roleFile) {
    const roleImg = document.createElement("img");
    roleImg.src = `/assets/role_icons/${encodeURIComponent(roleFile)}`;
    roleImg.alt = entry.role;
    roleRow.appendChild(roleImg);
    const roleLabel = document.createElement("span");
    roleLabel.textContent = entry.role;
    roleRow.appendChild(roleLabel);
  }
  card.appendChild(roleRow);

  // Il bordo comp sta sull'INVOLUCRO dell'icona, non sulla card: e' cosi'
  // che la griglia lo disegna (un contenitore con padding e l'immagine
  // dentro), e metterlo sulla card faceva girare il bordo anche attorno
  // all'etichetta della corsia - discrepanza segnalata dall'utente. Stesse
  // custom property della griglia, quindi segue da solo il toggle "Bordi
  // comp", che azzera --comp-border-width via la classe su <body>.
  const iconWrap = document.createElement("div");
  iconWrap.className = "suggestion-icon-wrap";
  applyCompBorderVar(iconWrap, champ);

  const img = document.createElement("img");
  img.className = "suggestion-icon";
  img.src = champ.icon;
  img.alt = entry.champion;
  img.draggable = false;
  iconWrap.appendChild(img);
  card.appendChild(iconWrap);

  // Nessun nome sotto l'icona: nessun'altra griglia/slot di questa UI lo
  // mostra, e l'utente ha chiesto coerenza ("o tutti o nessuno"). Il nome
  // resta nel title della card, insieme a corsia e punteggio.
  return card;
}

// Una delle due righe. `pickCount` sono i pick GIA' fatti dalla squadra a cui
// quella riga si riferisce: a cinque quella squadra e' completa e non c'e'
// piu' niente da suggerirle (richiesta esplicita "dopo il quinto pick, non
// devono apparire") - e le due squadre ci arrivano in momenti diversi,
// quindi il conteggio e' per riga, non uno solo per tutto il pannello.
function fillSuggestionsRow(side, entries, pickCount, thin) {
  const row = document.getElementById(`suggestions-row-${side}`);
  const list = row.querySelector(".suggestions-row-list");
  list.innerHTML = "";

  // Tre stati, non due. Oltre a "ecco i suggerimenti" e "riga via", c'e'
  // "non ho abbastanza dati": succede sui campioni che nei dati pro non
  // hanno una risposta perche' si gestiscono col ban (vedi MIN_SUPPORT lato
  // Python). Dirlo e' meglio che sparire - una riga che scompare sembra un
  // guasto, e mostrare comunque otto card costruite su una partita sarebbe
  // peggio ancora: sembrerebbe un consiglio.
  const attivo = suggestionsEnabled && pickCount < 5;
  const show = attivo && (entries.length > 0 || thin);
  row.classList.toggle("hidden", !show);
  if (!show) return;

  if (entries.length === 0) {
    const nota = document.createElement("span");
    nota.className = "suggestions-thin";
    nota.textContent = "Non ho abbastanza dati per suggerire qui";
    nota.title =
      "Nelle draft pro scaricate non ci sono abbastanza partite in cui qualcuno" +
      " sia stato pescato in risposta a questi campioni. Di solito succede con" +
      " i campioni che si gestiscono bannandoli, non rispondendogli in draft.";
    list.appendChild(nota);
    return;
  }

  for (const entry of entries) {
    const card = buildSuggestionCard(entry);
    if (card) list.appendChild(card);
  }
}

// Il pannello sinistro E' il Blue Side e il destro il Red Side: non c'e' piu'
// niente da dedurre, ed e' esattamente il punto della modifica del
// 2026-09-06. Questa costante esiste solo per non ripetere la corrispondenza
// in giro e per renderla cercabile.
const SIDE_TEAM = { blue: "left", red: "right" };

// I giocatori op.gg di un lato da mandare al server, o null se non c'e'
// niente con cui contestualizzare (nessuna squadra caricata per quel lato, o
// filtro spento dal chip).
//
// Prima si mandavano i soli NOMI dei campioni, cioe' una maschera
// acceso/spento. Ora si manda la squadra intera - chi gioca cosa e quanto -
// perche' il server ne ricostruisce lo stesso profilo che usa il bot di
// training (build_team_profile), che sa anche in quale CORSIA ognuno gioca
// cosa. E' il seguito chiesto dall'utente: stesso criterio per chi consiglia
// e per chi sceglie.
function poolPlayers(side) {
  if (!poolFilterEnabled) return null;
  return teamPlayers(side);
}

// Gli stessi giocatori, ma SENZA guardare il chip del filtro pool. Il chip
// dice "restringi i suggerimenti a cosa giocano", ed e' una scelta sensata da
// spegnere; sapere CHI gioca cosa per etichettare le corsie a fine draft non
// e' una restrizione, e' solo indovinare meglio. Spegnerlo insieme al filtro
// rimetterebbe le corsie a tirare a sorte senza che nessuno l'abbia chiesto.
function teamPlayers(side) {
  const players = teamPools[SIDE_TEAM[side]]?.players;
  return players && players.length ? players : null;
}

function renderSuggestionsPanel() {
  // Ridisegnato anche qui e non solo al cambio team: entrando in allenamento
  // o in torneo il lato lo sa l'app e il promemoria deve sparire da solo.
  renderContextSideChip();
  // Il PANNELLO non si nasconde mai (2026-09-05): ospita l'interruttore dei
  // pick suggeriti e il bottone "Aggiorna dati", che devono restare
  // raggiungibili anche a 0 pick - quando cioe' non c'e' ancora nessun
  // suggerimento da mostrare. A sparire sono solo le due RIGHE.
  // Il chip del filtro pool segue la disponibilita' del dato, non la
  // preferenza: senza nessuna pool caricata non c'e' niente da filtrare e
  // mostrarlo confonderebbe. Sparisce anche a suggerimenti spenti, dove non
  // avrebbe nulla su cui agire.
  const chip = document.getElementById("pool-filter");
  const quante = ["blue", "red"].filter((s) => teamPools[SIDE_TEAM[s]]?.pool).length;
  chip.classList.toggle("hidden", quante === 0 || !suggestionsEnabled);
  chip.classList.toggle("active", poolFilterEnabled);
  chip.textContent = quante === 2 ? "Solo pool op.gg (2 lati)" : "Solo pool op.gg";

  fillSuggestionsRow("blue", blueSuggestions, teams.left.filter((n) => n).length, blueThin);
  fillSuggestionsRow("red", redSuggestions, teams.right.filter((n) => n).length, redThin);
}

function refreshSuggestions() {
  if (suggestionsDebounceTimer) clearTimeout(suggestionsDebounceTimer);
  suggestionsDebounceTimer = setTimeout(_doRefreshSuggestions, 150);
}

async function _doRefreshSuggestions() {
  suggestionsDebounceTimer = null;
  if (!suggestionsEnabled) {
    if (blueNames.size > 0 || redNames.size > 0) {
      blueSuggestions = [];
      redSuggestions = [];
      blueNames = new Set();
      redNames = new Set();
      renderGrid();
    }
    blueThin = false;
    redThin = false;
    renderSuggestionsPanel();
    return;
  }
  const seq = ++suggestionsFetchSeq;
  let result;
  const bluePlayers = poolPlayers("blue");
  const redPlayers = poolPlayers("red");
  // Il lato del coach: in torneo quello connesso davvero, in allenamento
  // quello del trainee. Fuori da queste due non esiste un lato "nostro" e le
  // tier list restano fuori - dedurlo dall'ultimo slot cliccato e' gia' stato
  // un bug, vedi il passaggio dei pick suggeriti a blu/rosso.
  const ourSide = tournamentConnected
    ? tournamentSide
    : trainingConnected
      ? trainingState && trainingState.traineeSide
      : contextTeamSide;
  const ourTeam = ourSide && contextTeamName ? contextTeamName : null;
  if (tournamentConnected) {
    result = await backend.liveDraftSuggestions(
      bluePlayers, redPlayers, ourTeam, ourSide, compBordersEnabled
    );
  } else {
    result = await backend.pickSuggestions(
      teams.left.filter((n) => n),
      teams.right.filter((n) => n),
      [...allPickedNames(), ...allBannedNames()],
      bluePlayers,
      redPlayers,
      // In allenamento la squadra del bot sta nella sessione, non nei
      // pannelli laterali: e' il server a ripescarla, vedi api_pick_suggestions.
      trainingConnected,
      ourTeam,
      ourSide,
      // I "bordi comp" spenti significano "non guidarmi con le comp": spegne
      // il ragionamento sul NOSTRO lato. Vedi _comp_flags lato server.
      compBordersEnabled
    );
  }
  if (seq !== suggestionsFetchSeq) return; // superata da una richiesta piu' recente, scartata

  // I due elenchi si aggiornano SEMPRE insieme, anche in errore: sono due
  // letture della stessa risposta, e tenerne uno vecchio accanto a uno nuovo
  // falserebbe proprio il calcolo dei contesi (intersezione fra i due).
  const ok = !result.error;
  blueSuggestions = ok ? result.blue?.suggestions || [] : [];
  redSuggestions = ok ? result.red?.suggestions || [] : [];
  blueThin = ok && !!result.blue?.thin;
  redThin = ok && !!result.red?.thin;
  blueNames = new Set(blueSuggestions.map((s) => s.champion));
  redNames = new Set(redSuggestions.map((s) => s.champion));
  renderGrid();
  renderSuggestionsPanel();
}

// Grafico a 3 linee, disegnato a mano in SVG (stesso principio di
// renderCounterDiagram gia' in uso in questo file - niente libreria di
// grafici esterna). Scala Y auto-adattata ai valori reali (con margine)
// invece di un fisso 0-100, cosi' curve che oscillano in una fascia stretta
// (es. 40-60%) restano leggibili invece di apparire schiacciate al centro.
function buildEvaluationChartSvg(evaluation) {
  const width = 560;
  const height = 230;
  const padL = 34;
  const padR = 10;
  const padT = 12;
  const padB = 22;
  const plotW = width - padL - padR;
  const plotH = height - padT - padB;
  const buckets = evaluation.buckets;
  const n = buckets.length;

  const allValues = [...evaluation.blue, ...evaluation.red, ...evaluation.green];
  let yMin = Math.floor((Math.min(...allValues, 45) - 5) / 10) * 10;
  let yMax = Math.ceil((Math.max(...allValues, 55) + 5) / 10) * 10;
  yMin = Math.max(0, yMin);
  yMax = Math.min(100, yMax);
  if (yMax - yMin < 20) {
    yMax = Math.min(100, yMin + 20);
    yMin = Math.max(0, yMax - 20);
  }

  const xFor = (i) => padL + (plotW * i) / (n - 1);
  const yFor = (v) => padT + plotH * (1 - (v - yMin) / (yMax - yMin));
  const lineFor = (values) =>
    values.map((v, i) => `${i === 0 ? "M" : "L"} ${xFor(i).toFixed(1)} ${yFor(v).toFixed(1)}`).join(" ");

  let gridLines = "";
  for (let v = yMin; v <= yMax; v += 10) {
    const y = yFor(v);
    const isHalf = Math.abs(v - 50) < 0.01;
    gridLines += `<line x1="${padL}" y1="${y.toFixed(1)}" x2="${width - padR}" y2="${y.toFixed(1)}" stroke="${
      isHalf ? "var(--text-dim)" : "var(--border)"
    }" stroke-width="${isHalf ? 1.2 : 0.6}" stroke-dasharray="${isHalf ? "" : "3,3"}" />`;
    gridLines += `<text x="${padL - 5}" y="${(y + 3).toFixed(1)}" font-size="9" fill="var(--text-dim)" text-anchor="end">${Math.round(
      v
    )}</text>`;
  }

  let xLabels = "";
  buckets.forEach((b, i) => {
    xLabels += `<text x="${xFor(i).toFixed(1)}" y="${height - 6}" font-size="9" fill="var(--text-dim)" text-anchor="middle">${b}</text>`;
  });

  const bucketWidth = n > 1 ? plotW / (n - 1) : plotW;
  let bumpMarks = "";
  for (const note of evaluation.bumpNotes) {
    const i = buckets.indexOf(note.bucket);
    if (i === -1) continue;
    const color = note.direction === "push" ? "#4caf6d" : "#d64545";
    bumpMarks += `<rect x="${(xFor(i) - bucketWidth / 2).toFixed(1)}" y="${padT}" width="${bucketWidth.toFixed(
      1
    )}" height="${plotH}" fill="${color}" opacity="0.1" />`;
  }

  const dotsFor = (values, color) =>
    values.map((v, i) => `<circle cx="${xFor(i).toFixed(1)}" cy="${yFor(v).toFixed(1)}" r="2.5" fill="${color}" />`).join("");

  return `
    <svg viewBox="0 0 ${width} ${height}" width="100%">
      ${bumpMarks}
      ${gridLines}
      <path d="${lineFor(evaluation.red)}" fill="none" stroke="#d64545" stroke-width="2" />
      <path d="${lineFor(evaluation.blue)}" fill="none" stroke="#3ea8d8" stroke-width="1.5" stroke-dasharray="4,3" />
      <path d="${lineFor(evaluation.green)}" fill="none" stroke="#4caf6d" stroke-width="2.5" />
      ${dotsFor(evaluation.green, "#4caf6d")}
      ${xLabels}
    </svg>
  `;
}

// "Testa a testa per corsia" (richiesto esplicitamente dall'utente
// 2026-08-26, con uno schizzo a mano, poi affinato in un secondo schizzo:
// "al posto di 5 righe impilate, un blocco unico con le 5 corsie affiancate
// e i grafici piu' piccoli - tanto non servono enormi per capire come
// scalano i campioni a colpo d'occhio") - un mini-grafico a 2 linee (noi/
// nemico) per OGNUNA delle 5 corsie, sotto al grafico grande. Stessi dati
// gia' scaricati per BLU/ROSSO (myLaneCurves/enemyLaneCurves in
// draft_evaluation.py - nessun fetch in piu'), qui pero' non ancora mediati
// sulle 5 corsie: un vero drill-down di cosa alimenta quelle due linee,
// corsia per corsia. Deliberatamente minimale (niente etichette assi/
// griglia, solo una linea di riferimento al 50%, niente nome campione in
// chiaro - solo l'icona, il nome resta comunque disponibile via title al
// passaggio del mouse) - sono 5 di questi affiancati in poco spazio, un
// grafico completo/etichettato ripetuto 5 volte sarebbe stato illeggibile
// a quella scala.
function buildLaneFaceoffChartSvg(myCurve, enemyCurve, buckets) {
  const width = 96;
  const height = 34;
  const pad = 3;
  const plotW = width - pad * 2;
  const plotH = height - pad * 2;
  const n = buckets.length;

  const allValues = [...myCurve, ...enemyCurve];
  let yMin = Math.min(...allValues, 45) - 3;
  let yMax = Math.max(...allValues, 55) + 3;
  yMin = Math.max(0, yMin);
  yMax = Math.min(100, yMax);

  const xFor = (i) => pad + (plotW * i) / (n - 1);
  const yFor = (v) => pad + plotH * (1 - (v - yMin) / (yMax - yMin));
  const lineFor = (values) =>
    values.map((v, i) => `${i === 0 ? "M" : "L"} ${xFor(i).toFixed(1)} ${yFor(v).toFixed(1)}`).join(" ");
  const titleFor = (label, values) =>
    `${label}: ` + buckets.map((b, i) => `${b}min ${values[i].toFixed(0)}%`).join(", ");

  const y50 = yFor(50);
  return `
    <svg viewBox="0 0 ${width} ${height}" width="100%">
      <line x1="${pad}" y1="${y50.toFixed(1)}" x2="${width - pad}" y2="${y50.toFixed(1)}" stroke="var(--border)" stroke-width="0.6" stroke-dasharray="3,3" />
      <path d="${lineFor(enemyCurve)}" fill="none" stroke="#d64545" stroke-width="1.4"><title>${titleFor("Nemico", enemyCurve)}</title></path>
      <path d="${lineFor(myCurve)}" fill="none" stroke="#3ea8d8" stroke-width="1.4"><title>${titleFor("Noi", myCurve)}</title></path>
    </svg>
  `;
}

function buildLaneFaceoffSection(evaluation) {
  const champIconUrl = (name) => champions.find((c) => c.name === name)?.icon || "";
  // Costruito via stringa (template literal), non elementi DOM come nel
  // resto del file - qui non c'e' ancora un elemento a cui applicare
  // applyCompBorderVar(), quindi la custom property va scritta direttamente
  // nell'attributo style della stringa.
  const champBorderStyle = (name) => {
    const champ = champions.find((c) => c.name === name);
    const vars = champCompBorderVars(champ);
    return `--comp-border-width:${vars.width};--comp-border-color:${vars.color};--comp-border-image:${vars.image}`;
  };
  const roleIconUrl = (role) => `/assets/role_icons/${encodeURIComponent(ROLE_ICON_FILE[role])}`;

  const cols = TRAINING_ROLE_ORDER.map((role) => {
    const myChamp = evaluation.traineeRoles[role];
    const enemyChamp = evaluation.botRoles[role];
    const myCurve = evaluation.myLaneCurves[role];
    const enemyCurve = evaluation.enemyLaneCurves[role];
    return `
      <div class="lane-faceoff-col">
        <img class="lane-faceoff-role-icon" src="${roleIconUrl(role)}" alt="${role}" title="${role}">
        <img class="lane-faceoff-col-champ" style="${champBorderStyle(myChamp)}" src="${champIconUrl(myChamp)}" alt="${myChamp}" title="${myChamp}">
        ${buildLaneFaceoffChartSvg(myCurve, enemyCurve, evaluation.buckets)}
        <img class="lane-faceoff-col-champ" style="${champBorderStyle(enemyChamp)}" src="${champIconUrl(enemyChamp)}" alt="${enemyChamp}" title="${enemyChamp}">
      </div>
    `;
  }).join("");

  return `
    <div class="lane-faceoff-section">
      <h4>Testa a testa per corsia</h4>
      <div class="lane-faceoff-legend">
        <span><span class="training-eval-swatch" style="background:#3ea8d8"></span>Noi</span>
        <span><span class="training-eval-swatch" style="background:#d64545"></span>Avversario</span>
      </div>
      <div class="lane-faceoff-cols">${cols}</div>
    </div>
  `;
}

// Riepilogo testuale delle finestre "spingi qui"/"attenzione qui" - stesso
// dato dei rettangoli evidenziati nel grafico, ma leggibile senza dover
// interpretare un grafico (richiesta implicita dell'utente: "aiuta anche ai
// giocatori a capire quando si deve giocare e quando no" - un elenco
// testuale e' piu' immediato di una linea su un grafico durante una prep
// veloce).
// Nucleo condiviso training/torneo (richiesto esplicitamente dall'utente
// 2026-08-26 per il torneo, stesso identico pannello del training - vedi
// evaluate_picks in draft_evaluation.py per l'equivalente lato server) -
// pura resa grafica di un `evaluation` gia' pronto, nessuna logica di stato
// specifica di modalita' qui dentro (quella resta nei due chiamanti sottili
// renderTrainingEvaluation/renderTournamentEvaluation), stesso principio
// gia' usato per renderTeam(side).
function renderEvaluationPanel(panelId, connected, evaluation) {
  const panel = document.getElementById(panelId);
  if (!connected || !evaluation) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }
  panel.classList.remove("hidden");

  const legendHtml = `
    <div class="training-eval-legend">
      <span><span class="training-eval-swatch" style="background:#d64545"></span>Avversario</span>
      <span><span class="training-eval-swatch training-eval-swatch-dashed"></span>Nostro comp (senza contesto)</span>
      <span><span class="training-eval-swatch" style="background:#4caf6d"></span>Previsione reale (contro questo avversario)</span>
    </div>
  `;

  const notesHtml = evaluation.bumpNotes.length
    ? `<div class="training-eval-notes">${evaluation.bumpNotes
        .map((note) => {
          const label = note.direction === "push" ? "Spingi qui" : "Attenzione qui";
          return `<span class="training-eval-note ${note.direction}">${label} — ${note.bucket} min (${note.count}/5 corsie)</span>`;
        })
        .join("")}</div>`
    : '<div class="training-eval-notes-empty">Nessuna finestra con 3 o più corsie in vantaggio/svantaggio simultaneo.</div>';

  // "Piano B" (richiesto esplicitamente dall'utente 2026-08-26): una corsia
  // senza dati sufficienti non viene piu' esclusa dal calcolo, viene
  // trattata come neutra (50%) - qui si avvisa il coach di QUALE corsia e
  // perche', col messaggio dettagliato gia' pronto lato server.
  const fallbackMessages = Object.values(evaluation.laneErrors || {});
  const errorsHtml = fallbackMessages.length
    ? `<div class="training-eval-errors">${fallbackMessages
        .map((msg) => `<div>⚠ ${msg}</div>`)
        .join("")}</div>`
    : "";

  panel.innerHTML = `
    <h3>Valutazione: winrate stimato per durata partita</h3>
    ${legendHtml}
    ${buildEvaluationChartSvg(evaluation)}
    ${notesHtml}
    ${errorsHtml}
    ${buildLaneFaceoffSection(evaluation)}
  `;
}

function renderTrainingEvaluation() {
  renderEvaluationPanel("training-evaluation", trainingConnected, trainingEvaluation);
}

function renderTournamentEvaluation() {
  renderEvaluationPanel("tournament-evaluation", tournamentConnected, tournamentEvaluation);
}

async function startTraining() {
  const statusEl = document.getElementById("training-start-status");
  if (!trainingModeSelected) {
    statusEl.textContent = "Scegli se giocare contro una squadra o in modalità libera.";
    return;
  }
  if (!trainingSideSelected) {
    statusEl.textContent = "Scegli Blue Side o Red Side.";
    return;
  }
  const enemyTeamUrl = document.getElementById("training-enemy-pool-url").value.trim();
  statusEl.textContent = enemyTeamUrl
    ? "Avvio in corso... (carico prima il pool della squadra avversaria da op.gg)"
    : "Avvio in corso...";

  // Vuoto = a sorte, e la sorte la tira il server, che sa quali squadre ha.
  // Si prende quel che c'e' scritto e non la sola scelta fatta dall'elenco:
  // chi scrive il nome per intero e preme avvia si aspetta quella squadra, non
  // un sorteggio silenzioso. Se il nome non esiste, il server lo dice.
  const scritto = document.getElementById("training-team-combo").value.trim();
  const team = trainingModeSelected === "team" ? scritto : "";
  const result = await backend.trainingStart(
    trainingModeSelected,
    trainingSideSelected,
    enemyTeamUrl,
    team
  );
  if (result.error) {
    statusEl.textContent = result.error;
    return;
  }

  trainingConnected = true;
  trainingPendingChampion = null;
  trainingBusy = false;
  trainingRoleOrder = null;
  trainingEvaluation = null;
  activeSlot = null;
  closeTrainingModal();
  document.getElementById("training-mode-open").classList.add("training-active");
  document.getElementById("training-status").classList.remove("hidden");
  document.getElementById("tournament-mode-open").disabled = true; // mutuamente esclusiva con la modalita' torneo
  applyTrainingState(result);
}

async function stopTraining() {
  trainingConnected = false;
  trainingState = null;
  trainingPendingChampion = null;
  trainingBusy = false;
  trainingRoleOrder = null;
  trainingEvaluation = null;
  document.getElementById("training-mode-open").classList.remove("training-active");
  document.getElementById("training-status").classList.add("hidden");
  document.getElementById("tournament-mode-open").disabled = false;
  updateTrainingConfirmButton();
  renderTrainingRoleSummary();
  renderTrainingEvaluation();
  await backend.trainingStop();
  resetDraftForPlanningMode();
}

function setupTrainingMode() {
  document.getElementById("training-mode-open").addEventListener("click", () => {
    if (trainingConnected || tournamentConnected) return;
    trainingModeSelected = null;
    trainingSideSelected = null;
    document.getElementById("training-mode-team").classList.remove("active");
    document.getElementById("training-mode-freeform").classList.remove("active");
    trainingTeamSelected = "";
    document.getElementById("training-team-pick").classList.add("hidden");
    document.getElementById("training-team-combo").value = "";
    document.getElementById("training-side-blue").classList.remove("active");
    document.getElementById("training-side-red").classList.remove("active");
    openTrainingModal();
  });
  document.getElementById("training-close").addEventListener("click", closeTrainingModal);
  document
    .getElementById("training-mode-team")
    .addEventListener("click", () => selectTrainingMode("team"));
  setupCombo("training-team-picker", trainingTeamOptions, pickTrainingTeam, { filtra: true });
  document
    .getElementById("training-mode-freeform")
    .addEventListener("click", () => selectTrainingMode("freeform"));
  document.getElementById("training-side-blue").addEventListener("click", () => selectTrainingSide("blue"));
  document.getElementById("training-side-red").addEventListener("click", () => selectTrainingSide("red"));
  document.getElementById("training-start").addEventListener("click", startTraining);
  document.getElementById("training-stop").addEventListener("click", stopTraining);
  document.getElementById("training-confirm").addEventListener("click", () => {
    // Stesso bottone, due scopi (richiesto esplicitamente dall'utente
    // 2026-08-26) - durante la draft conferma il pick selezionato, a draft
    // finita lancia la valutazione (vedi updateTrainingConfirmButton).
    if (trainingState && trainingState.finished) {
      evaluateTrainingDraft();
    } else {
      confirmTrainingPick();
    }
  });
}

function renderTeam(team) {
  // Il popover della corsia vive nel <body>, non piu' dentro lo slot (vedi
  // openCounterPopover e il commento su .counter-role-popover in style.css):
  // l'innerHTML="" qui sotto non se lo porta piu' via da solo come faceva
  // quando ne era un discendente. Senza questa riga resterebbe aperto e
  // ancorato con position:fixed a coordinate ormai vecchie, "appeso" sopra
  // uno slot che nel frattempo e' stato ricostruito - possibile ad ogni
  // aggiornamento di stato (in modalita' torneo renderTeam gira ad ogni
  // lettura). Chiuderlo qui replica esattamente il comportamento di prima.
  closeCounterPopover();
  const el = document.getElementById(team === "left" ? "team-slots" : "team-slots-2");
  el.innerHTML = "";
  for (let i = 0; i < 5; i++) {
    const name = teams[team][i];
    const isActive =
      activeSlot && activeSlot.team === team && activeSlot.index === i && activeSlot.kind === "pick";
    const isPending =
      (tournamentPendingSlot &&
        tournamentPendingSlot.team === team &&
        tournamentPendingSlot.index === i &&
        tournamentPendingSlot.kind === "pick") ||
      picksPending[team][i];
    const slot = document.createElement("div");
    slot.className =
      "team-slot" +
      (name ? " filled" : "") +
      (isActive ? " active-slot" : "") +
      (isPending ? " pending" : "");

    if (name) {
      const champ = champions.find((c) => c.name === name);
      applyCompBorderVar(slot, champ);
      const img = document.createElement("img");
      // Splash art rettangolare (banner 16:9), non l'icona quadrata - replica
      // il comportamento di drafterlol per i pick fatti, richiesto
      // esplicitamente dall'utente 2026-09-03/04. Solo qui (team-slot/pick),
      // non in renderBans() sotto: scelta esplicita dell'utente via
      // AskUserQuestion, i ban restano icone piccole come su drafterlol/
      // client LoL (che non mostrano mai splash art per i ban).
      img.src = champ.splash;
      slot.appendChild(img);
      const label = document.createElement("span");
      label.className = "champ-name";
      label.textContent = name;
      slot.appendChild(label);
      renderCounterButton(slot, champ);

      // "Ripeti da qui" - SOLO sui pick del trainee (non i pick del bot,
      // non i ban - richiesta esplicita dell'utente 2026-08-26). Visibile
      // ANCHE a draft finita (non solo mentre in corso): rivalutare un pick
      // dopo aver visto la comp finale intera e' altrettanto utile, forse
      // di piu' - nessuna ragione per negarlo solo perche' e' finita.
      if (
        trainingConnected &&
        trainingState &&
        trainingState.traineeSide === (team === "left" ? "blue" : "red")
      ) {
        const step = trainingState.traineePickSteps[i];
        if (step !== null && step !== undefined) {
          const rewindBtn = document.createElement("button");
          rewindBtn.type = "button";
          rewindBtn.className = "slot-rewind-btn";
          rewindBtn.title = "Ripeti la draft da qui con una scelta diversa";
          rewindBtn.textContent = "↺";
          rewindBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            rewindTraining(step);
          });
          slot.appendChild(rewindBtn);
        }
      }
    } else {
      const label = document.createElement("span");
      label.className = "empty-label";
      label.textContent = `Slot ${i + 1}`;
      slot.appendChild(label);
    }

    slot.addEventListener("click", () => {
      // In modalita' torneo/training lo stato e' guidato solo dal mirror
      // della draft vera (o dalle mosse del bot) - niente editing manuale
      // (stessa regola di una draft reale: le scelte non si modificano una
      // volta fatte, richiesta esplicita).
      if (tournamentConnected || trainingConnected) return;
      if (teams[team][i]) {
        teams[team][i] = null;
      }
      activeSlot = { team, index: i, kind: "pick" };
      renderTeam("left");
      renderTeam("right");
      renderGrid();
      refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
      refreshDetection(team);
    });

    slot.addEventListener("dragover", (e) => {
      if (tournamentConnected || trainingConnected) return;
      e.preventDefault();
      slot.classList.add("drag-over");
    });
    slot.addEventListener("dragleave", () => slot.classList.remove("drag-over"));
    slot.addEventListener("drop", (e) => {
      e.preventDefault();
      slot.classList.remove("drag-over");
      if (tournamentConnected || trainingConnected) return;
      const dropName = e.dataTransfer.getData("text/plain");
      if (!dropName || allPickedNames().includes(dropName) || allBannedNames().includes(dropName)) return;
      teams[team][i] = dropName;
      renderTeam("left");
      renderTeam("right");
      renderGrid();
      refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
      refreshDetection(team);
    });

    el.appendChild(slot);
  }
  renderBans(team);
  updateSaveDraftButton(team);
}

// Sezione ban: stessa idea degli slot pick ma icone piccole "pure" (nessun
// nome/bottone counter - un ban non ha un ruolo da cercare su lolalytics).
// In modalita' torneo e' un puro specchio (stessa guardia di renderTeam,
// niente editing manuale); fuori torneo e' liberamente editabile via click
// (attiva lo slot, poi clicca un campione in griglia) o drag&drop, per
// pianificare/simulare una draft di prova.
function renderBans(team) {
  const el = document.getElementById(team === "left" ? "ban-slots" : "ban-slots-2");
  el.innerHTML = "";
  for (let i = 0; i < 5; i++) {
    const name = bans[team][i];
    const isActive =
      activeSlot && activeSlot.team === team && activeSlot.index === i && activeSlot.kind === "ban";
    const isPending =
      (tournamentPendingSlot &&
        tournamentPendingSlot.team === team &&
        tournamentPendingSlot.index === i &&
        tournamentPendingSlot.kind === "ban") ||
      bansPending[team][i];
    const slot = document.createElement("div");
    slot.className =
      "ban-slot" +
      (name ? " filled" : "") +
      (isActive ? " active-slot" : "") +
      (isPending ? " pending" : "");
    slot.title = name || `Ban ${i + 1}`;

    if (name) {
      const champ = champions.find((c) => c.name === name);
      applyCompBorderVar(slot, champ);
      const img = document.createElement("img");
      img.src = champ.icon;
      slot.appendChild(img);
    }

    slot.addEventListener("click", () => {
      if (tournamentConnected || trainingConnected) return;
      if (bans[team][i]) {
        bans[team][i] = null;
      }
      activeSlot = { team, index: i, kind: "ban" };
      renderTeam("left");
      renderTeam("right");
      renderGrid();
      refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
    });

    slot.addEventListener("dragover", (e) => {
      if (tournamentConnected || trainingConnected) return;
      e.preventDefault();
      slot.classList.add("drag-over");
    });
    slot.addEventListener("dragleave", () => slot.classList.remove("drag-over"));
    slot.addEventListener("drop", (e) => {
      e.preventDefault();
      slot.classList.remove("drag-over");
      if (tournamentConnected || trainingConnected) return;
      const dropName = e.dataTransfer.getData("text/plain");
      if (!dropName || allPickedNames().includes(dropName) || allBannedNames().includes(dropName)) return;
      bans[team][i] = dropName;
      renderTeam("left");
      renderTeam("right");
      renderGrid();
      refreshSuggestions(); // non await-ata deliberatamente, vedi commento sulla funzione
    });

    el.appendChild(slot);
  }
}

function bindTagFilterClick(el, tag) {
  el.addEventListener("click", (e) => {
    e.stopPropagation(); // non deve anche aprire/chiudere il profilo della card
    if (activeTagFilters.has(tag)) {
      activeTagFilters.delete(tag);
    } else {
      activeTagFilters.add(tag);
    }
    // lo stesso tag puo' comparire su piu' comp (es. "Disingaggio") - sincronizza
    // tutte le sue occorrenze, non solo quella cliccata
    const isActive = activeTagFilters.has(tag);
    document.querySelectorAll(".comp-tag").forEach((chip) => {
      if (chip.textContent === tag) {
        chip.classList.toggle("filter-active", isActive);
      }
    });
    renderGrid();
  });
}

function buildProfileSection(title, lines) {
  const section = document.createElement("div");
  section.className = "comp-profile-section";

  const heading = document.createElement("div");
  heading.className = "comp-profile-heading";
  heading.textContent = title;
  section.appendChild(heading);

  for (const line of lines) {
    const p = document.createElement("div");
    p.className = "comp-profile-line";
    p.textContent = line;
    section.appendChild(p);
  }

  return section;
}

let detectionRequestId = { left: 0, right: 0 };

async function refreshDetection(team) {
  const requestId = ++detectionRequestId[team];
  const results = await backend.detect(teams[team].filter(Boolean));
  if (requestId !== detectionRequestId[team]) return; // risposta superata da una richiesta piu' recente, scartata

  const el = document.getElementById(team === "left" ? "comp-status" : "comp-status-2");
  el.innerHTML = "";

  for (const [comp, meta] of Object.entries(compMeta)) {
    const status = results[comp];
    const card = document.createElement("div");
    card.className =
      "comp-card" +
      (status.satisfied ? " satisfied" : "") +
      (activeFilters.has(comp) ? " filter-active" : "");
    card.style.color = meta.color;
    card.addEventListener("click", () => {
      if (expandedComps[team].has(comp)) {
        expandedComps[team].delete(comp);
      } else {
        expandedComps[team].add(comp);
      }
      if (activeFilters.has(comp)) {
        activeFilters.delete(comp);
      } else {
        activeFilters.add(comp);
      }
      renderGrid();
      refreshDetection("left");
      refreshDetection("right");
    });

    const title = document.createElement("div");
    title.className = "comp-card-title";
    const dot = document.createElement("span");
    dot.className = "comp-dot";
    dot.style.background = meta.color;
    title.appendChild(dot);
    const label = document.createElement("span");
    label.style.color = "var(--text)";
    label.textContent = `${comp} (${status.member_count}/${status.member_threshold})`;
    title.appendChild(label);
    card.appendChild(title);

    const tagsEl = document.createElement("div");
    tagsEl.className = "comp-tags";
    for (const tag of meta.mandatory) {
      const t = document.createElement("span");
      t.className =
        "comp-tag" +
        (status.covered.includes(tag) ? " covered" : "") +
        (activeTagFilters.has(tag) ? " filter-active" : "");
      t.textContent = tag;
      tagsEl.appendChild(t);
      bindTagFilterClick(t, tag);
    }
    for (const tag of meta.optional) {
      const t = document.createElement("span");
      t.className =
        "comp-tag" +
        (status.optional_covered.includes(tag) ? " covered" : "") +
        (activeTagFilters.has(tag) ? " filter-active" : "");
      t.textContent = tag;
      tagsEl.appendChild(t);
      bindTagFilterClick(t, tag);
    }
    card.appendChild(tagsEl);

    if (status.satisfied || expandedComps[team].has(comp)) {
      const profile = document.createElement("div");
      profile.className = "comp-profile";
      profile.appendChild(buildProfileSection("Condizione di vittoria", meta.win_condition));
      profile.appendChild(buildProfileSection("Vantaggi", meta.pros));
      profile.appendChild(buildProfileSection("Svantaggi", meta.cons));
      card.appendChild(profile);
    }

    el.appendChild(card);
  }
}

init();
