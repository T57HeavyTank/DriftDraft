"""Rilevamento locale di una tierlist da screenshot.

Nessuna libreria di computer vision pesante (niente OpenCV) - solo Pillow +
NumPy, coerente col principio "leggero e locale" del progetto.

Approccio in due fasi, pensato per non dipendere dallo stile grafico
specifico dello strumento usato per fare lo screenshot (TierMaker o altro):

1. Segmentazione: profili di "attivita'" (deviazione standard dei pixel) per
   riga e per colonna. Le icone hanno molta variazione di colore al loro
   interno, gli spazi vuoti fra icone/righe sono quasi uniformi - le bande a
   bassa attivita' separano automaticamente righe e colonne senza dover
   riconoscere etichette di testo o bordi specifici.
2. Identificazione: ogni regione candidata viene ridotta a una miniatura e
   confrontata (correlazione normalizzata, robusta a piccole differenze di
   luminosita'/contrasto da compressione) contro immagini di riferimento
   gia' note. Un match sotto soglia viene scartato: meglio non rilevare un
   campione che assegnarne uno sbagliato - l'utente rivede sempre il
   risultato prima di salvare, ma un campione ASSENTE si nota subito, uno
   SBAGLIATO puo' sfuggire a un controllo veloce.

Le immagini di riferimento (assets/tiermaker_refs/) sono state scaricate UNA
TANTUM dal template pubblico "League of Legends ALWAYS Updated Champions"
di tiermaker.com (non dalla lista personale dell'utente, che resta privata -
il template vuoto e' pubblico) - sono pixel-identiche a quello che finisce
in QUALSIASI screenshot fatto da quel template, quindi lo stile combacia
esattamente invece di dover indovinare (verificato: le icone quadrate di
assets/icons/, prese da LoLWiki per un altro scopo, hanno uno stile/crop
troppo diverso dagli screenshot reali e producevano troppi errori, ~30%
invece del <10% richiesto). Alcuni campioni reworkati hanno 2 immagini
(vecchia + nuova, es. Skarner*.png e Skarner__alt1.png) - entrambe valide,
vince chi somiglia di piu' caso per caso.
"""

import io
import re
from pathlib import Path

import numpy as np
from PIL import Image

from driftdraft.roster import TIERS

TIERMAKER_REFS_DIR = Path(__file__).resolve().parent.parent / "assets" / "tiermaker_refs"

THUMB_SIZE = 32
MIN_SIMILARITY = 0.55
MIN_BOX_SIZE = 20  # px - scarta bande troppo sottili per essere un'icona

_reference_names: list[str] | None = None
_reference_matrix: np.ndarray | None = None


def _normalize(arr: np.ndarray) -> np.ndarray:
    flat = arr.flatten().astype(np.float32)
    flat -= flat.mean()
    norm = np.linalg.norm(flat)
    if norm < 1e-6:
        return flat
    return flat / norm


def _load_reference_matrix() -> tuple[list[str], np.ndarray]:
    global _reference_names, _reference_matrix
    if _reference_matrix is not None:
        return _reference_names, _reference_matrix

    names = []
    vecs = []
    for path in sorted(TIERMAKER_REFS_DIR.glob("*.png")):
        # "Skarner__alt1.png" -> "Skarner": entrambe le varianti (vecchia e
        # reworkata) restano candidate per lo stesso nome campione.
        name = re.sub(r"__alt\d+$", "", path.stem)
        img = Image.open(path).convert("RGB").resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        vecs.append(_normalize(np.asarray(img, dtype=np.float32)))
        names.append(name)

    _reference_names = names
    _reference_matrix = np.stack(vecs)
    return _reference_names, _reference_matrix


def _find_bands(profile: np.ndarray, min_gap: int) -> list[tuple[int, int]]:
    """Bande contigue sopra soglia lungo un profilo 1D (riga o colonna),
    tollerando piccoli buchi (min_gap campioni sotto soglia) per non
    spezzare un'icona in due a causa di un singolo pixel rumoroso."""
    threshold = profile.mean() * 0.5
    is_active = profile > threshold

    bands = []
    start = None
    gap = 0
    for i, active in enumerate(is_active):
        if active:
            if start is None:
                start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap > min_gap:
                bands.append((start, i - gap))
                start = None
    if start is not None:
        bands.append((start, len(is_active) - 1))
    return bands


