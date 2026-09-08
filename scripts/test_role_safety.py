"""Stress test per il filtro "sicurezza ruoli" aggiunto a _choose_bot_champion
(2026-08-26, su richiesta esplicita dell'utente: "c'e' un modo per
evitarlo?" dopo il warning a fine draft) - verifica che il lato BOT arrivi
SEMPRE a fullyCovered=True su molte draft simulate, con un trainee che
sceglie a caso (worst case per il bot: nessuna collaborazione dal trainee
nello svuotare il pool). Il ritardo "il bot sta pensando" e' azzerato SOLO
qui per velocita' di test - non tocca la costante reale usata dall'app."""
import sys

# I dati pro contengono nomi di squadra non latini (una polacca con la 'a'
# ogonek ha fatto fallire questo test a intermittenza, solo quando il
# sorteggio dell'ancora la pescava e l'output finiva su file, dove Windows
# usa cp1252). Il test non deve dipendere da chi esce a caso.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import driftdraft.training_bot as training_bot
from driftdraft.data import load_champions

training_bot.BOT_THINK_DELAY_MIN = 0.0
training_bot.BOT_THINK_DELAY_MAX = 0.0

all_names = [c.name for c in load_champions()]
N_RUNS = 40

not_covered = []
for i in range(N_RUNS):
    mode = random.choice(["freeform", "team"])
    side = random.choice(["blue", "red"])
    session = training_bot.start_session(mode, side)

    while not session.state()["finished"]:
        if session.is_trainee_turn():
            taken = session.all_taken()
            champion = random.choice([n for n in all_names if n not in taken])
            session.apply_trainee_action(champion)

    final = session.state()
    bot_side_key = "red" if side == "blue" else "blue"
    bot_role_result = final["roleAssignment"][bot_side_key]
    trainee_role_result = final["roleAssignment"][side]

    status = "OK" if bot_role_result["fullyCovered"] else "NON COPERTO"
    print(f"[{i+1}/{N_RUNS}] mode={mode} trainee={side} bot={bot_side_key}: {status}")
    if not bot_role_result["fullyCovered"]:
        not_covered.append((i, bot_role_result))

print(f"\n{N_RUNS - len(not_covered)}/{N_RUNS} draft con lato BOT fully covered.")
if not_covered:
    print("FALLITE:")
    for i, r in not_covered:
        print(f"  run {i}: {r}")
    sys.exit(1)
else:
    print("Tutte le draft: il bot ha sempre coperto 5 ruoli distinti.")
