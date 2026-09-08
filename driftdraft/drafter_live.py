"""Ponte live verso una draft room reale di drafter.lol.

A differenza di op.gg/lolalytics/tiermaker (un fetch, poi il browser si
chiude), qui la sessione Playwright resta APERTA per tutta la durata della
draft (decine di minuti): serve sia per LEGGERE lo stato in tempo reale
(fase corrente, timer, ban/pick gia' fatti da entrambi i lati) sia, in un
passo successivo, per INVIARE le scelte fatte in DriftDraft come azioni
vere sulla draft reale ("modalita' torneo").

ATTENZIONE - rischio reale, non solo tecnico: a differenza di tutte le
altre integrazioni di questo progetto (sola lettura di dati pubblici), qui
si scrive un'azione dentro una draft live, a tempo (~25s per azione,
verificato navigando il sito), che persone vere stanno guardando. Va
sempre testato su una draft di prova, mai la prima volta su uno
scrim/torneo vero.

Struttura pagina verificata navigando manualmente una draft reale (ID
stabili nel DOM, non e' stato necessario indovinare selettori CSS
generati): #step-name (fase corrente), #timer (secondi rimanenti),
#draft-button (bottone azione corrente), #blue-team-name/#red-team-name,
#blue-pick-1..5/#red-pick-1..5, #blue-ban-1..5/#red-ban-1..5 (ognuno
contiene uno span.champion-name con il nome del campione o "None" se
vuoto/scaduto).

GOTCHA IMPORTANTE (trovato testando, non ovvio in anticipo): l'API sync di
Playwright NON e' utilizzabile fra thread diversi - un browser/pagina creato
in un thread da' errore ("cannot switch to a different thread") se usato da
un thread diverso. Il server Bottle di questo progetto e' threaded (un
thread NUOVO per ogni richiesta HTTP, vedi server.py), quindi chiamare
Playwright direttamente dentro le funzioni delle route avrebbe fatto
scadere la sessione alla primissima richiesta successiva a "connect". Fix:
un singolo thread dedicato possiede l'intero ciclo di vita di Playwright
(creazione, interazione, chiusura); le richieste HTTP comunicano con quel
thread SOLO tramite una `queue.Queue` (sicura fra thread), mai chiamando
Playwright direttamente.
"""

import queue
import shutil
import tempfile
import threading

from playwright.sync_api import sync_playwright

from driftdraft.data import load_champions, slugify_champion_name
from driftdraft.paths import get_bundle_dir

# Ad-blocker (uBlock Origin Lite, Manifest V3) - vedi il commento esteso su
# _POPUP_WATCHDOG_JS/nell'uso qui sotto per il perche'. La versione
# "classica" Manifest V2 di uBlock Origin (quella comunemente installata a
# mano nei browser) NON si carica affatto in questa build di Chromium -
# verificato con un errore REALE ("Impossibile installare l'estensione
# perche' utilizza una versione del manifest non supportata"), non solo
# ipotizzato. uBlock Origin **Lite** e' la riscrittura Manifest V3 dello
# stesso autore (gorhill), unpacked da
# github.com/uBlockOrigin/uBOL-home/releases (uBOLite_*.chromium.zip),
# scaricata ed estratta a mano il 2026-09-04, GPL-3.0 - LICENSE.txt incluso
# nella cartella. `.exists()` controllato prima di passare gli argomenti
# (sotto) invece di richiederla sempre: se la cartella manca (es. checkout
# di sviluppo senza averla scaricata), la sessione si apre comunque, solo
# senza ad-blocking, invece di un crash all'avvio.
_EXTENSION_PATH = get_bundle_dir() / "vendor" / "ublock-origin-lite"


def _dismiss_known_popups(page) -> None:
    """Dialoghi CONOSCIUTI del sito (per nome/posizione, non pubblicita'
    imprevedibili - quelle restano gestite dall'ad-blocker, vedi
    _EXTENSION_PATH sopra) - 3 casi reali trovati testando dal vivo
    (2026-09-04): il muro anti-adblock del sito ("Skip once" - vedi sotto
    per il perche' NON e' un problema qui, a differenza di quando il
    profilo era persistente), la promo "Draft Prep Tool" ("Maybe later"),
    il tooltip "switch selected role" ("Got it"). Lista FISSA di testi noti,
    deliberata - richiesto esplicitamente dall'utente al posto del vecchio
    watchdog generico (_POPUP_WATCHDOG_JS sotto, addormentato) che nascondeva
    alla cieca qualunque cosa coprisse il bottone, rischiando di colpire
    anche funzioni legittime mai viste prima. Ogni tentativo e' tollerante
    (timeout basso, nessun errore se quel popup non c'e' in questo momento)
    - chiamata in PIU' punti del flusso di join (non tutti i popup compaiono
    nello stesso istante, vedi i due punti di chiamata)."""
    for text in ("Skip once", "Maybe later", "Got it"):
        try:
            page.click(f'button:has-text("{text}")', timeout=1500)
        except Exception:
            pass


_champion_name_by_riot_id: dict[int, str] | None = None  # cache pigra, vedi _resolve_ban_id


def _resolve_ban_id(id_str: str | None) -> str | None:
    """ID Riot (stringa, da _STATE_JS) -> nome campione, via la tabella
    dell'xlsx (colonna "ID"). Cache costruita al primo utilizzo, non ad ogni
    chiamata - il polling gira ogni 0.1s per tutta la draft, ricaricare
    l'xlsx da disco ogni volta sarebbe inutile (i dati non cambiano durante
    una connessione) oltre che lento."""
    global _champion_name_by_riot_id
    if id_str is None:
        return None
    if _champion_name_by_riot_id is None:
        _champion_name_by_riot_id = {
            c.riot_id: c.name for c in load_champions() if c.riot_id is not None
        }
    try:
        return _champion_name_by_riot_id.get(int(id_str))
    except ValueError:
        return None


def _normalize_role_tag(tag: str | None) -> str | None:
    """Etichetta del badge di conferma ruolo (vedi sideRoles in _STATE_JS) ->
    stesso nome usato da ROLE_ORDER in training_bot.py - unica differenza
    reale e' "Bottom" (badge) vs "Bot" (ROLE_ORDER), le altre 4 combaciano
    gia'."""
    if tag == "Bottom":
        return "Bot"
    return tag


_champion_id_by_name: dict[str, int] | None = None  # cache pigra, vedi _resolve_champion_id


def _resolve_champion_id(name: str) -> int | None:
    """Nome campione -> ID Riot: stessa tabella xlsx di _resolve_ban_id, ma
    in direzione opposta. Serve per SELEZIONARE un campione nella griglia
    senza affidarsi al testo dell'attributo alt delle immagini, che su
    drafter.lol NON e' il nome campione ma un "alias" interno senza spazi
    ne' apostrofi (verificato nel DOM reale, 2026-08-17: Kai'Sa ha
    alt="Kaisa", stesso schema di Data Dragon - AurelionSol, MasterYi,
    Belveth, ecc). La vecchia selezione via img[@alt="{nome}"] falliva
    sempre per questi campioni (bug segnalato dall'utente: pick con spazio
    o apostrofo mai inviati). L'ID e' pero' comunque incorporato nell'URL
    immagine (.../champion-icons/<id>.png), esattamente come gia' usato per
    leggere i ban - qui si legge la stessa colonna "ID" ma da nome a ID."""
    global _champion_id_by_name
    if _champion_id_by_name is None:
        _champion_id_by_name = {
            c.name: c.riot_id for c in load_champions() if c.riot_id is not None
        }
    return _champion_id_by_name.get(name)


_champion_name_by_cdragon_slug: dict[str, str] | None = None  # cache pigra, vedi _resolve_role_confirm_slug


def _resolve_role_confirm_slug(slug: str | None) -> str | None:
    """Slug CommunityDragon (dall'URL dell'immagine SPLASH ART nelle corsie
    di role confirmation, es. "garen" da
    .../assets/characters/garen/skins/base/images/garen_splash_....jpg) ->
    nome campione. IDENTITA' COMPLETAMENTE DIVERSA da quella usata per pick
    e ban altrove in questo file (ID Riot numerico incorporato in
    champion-icons/<id>.png) - trovato SOLO dopo un test reale dell'utente
    (2026-08-20, "'Yasuo' is not in list") che ha rivelato come queste
    immagini specifiche siano splash art per NOME campione (comunque un
    alias interno senza spazi/apostrofi, non il nome esatto - stesso schema
    gia' visto per gli alt delle icone in _resolve_champion_id), non icone
    per ID. Riusa slugify_champion_name() (data.py, gia' validata per
    op.gg/lolalytics) per costruire la tabella inversa - NON verificato al
    100% che CommunityDragon usi ESATTAMENTE la stessa convenzione per ogni
    caso speciale (es. Wukong, Nunu & Willump), ma e' la migliore
    approssimazione disponibile senza un nuovo fetch di rete; se un domani
    un nome speciale non risolve, il chiamante (confirm_role_order) lo
    riporta come errore leggibile invece di un crash o un'azione sbagliata."""
    global _champion_name_by_cdragon_slug
    if slug is None:
        return None
    if _champion_name_by_cdragon_slug is None:
        _champion_name_by_cdragon_slug = {
            slugify_champion_name(c.name): c.name for c in load_champions()
        }
    return _champion_name_by_cdragon_slug.get(slug)


