"""Ricerca counter-matchup per un campione da lolalytics.com.

Serve un browser vero (Playwright): i dati della tabella matchup sono
codificati in un formato compatto specifico di Qwik (il framework del sito)
e decodificati lato client - un fetch() HTTP semplice non porta a nulla di
leggibile per QUESTA pagina specifica (diverso dal singolo "winrate medio"
mostrato in cima alla pagina overview di un campione, quello si' e' gia'
testo semplice nell'HTML grezzo, verificato in una sessione precedente).
"""

from dataclasses import dataclass

from playwright.sync_api import sync_playwright

from driftdraft.data import load_champions, slugify_champion_name

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Vocabolario ruoli di questo progetto -> valore del parametro "lane" atteso
# da lolalytics (verificato navigando il sito, es. "?lane=middle" per Mid).
ROLE_TO_LANE = {
    "Top": "top",
    "Jungle": "jungle",
    "Mid": "middle",
    "Bot": "bottom",
    "Support": "support",
}

# Valori del parametro "tier" di lolalytics (verificato navigando il sito,
# menu' impostazioni sulla pagina counters - es. "?tier=diamond_plus").
# Sottoinsieme di quelli offerti dal sito: qui servono solo le 3 fasce che
# l'utente controlla davvero (richiesta esplicita 2026-08-24), non l'intero
# menu' (che arriva fino a IRON/UNRANKED, irrilevante per un coach).
DEFAULT_TIER = "emerald_plus"
VALID_TIERS = {"emerald_plus", "diamond_plus", "master_plus"}

# Ogni card matchup e' un <a href=".../vs/<slug>/build/..."> il cui
# textContent e' tipo "Teemo44.74%VS...599 Games" - split su "VS" (label
# testuale ripetuta due volte nella card) per isolare in modo affidabile la
# PRIMA percentuale (winrate del campione di riferimento contro l'avversario)
# dalla seconda (winrate medio) e dal conteggio partite, invece di cercare
# alla cieca il primo numero decimale nel testo intero: quando la percentuale
# e' un intero esatto (es. "49%", senza decimali) un regex generico salta
# quel numero e finisce per concatenare per errore due valori adiacenti
# senza spazio fra loro (bug reale trovato testando su Aatrox: "49%...-3.82"
# + "48.47%" letti insieme come "8248.47%").
_EXTRACT_JS = """
() => {
  const cards = [...document.querySelectorAll('a[href*="/vs/"]')].filter(a => a.textContent.includes('Games'));
  return cards.map(a => {
    const slugMatch = a.getAttribute('href').match(/\\/vs\\/([a-z0-9]+)\\/build/);
    const parts = a.textContent.split('VS');
    const pctMatch = parts[0] ? parts[0].match(/(\\d+(?:\\.\\d+)?)%/) : null;
    const gamesMatch = parts[2] ? parts[2].match(/([\\d,]+)\\s*Games/) : null;
    return {
      slug: slugMatch ? slugMatch[1] : null,
      refWinPct: pctMatch ? parseFloat(pctMatch[1]) : null,
      games: gamesMatch ? parseInt(gamesMatch[1].replace(/,/g, ''), 10) : null,
    };
  });
}
"""


@dataclass
class CounterEntry:
    champion: str
    winrate: float  # winrate DELL'AVVERSARIO (quello in griglia) contro il riferimento - gia' invertito
    games: int


class NoCounterDataError(Exception):
    """Lolalytics non ha abbastanza partite per questo campione/ruolo/tier
    per mostrare dei counter (soglia minima del sito: 100 partite su un
    matchup) - la pagina carica correttamente, non e' un errore di rete/
    scraping. Distinta da un'eccezione generica cosi' server.py puo' mostrare
    un messaggio chiaro ("dati insufficienti") invece del timeout tecnico
    grezzo di Playwright - caso reale segnalato dall'utente 2026-08-24
    (Brand Mid a Master+: pick raro in quella fascia, lolalytics stessa dice
    "insufficent games... minimum game requirement")."""


