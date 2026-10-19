"""La versione di DriftDraft, in un posto solo.

Stava in main.py fino al 2026-10-19. E' stata spostata qui per
l'aggiornamento dall'app (vedi updater.py): il server deve sapere che
versione sta girando per confrontarla con l'ultima release su GitHub, e
dentro l'eseguibile main.py non e' un modulo che il server possa importare.
La leggono main.py (titolo della finestra), updater.py e
scripts/build_installer.py (nome e versione dell'installer).

Si cambia SOLO qui, ad ogni release.
"""

VERSION = "2.5"
