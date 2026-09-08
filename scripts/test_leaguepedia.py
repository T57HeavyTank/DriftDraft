"""Script di verifica manuale per driftdraft/leaguepedia.py - NON parte del
prodotto, solo per controllare a mano che il fetch/parsing/aggregazione
funzionino su dati reali prima di collegare il resto (server, bot, UI).

NON SCRIVE NULLA su data/ se non glielo si chiede esplicitamente con
--salva (2026-09-06). Prima salvava sempre in fondo, e siccome scarica solo
25 draft di default, un semplice "faccio girare i test del progetto"
SOSTITUIVA le 1500 draft sincronizzate dall'utente con 25. E' successo
davvero: recuperate da git perche' data/ e' versionato, ma e' un incidente
che non deve poter capitare - un test di lettura non deve toccare i dati di
lavoro di chi lo lancia.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from driftdraft import leaguepedia

SALVA = "--salva" in sys.argv
_args = [a for a in sys.argv[1:] if not a.startswith("--")]
TOTAL = int(_args[0]) if _args else 25

print(f"Fetching {TOTAL} recent drafts from Leaguepedia...", flush=True)
t0 = time.time()
drafts = leaguepedia.fetch_recent_drafts(total=TOTAL)
print(f"Got {len(drafts)} drafts in {time.time() - t0:.1f}s", flush=True)

if not drafts:
    print("NESSUNA DRAFT SCARICATA - controllare l'errore sopra.")
    sys.exit(1)

d0 = drafts[0]
print("\n--- Prima draft (piu' recente) ---")
print(f"Torneo: {d0.tournament}")
print(f"Data: {d0.date} | Patch: {d0.patch}")
print(f"{d0.team1} vs {d0.team2} | Winner: team{d0.winner}")
print(f"Team1 picks: {d0.team1_picks}")
print(f"Team2 picks: {d0.team2_picks}")
print(f"Team1 roles: {d0.team1_roles}")
print(f"Team1 bans: {d0.team1_bans}")
print(f"Team2 bans: {d0.team2_bans}")

print("\n--- Ordine cronologico ricostruito (primi 5 pick) ---")
for entry in leaguepedia.chronological_picks(d0)[:5]:
    print(entry)

print("\n--- Aggregazione ---")
tables = leaguepedia.build_tables(drafts)
print(f"Campioni con almeno 1 pick: {len(tables['pick_counts'])}")
top_picked = sorted(tables["pick_counts"].items(), key=lambda x: -x[1])[:5]
print(f"Top 5 piu' pickati: {top_picked}")

if top_picked:
    sample_champ = top_picked[0][0]
    print(f"\nSinergia per '{sample_champ}' (top 5): "
          f"{sorted(tables['synergy'].get(sample_champ, {}).items(), key=lambda x: -x[1])[:5]}")
    print(f"Counter per '{sample_champ}' (top 5): "
          f"{sorted(tables['counter'].get(sample_champ, {}).items(), key=lambda x: -x[1])[:5]}")

if SALVA:
    print("\nSalvataggio su disco (--salva)...")
    leaguepedia.save_drafts(drafts)
    leaguepedia.save_tables(tables)
    print("Fatto:", leaguepedia.status())
else:
    print(f"\nNIENTE salvataggio: queste {len(drafts)} draft resterebbero al posto "
          "di quelle gia' su disco. Aggiungi --salva se e' proprio quello che vuoi.")