def fetch_counters(reference_champion: str, role: str, tier: str = DEFAULT_TIER) -> list[CounterEntry]:
    """reference_champion: nome del campione gia' piazzato in uno slot (es.
    "Camille"). role: uno tra Top/Jungle/Mid/Bot/Support (vocabolario di
    champion.roles) - stessa lane per il riferimento e per l'avversario
    (matchup di corsia diretta, il caso comune per una draft). tier: uno dei
    valori in VALID_TIERS - non validato qui (gia' fatto lato server, stesso
    pattern di role/ROLE_TO_LANE), un valore non riconosciuto da lolalytics
    farebbe semplicemente ignorare il filtro dal sito. Ritorna gli avversari
    ordinati per winrate CONTRO il riferimento, dal piu' forte."""
    slug = slugify_champion_name(reference_champion)
    lane = ROLE_TO_LANE[role]
    url = f"https://lolalytics.com/lol/{slug}/counters/?lane={lane}&vslane={lane}&tier={tier}"

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(viewport={"width": 1440, "height": 2200}, user_agent=_USER_AGENT)
        page = context.new_page()
        # "networkidle" va in timeout su questo sito (attivita' di rete di
        # sottofondo - analytics/ads - che non si azzera mai). Si aspetta
        # invece che compaia UNA DELLE DUE cose possibili: la prima card
        # matchup (caso normale) oppure il messaggio "insufficient games...
        # minimum game requirement" che lolalytics mostra quando sotto le
        # 100 partite per quel campione/ruolo/tier (verificato dal vivo:
        # in quel caso la pagina non ha NESSUN link "/vs/", 0 su 0 - nessun
        # rischio di falso positivo con altri link della pagina). Prima
        # della distinzione, questo caso restava appeso fino al timeout dei
        # 20s e usciva come errore tecnico grezzo di Playwright. wait_for_function
        # (non wait_for_selector) perche' Playwright non accetta un selettore
        # CSS e uno "text=" combinati con virgola nella stessa stringa
        # (provato, errore di parsing) - una funzione JS con querySelector +
        # innerText.includes evita del tutto il problema di sintassi.
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_function(
            """() => document.querySelector('a[href*="/vs/"]')
                || document.body.innerText.includes('minimum game requirement')""",
            timeout=20000,
        )

        if page.query_selector('a[href*="/vs/"]') is None:
            browser.close()
            raise NoCounterDataError(
                f"Dati insufficienti su lolalytics per {reference_champion} ({role}, fascia {tier})."
            )

        page.wait_for_timeout(800)
        raw = page.evaluate(_EXTRACT_JS)
        browser.close()

    slug_to_name = {slugify_champion_name(c.name): c.name for c in load_champions()}

    entries = []
    for item in raw:
        if item["slug"] is None or item["refWinPct"] is None or item["games"] is None:
            continue
        real_name = slug_to_name.get(item["slug"])
        if not real_name:
            continue
        # invertito: il sito mostra il winrate del RIFERIMENTO (es. Camille)
        # contro l'avversario, qui serve il winrate DELL'AVVERSARIO (quello
        # mostrato in griglia) contro il riferimento - richiesta esplicita.
        entries.append(
            CounterEntry(champion=real_name, winrate=round(100 - item["refWinPct"], 2), games=item["games"])
        )

    entries.sort(key=lambda e: e.winrate, reverse=True)
    return entries


# --- Curva "Win Rate vs Game Length" per un matchup specifico (feature 4,
# "valutazione della draft" - richiesto dall'utente 2026-08-26 dopo aver
# trovato lui stesso questo grafico su lolalytics). Vedi memoria progetto per
# il design completo. Verificato dal vivo: questo grafico esiste SOLO sulla
# pagina "vs" di un matchup specifico (.../vs/<avversario>/build/) - NON
# esiste una curva "solista" (un campione da solo, senza avversario
# specifico) su nessun'altra pagina del sito (controllate /build/,
# /counters/, /leaderboard/ - nessuna delle tre la mostra). Per questo la
# baseline "nostro team senza considerare il nemico" nel design finale non
# viene da un fetch separato, ma calcolata come media delle 5 curve di
# matchup stesse (vedi driftdraft/draft_evaluation.py). ---

GAME_LENGTH_BUCKETS = ["0-15", "15-20", "20-25", "25-30", "30-35", "35-40", "40+"]


@dataclass
class CurvePoint:
    bucket: str  # uno dei GAME_LENGTH_BUCKETS
    winrate: float  # winrate del campione DI RIFERIMENTO (non dell'avversario) a quella durata


class NoCurveDataError(Exception):
    """Il grafico "Win Rate vs Game Length" non e' presente per questo
    matchup/tier (stessa soglia minima partite del sito gia' vista per
    NoCounterDataError - un matchup troppo raro in quel tier semplicemente
    non mostra il grafico, la pagina carica correttamente comunque)."""


