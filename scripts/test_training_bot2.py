"""Verifica delle 4 rifiniture richieste dall'utente 2026-08-26: ritardo bot,
rewind, e assign_roles. Usa i dati gia' salvati su disco (leaguepedia.py)."""
import sys

# I dati pro contengono nomi di squadra non latini (una polacca con la 'a'
# ogonek ha fatto fallire questo test a intermittenza, solo quando il
# sorteggio dell'ancora la pescava e l'output finiva su file, dove Windows
# usa cp1252). Il test non deve dipendere da chi esce a caso.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from driftdraft import training_bot
from driftdraft.data import load_champions

all_names = [c.name for c in load_champions()]


def first_available(taken):
    return next(n for n in all_names if n not in taken)


print("=== Test 1: ritardo bot (deve esserci una pausa quando il bot risponde) ===")
session = training_bot.start_session("freeform", "blue")
t0 = time.time()
session.apply_trainee_action(first_available(session.all_taken()))
elapsed = time.time() - t0
# La soglia segue BOT_THINK_DELAY_MIN invece di ripetere il numero a mano:
# quando l'utente ha chiesto di accorciare l'attesa (5s -> 2s il 2026-09-06)
# questo test falliva solo perche' conservava il vecchio 3.0 scritto dentro.
soglia = training_bot.BOT_THINK_DELAY_MIN
print(f"Tempo per un'azione trainee + risposta bot: {elapsed:.2f}s (atteso >= {soglia}s)")
assert elapsed >= soglia, "il ritardo non e' scattato!"
print("OK\n")

print("=== Test 2: rewind ===")
session = training_bot.start_session("freeform", "red")  # bot=blue agisce per primo (ban)
# porta la draft avanti di qualche mossa (ban trainee + pick trainee)
while session.state()["step"] < 10:
    if not session.is_trainee_turn():
        break
    session.apply_trainee_action(first_available(session.all_taken()))

state_before = session.state()
print("Step prima del rewind:", state_before["step"])
pick_steps = state_before["traineePickSteps"]
print("traineePickSteps:", pick_steps)
first_pick_step = next(s for s in pick_steps if s is not None)
old_pick_champion = state_before["redPicks"][pick_steps.index(first_pick_step)]
print(f"Rewind al pick fatto allo step {first_pick_step} (era {old_pick_champion})")

session.rewind_to(first_pick_step)
state_after = session.state()
print("Step dopo il rewind:", state_after["step"])
assert state_after["step"] == first_pick_step, "step non corretto dopo il rewind!"
assert state_after["isTraineeTurn"] is True, "dopo il rewind dovrebbe tornare il turno del trainee!"
# rigioca con un campione DIVERSO da quello scelto prima
taken = session.all_taken()
new_champion = next(n for n in all_names if n not in taken and n != old_pick_champion)
session.apply_trainee_action(new_champion)
final = session.state()
print(f"Nuovo pick a quello step: {new_champion} (prima era {old_pick_champion})")
assert new_champion in final["redPicks"], "il nuovo pick non risulta piazzato!"
assert old_pick_champion not in final["redPicks"] or old_pick_champion == new_champion, "il vecchio pick e' rimasto!"
print("OK - rewind funziona, si puo' rigiocare con una scelta diversa\n")

print("=== Test 3: rewind non valido (su una mossa del BOT, non del trainee) ===")
session2 = training_bot.start_session("freeform", "red")  # step0 e' del bot
try:
    session2.rewind_to(0)
    print("ERRORE: doveva sollevare ValueError!")
except ValueError as e:
    print("OK, sollevato correttamente:", e)
print()

print("=== Test 4: assign_roles ===")
from driftdraft.training_bot import assign_roles

all_champs = load_champions()
single_role = {}  # ruolo -> lista di campioni con QUELLO E SOLO QUELLO come ruolo
for c in all_champs:
    if len(c.roles) == 1:
        single_role.setdefault(next(iter(c.roles)), []).append(c.name)

# 5 campioni DISTINTI, ognuno specialista di un ruolo diverso (verificato via
# frozenset di lunghezza 1, non assunto) - caso pulito, deve coprire tutto.
sample = []
for role in ["Top", "Jungle", "Mid", "Bot", "Support"]:
    candidate = next(n for n in single_role.get(role, []) if n not in sample)
    sample.append(candidate)
print("Campioni di test (uno specialista distinto per ruolo):", sample)
result = assign_roles(sample)
print("Risultato:", result)
assert result["fullyCovered"] is True, "con 5 specialisti distinti dovrebbe sempre riuscire a coprire tutti i ruoli!"
for role, entry in result["assignment"].items():
    assert entry["confident"] is True
    assert entry["champion"] == sample[["Top", "Jungle", "Mid", "Bot", "Support"].index(role)]

# caso patologico verificato: 5 specialisti DISTINTI dello STESSO ruolo (se
# l'xlsx ne ha almeno 5) - impossibile coprire 5 ruoli distinti per costruzione.
support_specialists = single_role.get("Support", [])
if len(support_specialists) >= 5:
    bad_sample = support_specialists[:5]
    print("\nCampioni di test (5 specialisti Support, caso patologico):", bad_sample)
    bad_result = assign_roles(bad_sample)
    print("Risultato:", bad_result)
    assert bad_result["fullyCovered"] is False, "5 specialisti Support non dovrebbero MAI coprire 5 ruoli distinti!"
    confident_count = sum(1 for e in bad_result["assignment"].values() if e["confident"])
    print(f"Ruoli assegnati con sicurezza: {confident_count}/5 (atteso 1, solo Support)")
    assert confident_count == 1
else:
    print(f"\n(solo {len(support_specialists)} specialisti Support puri nell'xlsx - salto il caso patologico)")

print("\nTutti i test passati.")
