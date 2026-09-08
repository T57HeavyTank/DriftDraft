"""Scraper per le pagine multisearch di op.gg.

I dati dei campioni giocati sono caricati lato client (non sono nell'HTML
grezzo, verificato) tramite un meccanismo interno di Next.js - serve un
browser vero (Playwright) che esegua il JS e aspetti il rendering, non basta
una richiesta HTTP semplice come per lolalytics.

Nota: op.gg ha protezione anti-bot a livello CDN (CloudFront) che blocca il
fingerprint di automazione di default di Playwright con un 403. Risolto
impostando uno user-agent/viewport realistici e disabilitando il flag
"navigator.webdriver" - nessun aggiramento di login o paywall, solo
presentarsi come un browser normale invece che come automazione headless di
default.
"""

import re
from dataclasses import dataclass, field
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from driftdraft.data import load_champions, slugify_champion_name

_slug_to_name_cache: dict[str, str] | None = None


def _get_slug_to_name() -> dict[str, str]:
    global _slug_to_name_cache
    if _slug_to_name_cache is None:
        _slug_to_name_cache = {slugify_champion_name(c.name): c.name for c in load_champions()}
    return _slug_to_name_cache


_CHAMP_ROW_MARKER = re.compile(r"\d+\.\d+:1")  # formato "3.22:1 KDA", usato per individuare le righe campione


def _normalize_summoner(name: str) -> str:
    """Un nome evocatore ridotto alla forma con cui si possono confrontare
    quello scritto nell'URL e quello mostrato da op.gg: minuscolo e senza
    spazi (vedi la nota in fetch_team_pool sul perche' gli spazi rompono
    tutto). Volutamente NON si toglie altro: accenti e caratteri non latini
    fanno parte del nome vero e togliendoli si rischierebbe di abbinare la
    colonna sbagliata."""
    return "".join(name.lower().split())

# Le icone di corsia su op.gg sono SVG inline, non immagini. Ogni icona
# contiene sempre gli stessi tre <path> e a cambiare e' solo QUALE non ha
# opacity="0.2": il path pieno disegna la corsia, gli altri due sono lo
# sfondo sbiadito. Concatenandoli TUTTI (primo tentativo, sbagliato) Top e
# Bot risultano identici - la firma sono i soli path pieni.
#
# Bastano i primi caratteri: il path vero arriva a ~570 caratteri (Jungle),
# ma i primi 20 separano gia' le cinque corsie - verificato su 3 squadre
# reali (15 giocatori). Un prefisso e' anche piu' tollerante di un confronto
# esatto se op.gg riesporta le icone con un'altra precisione decimale.
#
# ATTENZIONE: queste percentuali sono di SOLOQ, non di campionato. Su una
# squadra reale dell'utente due giocatori su cinque non mostravano nemmeno
# la loro corsia vera (il top compariva Mid 60%, il support Jungle 40%).
# Servono come SECONDO indizio accanto alla deduzione dai campioni, mai al
# suo posto: vedi assign_players_to_roles in training_bot.py.
_ROLE_SIG_LEN = 20
_ROLE_SIGNATURES = {
    "m19 3-4 4H7v8l-4 4V3": "Top",
    "M5.14 2c1.58 1.21 5.": "Jungle",
    "M18 3h3v3L6 21H3v-3z": "Mid",
    "m5 21 4-4h8V9l4-4v16": "Bot",
    "M12.833 10.833 14.5 ": "Support",
}

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class PlayerChampion:
    champion: str
    games: int
    winrate: int


@dataclass
class PlayerPool:
    summoner: str
    champions: list[PlayerChampion]
    # Corsia -> quota delle sue partite soloq (0..1), come la dichiara op.gg.
    # Vuoto se le icone non sono riconosciute: chi legge deve degradare alla
    # sola deduzione dai campioni, non fallire (vedi _ROLE_SIGNATURES).
    roles: dict[str, float] = field(default_factory=dict)