# Trova il grafico via il suo titolo testuale (SVG <text>, non canvas - il
# sito usa un chart library che renderizza tutto come SVG, verificato dal
# vivo) invece di un selettore CSS fragile legato a classi generate. Il
# grafico e' renderizzato PIGRO (solo quando scrollato in vista, verificato:
# assente subito dopo il caricamento, compare durante lo scroll) - lo scroll
# incrementale in fetch_winrate_curve() (lato Python) e' quello che lo fa
# comparire, questa funzione JS si limita a leggerlo una volta presente.
#
# Decodifica i valori NON da un attributo dati comodo (non esiste) ma dalla
# GEOMETRIA del grafico stesso: ogni punto e' un <circle cx cy>, e le
# etichette dell'asse Y (es. "25","30"..."85") sono posizionate via
# transform="translate(0,Y)" sullo stesso <g> - con almeno 2 etichette note
# si ricostruisce la scala lineare pixel->percentuale ed esattamente la
# stessa si applica alle coordinate cy dei punti dati. Stessa tecnica usata
# per verificare dal vivo questo grafico prima di scrivere questo codice.
_EXTRACT_CURVE_JS = """
() => {
  const titleEl = [...document.querySelectorAll('svg text')].find(
    t => t.textContent.trim() === 'Win Rate vs Game Length'
  );
  if (!titleEl) return null;
  const svg = titleEl.closest('svg');
  if (!svg) return null;

  const yTicks = [...svg.querySelectorAll('text')]
    .filter(t => /^\\d+$/.test(t.textContent.trim()))
    .map(t => {
      const transform = t.parentElement.getAttribute('transform') || '';
      const m = transform.match(/translate\\(([^,]+),([^)]+)\\)/);
      return m ? { value: parseFloat(t.textContent), y: parseFloat(m[2]) } : null;
    })
    .filter(Boolean);
  if (yTicks.length < 2) return null;

  const y1 = yTicks[0], y2 = yTicks[yTicks.length - 1];
  if (y1.y === y2.y) return null; // scala degenere, non dovrebbe succedere
  const slope = (y2.value - y1.value) / (y2.y - y1.y);
  const pctFromY = (y) => y1.value + (y - y1.y) * slope;

  // Posizione X di ogni etichetta bucket (stesso schema translate(X,0) degli
  // yTicks sopra, ma sul figlio del <g> orizzontale) - serve per ABBINARE
  // ogni cerchio al bucket piu' vicino per posizione, NON per indice/ordine.
  // BUG REALE TROVATO testando su un matchup raro (Aphelios vs Tahm Kench,
  // Bot): un bucket senza NESSUNA partita in quella fascia di durata non ha
  // proprio un <circle> disegnato (non uno a valore 0 - assente del tutto),
  // quindi contare "7 etichette ma solo 6 cerchi" e scartare l'intera curva
  // butterebbe via 6 punti buoni per colpa di 1 mancante. L'abbinamento per
  // posizione permette di sapere ESATTAMENTE quale dei 7 bucket manca,
  // invece di scartare tutto - vedi _fill_gaps in Python per come i bucket
  // mancanti vengono poi stimati dai vicini.
  const xLabels = [...svg.querySelectorAll('text')].filter(
    t => /^\\d+(-\\d+)?\\+?$/.test(t.textContent.trim()) && /-|\\+/.test(t.textContent.trim())
  );
  const slots = xLabels
    .map(t => {
      const transform = t.parentElement.getAttribute('transform') || '';
      const m = transform.match(/translate\\(([^,]+),/);
      return m ? { bucket: t.textContent.trim(), x: parseFloat(m[1]) } : null;
    })
    .filter(Boolean);
  if (slots.length === 0) return null;

  const circles = [...svg.querySelectorAll('circle')];
  const values = slots.map(() => null);
  for (const c of circles) {
    const cx = parseFloat(c.getAttribute('cx'));
    const cy = parseFloat(c.getAttribute('cy'));
    let bestIdx = -1, bestDist = Infinity;
    slots.forEach((s, i) => {
      const d = Math.abs(s.x - cx);
      if (d < bestDist) { bestDist = d; bestIdx = i; }
    });
    // tolleranza stretta (20px, molto meno della distanza tipica fra due
    // bucket adiacenti ~50px) per non abbinare per sbaglio un cerchio a uno
    // slot lontano se mai ce ne fossero di "extra" (es. punti di un altro
    // grafico letti per errore) - meglio lasciare lo slot vuoto che
    // inventare un valore sbagliato.
    if (bestIdx !== -1 && bestDist < 20 && values[bestIdx] === null) {
      values[bestIdx] = pctFromY(cy);
    }
  }

  if (values.every(v => v === null)) return null;
  return { buckets: slots.map(s => s.bucket), values };
}
"""

_CHART_PRESENT_JS = """
() => !![...document.querySelectorAll('svg text')].find(t => t.textContent.trim() === 'Win Rate vs Game Length')
"""


