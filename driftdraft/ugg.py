"""Ricerca counter di CORSIA (early game, differenza oro a 15 minuti) per un
campione da u.gg - dato diverso da quello di driftdraft/lolalytics.py (li'
e' il winrate medio sull'intera partita). Richiesto dall'utente 2026-08-24
dopo aver verificato lui stesso che lolalytics non ha una sezione dedicata a
questo: la fonte e' invece la colonna "Best Lane Counters" nella pagina
counter di u.gg.

Serve un browser vero (Playwright), stesso motivo di opgg.py/lolalytics.py:
una richiesta HTTP diretta senza browser viene bloccata (403, verificato) -
u.gg e' dietro una protezione anti-bot (Cloudflare challenge-platform,
visibile nelle richieste di rete della pagina). Gli stessi argomenti di
lancio gia' in uso per gli altri due siti bastano a superarla (verificato).
"""

import re
from dataclasses import dataclass

from playwright.sync_api import sync_playwright

from driftdraft.data import load_champions, slugify_champion_name
from driftdraft.lolalytics import DEFAULT_TIER, VALID_TIERS, _get_slug_to_name

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Vocabolario ruoli di questo progetto -> valore del parametro "role" atteso
# da u.gg (verificato cliccando le 5 icone ruolo sulla pagina counter e
# leggendo l'URL risultante - "adc", non "bottom" come lolalytics, unica
# vera differenza di convenzione tra i due siti).
ROLE_TO_UGG_ROLE = {
    "Top": "top",
    "Jungle": "jungle",
    "Mid": "mid",
    "Bot": "adc",
    "Support": "support",
}

# I valori del parametro "rank" di u.gg (es. "master_plus") sono risultati
# IDENTICI a quelli gia' verificati per il parametro "tier" di lolalytics
# (VALID_TIERS/DEFAULT_TIER, importati invece di duplicati) - non e' un
# caso: nell'app e' un'UNICA preferenza del coach (counterModeTier lato
# frontend) applicata a entrambe le fonti dati, non due concetti distinti.

# Ogni riga e' un <a href="/lol/champions/<slug>/build"> il cui textContent
# e' tipo "Mel+301 GD15477 games" (nessuno spazio tra GD15 e il numero di
# partite, o tra il nome e il segno +/- del GD15) - regex invece di uno
# split fragile, gestisce entrambi i segni e le virgole nel conteggio
# partite (es. "1,175 games").
_ROW_RE = re.compile(r"([+-]\d+)\s*GD15\s*([\d,]+)\s*games", re.IGNORECASE)

_EXTRACT_JS = """
() => {
  const header = [...document.querySelectorAll('div')].find(
    (el) => el.children.length === 0 && el.textContent.trim().startsWith('Best Lane Counters')
  );
  if (!header) return [];
  // header -> riga del titolo -> blocco titolo+descrizione -> colonna
  // (la lista delle righe e' una SORELLA di questo blocco, non un figlio -
  // verificato ispezionando la pagina reale, vedi note di progetto).
  const column = header.parentElement.parentElement.parentElement;
  return [...column.querySelectorAll('a[href*="/build"]')].map((a) => ({
    href: a.getAttribute('href'),
    text: a.textContent,
  }));
}
"""


@dataclass
class LaneCounterEntry:
    champion: str
    # differenza oro a 15' dell'AVVERSARIO (quello in griglia) contro il
    # riferimento - a differenza di lolalytics.py QUI NON serve invertire il
    # segno: la colonna "Best Lane Counters vs <riferimento>" di u.gg mostra
    # gia' il GD15 dal punto di vista di ogni avversario elencato ("Mel +301
    # GD15" = Mel e' avanti di 301 oro a 15' CONTRO il riferimento), non il
    # punto di vista del riferimento come invece fa lolalytics per il
    # winrate (verificato leggendo la descrizione della sezione sul sito).
    gd15: int
    games: int


def fetch_lane_counters(
    reference_champion: str, role: str, tier: str = DEFAULT_TIER
) -> list[LaneCounterEntry]:
    """reference_champion: nome del campione gia' piazzato in uno slot. role:
    uno tra Top/Jungle/Mid/Bot/Support. tier: uno dei valori in VALID_TIERS -
    non validato qui (gia' fatto lato server, stesso pattern di
    lolalytics.fetch_counters). Ritorna gli avversari ordinati per GD15
    CONTRO il riferimento, dal piu' forte in corsia - lista vuota (non
    un'eccezione) se u.gg non ha righe per questa combinazione, stesso
    trattamento "silenzioso" che la funzione gia' fa per un singolo slug non
    riconosciuto."""
    slug = slugify_champion_name(reference_champion)
    ugg_role = ROLE_TO_UGG_ROLE[role]
    url = f"https://u.gg/lol/champions/{slug}/counter?role={ugg_role}&rank={tier}"

    with sync_playwright() as p:
        browser = p.chromium.launch(args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--no-first-run",
        ])
        context = browser.new_context(viewport={"width": 1440, "height": 2200}, user_agent=_USER_AGENT)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Stesso approccio di lolalytics.py: aspettare la sezione invece di
        # "networkidle" (rumore di rete di sottofondo che non si azzera mai).
        page.wait_for_function(
            "() => [...document.querySelectorAll('div')].some("
            "el => el.children.length === 0 && el.textContent.trim().startsWith('Best Lane Counters'))",
            timeout=20000,
        )
        raw = page.evaluate(_EXTRACT_JS)
        browser.close()

    slug_to_name = _get_slug_to_name()

    entries = []
    for item in raw:
        slug_match = re.search(r"/champions/([a-z0-9]+)/build", item["href"] or "")
        row_match = _ROW_RE.search(item["text"] or "")
        if not slug_match or not row_match:
            continue
        real_name = slug_to_name.get(slug_match.group(1))
        if not real_name:
            continue
        entries.append(
            LaneCounterEntry(
                champion=real_name,
                gd15=int(row_match.group(1)),
                games=int(row_match.group(2).replace(",", "")),
            )
        )

    entries.sort(key=lambda e: e.gd15, reverse=True)
    return entries