_EXTRACT_JS = """
() => {
  // Le colonne si trovano cosi', non partendo dalle righe campione: un
  // giocatore con pochissime partite giocate (anche solo 2-3 campioni in
  // tutta la stagione, o 0) avrebbe zero righe che combaciano col pattern
  // KDA, e la sua colonna andrebbe persa silenziosamente se la cercassimo
  // solo a partire dalle righe campione.
  //
  // Selettore NON piu' basato sulla larghezza (w-[20%]) - bug trovato in un
  // caso reale (2026-08-18, link con 7 giocatori): op.gg usa colonne al 20%
  // SOLO fino a 5 giocatori, oltre passa a larghezze fisse in pixel
  // (es. w-[150px]) per un layout scorrevole - "w-[20%]" smetteva quindi di
  // trovare qualunque colonna. Verificato nel DOM reale (sia su una pagina a
  // 5 che a 7 giocatori) che queste 3 classi restano IDENTICHE in entrambi i
  // casi, indipendenti dalla larghezza - marcatore stabile per "questo e'
  // un contenitore-colonna giocatore", qualunque sia il numero di giocatori.
  const cols = Array.from(document.querySelectorAll('div')).filter(
    (el) =>
      el.classList.contains('border-b-[1px]') &&
      el.classList.contains('border-gray-200') &&
      el.classList.contains('bg-gray-0')
  );
  return cols.map(col => {
    const rows = Array.from(col.querySelectorAll('li')).filter(li =>
      /\\d+\\.\\d+:1/.test(li.textContent)
    );
    // Blocchi corsia: un <svg> con almeno un path pieno e, nella riga che
    // lo contiene, uno <span> "NN%". La firma la riconosce Python (vedi
    // _ROLE_SIGNATURES) cosi' resta scritta in un posto solo; qui si
    // raccolgono i candidati e basta, le icone ignote le scarta di la'.
    const roles = [];
    col.querySelectorAll('svg').forEach(svg => {
      const solid = Array.from(svg.querySelectorAll('path'))
        .filter(p => (p.getAttribute('opacity') || '1') === '1')
        .map(p => p.getAttribute('d') || '')
        .join('');
      if (!solid) return;
      const wrap = svg.closest('div');
      const row = wrap ? wrap.parentElement : null;
      const span = row ? row.querySelector('span') : null;
      const pct = span ? span.textContent.trim() : '';
      if (pct.endsWith('%')) roles.push({ sig: solid.slice(0, __SIG_LEN__), pct: pct });
    });
    return {
      headerText: col.textContent.slice(0, 200),
      roles: roles,
      champs: rows.map(li => {
        const img = li.querySelector('img');
        const spans = li.querySelectorAll('span');
        return {
          champion: img ? img.alt : null,
          games: spans[0] ? spans[0].textContent.trim() : null,
          winrate: spans[1] ? spans[1].textContent.trim() : null,
        };
      }),
    };
  });
}
""".replace("__SIG_LEN__", str(_ROLE_SIG_LEN))


def fetch_team_pool(multisearch_url: str, requested_summoners: list[str]) -> list[PlayerPool]:
    """requested_summoners: lista di "Nome#TAG" nell'ordine passato dall'utente.
    Serve per abbinare ogni colonna al giocatore giusto: op.gg non garantisce
    di renderizzare le colonne nello stesso ordine dei parametri dell'URL
    (verificato - l'ordine puo' differire)."""

    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--no-first-run",
        ])
        context = browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=_USER_AGENT)
        page = context.new_page()
        page.goto(multisearch_url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1500)
        raw_cols = page.evaluate(_EXTRACT_JS)
        browser.close()

    # nomi campioni validi conosciuti, per scartare eventuali righe rumorose
    real_slugs = _get_slug_to_name()

    results = []
    for col in raw_cols:
        header = col["headerText"]
        # Confronto NORMALIZZATO: op.gg mostra il nome reale dell'account, che
        # puo' differire da come l'utente l'ha digitato nell'URL per due
        # motivi indipendenti.
        #
        # 1. Maiuscole/minuscole ("eide" digitato, "Eide" in pagina).
        # 2. SPAZI. Un Riot ID puo' contenerli e op.gg accetta comunque il
        #    link senza: "insecjanna#12345" nell'URL, "Insec Janna#12345" in
        #    pagina. Con un confronto per sottostringa quel giocatore veniva
        #    scartato in SILENZIO - la colonna c'era, i dati pure, ma la
        #    squadra tornava di 4 giocatori invece di 5 e la deduzione dei
        #    ruoli si disattivava senza spiegare perche'. Caso reale, trovato
        #    dall'utente il 2026-09-07 su un suo avversario di campionato:
        #    "il nome è questo, e come noti c'è uno spazio, è possibile che
        #    abbia questo rotto il tuo modo di trovare questo giocatore?".
        #    Si', era esattamente quello.
        header_norm = _normalize_summoner(header)
        matched = next(
            (s for s in requested_summoners
             if _normalize_summoner(s.split("#")[0]) in header_norm),
            None,
        )
        if not matched:
            continue

        champs = []
        for c in col["champs"]:
            if not c["champion"]:
                continue
            real_name = real_slugs.get(slugify_champion_name(c["champion"]))
            if not real_name:
                continue
            games = int(c["games"]) if c["games"] and c["games"].isdigit() else 0
            winrate = int(c["winrate"].rstrip("%")) if c["winrate"] and c["winrate"].rstrip("%").isdigit() else 0
            champs.append(PlayerChampion(champion=real_name, games=games, winrate=winrate))

        roles: dict[str, float] = {}
        for r in col.get("roles") or []:
            ruolo = _ROLE_SIGNATURES.get(r.get("sig") or "")
            if not ruolo:
                continue  # icona non riconosciuta: si tace e si degrada
            pct = (r.get("pct") or "").rstrip("%")
            if pct.isdigit():
                # max e non somma: la stessa corsia non dovrebbe comparire due
                # volte, ma se capitasse sommare darebbe quote sopra 1
                roles[ruolo] = max(roles.get(ruolo, 0.0), int(pct) / 100.0)

        results.append(PlayerPool(summoner=matched, champions=champs, roles=roles))

    return results


