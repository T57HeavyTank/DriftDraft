"""Verifica manuale di driftdraft/training_bot.py - simula una sessione
completa (freeform e contro una squadra pro) usando qualunque dato gia' salvato su disco da
leaguepedia.py (vedi test_leaguepedia.py), senza toccare la rete."""
import sys

# I dati pro contengono nomi di squadra non latini (una polacca con la 'a'
# ogonek ha fatto fallire questo test a intermittenza, solo quando il
# sorteggio dell'ancora la pescava e l'output finiva su file, dove Windows
# usa cp1252). Il test non deve dipendere da chi esce a caso.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from driftdraft import training_bot
from driftdraft.data import load_champions


def run(mode, side):
    print(f"\n=== mode={mode} side={side} ===")
    session = training_bot.start_session(mode, side)
    print("Stato iniziale:", session.state())

    all_names = [c.name for c in load_champions()]
    turns = 0
    while not session.state()["finished"] and turns < 30:
        st = session.state()
        if not st["isTraineeTurn"]:
            raise AssertionError("il bot dovrebbe aver gia' agito prima di restituire il controllo")
        taken = session.all_taken()
        candidate = next(n for n in all_names if n not in taken)
        session.apply_trainee_action(candidate)
        turns += 1

    final = session.state()
    print("Step totali (dovrebbero essere 20):", final["step"])
    assert final["step"] == 20, "sequenza draft non completa!"
    assert final["finished"] is True

    blue_all = final["bluePicks"] + final["blueBans"]
    red_all = final["redPicks"] + final["redBans"]
    assert all(blue_all), "slot blue vuoto alla fine!"
    assert all(red_all), "slot red vuoto alla fine!"
    assert len(set(blue_all + red_all)) == 20, "campione duplicato nella draft finale!"

    print("Blue picks:", final["bluePicks"])
    print("Red picks:", final["redPicks"])
    print("Blue bans:", final["blueBans"])
    print("Red bans:", final["redBans"])
    if final["botTeam"]:
        print("Il bot gioca come:", final["botTeam"])
    print("OK - nessuna sovrapposizione, 20/20 slot pieni, sequenza corretta.")


run("freeform", "blue")
run("freeform", "red")
run("team", "blue")
run("team", "red")

print("\n--- Test errore: mossa fuori turno ---")
session = training_bot.start_session("freeform", "blue")
try:
    # Con blue trainee, il bot NON dovrebbe aver agito ancora (team1=blue
    # agisce per primo nel ban phase 1) - quindi step 0 e' del trainee, ok.
    # Forziamo un errore usando un nome invalido invece.
    session.apply_trainee_action("Nome Campione Inventato")
    print("ERRORE: doveva sollevare ValueError!")
except ValueError as e:
    print("OK, sollevato correttamente:", e)

print("\n--- Test errore: campione gia' preso ---")
session2 = training_bot.start_session("freeform", "red")  # bot=blue agisce per primo
first_bot_ban = session2.state()["blueBans"][0]
try:
    session2.apply_trainee_action(first_bot_ban)
    print("ERRORE: doveva sollevare ValueError!")
except ValueError as e:
    print("OK, sollevato correttamente:", e)

print("\nTutti i test passati.")
