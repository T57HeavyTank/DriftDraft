"""Collaudo di DriftDraft: le funzioni dell'app e i siti da cui prende i dati.

    python scripts/collaudo.py                 # tutto
    python scripts/collaudo.py --senza-drafter # senza la draft vera su drafter.lol

Nato il 2026-10-30 su richiesta dell'utente, da ripetere circa ogni due
settimane: i siti esterni (op.gg, u.gg, lolalytics, Leaguepedia, drafter.lol)
cambiano la loro grafica o le loro API senza avvisare, e l'app se ne accorge
solo quando qualcosa smette di funzionare a meta' di una draft. Meglio
accorgersene prima.

Tre parti:

1. FUNZIONI DELL'APP. Avvia il server di DriftDraft su una porta libera e ne
   chiama le API come fa l'interfaccia: comp rilevate, pick e ban suggeriti,
   counter, team, draft salvate, tag, un allenamento completo con valutazione.
   I file che l'app SCRIVE (roster, draft salvate, tag) sono copiati in una
   cartella temporanea e il server lavora su quelle copie: i dati veri di chi
   lancia il collaudo non vengono mai toccati. Le draft pro e i dati soloQ
   invece si leggono e basta.
2. SITI ESTERNI. Le stesse funzioni che usa l'app, con i dati veri. op.gg usa
   il team di default del roster (se non c'e', quella prova e' saltata).
   Leaguepedia limita le richieste anonime: un blocco e' un avviso, non un
   errore - i dati restano quelli che c'erano e l'app riprova da sola.
3. DRAFTER.LOL. Crea una draft room di prova ("DD Collaudo"), DriftDraft entra
   dal lato blu esattamente come in modalita' torneo, e il collaudo stesso
   gioca il lato rosso da un secondo browser. Si apre una finestra del
   browser per qualche minuto: e' normale, e non va toccata.

Stampa una riga per prova (OK / AVVISO / ERRORE) e un riepilogo; esce con
codice 1 se almeno una prova e' fallita.
"""

import argparse
import json
import re
import shutil
import socket
import sys
import tempfile
import threading
import time
import traceback
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from urllib.parse import quote

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OK, AVVISO, ERRORE = "OK", "AVVISO", "ERRORE"
risultati: list[tuple[str, str, str]] = []


class Avviso(Exception):
    """Qualcosa da guardare, ma non un guasto (es. Leaguepedia ci limita)."""


def prova(nome: str, fn) -> object:
    t0 = time.time()
    try:
        dettaglio = fn()
        esito = OK
    except Avviso as e:
        esito, dettaglio = AVVISO, str(e)
    except Exception as e:  # noqa: BLE001 - un collaudo deve arrivare in fondo
        esito, dettaglio = ERRORE, f"{type(e).__name__}: {e}"
        traceback.print_exc(limit=2)
    risultati.append((nome, esito, str(dettaglio or "")))
    print(f"[{esito:6}] {nome} ({time.time() - t0:.0f}s) - {dettaglio or ''}", flush=True)
    return dettaglio


def verifica(condizione, messaggio: str) -> None:
    if not condizione:
        raise AssertionError(messaggio)


# =========================================================== 1. FUNZIONI DELL'APP
def prepara_copie() -> Path:
    """Copia i file che l'app scrive e ci dirotta i moduli che li usano."""
    from driftdraft import champion_overrides, roster, saved_drafts

    tmp = Path(tempfile.mkdtemp(prefix="driftdraft-collaudo-"))
    for f in ("roster.json", "saved_drafts.json", "champion_overrides.json"):
        sorgente = RADICE / "data" / f
        if sorgente.exists():
            shutil.copy2(sorgente, tmp / f)
    roster.ROSTER_PATH = tmp / "roster.json"
    saved_drafts.SAVED_DRAFTS_PATH = tmp / "saved_drafts.json"
    # Questi tre hanno il percorso come valore di default, fissato quando il
    # modulo si carica: va cambiato li', non nella variabile del modulo.
    finto = tmp / "champion_overrides.json"
    champion_overrides.OVERRIDES_PATH = finto
    champion_overrides.load_overrides.__defaults__ = (finto,)
    champion_overrides.save_override.__defaults__ = (None, None, None, finto)
    champion_overrides.reset_override.__defaults__ = (finto,)
    return tmp