_PLAYER_EXTRACT_JS = """
() => {
  // Tabella "Campioni" della tab stagionale di un profilo op.gg (diversa dal
  // multisearch sopra) - le righe di primo livello hanno class="cursor-pointer"
  // e un'icona campione; le righe "vs <avversario>" annidate (dettaglio
  // matchup, espandibili con "Mostra di piu'") hanno invece class="" vuota -
  // verificato nel DOM reale, e' l'unico modo affidabile di escluderle (senza
  // questo filtro finiscono in mezzo alla lista come falsi campioni extra).
  const table = document.querySelectorAll('table')[0];
  if (!table) return [];
  const rows = Array.from(table.querySelectorAll('tr')).filter(
    (tr) => tr.classList.contains('cursor-pointer') && tr.querySelector('td img[alt]')
  );
  return rows.map((tr) => {
    const img = tr.querySelector('td img[alt]');
    const spans = Array.from(tr.querySelectorAll('span'));
    const winSpan = spans.find((s) => /^\\d+V$/.test(s.textContent.trim()));
    const loseSpan = spans.find((s) => /^\\d+S$/.test(s.textContent.trim()));
    const winrateSpan = spans.find((s) => /^\\d+%$/.test(s.textContent.trim()) && s.className.includes('basis'));
    return {
      champion: img ? img.alt : null,
      wins: winSpan ? winSpan.textContent.trim() : null,
      losses: loseSpan ? loseSpan.textContent.trim() : null,
      winrate: winrateSpan ? winrateSpan.textContent.trim() : null,
    };
  });
}
"""


def fetch_player_champions(region: str, riot_id: str) -> PlayerPool:
    """Tutti i campioni giocati in stagione da UN singolo evocatore, dalla tab
    "Campioni" del suo profilo op.gg - a differenza di fetch_team_pool sopra
    (un resoconto sintetico da link multisearch), qui interessa lo storico
    COMPLETO di una persona gestita direttamente nel roster (richiesta
    esplicita dell'utente, 2026-08-19). riot_id nel formato "Nome#TAG" (come
    salvato nel roster); op.gg vuole "Nome-TAG" nell'URL (verificato
    navigando un profilo reale)."""
    name, _, tag = riot_id.partition("#")
    if not tag:
        raise ValueError(f'Riot ID incompleto (manca #TAG): "{riot_id}"')
    slug = quote(f"{name}-{tag}")
    url = f"https://op.gg/it/lol/summoners/{region}/{slug}/champions"

    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--no-first-run",
        ])
        context = browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=_USER_AGENT)
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1500)
        raw_rows = page.evaluate(_PLAYER_EXTRACT_JS)
        browser.close()

    real_slugs = _get_slug_to_name()
    champs = []
    for r in raw_rows:
        if not r["champion"]:
            continue
        real_name = real_slugs.get(slugify_champion_name(r["champion"]))
        if not real_name:
            continue
        wins = int(r["wins"].rstrip("V")) if r["wins"] and r["wins"].rstrip("V").isdigit() else 0
        losses = int(r["losses"].rstrip("S")) if r["losses"] and r["losses"].rstrip("S").isdigit() else 0
        winrate = int(r["winrate"].rstrip("%")) if r["winrate"] and r["winrate"].rstrip("%").isdigit() else 0
        champs.append(PlayerChampion(champion=real_name, games=wins + losses, winrate=winrate))

    return PlayerPool(summoner=riot_id, champions=champs)


def aggregate_pool(players: list[PlayerPool]) -> dict[str, list[dict]]:
    """Campione -> lista di {summoner, games, winrate}, una voce per ogni
    giocatore che lo ha in pool. Non aggregate/sommate: se piu' giocatori
    condividono un campione, vanno mostrate come righe separate, non un
    numero unico (richiesta esplicita dell'utente)."""
    pool: dict[str, list[dict]] = {}
    for player in players:
        for c in player.champions:
            pool.setdefault(c.champion, []).append(
                {"summoner": player.summoner, "games": c.games, "winrate": c.winrate}
            )
    return pool
