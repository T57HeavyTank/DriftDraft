"""Draft salvate (modalita' training).

Un coach segna 5 campioni (nessun ban, nessun lato blue/red - solo una
selezione da poter rivedere in seguito, es. per studiare una comp prima di
un allenamento). A differenza di roster.py (un dict per NOME profilo, un
nome = un'entita'), qui ogni draft salvata e' gia' un'unita' a se' e un nome
duplicato e' normale (es. "vs TeamA game1"/"vs TeamA game2") - quindi una
LISTA di entry con id proprio, non un dict tenuto per nome.
"""

import json
import uuid

from driftdraft.paths import get_app_dir

# Stesso motivo di ROSTER_PATH in roster.py: dato SCRITTO dall'app, vive
# accanto all'eseguibile (get_app_dir), non dentro il bundle di sola lettura.
SAVED_DRAFTS_PATH = get_app_dir() / "data" / "saved_drafts.json"


def _load_all() -> list[dict]:
    if not SAVED_DRAFTS_PATH.exists():
        return []
    raw = json.loads(SAVED_DRAFTS_PATH.read_text(encoding="utf-8"))
    drafts = raw.get("drafts", [])
    return drafts if isinstance(drafts, list) else []


def _save_all(drafts: list[dict]) -> None:
    SAVED_DRAFTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAVED_DRAFTS_PATH.write_text(
        json.dumps({"drafts": drafts}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def list_saved_drafts() -> list[dict]:
    return _load_all()


def add_saved_draft(name: str, champions: list[str]) -> dict:
    drafts = _load_all()
    entry = {"id": uuid.uuid4().hex, "name": name, "champions": champions}
    drafts.append(entry)
    _save_all(drafts)
    return entry


def delete_saved_draft(draft_id: str) -> None:
    drafts = [d for d in _load_all() if d.get("id") != draft_id]
    _save_all(drafts)
