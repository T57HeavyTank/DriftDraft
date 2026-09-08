# Riconoscimenti e provenienza dei dati

DriftDraft è distribuito sotto **GPL-3.0** (vedi [LICENSE](LICENSE)). Questo
documento elenca tutto ciò che il progetto **non** ha scritto: software di
terzi spedito insieme all'applicazione, librerie, immagini e dati.

Dove è scritto *verificato*, la licenza è stata letta dal pacchetto installato
o dal file incluso nella repo. Dove è scritto *da confermare*, va controllata
sui termini correnti del servizio prima di una distribuzione pubblica: quelle
condizioni cambiano nel tempo e non dipendono da noi.

---

## Software di terzi spedito dentro il pacchetto

### uBlock Origin Lite — GPL-3.0 *(verificato)*

`vendor/ublock-origin-lite/`, di Raymond Hill (gorhill).
Release ufficiale **non modificata**, presa da
<https://github.com/uBlockOrigin/uBOL-home/releases>, con il suo `LICENSE.txt`
incluso nella cartella.

Serve solo alla modalità torneo: viene caricata come estensione da Chromium
per togliere la pubblicità dalle pagine di drafter.lol. **Non è collegata al
codice di DriftDraft** — è un programma separato che carica il browser, ed è
opzionale (se la cartella manca, l'applicazione parte lo stesso senza
ad-blocking). Il sorgente corrispondente è quello della release upstream
linkata sopra.

### Chromium — BSD-3-Clause e altre *(da confermare)*

Scaricato e gestito da Playwright, spedito dentro il pacchetto perché le
integrazioni con op.gg, lolalytics e drafter.lol hanno bisogno di un browser
vero. È la parte più grande del pacchetto (~430 MB). Le licenze complete sono
consultabili da `chrome://credits` nel browser stesso.

## Librerie Python

| Libreria | Versione | Licenza |
|---|---|---|
| bottle | 0.13.4 | MIT *(verificato)* |
| openpyxl | 3.1.5 | MIT *(verificato)* |
| playwright | 1.62.0 | Apache-2.0 *(verificato)* |
| pywebview | 6.2.1 | BSD-3-Clause *(verificato)* |
| pillow | 12.3.0 | MIT-CMU *(verificato)* |
| numpy | 2.5.2 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 *(verificato)* |

## Immagini dei campioni — NON ridistribuite

Icone e splash art dei campioni sono materiale di **Riot Games**, e questo
progetto **non le ridistribuisce**: non stanno nella repository e non stanno
nel pacchetto.

L'applicazione le scarica al primo avvio sul computer di chi la usa, dai CDN
di riferimento — **Data Dragon** (`ddragon.leagueoflegends.com`, ufficiale
Riot) per le icone e **Community Dragon** (<https://communitydragon.org>) per
le splash art centrate. Chi usa DriftDraft prende quelle immagini dalla fonte,
come farebbe aprendo il sito.

Vedi `driftdraft/champion_art.py`. Le uniche immagini che restano nel
pacchetto sono le icone generiche di ruolo e di rank, che non sono materiale
Riot.

## Dati delle draft pro

`data/leaguepedia_drafts.json` e `data/leaguepedia_tables.json` sono ricavati
da **Leaguepedia** (`lol.fandom.com`), wiki di Fandom, tramite la sua API
pubblica.

Il contenuto di Leaguepedia è pubblicato sotto **Creative Commons
Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)** *(verificato sulla loro
pagina Copyrights)*.

**Questi dati NON sono coperti dalla GPL-3 del resto del progetto**, e non
potrebbero esserlo: CC BY-SA 3.0 e GPL-3 sono due licenze copyleft
incompatibili fra loro. `data/leaguepedia_drafts.json` è un'estrazione
sostanziale della loro raccolta e resta sotto **CC BY-SA 3.0, con attribuzione
a Leaguepedia**; chi lo ridistribuisce deve farlo alle stesse condizioni.

`data/leaguepedia_tables.json` contiene invece conteggi aggregati ricavati da
quei dati (quante volte due campioni sono comparsi insieme, e simili), non una
copia delle pagine.

## Servizi interrogati dal vivo

Non ridistribuiti: l'applicazione li apre nel momento in cui l'utente lo
chiede, con le sue credenziali quando servono.

- **op.gg** — pool di campioni di giocatori e squadre
- **lolalytics** — curve di winrate e counter
- **u.gg** — dati di supporto
- **drafter.lol** — la draft room vera della modalità torneo

*(da confermare: i termini d'uso di ciascuno, in particolare sull'accesso
automatizzato.)*

## Lavoro originale

`data/champions.xlsx` — i tag funzionali di tutti i campioni e le cinque
composizioni (TeamFight/WomboCombo, Pick, Proteggi il presidente, Poke/Siege,
Split), con i loro requisiti e la matrice dei counter naturali, sono **lavoro
originale dell'autore di DriftDraft**, compilato a mano. Sono coperti dalla
GPL-3 come il resto del progetto.

---

## Nota legale Riot Games

Questo è il testo che la policy "Legal Jibber Jabber" di Riot **richiede** ai
progetti amatoriali, ed è diverso dal disclaimer generico usato in giro:

DriftDraft was created under Riot Games' "Legal Jibber Jabber" policy using
assets owned by Riot Games. Riot Games does not endorse or sponsor this
project.

*In italiano: DriftDraft è stato creato secondo la policy "Legal Jibber
Jabber" di Riot Games, usando materiali di proprietà di Riot Games. Riot Games
non approva né sponsorizza questo progetto.*

**Questione nota**: la stessa policy vieta l'uso della IP di Riot dentro
*giochi e applicazioni*, e indica come strada per gli strumenti una chiave API
concessa per il progetto specifico. DriftDraft è un'applicazione desktop.

Per ridurre il più possibile la sovrapposizione, il progetto **ha smesso di
ridistribuire materiale Riot** (vedi la sezione sulle immagini): non spedisce
icone né splash art, le scarica l'utente dalla fonte. Resta il fatto che è
un'applicazione, e questo va valutato da chi la pubblica.
