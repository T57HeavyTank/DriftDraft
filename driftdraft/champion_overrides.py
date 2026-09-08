"""Override persistiti in locale per comp/tag/ruoli di un campione -
richiesto esplicitamente dall'utente (2026-08-27): "non tutti hanno excel
sul proprio pc... vorrei introdurre un modo per dare modo ai coach di poter
modificare i tag direttamente in app".

Deliberatamente un file JSON SEPARATO da champions.xlsx, non una scrittura
diretta nell'xlsx: aprire+salvare quel file via openpyxl CANCELLA le 173
immagini incorporate silenziosamente (bug reale gia' documentato, vedi
scripts/sync_champion_ids.py) - qualunque scrittura automatica in risposta a
un'azione dell'utente rischierebbe di corrompere in modo invisibile il file
che l'utente stesso continua a editare a mano in Excel. Questi override sono
uno strato SEPARATO, applicato SOPRA i dati xlsx a runtime (vedi
data.py::load_champions) - l'xlsx resta la base "di riferimento", questo
file e' solo le modifiche fatte dai coach dentro l'app. Stesso principio
gia' in uso per roster.json/saved_drafts.json: dato mutabile dall'app, MAI
bundlato nel pacchetto (dati dell'utente, non generici)."""

import json
from pathlib import Path

from driftdraft.paths import get_app_dir

OVERRIDES_PATH = get_app_dir() / "data" / "champion_overrides.json"

# Le uniche 3 categorie modificabili - stessi nomi campo di Champion in
# data.py (comps/tags/roles), MAI "name"/"riot_id" (quelli restano sempre
# quello che dice l'xlsx, non ha senso "correggerli" per campione).
_FIELDS = ("comps", "tags", "roles")


def load_overrides(path: Path = OVERRIDES_PATH) -> dict[str, dict]:
    """{nome_campione: {"comps": [...], "tags": [...], "roles": [...]}} -
    una entry puo' avere solo alcune delle 3 chiavi (es. il coach ha
    corretto solo i comp di un campione, non i tag): una chiave ASSENTE
    significa "usa il valore dell'xlsx", non "vuoto"."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write(overrides: dict[str, dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding="utf-8")


def save_override(
    name: str,
    comps: list[str] | None = None,
    tags: list[str] | None = None,
    roles: list[str] | None = None,
    path: Path = OVERRIDES_PATH,
) -> dict:
    """Sostituzione COMPLETA (non merge) di ciascuna categoria passata - il
    chiamante (server.py) manda sempre l'elenco intero delle checkbox
    spuntate per quella categoria, non un diff, quindi non c'e' ambiguita'
    su cosa "aggiungere/togliere"."""
    overrides = load_overrides(path)
    entry = dict(overrides.get(name, {}))
    if comps is not None:
        entry["comps"] = sorted(set(comps))
    if tags is not None:
        entry["tags"] = sorted(set(tags))
    if roles is not None:
        entry["roles"] = sorted(set(roles))
    overrides[name] = entry
    _write(overrides, path)
    return entry


def reset_override(name: str, path: Path = OVERRIDES_PATH) -> None:
    """Rimuove l'intero override del campione - torna a mostrare esattamente
    quello che dice l'xlsx, per tutte e 3 le categorie insieme (un reset
    "parziale" per una sola categoria non e' stato richiesto e aggiungerebbe
    un secondo concetto - "chiave assente vs chiave esplicitamente vuota" -
    per un bisogno che non c'e' ancora)."""
    overrides = load_overrides(path)
    if name in overrides:
        del overrides[name]
        _write(overrides, path)