def _fill_gaps(values: list[float | None]) -> list[float] | None:
    """Un bucket senza dati (nessuna partita di quella durata in questo
    matchup specifico - visto dal vivo, non un caso ipotetico) viene stimato
    dai vicini invece di far fallire l'intera curva: interpolazione lineare
    fra i due vicini piu' vicini se il buco e' in mezzo, altrimenti si porta
    avanti/indietro l'unico vicino disponibile se il buco e' a un'estremita'
    (es. "40+" senza partite - capita spesso, e' l'ultimo bucket). None solo
    se TUTTI i bucket sono vuoti (nessun dato utilizzabile)."""
    if all(v is None for v in values):
        return None
    filled = list(values)
    n = len(filled)
    for i in range(n):
        if filled[i] is not None:
            continue
        left = next((j for j in range(i - 1, -1, -1) if filled[j] is not None), None)
        right = next((j for j in range(i + 1, n) if filled[j] is not None), None)
        if left is not None and right is not None:
            filled[i] = filled[left] + (filled[right] - filled[left]) * (i - left) / (right - left)
        elif left is not None:
            filled[i] = filled[left]
        else:
            filled[i] = filled[right]
    return filled


def fetch_winrate_curve(
    reference_champion: str, role: str, vs_champion: str | None = None, tier: str = DEFAULT_TIER
) -> list[CurvePoint]:
    """Curva winrate-per-durata-partita di `reference_champion` nel ruolo
    `role`. Se `vs_champion` e' dato, e' la curva SPECIFICA di quel matchup
    (pagina .../vs/<avversario>/build/); se None, e' la curva SOLISTA del
    campione da solo, senza un avversario specifico (pagina .../build/ -
    ATTENZIONE, trovata SOLO dopo un secondo giro di verifica: il primo
    controllo di questa sessione l'aveva mancata per un bug del tutto mio,
    non del sito - un tab del browser aperto a larghezza mobile di default
    senza ridimensionarlo esplicitamente, il grafico su schermi stretti
    semplicemente non compare mai. L'utente stesso ha notato dal vivo, con
    due screenshot alla mano, che la curva "solista" esiste davvero - non
    fidarsi di un solo giro di verifica quando il risultato e' "non c'e'",
    soprattutto se il layout del sito e' responsive).

    Solleva NoCurveDataError se il grafico non compare per questo campione/
    matchup/tier (campione raro in quel tier/ruolo, stessa soglia minima del
    sito gia' vista per i counter)."""
    ref_slug = slugify_champion_name(reference_champion)
    lane = ROLE_TO_LANE[role]
    if vs_champion is not None:
        vs_slug = slugify_champion_name(vs_champion)
        url = f"https://lolalytics.com/lol/{ref_slug}/vs/{vs_slug}/build/?lane={lane}&vslane={lane}&tier={tier}"
    else:
        url = f"https://lolalytics.com/lol/{ref_slug}/build/?lane={lane}&tier={tier}"

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(viewport={"width": 1440, "height": 1000}, user_agent=_USER_AGENT)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Descrive il campione/matchup nei messaggi d'errore sotto - "solo"
        # se non c'e' un avversario specifico, altrimenti "vs <avversario>".
        subject = reference_champion if vs_champion is None else f"{reference_champion} vs {vs_champion}"

        # Il grafico e' renderizzato pigro (solo quando entra in vista,
        # verificato dal vivo: assente a scroll 0, compare durante lo
        # scroll) - si scorre a incrementi finche' non compare o si esaurisce
        # la pagina, invece di un valore fisso di scroll (varia a seconda di
        # quanto contenuto (build, rune) precede il grafico per campioni
        # diversi).
        found = False
        for y in range(0, 6001, 800):
            page.evaluate(f"window.scrollTo(0, {y})")
            page.wait_for_timeout(350)
            if page.evaluate(_CHART_PRESENT_JS):
                found = True
                break

        if not found:
            browser.close()
            raise NoCurveDataError(f"Nessuna curva winrate/durata per {subject} ({role}, fascia {tier}).")

        page.wait_for_timeout(300)  # respiro extra per l'animazione di disegno del grafico
        raw = page.evaluate(_EXTRACT_CURVE_JS)
        browser.close()

    if not raw:
        raise NoCurveDataError(f"Curva winrate/durata trovata ma non decodificabile per {subject} ({role}).")

    filled = _fill_gaps(raw["values"])
    if filled is None:
        raise NoCurveDataError(f"Curva winrate/durata vuota per {subject} ({role}).")

    return [
        CurvePoint(bucket=bucket, winrate=round(value, 2))
        for bucket, value in zip(raw["buckets"], filled)
    ]
