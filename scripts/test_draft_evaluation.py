"""Verifica end-to-end di driftdraft/draft_evaluation.py con dati REALI da
lolalytics (5 fetch paralleli veri) - non un mock."""
import sys

# I dati pro contengono nomi di squadra non latini (una polacca con la 'a'
# ogonek ha fatto fallire questo test a intermittenza, solo quando il
# sorteggio dell'ancora la pescava e l'output finiva su file, dove Windows
# usa cp1252). Il test non deve dipendere da chi esce a caso.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import driftdraft.training_bot as training_bot
from driftdraft.data import load_champions
from driftdraft.draft_evaluation import evaluate_session

training_bot.BOT_THINK_DELAY_MIN = 0.0
training_bot.BOT_THINK_DELAY_MAX = 0.0

all_names = [c.name for c in load_champions()]

session = training_bot.start_session("freeform", "blue")
while not session.state()["finished"]:
    if session.is_trainee_turn():
        taken = session.all_taken()
        session.apply_trainee_action(random.choice([n for n in all_names if n not in taken]))

own_picks = session.picks[session.trainee_side]
print("I miei pick:", own_picks)
print("I pick del bot:", session.picks[session.bot_side])

# assegna i ruoli nell'ordine "naturale" suggerito (non serve testare il drag qui)
from driftdraft.training_bot import assign_roles
suggestion = assign_roles(own_picks)
order = [suggestion["assignment"][role]["champion"] for role in training_bot.ROLE_ORDER]
session.confirm_trainee_role_order(order)
print("Ruoli confermati:", dict(zip(training_bot.ROLE_ORDER, order)))

print("\nValutazione in corso (fetch reali, paralleli)...")
t0 = time.time()
result = evaluate_session(session, "emerald_plus")
print(f"Completata in {time.time() - t0:.1f}s\n")

print("Buckets:  ", result["buckets"])
print("Blu:      ", result["blue"])
print("Rosso:    ", result["red"])
print("Verde:    ", result["green"])
print("Bump:     ", result["bumpNotes"])
print("Errori corsia:", result["laneErrors"])
print("\nCurve per corsia:")
for role, curve in result["laneCurves"].items():
    print(f"  {role}: {curve}")

# sanity check: blu/rosso sono curve SOLISTE indipendenti (non piu' un
# complemento a 100 l'una dell'altra, dopo la correzione del 2026-08-26 -
# vedi draft_evaluation.py) - qui si controlla solo che siano nel range
# plausibile 0-100, non una relazione fissa fra loro.
for b, r in zip(result["blue"], result["red"]):
    assert 0 <= b <= 100 and 0 <= r <= 100, f"valore fuori range: blu={b} rosso={r}"
print("\nOK - blu e rosso sono curve soliste indipendenti, entrambe in range 0-100.")