def avvia_server() -> str:
    from driftdraft.server import run_server

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    threading.Thread(target=run_server, kwargs={"port": porta}, daemon=True).start()
    base = f"http://127.0.0.1:{porta}"
    for _ in range(60):
        try:
            urllib.request.urlopen(base + "/api/version", timeout=2).read()
            return base
        except OSError:
            time.sleep(0.5)
    raise RuntimeError("il server di prova non risponde")


def api(base: str, percorso: str, corpo=None, timeout: int = 120):
    dati = None if corpo is None else json.dumps(corpo).encode("utf-8")
    req = urllib.request.Request(base + percorso, data=dati, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        risposta = json.loads(r.read().decode("utf-8"))
    if isinstance(risposta, dict) and risposta.get("error"):
        raise AssertionError(f"{percorso}: {risposta['error']}")
    return risposta


BLU = ["Rakan", "Orianna", "Xayah"]
ROSSI = ["Xin Zhao", "Ezreal", "Braum"]


def collaudo_app(base: str) -> None:
    def campioni():
        c = api(base, "/api/champions")
        verifica(len(c) >= 160, f"solo {len(c)} campioni")
        return f"{len(c)} campioni"

    def comp():
        meta = api(base, "/api/comp-meta")
        rilevate = api(base, "/api/detect", ["Orianna", "Jarvan IV", "Miss Fortune", "Leona", "Malphite"])
        verifica(len(rilevate) == 5, "attese 5 comp")
        prese = [k for k, v in rilevate.items() if v["member_count"] > 0]
        return f"{len(meta.get('comps', meta))} comp nei metadati, rilevamento ok ({len(prese)} comp con membri)"

    def suggerimenti():
        r = api(base, "/api/pick-suggestions", {
            "bluePicks": BLU[:1], "redPicks": ROSSI[:2], "taken": [],
            "blueBans": ["Yone", "Ambessa", "Rumble"], "redBans": ["Vi", "Kalista", "Taliyah"],
        })
        blu, rossi = r["blue"]["suggestions"], r["red"]["suggestions"]
        verifica(blu and rossi, "nessun pick suggerito")
        r2 = api(base, "/api/pick-suggestions", {
            "bluePicks": BLU, "redPicks": ROSSI, "taken": [],
            "blueBans": ["Yone", "Ambessa", "Rumble"], "redBans": ["Vi", "Kalista", "Taliyah"],
        })
        ban = r2["bans"]["blue"]["bans"]
        verifica(ban and r2["bans"]["blue"]["phase"] == 2, "nessun ban di seconda fase")
        return f"pick blu {len(blu)}, rossi {len(rossi)}; ban di 2a fase {len(ban)} (es. {ban[0]['champion']}: {'; '.join(ban[0]['reasons'][:1])})"

    def counter():
        r = api(base, "/api/counters", {"champion": "Ahri", "role": "Mid", "tier": "emerald_plus"})
        verifica(len(r["counters"]) >= 5, "meno di 5 counter")
        return f"{len(r['counters'])} counter per Ahri mid (fonte: {r.get('source', 'lolalytics dal vivo')})"

    def ruoli():
        r = api(base, "/api/live-draft/role-guess", {"picks": ["Orianna", "Xayah", "Rakan", "Xin Zhao", "Gnar"]})
        return f"ruoli indovinati: {json.dumps(r, ensure_ascii=False)[:120]}"

    def roster():
        nome = "Collaudo DriftDraft"
        dati = {"Top": [{"name": "Prova", "riot_id": "", "tiers": {"S": ["Ornn"], "A": [], "B": [], "C": [], "D": []}}]}
        api(base, "/api/roster-profile", {"name": nome, "data": dati})
        letto = api(base, f"/api/roster-profile?name={quote(nome)}")
        verifica(letto["Top"][0]["tiers"]["S"] == ["Ornn"], "il profilo riletto non coincide")
        api(base, "/api/roster-profile-rename", {"old_name": nome, "new_name": nome + " 2"})
        api(base, "/api/roster-profile-delete", {"name": nome + " 2"})
        rimasti = api(base, "/api/roster-profiles")
        verifica(nome + " 2" not in rimasti["profiles"], "il profilo non e' stato cancellato")
        return "salva, rileggi, rinomina, cancella (su una copia)"

    def draft_salvate():
        prima = len(api(base, "/api/saved-drafts")["drafts"])
        voce = api(base, "/api/saved-drafts", {"name": "Collaudo", "champions": ["Ornn", "Vi", "Orianna", "Xayah", "Rakan"]})
        verifica(len(voce["drafts"]) == prima + 1, "la draft non risulta salvata")
        dopo = api(base, "/api/saved-drafts-delete", {"id": voce["added"]["id"]})
        verifica(len(dopo["drafts"]) == prima, "la draft non e' stata cancellata")
        return "salva e cancella (su una copia)"

    def tag():
        api(base, "/api/champion-tags", {"champion": "Ahri", "tags": ["Mobilità"]})
        ahri = next(c for c in api(base, "/api/champions") if c["name"] == "Ahri")
        verifica(ahri.get("tags") == ["Mobilità"] or "Mobilità" in json.dumps(ahri, ensure_ascii=False), "la modifica ai tag non si vede")
        api(base, "/api/champion-tags/reset", {"champion": "Ahri"})
        return "modifica e ripristina (su una copia)"

    for nome, fn in [
        ("App: campioni", campioni),
        ("App: comp rilevate", comp),
        ("App: pick e ban suggeriti", suggerimenti),
        ("App: ricerca counter (dati soloQ locali)", counter),
        ("App: ruoli indovinati", ruoli),
        ("App: team e tier list", roster),
        ("App: draft salvate", draft_salvate),
        ("App: tag campioni", tag),
    ]:
        prova(nome, fn)

    def allenamento():
        squadre = api(base, "/api/training/teams")["teams"]
        verifica(len(squadre) >= 50, f"solo {len(squadre)} squadre pro")
        nomi = [s["name"] for s in squadre]
        squadra = "T1" if "T1" in nomi else nomi[0]
        st = api(base, "/api/training/start", {"mode": "team", "side": "blue", "team": squadra, "series": 1})
        nostri = ["Yone", "Ambessa", "Rumble", "Orianna", "Rakan", "Xayah", "Azir", "Sejuani", "Varus",
                  "Nautilus", "Kai'Sa", "Taliyah", "Gnar", "Vi", "Ahri", "Jax", "Ornn", "Leona"]
        for _ in range(40):
            if st.get("finished"):
                break
            usati = {x for x in st["bluePicks"] + st["redPicks"] + st["blueBans"] + st["redBans"] if x}
            scelta = next(n for n in nostri if n not in usati)
            st = api(base, "/api/training/pick", {"champion": scelta})
        verifica(st.get("finished"), "la draft di allenamento non e' finita")
        ordine = [st["roleAssignment"]["blue"]["assignment"][r]["champion"] for r in ("Top", "Jungle", "Mid", "Bot", "Support")]
        api(base, "/api/training/assign-roles", {"order": ordine})
        return st, squadra

    def allenamento_riassunto():
        st, squadra = allenamento()
        return f"contro {squadra}, il bot ha scelto {', '.join(st['redPicks'])}; ruoli assegnati"

    prova("App: allenamento contro una squadra pro (draft completa)", allenamento_riassunto)


# ============================================================== 2. SITI ESTERNI
def collaudo_siti(base: str) -> None:
    from driftdraft import champion_art, leaguepedia, lolalytics, opgg, soloq, ugg, updater

    def titolari():
        d = json.loads((RADICE / "data" / "roster.json").read_text(encoding="utf-8"))
        nome = d.get("default")
        if not nome or nome not in d.get("profiles", {}):
            raise Avviso("nessun team di default nel roster: prova saltata")
        prof = d["profiles"][nome]
        ids = [prof[r][0]["riot_id"] for r in ("Top", "Jungle", "Mid", "Bot", "Support") if prof.get(r) and prof[r][0].get("riot_id")]
        if not ids:
            raise Avviso("il team di default non ha Riot ID: prova saltata")
        return ids

    def opgg_multi():
        ids = titolari()
        url = "https://op.gg/it/lol/multisearch/euw?summoners=" + quote(",".join(ids), safe=",")
        giocatori = opgg.fetch_team_pool(url, ids)
        verifica(len(giocatori) == len(ids), f"colonne abbinate {len(giocatori)}/{len(ids)}")
        verifica(all(g.champions for g in giocatori), "qualche giocatore senza campioni")
        verifica(any(g.roles for g in giocatori), "nessuna corsia riconosciuta (icone cambiate?)")
        return f"{len(giocatori)} giocatori, {sum(len(g.champions) for g in giocatori)} campioni, corsie lette"

    def opgg_profilo():
        p = opgg.fetch_player_champions("euw", titolari()[0])
        partite = sum(c.games for c in p.champions)
        verifica(p.champions and partite > 0, "nessun campione o partite a zero")
        return f"{len(p.champions)} campioni, {partite} partite"

    def ugg_counter():
        e = ugg.fetch_lane_counters("Ahri", "Mid")
        verifica(len(e) >= 5, f"solo {len(e)} righe")
        return f"{len(e)} avversari (primo: {e[0].champion} GD15 {e[0].gd15:+d})"

    def lola_counter():
        e = lolalytics.fetch_counters("Ahri", "Mid")
        verifica(len(e) >= 5, f"solo {len(e)} righe")
        return f"{len(e)} counter"

    def lola_curva():
        c = lolalytics.fetch_winrate_curve("Ahri", "Mid")
        verifica(len(c) >= 5, "curva incompleta")
        return " ".join(f"{p.bucket}:{p.winrate:.0f}" for p in c)

    def lola_api():
        raw = soloq._get(soloq._base("ahri"))
        st, cs = raw.get("stats") or {}, raw.get("counters") or []
        verifica(st.get("lane") and st.get("lanes") and cs, "pagina counter senza stats o counter")
        verifica({"cid", "n", "d2", "vsWr"} <= set(cs[0]), f"campi counter cambiati: {sorted(cs[0])}")
        team = ((soloq._get({**soloq._base("thresh"), "ep": "build-team", "lane": "support"}).get("team") or {}).get("bottom")) or []
        verifica(team and len(team[0]) >= 6, "compagni dei support assenti o cambiati")
        return f"counter {len(cs)}, compagni bot di Thresh {len(team)}"

    def leaguepedia_nuove():
        leaguepedia._cargo_request = partial(leaguepedia._cargo_request, max_attempts=2)
        da = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            drafts, _ = leaguepedia.fetch_drafts_since(da, limit=500)
        except RuntimeError as e:
            raise Avviso(f"Leaguepedia ci sta limitando ({e}); i dati restano quelli che c'erano") from e
        recenti = sorted(d.date for d in drafts if d.date)
        if not drafts:
            raise Avviso("nessuna partita pro negli ultimi 3 giorni (pausa fra un torneo e l'altro?)")
        return f"{len(drafts)} draft negli ultimi 3 giorni, l'ultima {recenti[-1]}"

    def immagini():
        v = champion_art._fetch_json(champion_art.DDRAGON_VERSIONS_URL)[0]
        icona = champion_art._fetch_bytes(f"https://ddragon.leagueoflegends.com/cdn/{v}/img/champion/Ahri.png")
        splash = champion_art._fetch_bytes("https://cdn.communitydragon.org/latest/champion/Ahri/splash-art/centered")
        verifica(icona[:4] == b"\x89PNG" and len(splash) > 50000, "icona o splash non validi")
        return f"Data Dragon {v}, icona e splash ok"

    def github():
        c = updater.check()
        verifica(not c.get("error"), c.get("error"))
        verifica(c.get("asset"), "l'ultima release non ha l'installer")
        return f"ultima release v{c['latest']} ({c['asset']['name']}), qui v{c['current']}"

    def valutazione():
        r = api(base, "/api/training/evaluate", {"tier": "emerald_plus"}, timeout=180)
        verifica(len(r.get("green") or []) >= 5, "valutazione senza curva")
        errori = r.get("laneErrors") or []
        if errori:
            raise Avviso(f"valutazione fatta, ma con {len(errori)} curve mancanti: {errori[0]}")
        return "curve di tutte e 5 le corsie scaricate, previsione " + " ".join(f"{v:.0f}" for v in r["green"])

    for nome, fn in [
        ("op.gg: link multisearch del team di default", opgg_multi),
        ("op.gg: profilo di un giocatore", opgg_profilo),
        ("u.gg: counter di corsia", ugg_counter),
        ("lolalytics: counter (pagina)", lola_counter),
        ("lolalytics: curva winrate per durata", lola_curva),
        ("lolalytics: API dei dati soloQ", lola_api),
        ("Leaguepedia: partite nuove", leaguepedia_nuove),
        ("Riot: immagini dei campioni", immagini),
        ("GitHub: controllo aggiornamenti", github),
        ("lolalytics: valutazione della draft di allenamento", valutazione),
    ]:
        prova(nome, fn)


# =============================================================== 3. DRAFTER.LOL
GIOCA_ROSSO_JS = r"""
(mossa) => {
  const btn = document.getElementById('draft-button');
  const step = (document.getElementById('step-name')?.textContent || '');
  const testo = (btn?.textContent || '').trim();
  if (!btn || btn.disabled || !/red/i.test(step) || !['Ban', 'Pick'].includes(testo)) return {fatto: false, step, testo};
  const norm = s => (s || '').replace(/[^A-Za-z]/g, '').toLowerCase();
  const img = [...document.querySelectorAll('img')].find(i => norm(i.alt) === norm(mossa) && /champions(%2F|\/)\d+(-\d+)?\.(png|webp)/.test(i.src));
  if (!img) {
    const tutte = [...document.querySelectorAll('img')];
    const esempi = tutte.filter(i => i.alt).slice(0, 4).map(i => i.alt + ' <' + (i.currentSrc || i.src).slice(0, 70) + '>');
    return {fatto: false, step, testo, errore: 'campione non trovato: ' + mossa + ' (immagini nella pagina: ' + tutte.length + ', es. ' + esempi.join(' | ') + ')'};
  }
  img.parentElement.click();
  return {fatto: true, step, testo};
}
"""


def collaudo_drafter() -> None:
    from playwright.sync_api import sync_playwright

    from driftdraft.drafter_live import LiveDraftSession

    blu_team, rosso_team = "DD Collaudo Blu", "DD Collaudo Rosso"
    mosse_blu = ["Ziggs", "Yasuo", "LeBlanc", "Kai'Sa", "Orianna", "Thresh", "Gwen", "Kalista", "Darius", "Wukong"]
    mosse_rosse = ["Zed", "Akali", "Sylas", "Aatrox", "Lee Sin", "Braum", "Katarina", "Fizz", "Jinx", "Ahri"]
    ordine_ruoli = ["Darius", "Wukong", "Orianna", "Kai'Sa", "Thresh"]

    from driftdraft.opgg import _USER_AGENT

    with sync_playwright() as p:
        # Come per op.gg: con l'impronta di automazione di default drafter.lol
        # restituisce una pagina bianca (verificato il 2026-10-30).
        browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
        page = browser.new_context(viewport={"width": 1280, "height": 900}, user_agent=_USER_AGENT).new_page()

        def rifiuta_cookie(attesa: int) -> None:
            try:
                page.click('button:has-text("Do not consent")', timeout=attesa)
            except Exception:  # noqa: BLE001 - il banner non sempre compare
                pass

        # Il lato rosso: crea la stanza, entra, gioca. Il banner dei cookie
        # puo' comparire anche DOPO il click su Create Draft e svuotare i
        # nomi gia' scritti (successo a mano): per questo il secondo giro.
        page.goto("https://drafter.lol/", wait_until="domcontentloaded")
        page.wait_for_selector('input[placeholder="Team 1"]', timeout=30000)
        rifiuta_cookie(5000)
        for _ in range(2):
            page.fill('input[placeholder="Team 1"]', blu_team)
            page.fill('input[placeholder="Team 2"]', rosso_team)
            page.click("text=Create Draft")
            rifiuta_cookie(3000)
            try:
                page.wait_for_url("**/draft/**", timeout=15000)
                break
            except Exception:  # noqa: BLE001
                continue
        url = page.url
        verifica("/draft/" in url, f"stanza non creata (pagina: {url})")
        prova("drafter.lol: creazione della draft room di prova", lambda: url)

        sessione = LiveDraftSession()
        try:
            def entra_blu():
                opzioni = sessione.connect(url)
                verifica(opzioni.get("present"), f"dialogo di ingresso non letto: {opzioni}")
                nomi = [t["name"] for t in opzioni.get("teams", [])]
                verifica(blu_team in nomi, f"team letti: {nomi}")
                sessione.join_options(blu_team)
                esito = sessione.join(blu_team, "blue")
                verifica(esito.get("joined"), f"ingresso non riuscito: {esito}")
                return f"team letti dalla stanza: {nomi}"

            prova("drafter.lol: DriftDraft entra dal lato blu", entra_blu)

            page.click(f"text={rosso_team}", timeout=15000)
            page.click("text=Red drafter", timeout=15000)
            for testo in ("Got it", "Maybe later", "Not now"):
                try:
                    page.click(f'button:has-text("{testo}")', timeout=1500)
                except Exception:  # noqa: BLE001
                    pass

            def gioca():
                mossa_b = mossa_r = 0
                pronto_rosso = pronto_ruoli_rosso = ruoli_blu = ruoli_rosso = pronto_ruoli_blu = False
                inizio = time.time()
                while time.time() - inizio < 420:
                    st = sessione.read_state()
                    verifica(st.get("connected"), f"DriftDraft disconnesso: {st}")
                    testo = (st.get("buttonText") or "").strip()
                    step = (st.get("step") or "").lower()
                    # lato blu: esattamente le chiamate della modalita' torneo
                    if testo == "Ready":
                        sessione.click_ready()
                    elif "blue" in step and testo in ("Ban", "Pick") and mossa_b < len(mosse_blu):
                        kind = "ban" if testo == "Ban" else "pick"
                        sospesi = st.get("blueBansPending" if kind == "ban" else "bluePicksPending") or []
                        sessione.select_champion(mosse_blu[mossa_b])
                        time.sleep(0.6)
                        sessione.confirm_selection("blue", kind, sospesi.index(True) if True in sospesi else 0)
                        mossa_b += 1
                    elif "ready for role confirmation" in testo.lower() and not pronto_ruoli_blu:
                        sessione.click_ready()
                        pronto_ruoli_blu = True
                    elif st.get("roleConfirmActive") and "confirm roles" in testo.lower() and not ruoli_blu:
                        r = sessione.confirm_role_order(ordine_ruoli)
                        verifica(all(d.get("ok") for d in r.get("dragResults", [])), f"trascinamento ruoli: {r}")
                        ruoli_blu = True
                    if ruoli_blu and any(st.get("blueRoleTags") or []):
                        return st
                    # lato rosso, dal secondo browser
                    bottone = page.locator("#draft-button")
                    rt = (bottone.text_content(timeout=2000) or "").strip() if bottone.count() else ""
                    if rt == "Ready" and not pronto_rosso:
                        bottone.click()
                        pronto_rosso = True
                    elif rt in ("Ban", "Pick") and mossa_r < len(mosse_rosse) and not bottone.is_disabled():
                        # Dalla casella di ricerca del sito, come farebbe una
                        # persona: la griglia carica i campioni solo quando
                        # entrano in vista, e Zed non c'era (2026-10-30).
                        ricerca = page.locator('input[placeholder="Search champions"]')
                        ricerca.fill(mosse_rosse[mossa_r])
                        time.sleep(0.6)
                        r = page.evaluate(GIOCA_ROSSO_JS, mosse_rosse[mossa_r])
                        if r.get("fatto"):
                            time.sleep(0.5)
                            bottone.click()
                            ricerca.fill("")
                            mossa_r += 1
                        elif r.get("errore") and "red" in (r.get("step") or "").lower():
                            foto = Path(tempfile.gettempdir()) / "driftdraft-collaudo-drafter.png"
                            page.screenshot(path=str(foto))
                            raise AssertionError(f"{r['errore']} - schermata del lato rosso: {foto}")
                    elif "ready for role confirmation" in rt.lower() and not pronto_ruoli_rosso:
                        bottone.click()
                        # Il riquadro "Role confirmation has changed" (dal
                        # 2026-10-30), apostrofo tipografico compreso.
                        try:
                            page.get_by_role("button", name=re.compile(r"Got it, I.m ready")).click(timeout=5000)
                        except Exception:  # noqa: BLE001
                            pass
                        pronto_ruoli_rosso = True
                    elif rt.lower() == "confirm roles" and not ruoli_rosso:
                        bottone.click()
                        ruoli_rosso = True
                    time.sleep(0.4)
                foto = Path(tempfile.gettempdir()) / "driftdraft-collaudo-drafter.png"
                page.screenshot(path=str(foto))
                raise AssertionError(
                    f"draft non finita in 7 minuti (blu {mossa_b}/10, rosso {mossa_r}/10). Ultimo stato letto da "
                    f"DriftDraft: step={st.get('step')!r} bottone={st.get('buttonText')!r} "
                    f"ruoliLive={st.get('roleConfirmActive')} badge={st.get('blueRoleTags')}; bottone rosso={rt!r}; "
                    f"pronto/conferma rosso={pronto_ruoli_rosso}/{ruoli_rosso}, blu={pronto_ruoli_blu}/{ruoli_blu}; schermata: {foto}"
                )

            def draft_completa():
                st = gioca()
                verifica([x for x in st.get("bluePicks") or [] if x] and len([x for x in st["bluePicks"] if x]) == 5, f"pick blu letti: {st.get('bluePicks')}")
                verifica(len([x for x in st.get("redPicks") or [] if x]) == 5, f"pick rossi letti: {st.get('redPicks')}")
                verifica(len([x for x in st.get("blueBans") or [] if x]) == 5, f"ban blu letti: {st.get('blueBans')}")
                ruoli = dict(zip(st["bluePicks"], st["blueRoleTags"]))
                verifica(ruoli.get("Darius") == "Top" and ruoli.get("Thresh") == "Support", f"ruoli blu: {ruoli}")
                return f"10 ban e 10 pick letti, ruoli blu {ruoli}"

            prova("drafter.lol: draft completa (ban, pick, conferma ruoli)", draft_completa)
        finally:
            sessione.disconnect()
            browser.close()


# ===================================================================== avvio
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--senza-drafter", action="store_true", help="salta la draft vera su drafter.lol")
    parser.add_argument("--solo-drafter", action="store_true", help="solo la draft vera su drafter.lol")
    args = parser.parse_args()
    if args.solo_drafter:
        try:
            collaudo_drafter()
        except Exception as e:  # noqa: BLE001
            risultati.append(("drafter.lol", ERRORE, f"{type(e).__name__}: {e}"))
            traceback.print_exc(limit=3)
        return riepilogo()

    print(f"Collaudo DriftDraft - {datetime.now():%d/%m/%Y %H:%M}\n", flush=True)

    def dizionari():
        lang = RADICE / "web" / "lang"
        en = json.loads((lang / "en.json").read_text(encoding="utf-8"))
        diverse = []
        for f in sorted(lang.glob("*.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            if set(d["testi"]) != set(en["testi"]) or set(d["frammenti"]) != set(en["frammenti"]):
                diverse.append(f.name)
        verifica(not diverse, f"chiavi diverse da en.json in: {diverse}")
        return f"{len(list(lang.glob('*.json')))} lingue, {len(en['testi'])} frasi ciascuna"

    prova("Lingue: dizionari allineati", dizionari)

    copie = prepara_copie()
    try:
        base = avvia_server()
        collaudo_app(base)
        collaudo_siti(base)
        if not args.senza_drafter:
            try:
                collaudo_drafter()
            except Exception as e:  # noqa: BLE001
                risultati.append(("drafter.lol", ERRORE, f"{type(e).__name__}: {e}"))
                traceback.print_exc(limit=3)
    finally:
        shutil.rmtree(copie, ignore_errors=True)
    return riepilogo()


def riepilogo() -> int:
    print("\n================ RIEPILOGO ================")
    for nome, esito, dettaglio in risultati:
        if esito != OK:
            print(f"[{esito}] {nome}: {dettaglio}")
    n = {e: sum(1 for _, x, _ in risultati if x == e) for e in (OK, AVVISO, ERRORE)}
    print(f"{n[OK]} ok, {n[AVVISO]} avvisi, {n[ERRORE]} errori su {len(risultati)} prove")
    return 1 if n[ERRORE] else 0


if __name__ == "__main__":
    sys.exit(main())
