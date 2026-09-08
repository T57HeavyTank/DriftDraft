"""Roster delle squadre allenate dal coach.

Un coach puo' avere piu' team ("profili"). Ogni profilo ha 5 ruoli; ogni
ruolo ha una LISTA di giocatori (il titolare + eventuali sub, questi ultimi
salvati con nome "sub - <nome>" per convenzione, niente flag separato).
Ogni giocatore ha la sua tier list personale (S/A/B/C/D -> campioni).

Dato per-giocatore/per-profilo, non per-campione: non entra nell'xlsx (che
resta solo per i tag generici dei campioni), vive in un file separato
modificabile dal sotto-menu dedicato.
"""

import json

from driftdraft.paths import get_app_dir

ROLES = ["Top", "Jungle", "Mid", "Bot", "Support"]
TIERS = ["S", "A", "B", "C", "D"]

# Dato SCRITTO dall'app, vive accanto all'eseguibile - vedi get_app_dir per
# il perche' e' diversa da get_bundle_dir (usata invece per web/, codice
# dell'app che non ha senso l'utente apra/modifichi).
ROSTER_PATH = get_app_dir() / "data" / "roster.json"


def _empty_player() -> dict:
    return {"name": "", "riot_id": "", "tiers": {tier: [] for tier in TIERS}}


def _empty_profile() -> dict:
    return {role: [] for role in ROLES}


def _load_all() -> dict:
    if not ROSTER_PATH.exists():
        return {"profiles": {}}
    raw = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    raw.setdefault("profiles", {})
    return raw


def _save_all(data: dict) -> None:
    ROSTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROSTER_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_profiles() -> list[str]:
    return sorted(_load_all()["profiles"].keys())


def load_profile(name: str) -> dict:
    all_data = _load_all()
    profile = all_data["profiles"].get(name)
    if profile is None:
        return _empty_profile()

    # riempie eventuali ruoli mancanti/malformati invece di rompersi
    empty = _empty_profile()
    for role in ROLES:
        players = profile.get(role, empty[role])
        if not isinstance(players, list):
            players = []
        cleaned = []
        for p in players:
            if not isinstance(p, dict):
                continue
            player = _empty_player()
            player["name"] = str(p.get("name", ""))
            player["riot_id"] = str(p.get("riot_id", ""))
            for tier in TIERS:
                champs = p.get("tiers", {}).get(tier, [])
                player["tiers"][tier] = champs if isinstance(champs, list) else []
            cleaned.append(player)
        profile[role] = cleaned

    return profile


def save_profile(name: str, profile: dict) -> None:
    if not name.strip():
        raise ValueError("Il profilo deve avere un nome.")
    all_data = _load_all()
    all_data["profiles"][name] = profile
    _save_all(all_data)


def rename_profile(old_name: str, new_name: str) -> None:
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Il nuovo nome non puo' essere vuoto.")
    all_data = _load_all()
    profiles = all_data["profiles"]
    if old_name not in profiles:
        raise ValueError("Profilo non trovato.")
    if new_name != old_name and new_name in profiles:
        raise ValueError(f'Esiste gia\' un profilo chiamato "{new_name}".')
    profiles[new_name] = profiles.pop(old_name)
    _save_all(all_data)


def delete_profile(name: str) -> None:
    all_data = _load_all()
    all_data["profiles"].pop(name, None)
    _save_all(all_data)
