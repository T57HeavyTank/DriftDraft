# Lavorare sul codice

Tutto quello che serve per far girare DriftDraft da sorgente, capire com'è
fatto e ricostruire il pacchetto distribuibile. Se invece vuoi solo **usarlo**,
ti basta l'installer: vedi il [README](README.md).

## Requisiti

- Python 3.11+ su Windows
- Circa 1 GB liberi (il grosso è il Chromium di Playwright)

## Setup da zero

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

`playwright install chromium` scarica ~150 MB nella cache utente
(`%LOCALAPPDATA%\ms-playwright`), fuori dal progetto. Serve alle modalità
torneo e agli import da op.gg.

L'ad-blocker usato dalla modalità torneo (`vendor/ublock-origin-lite/`) è già
incluso nella repo: non va scaricato a parte.

Le immagini dei campioni non sono nella repo (vedi
[THIRD-PARTY.md](THIRD-PARTY.md) per il perché): le scarica l'app al primo
avvio. Per forzarle a mano:

```bash
.venv\Scripts\python.exe scripts\sync_champion_art.py
```

## Avvio

```bash
.venv\Scripts\python.exe main.py
```

Oppure `avvia_driftdraft.bat`. L'app apre una finestra sulla porta 8721.
Per lavorare solo sul frontend, il server da solo basta e avanza:

```bash
.venv\Scripts\python.exe -m driftdraft.server
```

## Com'è fatto

| Percorso | Cosa contiene |
|---|---|
| `main.py` | Avvio: server in un thread + finestra pywebview |
| `driftdraft/` | Server Bottle, rilevamento comp, bot di training, valutazione draft, automazione di drafter.lol |
| `web/` | Frontend: `index.html`, `style.css`, `app.js` (nessun framework, nessun build step) |
| `data/` | `champions.xlsx` (tag e ruoli), roster, draft salvate, cache Leaguepedia |
| `assets/` | Icone di ruolo e rank; le immagini dei campioni le scarica l'app |
| `scripts/` | Sincronizzazione asset, build dell'installer, test |
| `installer/` | Script Inno Setup per il pacchetto Windows |
| `vendor/` | uBlock Origin Lite (GPL-3.0), usato dalla modalità torneo |

Il codice è commentato in italiano, e i commenti lunghi spiegano *perché* una
cosa è fatta così — spesso raccontano il tentativo fallito che ha portato alla
soluzione attuale. Vale la pena leggerli prima di "semplificare" qualcosa.

## Test

```bash
.venv\Scripts\python.exe scripts\test_training_bot.py
.venv\Scripts\python.exe scripts\test_training_bot2.py
.venv\Scripts\python.exe scripts\test_role_safety.py
.venv\Scripts\python.exe scripts\test_draft_evaluation.py
```

Girano sui dati già salvati su disco, senza rete.

## Modalità torneo: l'ad-blocker

L'estensione uBlock Origin Lite viene caricata nella finestra Chromium perché
i banner di drafter.lol finiscono sopra i bottoni di ban/pick e ne
intercettano i click. Deve essere **Lite** (Manifest V3): uBlock Origin
classico è MV2 e questo Chromium si rifiuta di caricarlo.

Per aggiornarla quando esce una versione nuova:

```bash
python scripts\fetch_adblocker.py
```

Scarica l'ultima release, la installa in `vendor/ublock-origin-lite/` e va
committata (è versionata).

## Ricostruire il pacchetto e l'installer

```bash
.venv\Scripts\python.exe -m PyInstaller driftdraft.spec --noconfirm
.venv\Scripts\python.exe scripts\build_installer.py
```

Il primo comando produce `dist/DriftDraft/` (~935 MB non compressi, di cui il
grosso è il Chromium bundlato). Il secondo lo impacchetta in
`dist/DriftDraft-v<versione>-setup.exe` (~280 MB), leggendo la versione da
`main.py` — non va scritta a mano da nessun'altra parte.

Serve **Inno Setup 6** installato (gratuito). Se manca, lo script lo dice e
suggerisce `winget install JRSoftware.InnoSetup`.

## Cosa NON è nella repo

- `.venv/`, `dist/`, `build/` — si rigenerano
- `assets/icons/`, `assets/splash/` — le immagini dei campioni: materiale di
  Riot Games che il progetto **non ridistribuisce**, le scarica l'app
- `data/roster.json`, `data/saved_drafts.json` — **dati personali**: nomi
  reali e Riot ID dei giocatori seguiti dal coach. Sono in `.gitignore` e non
  devono tornare nella repository — un commit che cancella un file non basta,
  resta leggibile nei commit precedenti. Non finiscono nemmeno nel pacchetto
  distribuito: lo spec di build li esclude esplicitamente
- `assets/Icon Pack League of Legends + Borders/`, `assets/icons_bordered_backup_*/`,
  `assets/tiermaker_refs/`, `backups/` — materiale preparato a mano, circa
  320 MB, tenuto fuori solo per dimensione
- `vendor/ublock-origin-lite/_metadata/` — ruleset che Chromium compila da
  solo al primo caricamento