_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Stessa identica logica del watchdog qui sotto (di proposito NON
# refactorizzata per condividerla - comporrebbe due stringhe JS incrociate,
# rischioso da sbagliare senza un vantaggio concreto), ma richiamabile "sul
# momento" invece di aspettare il prossimo giro del setInterval a 500ms.
# Trovato utile in un test reale (2026-08-17): il watchdog di sottofondo
# ripuliva comunque il pannello Preferenze del sito comparso dopo una
# selezione, ma non abbastanza in fretta da non intralciare un click di
# Conferma dato nell'istante sbagliato - chiamare questa PRIMA di ogni
# click (select e conferma) restringe quella finestra al minimo.
_CLEAR_BLOCKING_OVERLAY_JS = """
() => {
  const target = document.getElementById('draft-button');
  if (!target) return false;
  const rect = target.getBoundingClientRect();
  if (rect.width === 0 || rect.height === 0) return false;
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  const topEl = document.elementFromPoint(cx, cy);
  if (!topEl || topEl === target || target.contains(topEl)) return false;

  let el = topEl;
  while (el && el !== document.body) {
    if (getComputedStyle(el).position === 'fixed') {
      // Log diagnostico, non cambia il comportamento (nasconde comunque
      // subito) - aggiunto 2026-08-17 per scoprire finalmente COSA sia
      // davvero questo overlay, mai identificato con certezza finora.
      // Il TESTO leggibile (non l'HTML grezzo, che con 400 caratteri
      // veniva consumato quasi tutto dalle classi CSS prima di arrivare
      // al contenuto vero - bug trovato in un test reale) e' molto piu'
      // immediato per capire di cosa si tratta. Controllabile con F12 ->
      // Console sulla finestra vera di drafter.lol.
      console.log(
        '[DriftDraft watchdog] nascosto - testo:',
        el.textContent.trim().slice(0, 300),
        '| classi:', el.className.toString().slice(0, 150)
      );
      el.style.setProperty('display', 'none', 'important');
      return true;
    }
    el = el.parentElement;
  }
  return false;
}
"""

# ADDORMENTATA (2026-09-04, decisione esplicita dell'utente) - non piu'
# richiamata (vedi il punto di chiamata, subito dopo essersi uniti alla
# room, per il ragionamento completo): un test end-to-end reale ha
# dimostrato che questo watchdog nasconde alla cieca ANCHE funzioni
# legittime del sito (non solo pubblicita' - un tooltip "switch selected
# role" a schermo intero e' stato nascosto insieme alle vere pubblicita').
# Sostituita da due meccanismi mirati: _dismiss_known_popups (in cima al
# file) per i pochi dialoghi CONOSCIUTI del sito stesso, e un ad-blocker
# vero in Playwright (uBlock Origin Lite, vedi _EXTENSION_PATH) per le
# pubblicita' imprevedibili - tramite le sue regole di blocco incorporate,
# NON filtri personalizzati salvati a mano (richiederebbero un profilo
# Chromium persistente, scartato lo stesso giorno: esaurisce per sempre il
# bypass "Skip once" del muro anti-adblock del sito dopo la prima draft).
# Codice lasciato intatto (non cancellato) - riattivabile all'istante se
# in futuro serve di nuovo un'ultima rete di sicurezza generica.
_POPUP_WATCHDOG_JS = """
() => {
  if (window.__driftdraftWatchdog) return;
  window.__driftdraftWatchdog = true;

  // Il sito mostra ogni tanto popup promozionali/annunci non prevedibili in
  // anticipo (visti durante i test: card "did you know...", altri overlay -
  // il sito e' pieno di infrastruttura pubblicitaria, prebid/GPT/btloader,
  // che ne apre di nuovi ad ogni interazione) che intercettano i click sul
  // bottone azione - invece di elencare i popup conosciuti (fragile, ne
  // comparirebbe sempre uno nuovo), controlla COSA sta davvero sopra il
  // bottone in questo momento: se non e' il bottone stesso, risali al primo
  // antenato "fixed" (il contenitore dell'overlay) e nascondilo.
  //
  // NASCONDE, non rimuove (bug trovato in un test reale, 2026-08-16): un
  // `.remove()` diretto sul DOM confonde la mappa interna di React (il
  // framework di drafter.lol) rispetto al DOM reale - al primo
  // re-render successivo React prova a rimuovere lo stesso nodo che
  // pensa di avere ancora e crasha con "NotFoundError: Failed to
  // execute 'removeChild'... is not a child of this node", mandando
  // l'intera pagina in errore. display:none ottiene lo stesso risultato
  // pratico (il popup non blocca piu' i click, elementFromPoint lo
  // salta) senza staccare il nodo dal DOM, quindi React resta coerente.
  setInterval(() => {
    const target = document.getElementById('draft-button');
    if (!target) return;
    const rect = target.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const topEl = document.elementFromPoint(cx, cy);
    if (!topEl || topEl === target || target.contains(topEl)) return;

    let el = topEl;
    while (el && el !== document.body) {
      if (getComputedStyle(el).position === 'fixed') {
        // Vedi stesso log in _CLEAR_BLOCKING_OVERLAY_JS - diagnostico, non
        // cambia il comportamento.
        console.log(
          '[DriftDraft watchdog] nascosto - testo:',
          el.textContent.trim().slice(0, 300),
          '| classi:', el.className.toString().slice(0, 150)
        );
        el.style.setProperty('display', 'none', 'important');
        return;
      }
      el = el.parentElement;
    }
  }, 500);
}
"""

# Causa REALE del pannello Preferenze visto piu' volte durante i test,
# trovata il 2026-08-17 ispezionando il DOM con l'aiuto dell'utente: un
# pulsante quasi invisibile (10% di opacita' di base) con testo
# "navigation" in cima alla pagina che, se toccato, rivela un'intera barra
# di navigazione del sito (New Draft/Login/impostazioni ecc, estranea alla
# draft) - dentro c'e' l'icona a ingranaggio che apre Preferences. Due
# tocchi quasi invisibili, non un singolo bottone - da qui il pattern
# "compare ogni tanto" mai capito prima. Normalmente l'utente non la vede
# mai nel suo browser reale perche' Opera GX con uBlock Origin la blocca di
# default - il NOSTRO browser automatizzato pero' non ha alcun blocco
# pubblicitario installato (scelta deliberata di questo progetto fin dalla
# Fase 1), quindi la vede per intero e puo' finirci sopra per sbaglio.
#
# TENTATIVO FALLITO, PEGGIORATIVO (2026-08-17) - NON RICHIAMARE PIU' QUESTA
# FUNZIONE senza aver capito meglio la causa: la versione ricorrente
# (setInterval ogni 500ms) ha reso il problema costante (20/20 volte a
# draft, prima 2/10) invece di risolverlo, e ha introdotto un flickering
# visibile del pannello (apre, va tutto "acceso", si richiude scartando,
# si ripete) - sintomo di React che rimonta ripetutamente il componente per
# colpa del nostro `display:none` diretto sul DOM che confonde la sua
# mappa interna (stesso meccanismo del crash gia' visto con `.remove()`,
# manifestato stavolta come remount invece che crash). Probabile causa
# anche di un bug nuovo comparso nello stesso test (il primo ban di ogni
# lato non veniva mai registrato da DriftDraft). Codice lasciato qui per
# riferimento futuro, ma NON chiamato: manipolare ripetutamente elementi
# gestiti da React via DOM diretto e' rischioso, va ripensato con un
# approccio diverso (es. intercettare a livello di click invece di
# nascondere l'elemento sorgente) prima di riattivarlo.
_HIDE_SITE_NAV_JS = """
() => {
  if (window.__driftdraftNavHider) return;
  window.__driftdraftNavHider = true;

  const hide = () => {
    const navPillBtn = [...document.querySelectorAll('button')].find(
      (b) => b.textContent.trim().toLowerCase() === 'navigation'
    );
    if (navPillBtn) {
      let wrapper = navPillBtn;
      while (wrapper.parentElement && getComputedStyle(wrapper).position !== 'fixed') {
        wrapper = wrapper.parentElement;
      }
      wrapper.style.setProperty('display', 'none', 'important');
    }

    document.querySelectorAll('nav').forEach((nav) => {
      if (getComputedStyle(nav).position === 'fixed') {
        nav.style.setProperty('display', 'none', 'important');
      }
    });
  };

  hide();
  setInterval(hide, 500);
}
"""

# Legge il dialogo "Join the Draft" (la schermata che drafter.lol mostra
# appena si apre il link) SENZA cliccare nulla: quali team esistono in questa
# room e quali lati sono ancora liberi. Serve alla connessione in due tempi
# introdotta 2026-09-05 su richiesta dell'utente - prima il nome del team
# andava digitato a mano ad ogni connessione, ora si incolla solo il link e
# si sceglie da un elenco vero.
#
# Struttura verificata dal vivo su una draft room di prova (2026-09-05):
#
#   <section>
#     <div><label>Team Selection</label></div>
#     <div class="grid..."><button>NomeTeam1</button><button>NomeTeam2</button></div>
#     <button>Clear Team Selection</button>
#   </section>
#   <section>
#     <div><label>Role Selection</label><span>Not selected</span></div>
#     <button>Blue Side ...</button><button>Red Side ...</button>
#     <button>Continue as Spectator</button>
#   </section>
#
# Ci si aggancia alle <label> di testo ("Team Selection"/"Role Selection") e
# si risale al primo antenato che contiene almeno 2 bottoni - NON alle classi
# CSS, che sono Tailwind generate e cambiano senza preavviso.
#
# Significato di `disabled`, misurato sul sito (non dedotto):
#  - su un bottone TEAM  -> e' il team attualmente selezionato da noi;
#  - su un bottone LATO  -> quel lato NON e' disponibile, o perche' non
#    abbiamo ancora scelto un team, o perche' l'ha gia' preso qualcun altro.
# Verificato anche il caso incrociato: scegliendo lo stesso team di chi ha
# gia' preso blue, ENTRAMBI i lati risultano disabled (il sito lega team e
# lato) - quindi non serve nessuna euristica nostra, basta leggere il flag.
_JOIN_OPTIONS_JS = r"""
() => {
  const sezione = (nome) => {
    const lbl = [...document.querySelectorAll("label")].find(
      (e) => e.textContent.trim().toLowerCase() === nome
    );
    if (!lbl) return null;
    let n = lbl.parentElement;
    for (let i = 0; i < 5 && n; i++) {
      if (n.querySelectorAll("button").length >= 2) return n;
      n = n.parentElement;
    }
    return null;
  };

  const teamSec = sezione("team selection");
  const roleSec = sezione("role selection");
  if (!teamSec || !roleSec) return { present: false };

  const teams = [...teamSec.querySelectorAll("button")]
    .filter((b) => !/clear team selection/i.test(b.textContent))
    .map((b) => ({
      name: b.textContent.trim(),
      // vedi commento Python: disabled su un team = e' quello scelto da noi
      selected: b.disabled,
    }));

  const sideBtns = [...roleSec.querySelectorAll("button")];
  const findSide = (re) => sideBtns.find((b) => re.test(b.textContent));
  const blue = findSide(/blue\s*side/i);
  const red = findSide(/red\s*side/i);

  return {
    present: true,
    teams,
    sides: {
      blue: blue ? !blue.disabled : false,
      red: red ? !red.disabled : false,
    },
  };
}
"""


# Clicca un bottone del dialogo di join (team o lato). Volutamente JS e non
# un selettore Playwright: i selettori con :has()/:text-is() su questa
# struttura fallivano in silenzio (provato dal vivo 2026-09-05 - il click non
# avveniva, i lati restavano tutti "occupati" e l'errore veniva ingoiato da
# un try/except). Qui invece si riusa esattamente la stessa funzione
# `sezione()` di _JOIN_OPTIONS_JS, che sappiamo trovare i contenitori giusti,
# e si restituisce un esito ESPLICITO: chi chiama sa se il click e' avvenuto.
_JOIN_CLICK_JS = r"""
({ section, text, exact }) => {
  const sezione = (nome) => {
    const lbl = [...document.querySelectorAll("label")].find(
      (e) => e.textContent.trim().toLowerCase() === nome
    );
    if (!lbl) return null;
    let n = lbl.parentElement;
    for (let i = 0; i < 5 && n; i++) {
      if (n.querySelectorAll("button").length >= 2) return n;
      n = n.parentElement;
    }
    return null;
  };

  const sec = sezione(section);
  if (!sec) return { ok: false, reason: "sezione non trovata" };

  const btns = [...sec.querySelectorAll("button")];
  const wanted = exact
    ? btns.find((b) => b.textContent.trim() === text)
    : btns.find((b) => new RegExp(text, "i").test(b.textContent));

  if (!wanted) {
    return {
      ok: false,
      reason: "bottone non trovato",
      disponibili: btns.map((b) => b.textContent.trim()),
    };
  }
  if (wanted.disabled) {
    // Su un TEAM disabled significa "gia' selezionato" (quindi va bene), su
    // un LATO significa "non disponibile" - distinguerlo tocca al chiamante.
    return { ok: true, alreadyDisabled: true };
  }
  wanted.click();
  return { ok: true, alreadyDisabled: false };
}
"""


_STATE_JS = r"""
() => {
  const slotText = (id) => {
    const el = document.getElementById(id);
    if (!el) return null;
    const span = el.querySelector('.champion-name');
    return span ? span.textContent.trim() : null;
  };
  const sideSlots = (side, kind) =>
    [1, 2, 3, 4, 5].map((i) => slotText(`${side}-${kind}-${i}`));

  // "In sospeso" (selezionato ma non ancora bloccato, o slot vuoto in
  // attesa di questo turno) - trovato ispezionando il DOM reale mentre uno
  // slot era in questo stato (2026-08-17): una classe CSS
  // "pulse-animation-blue"/"pulse-animation-red" compare su un div dentro
  // lo slot corrente, presente sia a vuoto che con un campione gia'
  // scelto-ma-non-confermato, e sparisce non appena la scelta e' bloccata
  // davvero. Vale sia per i pick che per i ban, stesso pattern su entrambi.
  const isPending = (id) => {
    const el = document.getElementById(id);
    return !!(el && el.querySelector('[class*="pulse-animation"]'));
  };
  const sidePending = (side, kind) =>
    [1, 2, 3, 4, 5].map((i) => isPending(`${side}-${kind}-${i}`));

  // I ban NON hanno un nome in chiaro nel DOM (trovato testando su una
  // draft reale, 2026-08-17 - diverso dai pick, che invece hanno
  // span.champion-name): solo un'icona con alt="ban" generico. L'unica
  // identita' disponibile e' l'ID numerico Riot incorporato nell'URL
  // dell'immagine (es. ".../champion-icons/115.png" = Ziggs). Ritorna
  // l'ID come stringa (o null se lo slot e' vuoto/nessuna img) - la
  // conversione ID->nome campione avviene lato Python (read_state), dove
  // e' gia' caricata la tabella ID->nome dall'xlsx (colonna "ID",
  // sincronizzata da scripts/sync_champion_ids.py).
  const banId = (id) => {
    const el = document.getElementById(id);
    if (!el) return null;
    // Il PRIMO ban di ogni lato ha una struttura in piu' rispetto agli
    // altri 4 (verificato nel DOM reale, 2026-08-17): un bottone "Request
    // swap for this ban" (probabile regola di torneo specifica per il
    // primissimo ban) posizionato PRIMA dell'icona campione nell'ordine
    // del DOM. Un semplice el.querySelector('img') (bug trovato in un
    // test reale: il primo ban di ogni lato non risultava mai registrato)
    // rischia di trovare un'eventuale icona DENTRO quel bottone invece
    // dell'icona campione - richiedere alt="ban" (etichetta SOLO
    // dell'icona campione, verificata su tutti gli slot) la trova sempre
    // quella giusta, a prescindere da cos'altro c'e' nello slot.
    const img = el.querySelector('img[alt="ban"]');
    if (!img) return null;
    const src = img.currentSrc || img.src || '';
    const m = src.match(/champion-icons(?:%2F|\/)(-?\d+)\.png/);
    return m ? m[1] : null;
  };
  const sideBanIds = (side) => [1, 2, 3, 4, 5].map((i) => banId(`${side}-ban-${i}`));

  // Tag ruolo CONFERMATO (es. "Top"/"Jungle"/"Mid"/"Bottom"/"Support"),
  // trovato tramite un'indagine dal vivo (2026-08-26) dopo che l'utente ha
  // segnalato un caso reale (Hecarim indovinato come Support da assign_roles
  // quando in realta' era il toplaner - vedi driftdraft/draft_evaluation.py
  // per la storia completa). A differenza delle lane di drag
  // ([data-role-confirm-lane], private per lato - esistono nel DOM SOLO per
  // il lato a cui siamo connessi, mai per l'avversario), questo badge
  // compare SUL PICK STESSO (".role-badge-fade-in", figlio diretto dello
  // stesso elemento "{side}-pick-{n}" gia' letto da slotText sopra - NESSUN
  // riordino dei pick-slot, solo un badge aggiunto) UNA VOLTA CHE ENTRAMBI I
  // LATI hanno superato la fase di conferma ruoli (per drag riuscito O per
  // timeout col default) - ed e' leggibile da ENTRAMBI i lati, confermato
  // dal vivo leggendolo dal lato opposto a quello che l'aveva confermato.
  // null finche' non confermato (prima di allora l'elemento .role-badge-
  // fade-in semplicemente non esiste) - il chiamante (read_state) lo tratta
  // come "non ancora disponibile", non come un errore.
  const roleTag = (id) => {
    const el = document.getElementById(id);
    const badge = el ? el.querySelector('.role-badge-fade-in') : null;
    const span = badge ? badge.querySelector('span') : null;
    return span ? span.textContent.trim() : null;
  };
  const sideRoles = (side) => [1, 2, 3, 4, 5].map((i) => roleTag(`${side}-pick-${i}`));

  // Fearless draft - "Used Champions This Series", funzione nuova di
  // drafter.lol (introdotta pochi giorni prima di questa integrazione).
  // Ogni pick di ogni game gia' giocata nella serie ha un elemento con id
  // "{lato}-fearless-game-{indice0}-pick-{indice}" (lato = blue/red DI
  // QUELLA game specifica, non un'identita' di squadra persistente - ne'
  // lo fa il sito stesso quando le squadre si scambiano lato). Lo slot
  // "None" (pick scaduto/saltato) non ha nessuna img e va scartato.
  // Verificato dal vivo creando una draft di test completa a 2 game.
  const fearlessPicks = Array.from(document.querySelectorAll('[id*="-fearless-game-"]'))
    .map((el) => {
      const m = el.id.match(/^(blue|red)-fearless-game-(\d+)-pick-\d+$/);
      if (!m) return null;
      const img = el.querySelector('img[alt]');
      return img ? { side: m[1], game: parseInt(m[2], 10) + 1, champion: img.alt } : null;
    })
    .filter(Boolean);

  const stepEl = document.getElementById('step-name');
  const timerEl = document.getElementById('timer');
  const btnEl = document.getElementById('draft-button');
  const blueNameEl = document.getElementById('blue-team-name');
  const redNameEl = document.getElementById('red-team-name');

  // Role confirmation (funzione nuova di drafter.lol, dopo i 20 pick/ban -
  // vedi sezione dedicata nelle note di progetto). La fase di drag vera e
  // propria (libreria dnd-kit) esiste nel DOM SOLO una volta che ENTRAMBI i
  // lati hanno cliccato il proprio "Ready for role confirmation" - prima di
  // allora questi elementi semplicemente non ci sono. E' il segnale che
  // confirm_role_order() aspetta prima di agire: nessun drag ha senso
  // (nulla da trovare/cliccare) finche' questo non e' true.
  const roleConfirmActive = document.querySelectorAll('[data-role-confirm-lane]').length > 0;

  return {
    step: stepEl ? stepEl.textContent.trim() : null,
    timer: timerEl ? timerEl.textContent.trim() : null,
    buttonText: btnEl ? btnEl.textContent.trim() : null,
    buttonDisabled: btnEl ? !!btnEl.disabled : null,
    blueTeamName: blueNameEl ? blueNameEl.textContent.trim() : null,
    redTeamName: redNameEl ? redNameEl.textContent.trim() : null,
    blueBanIds: sideBanIds('blue'),
    redBanIds: sideBanIds('red'),
    bluePicks: sideSlots('blue', 'pick'),
    redPicks: sideSlots('red', 'pick'),
    blueRoleTags: sideRoles('blue'),
    redRoleTags: sideRoles('red'),
    bluePicksPending: sidePending('blue', 'pick'),
    redPicksPending: sidePending('red', 'pick'),
    blueBansPending: sidePending('blue', 'ban'),
    redBansPending: sidePending('red', 'ban'),
    fearlessPicks,
    roleConfirmActive,
  };
}
"""

# Role confirmation - ordine delle 5 corsie come richiesto dal sito
# (data-role-confirm-lane="top|jungle|mid|adc|support" - la 4a e' "adc", MAI
# "bottom": ipotesi iniziale sbagliata, mai verificata sul valore vero
# dell'attributo finche' un errore reale dell'utente non l'ha rivelato,
# 2026-08-20 - vedi confirm_role_order per il dettaglio del bug che ha
# causato). Il riordino sul sito e' una sortable-list dnd-kit (arrayMove:
# estrai un elemento e reinseriscilo altrove, MAI uno scambio a coppia -
# confermato trascinando Top->Support in un test reale: tutto cio' che
# stava in mezzo si e' spostato di una posizione, non solo i due estremi).
_ROLE_CONFIRM_LANES = ["top", "jungle", "mid", "adc", "support"]


def _compute_role_moves(current: list[str], desired: list[str]) -> list[dict[str, str]]:
    """current/desired sono la stessa permutazione di 5 nomi campione (ordine
    pick vs ordine scelto dal coach in DriftDraft) - ritorna la sequenza
    minima di mosse {from, to} (nomi di corsia) che trasforma current in
    desired tramite arrayMove ripetuti, stesso identico meccanismo del sito.
    Al massimo 4 mosse per 5 elementi (l'ultima posizione e' sempre gia'
    corretta una volta sistemate le prime 4)."""
    working = list(current)
    moves: list[dict[str, str]] = []
    for pos in range(5):
        want = desired[pos]
        at = working.index(want)
        if at != pos:
            moves.append({"from": _ROLE_CONFIRM_LANES[at], "to": _ROLE_CONFIRM_LANES[pos]})
            item = working.pop(at)
            working.insert(pos, item)
    return moves


# Replica via eventi sintetici il drag validato manualmente (vedi note di
# progetto, sessione investigativa 2026-08-19): dnd-kit usa PointerSensor,
# serve un pointerdown sull'elemento draggable sorgente, ALCUNI pointermove
# intermedi (non un salto diretto - la sensor/collision-detection di
# dnd-kit ha bisogno di attraversare la posizione, un singolo down->up senza
# movimento nel mezzo viene trattato come un click, non un drag) fino al
# centro della corsia target, poi pointerup. mousedown/mousemove/mouseup
# paralleli per ridondanza (visti utili nel test dal vivo, costano nulla in
# piu'). Le coordinate si leggono al MOMENTO (getBoundingClientRect), mai
# riusate da una lettura precedente - il layout cambia quando la fase di
# drag si apre.
_ROLE_DRAG_JS = r"""
async ({ side, moves }) => {
  // NON scoped su #{side}-picks-row (bug reale trovato dal vivo,
  // 2026-08-20: quell'id NON e' un antenato vero delle corsie, per motivi
  // mai chiariti - forse un ID duplicato altrove nella pagina che
  // getElementById/lo scoping intercettava per primo). Non serve comunque:
  // le corsie esistono UNA SOLA VOLTA nell'intera pagina in ogni momento
  // (solo il lato a cui siamo connessi mostra la propria UI di drag,
  // confermato: sempre esattamente 5 elementi [data-role-confirm-lane],
  // mai 10), quindi una query diretta e' gia' univoca da sola.
  const laneEl = (lane) => document.querySelector(`[data-role-confirm-lane="${lane}"]`);
  const draggableIn = (el) => (el ? el.querySelector('[aria-roledescription="draggable"]') : null);

  const fire = (Ctor, type, x, y, el) => {
    const target = el || document.elementFromPoint(x, y);
    if (!target) return;
    target.dispatchEvent(new Ctor(type, {
      bubbles: true, cancelable: true, clientX: x, clientY: y,
      button: 0, buttons: 1, pointerId: 1, pointerType: 'mouse', isPrimary: true,
    }));
  };
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const results = [];
  for (const { from, to } of moves) {
    const source = draggableIn(laneEl(from));
    const targetLane = laneEl(to);
    const target = draggableIn(targetLane) || targetLane;
    if (!source || !target) {
      results.push({ from, to, ok: false });
      continue;
    }

    const r1 = source.getBoundingClientRect();
    const r2 = target.getBoundingClientRect();
    const sx = r1.x + r1.width / 2, sy = r1.y + r1.height / 2;
    const tx = r2.x + r2.width / 2, ty = r2.y + r2.height / 2;

    fire(PointerEvent, 'pointerdown', sx, sy, source);
    fire(MouseEvent, 'mousedown', sx, sy, source);
    const steps = 10;
    for (let i = 1; i <= steps; i++) {
      const x = sx + (tx - sx) * i / steps;
      const y = sy + (ty - sy) * i / steps;
      fire(PointerEvent, 'pointermove', x, y);
      fire(MouseEvent, 'mousemove', x, y);
      await sleep(30);
    }
    fire(PointerEvent, 'pointerup', tx, ty);
    fire(MouseEvent, 'mouseup', tx, ty);
    await sleep(300); // la lista si re-renderizza (arrayMove) - respiro prima della mossa successiva
    results.push({ from, to, ok: true });
  }
  return results;
}
"""

# Legge cosa c'e' DAVVERO in ogni corsia (prima E dopo il drag - vedi
# confirm_role_order, usata in entrambi i momenti) - mai il testo/alt, per lo
# stesso motivo di sempre: piu' stabile. Serve a VERIFICARE che il drag
# abbia funzionato PRIMA di bloccare la selezione, non solo a dedurlo dal
# fatto che page.evaluate non ha sollevato eccezioni - lezione dello stesso
# bug gia' preso una volta con confirm_selection (un'azione puo' "riuscire"
# secondo Playwright senza aver fatto quello che doveva davvero).
#
# IDENTITA' PER SLUG, non per ID numerico (a differenza di ban/pick altrove
# in questo file) - BUG REALE TROVATO da un test dell'utente (2026-08-20,
# "'Yasuo' is not in list"): l'immagine del campione qui dentro NON e'
# un'icona champion-icons/<id>.png ma uno SPLASH ART
# characters/<slug>/skins/base/images/<slug>_splash_*.jpg - percorso
# completamente diverso, il regex per ID non ha mai potuto combaciare.
# _resolve_role_confirm_slug() (sopra) risolve lo slug a nome campione.
_ROLE_CONFIRM_STATE_JS = r"""
(side) => {
  const slugFor = (lane) => {
    // NON scoped su #{side}-picks-row - stesso bug/fix di _ROLE_DRAG_JS,
    // vedi li' per il dettaglio.
    const el = document.querySelector(`[data-role-confirm-lane="${lane}"]`);
    // Ogni corsia contiene DUE img - la prima e' l'iconcina SVG del ruolo
    // stesso (alt="Top"/"Jungle"/ecc, src /roleicons/*.svg, sempre presente
    // a prescindere dal campione), la SECONDA e' il vero ritratto/splash
    // art del campione (alt="pick" - quella che ci serve). BUG REALE
    // TROVATO da un test dell'utente (2026-08-20): il primo
    // el.querySelector('img') (senza filtro) prendeva sempre la prima,
    // un'icona SVG che non ha nulla a che vedere col campione - da qui
    // "sempre null", non un caso limite. Selettore esplicito invece di
    // "la seconda trovata", piu' resistente a un eventuale ordine diverso.
    const img = el ? el.querySelector('img[alt="pick"]') : null;
    if (!img) return null;
    const src = img.currentSrc || img.src || '';
    const m = src.match(/characters(?:%2F|\/)([a-z0-9]+)(?:%2F|\/)skins/);
    return m ? m[1] : null;
  };
  return ['top', 'jungle', 'mid', 'adc', 'support'].map(slugFor);
}
"""


class LiveDraftSession:
    """Una sessione connessa a UNA draft room. Tutto Playwright vive ed
    esclusivamente opera dentro `_worker_thread` - le altre chiamate
    (connect/read_state/disconnect, tipicamente da thread di richiesta HTTP
    diversi) parlano con quel thread solo tramite `_cmd_queue`."""

    def __init__(self):
        self._cmd_queue: "queue.Queue | None" = None
        self._worker_thread: threading.Thread | None = None
        self.url: str | None = None
        self.side: str | None = None

    def is_connected(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.is_alive()

    def connect(self, url: str) -> dict:
        """Fase 1 di 2: apre la draft room e si FERMA sul dialogo "Join the
        Draft", restituendo i team della room e i lati ancora liberi.

        Fino al 2026-09-05 questo metodo faceva tutto in un colpo solo e
        pretendeva `side` e `team_name` gia' noti - il nome andava quindi
        digitato a mano, esatto, ad ogni connessione. Richiesta esplicita
        dell'utente: "vorrei evitare di scrivere il nome completo ogni
        volta... una volta caricato il link, dato che si riesce a leggere
        effettivamente il nome del team, potrò selezionare il team/side".
        La scelta vera avviene ora in `join()`, sulle opzioni LETTE dalla
        pagina: niente piu' nomi digitati e nessun lato gia' occupato
        proposto per errore."""
        if self.is_connected():
            self.disconnect()

        self._cmd_queue = queue.Queue()
        ready_queue: "queue.Queue" = queue.Queue()
        self._worker_thread = threading.Thread(
            target=self._run_worker,
            args=(url, self._cmd_queue, ready_queue),
            daemon=True,
        )
        self._worker_thread.start()

        try:
            status, payload = ready_queue.get(timeout=40)
        except queue.Empty:
            raise RuntimeError("Timeout durante la connessione alla draft room.")

        if status == "error":
            self._worker_thread = None
            self._cmd_queue = None
            raise RuntimeError(payload)

        self.url = url
        self.side = None
        return payload or {}

    def join_options(self, team_name: str | None = None) -> dict:
        """Rilegge il dialogo di join. Con `team_name` seleziona prima quel
        team (i lati disponibili dipendono dal team scelto: e' il sito a
        legarli, vedi _JOIN_OPTIONS_JS) e restituisce le opzioni aggiornate."""
        if not self.is_connected():
            return {"error": "Nessuna sessione aperta."}

        result_queue: "queue.Queue" = queue.Queue()
        self._cmd_queue.put(("join_options", team_name, result_queue))
        try:
            status, payload = result_queue.get(timeout=20)
        except queue.Empty:
            return {"error": "Timeout durante la lettura delle opzioni di join."}
        if status == "error":
            return {"error": payload}
        return payload

    def join(self, team_name: str, side: str) -> dict:
        """Fase 2 di 2: entra davvero nella draft con il team e il lato
        scelti fra quelli letti dalla pagina."""
        if side not in ("blue", "red"):
            return {"error": "Scegli un lato (Blue o Red)."}
        if not self.is_connected():
            return {"error": "Nessuna sessione aperta: riconnettiti al link."}

        result_queue: "queue.Queue" = queue.Queue()
        self._cmd_queue.put(("join", {"team": team_name, "side": side}, result_queue))
        try:
            status, payload = result_queue.get(timeout=30)
        except queue.Empty:
            return {"error": "Timeout durante l'ingresso nella draft."}
        if status == "error":
            return {"error": payload}

        # Solo ORA la sessione ha un lato: read_state lo usa per dire "chi
        # siamo" nello stato restituito alla UI.
        self.side = side
        return {"joined": True, "side": side, "team": team_name}

    def disconnect(self) -> None:
        if self.is_connected():
            self._cmd_queue.put(("disconnect", None, None))
            self._worker_thread.join(timeout=10)
        self._worker_thread = None
        self._cmd_queue = None
        self.url = None
        self.side = None

    def read_state(self) -> dict:
        if not self.is_connected():
            return {"connected": False}

        result_queue: "queue.Queue" = queue.Queue()
        self._cmd_queue.put(("read_state", None, result_queue))
        try:
            status, payload = result_queue.get(timeout=10)
        except queue.Empty:
            return {"connected": False, "error": "Timeout durante la lettura dello stato."}

        if status == "error":
            return {"connected": False, "error": payload}

        payload["blueBans"] = [_resolve_ban_id(i) for i in payload.pop("blueBanIds")]
        payload["redBans"] = [_resolve_ban_id(i) for i in payload.pop("redBanIds")]
        # Il sito etichetta la 4a corsia "Bottom" nel badge di conferma ruolo
        # (diverso da "adc", l'etichetta usata invece durante il drag - vedi
        # _ROLE_CONFIRM_LANES) - normalizzato qui a "Bot" per combaciare con
        # ROLE_ORDER (training_bot.py), unica differenza fra le due etichette.
        payload["blueRoleTags"] = [_normalize_role_tag(r) for r in payload["blueRoleTags"]]
        payload["redRoleTags"] = [_normalize_role_tag(r) for r in payload["redRoleTags"]]
        payload["connected"] = True
        payload["side"] = self.side
        return payload

    def click_ready(self) -> dict:
        """Segnala "pronto" per iniziare la draft - a differenza di una
        scelta di campione, non e' un'azione a rischio (non sceglie/invia
        nulla), serve solo a far partire la sequenza ban/pick."""
        if not self.is_connected():
            return {"connected": False}

        result_queue: "queue.Queue" = queue.Queue()
        self._cmd_queue.put(("click_ready", None, result_queue))
        try:
            status, payload = result_queue.get(timeout=10)
        except queue.Empty:
            return {"connected": False, "error": "Timeout durante il click su Ready."}

        if status == "error":
            return {"connected": False, "error": payload}
        return {"connected": True}

    def select_champion(self, champion_name: str) -> dict:
        """FASE 2 - azione a rischio reale: seleziona (senza confermare) un
        campione nella griglia della draft vera, visibile all'avversario ma
        ancora modificabile. Il chiamante (server.py) deve gia' aver
        verificato che sia effettivamente il turno del nostro lato - qui non
        si ripete quel controllo, ci si affida al fatto che drafter.lol
        stesso rifiuta l'azione se la griglia non e' interattiva in questo
        momento (Playwright fallisce/timeouta senza effetti collaterali)."""
        if not self.is_connected():
            return {"connected": False}

        champion_id = _resolve_champion_id(champion_name)
        result_queue: "queue.Queue" = queue.Queue()
        self._cmd_queue.put(("select_champion", (champion_name, champion_id), result_queue))
        try:
            status, payload = result_queue.get(timeout=10)
        except queue.Empty:
            return {"connected": False, "error": "Timeout durante la selezione del campione."}

        if status == "error":
            return {"connected": False, "error": payload}
        return {"connected": True}

    def confirm_selection(self, side: str, kind: str, index: int) -> dict:
        """FASE 2 - blocca la selezione corrente (equivalente al click
        dell'utente su #draft-button), qualunque sia il testo attuale
        (Ban/Pick) - il sito stesso decide l'azione in base alla fase
        corrente, noi clicchiamo solo il bottone. Playwright non forza il
        click se il bottone e' disabled (nessuna selezione pending), quindi
        una chiamata "a vuoto" fallisce in modo innocuo invece di fare
        qualcosa di indesiderato.

        side/kind/index identificano lo slot che ci aspettiamo si sblocchi
        (es. "blue"/"ban"/0) - servono per VERIFICARE che il click abbia
        davvero funzionato, non solo che non abbia sollevato un'eccezione.
        Trovato necessario in un test reale (2026-08-17): un click puo'
        "riuscire" secondo Playwright (ha colpito qualcosa, es. un pannello
        Preferenze del sito comparso per un attimo al posto del bottone) pur
        non avendo affatto confermato la selezione - senza questa verifica
        il chiamante crederebbe erroneamente che sia andato tutto bene."""
        if not self.is_connected():
            return {"connected": False}

        result_queue: "queue.Queue" = queue.Queue()
        self._cmd_queue.put(("confirm_selection", (side, kind, index), result_queue))
        try:
            status, payload = result_queue.get(timeout=10)
        except queue.Empty:
            return {"connected": False, "error": "Timeout durante la conferma."}

        if status == "error":
            return {"connected": False, "error": payload}
        return {"connected": True}

    def confirm_role_order(self, desired_order: list[str]) -> dict:
        """Role confirmation - il coach ha riordinato i 5 pick del nostro
        lato DENTRO DriftDraft (nessuna fretta, quello e' locale); questo
        replica il risultato sul sito VERO: legge l'ordine pick attuale
        (invariato dal termine del draft), calcola la sequenza minima di
        drag (_compute_role_moves) e la esegue (_ROLE_DRAG_JS), poi blocca
        cliccando "Confirm roles". Il chiamante (server.py) dovrebbe gia'
        aver verificato state.roleConfirmActive prima di chiamare - qui non
        si ripete quel controllo: se la fase di drag non e' ancora live sul
        sito, gli elementi semplicemente non si trovano (ogni mossa torna
        ok:false) e il click finale su "Confirm roles" fallisce in modo
        innocuo (bottone non trovato/testo diverso), senza effetti
        collaterali - stessa filosofia "fallisce a vuoto invece di fare
        qualcosa di indesiderato" gia' usata in confirm_selection."""
        if not self.is_connected():
            return {"connected": False}

        result_queue: "queue.Queue" = queue.Queue()
        self._cmd_queue.put(("confirm_role_order", desired_order, result_queue))
        try:
            status, payload = result_queue.get(timeout=15)
        except queue.Empty:
            return {"connected": False, "error": "Timeout durante il riordino dei ruoli."}

        if status == "error":
            return {"connected": False, "error": payload}
        return {"connected": True, **payload}

    def _run_worker(
        self,
        url: str,
        cmd_queue: "queue.Queue",
        ready_queue: "queue.Queue",
    ) -> None:
        """Gira interamente dentro il thread dedicato: crea Playwright, apre
        la room e si ferma sul dialogo di join (restituendo i team e i lati
        liberi), poi resta in ascolto di comandi finche' non arriva
        "disconnect" (o la pagina smette di rispondere). L'ingresso vero
        avviene col comando "join", vedi il ciclo piu' sotto."""

        playwright = sync_playwright().start()

        # Cartella profilo dedicata a QUESTA sessione - Chromium richiede un
        # contesto "persistente" (launch_persistent_context, non piu' il
        # vecchio launch()+new_context()) per poter caricare un'estensione,
        # e un contesto persistente richiede sempre una cartella vera su
        # disco. Creata da zero ad ogni connessione, cancellata alla
        # disconnessione (vedi fondo funzione).
        #
        # EFFIMERA DI PROPOSITO (2026-09-04) - tornata indietro da un
        # tentativo con cartella PERSISTENTE (accanto all'eseguibile, come
        # data/roster.json) fatto lo stesso giorno su richiesta dell'utente,
        # poi scartato dopo un problema reale trovato testando: il muro
        # anti-adblock del sito (vedi _dismiss_known_popups sopra) offre il
        # bypass "Skip once" SOLO la prima volta in assoluto su un profilo
        # Chromium dato (tracking lato client, probabilmente localStorage) -
        # un profilo persistente lo esaurirebbe per sempre dopo la prima
        # draft, rompendo sistematicamente tutte le successive. L'utente ha
        # fatto notare che con un profilo EFFIMERO questo problema non
        # esiste affatto (ogni sessione e' "la prima volta" per il sito) -
        # il prezzo e' che i filtri "My filters" dell'utente in uBlock
        # Origin Lite NON sopravvivono da una draft alla successiva, ma
        # l'utente ha valutato il compromesso e preferisce cosi': "Skip
        # once" automatizzato copre il muro anti-adblock,
        # _dismiss_known_popups copre gli altri 2 popup noti del sito, resta
        # solo l'ad-blocker stesso (le sue regole di blocco, non i filtri
        # personalizzati salvati a mano) per le pubblicita' imprevedibili.
        user_data_dir = tempfile.mkdtemp(prefix="driftdraft-drafter-")

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--window-size=1280,900",
            "--window-position=80,60",
            # L'utente lavora sempre dentro DriftDraft, non in questa
            # finestra - che quindi resta "in secondo piano", spesso
            # coperta/sovrapposta da quella di DriftDraft per l'intera
            # draft. Chrome (specialmente su Windows, che rileva
            # attivamente quando una finestra e' "occlusa" da altre)
            # mette in pausa il rendering di una finestra coperta per
            # risparmiare risorse - e con lui si ferma DEL TUTTO
            # requestAnimationFrame, da cui dipende sia React sia la
            # libreria di drag&drop del sito (dnd-kit) per registrare
            # un trascinamento. BUG REALE TROVATO da un test
            # dell'utente (2026-08-20): "role confirmation" sembrava
            # fallire sempre (l'ordine tornava sempre quello di
            # default) - causa, il drag sintetico non veniva mai
            # registrato mentre la finestra restava coperta, e il
            # codice cliccava comunque "Confirm roles" alla cieca
            # subito dopo (bug gemello corretto qui sotto, vedi
            # verifica in confirm_role_order). Questi 4 flag
            # disattivano quel risparmio-risorse - stesso trio che usa
            # Puppeteer di default per lo stesso identico motivo, piu'
            # uno specifico per il rilevamento "occlusione" di
            # Windows - cosi' la finestra renderizza sempre a piena
            # velocita' anche se resta coperta per tutta la draft,
            # senza dover cambiare le abitudini dell'utente.
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
            "--disable-features=CalculateNativeWinOcclusion",
        ]
        if _EXTENSION_PATH.exists():
            launch_args += [
                f"--disable-extensions-except={_EXTENSION_PATH}",
                f"--load-extension={_EXTENSION_PATH}",
            ]

        try:
            # headless=False DELIBERATO, non un dimenticato debug flag:
            # questa finestra deve restare SEMPRE visibile e utilizzabile
            # dall'utente come "paracadute umano" - se l'automazione si
            # blocca su qualcosa di imprevisto (un popup mai visto, un bug
            # nostro), puo' agire direttamente li' con mouse/tastiera invece
            # di perdere la draft. Richiesta esplicita dell'utente, non un
            # fallback nascosto: la finestra va sempre aperta, non solo
            # quando rileviamo un problema (la nostra capacita' di
            # accorgerci di un problema non e' perfetta).
            context = playwright.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=False,
                viewport=None,
                user_agent=_USER_AGENT,
                args=launch_args,
            )
        except Exception as e:
            # es. binari di Chromium mancanti ("playwright install" mai
            # eseguito per questo utente/versione) - senza questo try, il
            # thread crashava senza avvisare mai chi aspetta su ready_queue,
            # lasciando la UI bloccata su "Connessione in corso..." per 40s
            # prima di un timeout generico invece dell'errore vero e proprio.
            ready_queue.put(("error", f"{e}"))
            playwright.stop()
            shutil.rmtree(user_data_dir, ignore_errors=True)
            return

        try:
            # launch_persistent_context ne apre gia' una in automatico
            # (verificato: mai zero) - a differenza del vecchio
            # browser.new_context(), qui new_page() andrebbe ad aprirne una
            # SECONDA inutile.
            page = context.pages[0] if context.pages else context.new_page()

            # Il sito ha pubblicita' dinamica in sottofondo (prebid/GPT/
            # btloader, gia' visti nei log errori) che puo' aprire una
            # scheda nuova - sia per un nostro click finito su un annuncio,
            # sia (sospetto, non confermato) per motivi propri degli script
            # pubblicitari stessi, senza bisogno di alcun nostro click.
            # Vogliamo chiuderla in automatico, ma l'evento "page" di
            # Playwright scatta sul thread INTERNO di Playwright, non sul
            # nostro thread dedicato - chiamare li' `.close()`/
            # `.bring_to_front()` viola lo stesso vincolo "un solo thread
            # alla volta" che ci ha gia' dato un crash in Fase 1 (vedi nota
            # in cima al file). Bug trovato in un test reale (2026-08-17):
            # dopo aver aggiunto la prima versione di questa protezione
            # (che chiamava .close() direttamente nel callback), le
            # selezioni campione hanno iniziato a fallire in timeout circa
            # 1 volta su 2, sospetto proprio per questa interferenza fra
            # thread. Fix: il callback si limita a mettere la pagina in
            # coda (thread-safe), la CHIUDE solo il nostro worker thread,
            # fra un comando e l'altro.
            stray_pages: "queue.Queue" = queue.Queue()
            context.on("page", stray_pages.put)

            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)  # tempo per l'idratazione JS (Next.js)

            try:
                page.click('button:has-text("Do not consent")', timeout=4000)
            except Exception:
                pass

            # Muro anti-adblock del sito ("Skip once") + promo "Draft Prep
            # Tool" ("Maybe later") - entrambi compaiono qui, prima ancora
            # di scegliere nome team/lato. Il tooltip "switch selected role"
            # ("Got it") invece no - compare DOPO la scelta del lato, vedi
            # la seconda chiamata piu' sotto - _dismiss_known_popups prova
            # comunque tutti e 3 i testi ad ogni chiamata (tollerante,
            # nessun danno se un testo non e' ancora/piu' presente).
            _dismiss_known_popups(page)

            # NIENTE click su team/lato qui: dal 2026-09-05 la connessione e'
            # in due tempi (vedi connect()/join()). Qui ci si limita a LEGGERE
            # cosa offre il dialogo, cosi' la UI puo' proporre i team veri
            # della room invece di farne digitare il nome a memoria.
            options = page.evaluate(_JOIN_OPTIONS_JS)
            if not options.get("present"):
                raise RuntimeError(
                    "Dialogo di ingresso non trovato: il link porta a una draft "
                    "gia' iniziata o non e' una draft room valida."
                )

            # ADDORMENTATO, non cancellato (2026-09-04, decisione esplicita
            # dell'utente) - stesso trattamento gia' riservato a
            # _HIDE_SITE_NAV_JS sotto. Un test end-to-end completo (vedi
            # commento su _POPUP_WATCHDOG_JS piu' sotto per i dettagli) ha
            # mostrato che questo watchdog nascondeva alla cieca anche
            # funzioni legittime del sito, non solo pubblicita'. Sostituito
            # da DUE meccanismi mirati invece di un'euristica generica: (1)
            # _dismiss_known_popups sopra, per i pochi dialoghi CONOSCIUTI
            # del sito stesso (bersaglio preciso, per nome); (2) l'ad-blocker
            # (uBlock Origin Lite, vedi _EXTENSION_PATH sopra) per le vere
            # pubblicita' imprevedibili, tramite le sue regole di blocco
            # incorporate - NON tramite filtri personalizzati salvati a mano
            # dall'utente ("My filters"), che richiederebbero un profilo
            # Chromium PERSISTENTE: scartato lo stesso giorno (vedi
            # user_data_dir sopra per il perche') proprio perche' un profilo
            # persistente esaurisce per sempre il bypass "Skip once" del
            # muro anti-adblock del sito dopo la primissima draft. Se un
            # popup non coperto blocca di nuovo il bottone, riattivare la
            # riga sotto (togliere il commento) e' immediato, il codice
            # resta intatto.
            # page.evaluate(_POPUP_WATCHDOG_JS)
            # _HIDE_SITE_NAV_JS NON richiamata - vedi commento sopra sulla
            # sua definizione, ha peggiorato la situazione in un test reale.
        except Exception as e:
            ready_queue.put(("error", f"{e}"))
            context.close()
            playwright.stop()
            shutil.rmtree(user_data_dir, ignore_errors=True)
            return

        ready_queue.put(("ok", options))

        # Popup "DRAFT COMPLETE - Save this draft for later" (Continue with
        # Discord/Google, o "Not now") - il sito lo mostra SOLO dopo
        # l'ultimo pick della draft (10/10), richiesto esplicitamente
        # dall'utente 2026-09-04 ("dato che e' programmata sulla prima
        # draft effettuata" - un popup di ONBOARDING lato sito, slegato
        # dall'ad-blocker/dal muro anti-adblock visti sopra). Un flag invece
        # di riprovare ad ogni read_state (ogni ~0.1s): il PRIMO tentativo
        # fallito NON viene ripetuto all'infinito (settato comunque a True),
        # cosi' un timeout non riprova mai piu' di una volta - vedi il
        # controllo dentro "read_state" sotto per il perche' economico anche
        # nei tick in cui non serve (un controllo booleano su dati gia'
        # letti, non un nuovo giro di rete).
        _dismissed_draft_complete_popup = False

        while True:
            # Chiude eventuali schede impreviste (vedi commento sopra su
            # stray_pages) - fatto qui, dentro l'unico thread che possiede
            # Playwright, MAI dal callback dell'evento "page" stesso.
            # bring_to_front() SOLO se ne abbiamo chiusa almeno una - farlo
            # ad ogni giro (quindi ogni ~0.1s durante il polling) ruberebbe
            # continuamente il focus della finestra automatizzata, fastidio
            # inutile quando non c'e' nulla da recuperare.
            closed_any = False
            while not stray_pages.empty():
                try:
                    stray_pages.get_nowait().close()
                    closed_any = True
                except Exception:
                    pass
            if closed_any:
                try:
                    page.bring_to_front()
                except Exception:
                    pass

            try:
                cmd, _payload, result_queue = cmd_queue.get(timeout=120)
            except queue.Empty:
                break  # nessun comando da 2 minuti - la connessione e' considerata abbandonata

            if cmd == "disconnect":
                break

            # --- Connessione in due tempi (2026-09-05) ---------------------
            # "join_options": rilegge il dialogo, opzionalmente dopo aver
            # selezionato un team (i lati liberi dipendono dal team scelto -
            # e' il sito a legarli, vedi _JOIN_OPTIONS_JS).
            if cmd == "join_options":
                try:
                    if _payload:
                        clicked = page.evaluate(
                            _JOIN_CLICK_JS,
                            {"section": "team selection", "text": _payload, "exact": True},
                        )
                        if not clicked.get("ok"):
                            result_queue.put((
                                "error",
                                f"Team '{_payload}' non selezionabile ({clicked.get('reason')}).",
                            ))
                            continue
                        # Il sito riabilita i lati in modo asincrono dopo la
                        # scelta del team: senza questa attesa si leggerebbe
                        # lo stato PRECEDENTE (tutti i lati ancora occupati).
                        page.wait_for_timeout(800)
                    result_queue.put(("ok", page.evaluate(_JOIN_OPTIONS_JS)))
                except Exception as e:
                    result_queue.put(("error", f"{e}"))
                continue

            # "join": entra davvero. Team e lato arrivano gia' validati dalla
            # UI fra quelli LETTI dalla pagina, quindi qui non si indovina
            # nulla - ma i click restano protetti perche' fra la lettura e la
            # scelta dell'utente l'altro team puo' aver preso lo stesso lato.
            if cmd == "join":
                try:
                    team = _payload["team"]
                    # Stringa passata a `new RegExp` lato JS, non a Python:
                    # raw string per non far interpretare \s a Python stesso.
                    side_label = r"Blue\s*Side" if _payload["side"] == "blue" else r"Red\s*Side"
                    t = page.evaluate(
                        _JOIN_CLICK_JS,
                        {"section": "team selection", "text": team, "exact": True},
                    )
                    if not t.get("ok"):
                        result_queue.put(("error", f"Team '{team}' non selezionabile."))
                        continue
                    page.wait_for_timeout(800)
                    r = page.evaluate(
                        _JOIN_CLICK_JS,
                        {"section": "role selection", "text": side_label, "exact": False},
                    )
                    if not r.get("ok"):
                        result_queue.put(("error", "Lato non selezionabile."))
                        continue
                    if r.get("alreadyDisabled"):
                        # Su un LATO disabled vuol dire occupato: fra la
                        # lettura e il click puo' averlo preso l'altro team.
                        result_queue.put((
                            "error",
                            "Quel lato e' appena stato occupato: riapri le opzioni e riprova.",
                        ))
                        continue
                    page.wait_for_timeout(1000)
                    # "Got it" (tooltip "switch selected role") compare solo
                    # ORA, dopo la scelta del lato - stessa ragione per cui
                    # la seconda chiamata stava qui anche nel flusso vecchio.
                    _dismiss_known_popups(page)
                    result_queue.put(("ok", {"joined": True}))
                except Exception as e:
                    result_queue.put(("error", f"{e}"))
                continue

            if cmd == "read_state":
                try:
                    state = page.evaluate(_STATE_JS)
                    result_queue.put(("ok", state))
                except Exception as e:
                    result_queue.put(("error", f"{e}"))
                    break  # la pagina non risponde piu' - chiudi la sessione

                # Vedi il commento esteso su _dismissed_draft_complete_popup
                # sopra. Controllo economico: un confronto su una stringa
                # gia' in memoria (nessuna nuova richiesta), quasi sempre
                # False finche' la draft non e' davvero completa - il click
                # vero (l'unica parte che potrebbe "costare" fino a 800ms)
                # scatta al massimo UNA volta per l'intera sessione, non ad
                # ogni tick da 0.1s.
                #
                # Sulla FASE (state.step), non sul conteggio dei pick - BUG
                # REALE trovato in un test (2026-09-04): un pick scaduto per
                # timeout (nessuna scelta fatta) risulta "None" (stringa
                # letterale, non un valore mancante) invece di un vero nome
                # campione, ma la draft passa comunque a "Role confirmation"
                # - un controllo "tutti e 10 i pick hanno un nome vero" non
                # avrebbe MAI scattato in quel caso, pur essendo la draft
                # gia' finita per il sito (e gia' mostrando il popup).
                if not _dismissed_draft_complete_popup:
                    if "role confirmation" in (state.get("step") or "").lower():
                        _dismissed_draft_complete_popup = True
                        try:
                            page.click('button:has-text("Not now")', timeout=800)
                        except Exception:
                            pass

            if cmd == "click_ready":
                try:
                    # NIENTE PIU' Escape qui (rimosso 2026-08-17): sul sito
                    # vero e' legato alla scorciatoia che apre il pannello
                    # Preferences (confermato dall'utente premendolo a mano,
                    # nessun'altra azione necessaria - causa vera di un
                    # flickering visto in ogni test recente, 20 volte a
                    # draft). I popup che doveva chiudere sono gia' gestiti
                    # dal watchdog di sottofondo e dal controllo "sul
                    # momento" prima di ogni click, senza bisogno di Escape.
                    page.click('#draft-button:has-text("Ready")', timeout=5000)
                    result_queue.put(("ok", None))
                except Exception as e:
                    result_queue.put(("error", f"{e}"))

            if cmd == "select_champion":
                # Selettore corretto dopo un test reale (2026-08-16): l'img
                # ha pointer-events:none, e un click REALE del mouse "passa
                # attraverso" verso il div-contenitore sottostante - ma
                # Playwright fa un proprio controllo di "actionability" PRIMA
                # di cliccare (l'elemento target riceve davvero l'evento in
                # quel punto?), e per un'img pointer-events:none quel
                # controllo fallisce sempre (l'evento risulterebbe ricevuto
                # dal div genitore, non dall'img) - quindi Playwright ritenta
                # all'infinito e va in timeout, anche se un utente umano li'
                # cliccherebbe senza problemi. Fix: risali via XPath al primo
                # antenato con classe "cursor-pointer" (il tile vero e
                # proprio, verificato nel DOM reale) e clicca quello -
                # niente force=True: se un popup reale coprisse il tile,
                # vogliamo che Playwright continui a segnalarlo con un
                # timeout invece di cliccare "alla cieca" attraverso di esso.
                champion_name, champion_id = _payload
                try:
                    # NIENTE PIU' Escape qui (rimosso 2026-08-17 - vedi nota
                    # su click_ready piu' sopra, causa vera del flickering
                    # di Preferences visto in ogni test, confermato
                    # dall'utente premendolo a mano sul sito senza nessun'altra
                    # azione). Piccola pausa prima del click: il sito ha
                    # pubblicita' dinamica che sposta il layout senza
                    # preavviso (gia' vista causare un click finito su un
                    # annuncio) - non elimina il rischio, ma da' un attimo
                    # in piu' perche' un caricamento in corso si assesti
                    # prima di calcolare dove cliccare.
                    page.wait_for_timeout(200)
                    try:
                        page.evaluate(_CLEAR_BLOCKING_OVERLAY_JS)
                    except Exception:
                        pass
                    # BUG segnalato dall'utente (2026-08-17): i pick con
                    # spazio (Aurelion Sol, Master Yi) o apostrofo (Bel'Veth,
                    # Kai'Sa) non venivano mai inviati. Causa verificata nel
                    # DOM reale di drafter.lol (aperto apposta per controllo,
                    # draft di prova): l'attributo alt di queste immagini
                    # NON e' il nome campione ma un alias interno stile Data
                    # Dragon senza spazi/apostrofi (es. Kai'Sa -> "Kaisa") -
                    # img[@alt="Kai'Sa"] non trovava mai nulla. Fix: cerca
                    # invece per ID Riot numerico nell'URL immagine
                    # (.../champion-icons/<id>.png), la stessa identita'
                    # stabile gia' usata per leggere i ban - richiede sia
                    # %2F (slash con URL-encoding, confermato nel DOM reale:
                    # il sito passa l'URL CommunityDragon come query string
                    # del proxy immagini di Next.js) sia / semplice.
                    if champion_id is not None:
                        tile_xpath = (
                            f'xpath=//img[contains(@src, "champion-icons/{champion_id}.png") '
                            f'or contains(@src, "champion-icons%2F{champion_id}.png")]'
                            '/ancestor::div[contains(@class, "cursor-pointer")][1]'
                        )
                    else:
                        # Fallback SOLO per un campione non ancora presente
                        # nella colonna "ID" dell'xlsx (es. appena aggiunto,
                        # sync_champion_ids.py non ancora rilanciato) -
                        # stesso limite di sempre: fallisce per nomi con
                        # spazio/apostrofo, ma e' meglio di un errore secco.
                        tile_xpath = (
                            f'xpath=//img[@alt="{champion_name}"]'
                            '/ancestor::div[contains(@class, "cursor-pointer")][1]'
                        )
                    page.click(tile_xpath, timeout=5000)
                    result_queue.put(("ok", None))
                except Exception as e:
                    result_queue.put(("error", f"{e}"))

            if cmd == "confirm_selection":
                # Nessun filtro sul testo (a differenza di click_ready): qui
                # va bene sia "Ban" che "Pick", decide il sito in base alla
                # fase corrente. Playwright non clicca se il bottone e'
                # disabled (nessuna selezione pending) - fallisce con
                # timeout invece di fare un click a vuoto.
                side, kind, index = _payload
                try:
                    # NIENTE PIU' Escape qui - vedi nota su click_ready.
                    page.wait_for_timeout(200)  # stesso motivo di select_champion sopra
                    try:
                        page.evaluate(_CLEAR_BLOCKING_OVERLAY_JS)
                    except Exception:
                        pass
                    page.click("#draft-button", timeout=5000)

                    # VERIFICA che il click abbia davvero funzionato, non solo
                    # che non abbia sollevato un'eccezione - trovato
                    # necessario in un test reale (2026-08-17): un click puo'
                    # "riuscire" secondo Playwright pur avendo colpito il
                    # bersaglio sbagliato (es. un pannello Preferenze del
                    # sito comparso per un attimo al posto del bottone),
                    # senza aver confermato nulla per davvero. Stesso segnale
                    # pulse-animation-* gia' usato per il lampeggio - se lo
                    # slot che ci aspettavamo si sbloccasse ce l'ha ancora,
                    # il click non e' andato a segno.
                    page.wait_for_timeout(400)
                    slot_id = f"{side}-{kind}-{index + 1}"
                    still_pending = page.evaluate(
                        """(id) => {
                            const el = document.getElementById(id);
                            return !!(el && el.querySelector('[class*="pulse-animation"]'));
                        }""",
                        slot_id,
                    )
                    if still_pending:
                        result_queue.put((
                            "error",
                            "il click non sembra aver bloccato la selezione (il sito la mostra ancora "
                            "in sospeso) - riprova, o conferma manualmente dalla finestra.",
                        ))
                    else:
                        result_queue.put(("ok", None))
                except Exception as e:
                    result_queue.put(("error", f"{e}"))

            if cmd == "confirm_role_order":
                desired_order = _payload
                try:
                    # L'ordine ATTUALE non si legge piu' da _STATE_JS
                    # (bluePicks/redPicks, via #{side}-pick-{n}) - BUG REALE
                    # TROVATO da un test dell'utente (2026-08-20): per come e'
                    # disegnato questo comando, arriva qui SOLO dopo che il
                    # chiamante ha gia' verificato state.roleConfirmActive
                    # (la fase di drag e' davvero live) - ma a quel punto il
                    # sito ha GIA' sostituito la vecchia struttura
                    # #{side}-pick-{n} con quella nuova a corsie
                    # (#{side}-pick-role-{lane}), quindi i vecchi selettori
                    # non trovano piu' nulla: bluePicks/redPicks tornano
                    # [null]*5, e _compute_role_moves falliva SEMPRE al primo
                    # nome cercato ("'Yasuo' is not in list", ValueError di
                    # list.index() su una lista di soli None - errore Python
                    # grezzo, non un caso limite). Fix: legge l'ordine
                    # attuale DIRETTAMENTE dalle corsie (stessa funzione gia'
                    # usata per la verifica POST-drag qui sotto, riusata per
                    # leggere lo stato PRIMA del drag) - nessun trascinamento
                    # e' ancora avvenuto a questo punto, quindi riflette
                    # comunque l'ordine di partenza (il sito non fa che
                    # rietichettare l'ordine pick per corsia, mai un
                    # riordino proprio finche' non si trascina davvero).
                    current_slugs = page.evaluate(_ROLE_CONFIRM_STATE_JS, side)
                    current_order = [_resolve_role_confirm_slug(s) for s in current_slugs]
                    if None in current_order:
                        # Le corsie esistono ma non sono ancora popolate del
                        # tutto (visto raramente, un singolo retry dopo una
                        # breve pausa e' sufficiente nei test) - non un
                        # errore silenzioso: se persiste, il confronto sotto
                        # in _compute_role_moves fallisce comunque con un
                        # messaggio chiaro invece di uno grezzo di Python.
                        page.wait_for_timeout(400)
                        current_slugs = page.evaluate(_ROLE_CONFIRM_STATE_JS, side)
                        current_order = [_resolve_role_confirm_slug(s) for s in current_slugs]

                    if set(current_order) != set(desired_order) or None in current_order:
                        result_queue.put((
                            "error",
                            f"non riesco a leggere correttamente l'ordine attuale sul sito "
                            f"(letto {current_order}, atteso una permutazione di {desired_order}) - "
                            "non ho toccato nulla, riprova o sistema manualmente dalla finestra.",
                        ))
                        continue

                    moves = _compute_role_moves(current_order, desired_order)

                    results = page.evaluate(_ROLE_DRAG_JS, {"side": side, "moves": moves})

                    page.wait_for_timeout(300)

                    # VERIFICA che il drag abbia davvero prodotto l'ordine
                    # voluto PRIMA di bloccare - trovato necessario in un
                    # test reale dell'utente (2026-08-20): il drag sintetico
                    # non si registrava mai se la finestra automatica restava
                    # coperta da quella di DriftDraft (RAF in pausa, vedi
                    # commento sui flag di lancio piu' sopra), e il codice
                    # confermava comunque alla cieca l'ordine di default
                    # invariato.
                    actual_slugs = page.evaluate(_ROLE_CONFIRM_STATE_JS, side)
                    actual_order = [_resolve_role_confirm_slug(s) for s in actual_slugs]
                    if actual_order != desired_order:
                        result_queue.put((
                            "error",
                            "il trascinamento non sembra aver funzionato (il sito mostra ancora "
                            f"{actual_order} invece di {desired_order}) - non ho confermato nulla, "
                            "riprova o sistema manualmente dalla finestra prima che scada il timer.",
                        ))
                        continue

                    try:
                        page.evaluate(_CLEAR_BLOCKING_OVERLAY_JS)
                    except Exception:
                        pass
                    page.click('#draft-button:has-text("Confirm")', timeout=5000)

                    result_queue.put(("ok", {"moves": moves, "dragResults": results}))
                except Exception as e:
                    result_queue.put(("error", f"{e}"))

        try:
            context.close()
        except Exception:
            pass
        try:
            playwright.stop()
        except Exception:
            pass
        shutil.rmtree(user_data_dir, ignore_errors=True)


_session = LiveDraftSession()


def get_session() -> LiveDraftSession:
    return _session
