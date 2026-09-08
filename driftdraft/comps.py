from dataclasses import dataclass

from driftdraft.data import Champion

# Tag "funzionali" per ciascuna comp - NON decidono piu' se la comp e'
# rilevata (vedi MEMBER_THRESHOLD sotto), servono solo a illuminare cosa la
# squadra copre gia' funzionalmente e cosa manca ancora, come una sotto-quest.
COMP_REQUIREMENTS: dict[str, dict] = {
    "TeamFight \\ WomboCombo": {
        "mandatory": [
            "Hard Engage AoE",
            "Danno DPS AoE",
            "Danno burst AoE",
            "Hard CC AoE",
        ],
        "optional": [],
    },
    "Pick": {
        "mandatory": [
            "Danno burst singolo",
            "Hard CC Singolo",
            "Hard Engage singolo",
        ],
        "optional": ["Mobilità"],
    },
    "Proteggi il presidente": {
        "mandatory": [
            "Danno DPS singolo",
            "Disingaggio",
            "Protezione \\ peeling",
        ],
        "optional": ["Utility generica"],
    },
    "Poke \\ Siege": {
        "mandatory": [
            "Long Range",
            "Disingaggio",
            "Danno burst singolo",
        ],
        "optional": ["Hard CC Singolo"],
    },
    "Split": {
        "mandatory": [
            "Side forte",
            "Waveclear",
            "Disingaggio",
        ],
        "optional": ["Utility generica"],
    },
}

# COUNTER NATURALI fra le comp - il diagramma dell'utente (2026-08-16).
#
# Due cicli a 5 che insieme coprono TUTTE E DIECI le coppie possibili: ogni
# comp ne batte esattamente due ed e' battuta da esattamente due. Non c'e'
# nessuna coppia indefinita, ed e' bilanciato per costruzione.
#
# Stava solo in web/app.js, dove serviva a disegnare il pentagono: da qui lo
# legge anche il bot, che e' Python. Una copia sola - il diagramma la riceve
# dal server insieme al resto dei metadati comp (vedi /api/comp-meta), invece
# di tenersene una sua che col tempo divergerebbe.
#
# Le frecce del diagramma sono colorate come il nodo di PARTENZA (chi
# counter-a), non come l'arrivo.
COMP_INNER_CYCLE = [  # le diagonali del pentagono
    ("TeamFight \\ WomboCombo", "Poke \\ Siege"),
    ("Poke \\ Siege", "Pick"),
    ("Pick", "Split"),
    ("Split", "Proteggi il presidente"),
    ("Proteggi il presidente", "TeamFight \\ WomboCombo"),
]

COMP_OUTER_CYCLE = [  # i lati del pentagono
    ("Pick", "TeamFight \\ WomboCombo"),
    ("TeamFight \\ WomboCombo", "Split"),
    ("Split", "Poke \\ Siege"),
    ("Poke \\ Siege", "Proteggi il presidente"),
    ("Proteggi il presidente", "Pick"),
]

# comp -> le due che batte. Forma comoda per chi deve solo chiedersi "questa
# e' in vantaggio contro quella?"; i due cicli restano separati perche' il
# diagramma li disegna con geometrie diverse.
COMP_BEATS: dict[str, frozenset[str]] = {}
for _a, _b in COMP_INNER_CYCLE + COMP_OUTER_CYCLE:
    COMP_BEATS.setdefault(_a, set()).add(_b)
COMP_BEATS = {k: frozenset(v) for k, v in COMP_BEATS.items()}


# Quanti campioni APPARTENENTI alla comp (colonne di appartenenza dell'xlsx,
# non i tag) servono perche' la draft sia considerata "rilevata" per quella
# comp. Un solo campione con tutti i tag giusti non basta - serve la gente.
MEMBER_THRESHOLD = 3


@dataclass
class CompStatus:
    comp: str
    member_count: int
    member_threshold: int
    satisfied: bool
    covered_tags: frozenset[str]
    missing_tags: frozenset[str]
    optional_covered: frozenset[str]
    mandatory_count: int


def detect_comps(picked: list[Champion]) -> dict[str, CompStatus]:
    team_tags: set[str] = set()
    for champ in picked:
        team_tags |= champ.tags

    results = {}
    for comp, reqs in COMP_REQUIREMENTS.items():
        mandatory = reqs["mandatory"]
        optional = reqs["optional"]

        covered = frozenset(t for t in mandatory if t in team_tags)
        missing = frozenset(t for t in mandatory if t not in team_tags)
        optional_covered = frozenset(t for t in optional if t in team_tags)

        member_count = sum(1 for champ in picked if comp in champ.comps)
        satisfied = member_count >= MEMBER_THRESHOLD

        results[comp] = CompStatus(
            comp=comp,
            member_count=member_count,
            member_threshold=MEMBER_THRESHOLD,
            satisfied=satisfied,
            covered_tags=covered,
            missing_tags=missing,
            optional_covered=optional_covered,
            mandatory_count=len(mandatory),
        )

    return results