def _typical_row_height(heights: list[float]) -> float:
    """Altezza "tipica" fra le bande-riga rilevate: quella con piu' altre
    bande entro il 25% di se stessa (voto di maggioranza). Robusta sia a una
    banda anomala troppo ALTA (una tier avvolta su piu' righe fisiche) sia a
    una troppo BASSA (una barra spuria tipo bottoni "Share on Twitter/FB") -
    a differenza di mediana o minimo, che si lasciano trascinare da un
    singolo outlier quando le bande "normali" sono poche (bug reale scovato
    dagli screenshot dell'utente, 2026-08-19: un primo fix basato sul minimo
    risolveva il caso della tier avvolta ma rompeva quello della barra
    spuria, e viceversa - verificato con test sintetici mirati)."""
    best_h, best_count = heights[0], -1
    for h in heights:
        count = sum(1 for other in heights if abs(other - h) <= h * 0.25)
        if count > best_count:
            best_h, best_count = h, count
    return float(best_h)


def _segment_rows(img: Image.Image) -> list[list[tuple[int, int, int, int]]]:
    """Righe di icone rilevate dall'alto in basso, ciascuna come lista di
    bounding box (x0, y0, x1, y1) da sinistra a destra. Righe senza nessuna
    banda-colonna valida (es. rumore, testo di intestazione con poco
    contrasto) vengono scartate qui, PRIMA che diventino un tier vuoto."""
    gray = np.asarray(img.convert("L"), dtype=np.float32)
    h, w = gray.shape

    # min_gap=0: righe tier reali possono essere separate da un divisore di
    # un solo pixel (verificato su screenshot reale) - qualunque tolleranza
    # maggiore le fonde tutte in un'unica banda gigante.
    row_bands = _find_bands(gray.std(axis=1), min_gap=0)
    row_bands = [(y0, y1) for y0, y1 in row_bands if (y1 - y0) >= MIN_BOX_SIZE]

    if not row_bands:
        return []

    icon_size = _typical_row_height([y1 - y0 for y0, y1 in row_bands])

    # Fonde bande consecutive separate da un varco piu' STRETTO del tipico
    # (stesso voto di maggioranza di sopra, applicato ai varchi invece che
    # alle altezze) - le icone vere hanno spesso un margine trasparente
    # intorno al disegno, quindi una tier avvolta su una seconda riga fisica
    # a volte non si fonde in un'unica banda gigante ma resta separata da un
    # piccolo margine residuo (diverso dal margine PIU' ampio, deliberato,
    # fra una tier e la successiva) - un varco molto piu' STRETTO del
    # distacco normale fra tier e' un forte indizio di continuazione della
    # STESSA tier, non di una tier nuova (bug reale scovato con un test
    # sintetico su icone vere, 2026-08-19: senza questa fusione, le 2 righe
    # fisiche di una tier avvolta finivano su 2 tier diverse).
    merged: list[list[tuple[int, int]]] = [[row_bands[0]]]
    if len(row_bands) > 1:
        gaps = [row_bands[i + 1][0] - row_bands[i][1] for i in range(len(row_bands) - 1)]
        typical_gap = _typical_row_height(gaps) if any(g > 0 for g in gaps) else 0.0
        for i in range(1, len(row_bands)):
            if typical_gap > 0 and gaps[i - 1] < typical_gap * 0.5:
                merged[-1].append(row_bands[i])
            else:
                merged.append([row_bands[i]])

    # Una banda (o un gruppo appena fuso) molto piu' alta di una singola
    # icona e' quasi certamente una tier avvolta su piu' righe fisiche senza
    # alcun varco rilevabile - va ri-segmentata nelle sue sotto-righe reali
    # (stessa tecnica del rilevamento riga sopra, applicata solo alla fetta
    # y0:y1) invece di restare un'unica banda gigante: altrimenti ogni
    # box-colonna prenderebbe l'intera altezza (piu' icone impilate in un
    # solo ritaglio), producendo ritagli deformi che il confronto quasi mai
    # riconosce. Le sotto-righe restano tutte nella STESSA tier del
    # genitore (l'avvolgimento non cambia la tier) - fuse di nuovo in
    # un'unica lista di box piu' sotto.
    row_groups: list[list[tuple[int, int]]] = []
    for group in merged:
        total_h = sum(y1 - y0 for y0, y1 in group)
        if len(group) == 1 and total_h > icon_size * 1.6:
            y0, y1 = group[0]
            sub_bands = _find_bands(gray[y0 : y1 + 1, :].std(axis=1), min_gap=0)
            sub_bands = [(y0 + sy0, y0 + sy1) for sy0, sy1 in sub_bands if (sy1 - sy0) >= MIN_BOX_SIZE]
            if len(sub_bands) < 2:
                # Nessun varco rilevabile fra le righe fisiche (icone
                # impilate senza alcun gap fra un avvolgimento e l'altro) -
                # dividerla alla cieca in fette di altezza icon_size resta
                # comunque meglio di tenerla intera: ogni fetta e' un
                # rettangolo quadrato invece di un blocco alto 2+ icone.
                n_lines = max(2, round(total_h / icon_size))
                step = total_h / n_lines
                sub_bands = [
                    (int(y0 + k * step), int(y0 + (k + 1) * step) if k < n_lines - 1 else y1)
                    for k in range(n_lines)
                ]
            row_groups.append(sub_bands)
        else:
            row_groups.append(group)

    rows = []
    for sub_bands in row_groups:
        boxes = []
        for y0, y1 in sub_bands:
            col_profile = gray[y0 : y1 + 1, :].std(axis=0)
            col_bands = _find_bands(col_profile, min_gap=max(2, w // 300))
            for x0, x1 in col_bands:
                width = x1 - x0
                if width < MIN_BOX_SIZE:
                    continue
                n_icons = max(1, round(width / icon_size))
                step = width / n_icons
                for k in range(n_icons):
                    bx0 = int(x0 + k * step)
                    bx1 = int(x0 + (k + 1) * step) if k < n_icons - 1 else x1
                    boxes.append((bx0, y0, bx1, y1))

        # Scarta righe senza nessun box "a forma di icona" (larghezza vicina
        # alla propria altezza) - filtra bande spurie che superano la sola
        # soglia di altezza ma non sono affatto una tier, es. una barra di
        # bottoni "Share on Twitter/FB" di tiermaker.com (vista in uno
        # screenshot reale dell'utente, 2026-08-19: veniva letta come una
        # tier vuota extra, spostando TUTTE le righe vere di una posizione -
        # S restava vuota, il vero S finiva in A, il vero A in B, ecc).
        if boxes and any(
            abs((bx1 - bx0) - (by1 - by0)) <= (by1 - by0) * 0.6 for bx0, by0, bx1, by1 in boxes
        ):
            rows.append(boxes)
    return rows


def _identify(crop: Image.Image, names: list[str], matrix: np.ndarray) -> tuple[str, float]:
    thumb = crop.convert("RGB").resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
    vec = _normalize(np.asarray(thumb, dtype=np.float32))
    scores = matrix @ vec
    idx = int(np.argmax(scores))
    return names[idx], float(scores[idx])


def detect_tierlist(image_bytes: bytes) -> dict[str, list[str]]:
    """Ritorna {tier: [nomi campione,...]}. Le righe rilevate vengono
    mappate 1:1 su TIERS nell'ordine in cui compaiono dall'alto in basso -
    oltre la 5a riga viene ignorato (il modello dati ha solo 5 tier fissi).
    Ogni campione compare al massimo una volta: se rilevato in piu' punti
    (es. un falso positivo altrove nell'immagine), vince il match con
    similarita' piu' alta, non il primo trovato."""
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    rows = _segment_rows(img)
    names, matrix = _load_reference_matrix()

    candidates = []  # (tier, nome, punteggio)
    for row_idx, boxes in enumerate(rows):
        if row_idx >= len(TIERS):
            break
        tier = TIERS[row_idx]
        for x0, y0, x1, y1 in boxes:
            crop = img.crop((x0, y0, x1 + 1, y1 + 1))
            name, score = _identify(crop, names, matrix)
            if score >= MIN_SIMILARITY:
                candidates.append((tier, name, score))

    best_per_champion: dict[str, tuple[str, float]] = {}
    for tier, name, score in candidates:
        current = best_per_champion.get(name)
        if current is None or score > current[1]:
            best_per_champion[name] = (tier, score)

    result: dict[str, list[str]] = {t: [] for t in TIERS}
    for name, (tier, _score) in best_per_champion.items():
        result[tier].append(name)
    return result
