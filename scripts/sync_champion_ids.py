"""Sincronizza la colonna "ID" (ID campione Riot/CommunityDragon) nell'xlsx
sorgente con i dati campioni.

Perche' esiste: drafter.lol mostra i campioni BANNATI solo come icona (senza
nome in chiaro nel DOM, verificato 2026-08-17 - vedi drafter_live.py), e
l'unico identificatore disponibile e' l'ID numerico Riot incorporato nell'URL
dell'immagine. Questo ID e' stabile e proviene dalla stessa fonte delle icone
gia' usate nel progetto (raw.communitydragon.org), quindi va tenuto
nell'xlsx come gli altri dati a livello di campione (regola gia' in vigore:
solo dati generici del campione nell'xlsx, mai dati giocatore/team).

Quando rilanciarlo: ogni volta che LoL introduce nuovi campioni e vengono
aggiunti a mano all'xlsx (stessa occasione in cui si ritaggano manualmente) -
questo script si limita a COMPLETARE la colonna ID per righe che la hanno
vuota o mancante, non tocca nient'altro nell'xlsx.

Uso: python scripts/sync_champion_ids.py [percorso_xlsx] [--force]
Default: C:\\Users\\Tank\\Desktop\\tag DriftDraft.xlsx
--force sovrascrive anche le righe che hanno gia' un ID (di norma lo
script tocca solo le righe vuote) - serve solo per correggere dati gia'
scritti male, come nel caso del 2026-08-17 (vedi fetch_champion_id_map).

ATTENZIONE - gotcha gia' noto in questo progetto: aprire l'xlsx con
openpyxl.load_workbook().save() CANCELLA le 173 immagini incorporate
silenziosamente. Questo script non usa MAI openpyxl per scrivere - modifica
solo xl/worksheets/sheet1.xml dentro lo zip via ElementTree, ricopiando ogni
altra parte del pacchetto byte per byte, esattamente come gia' fatto per le
colonne ruolo (Top/Jungle/Mid/Bot/Support).
"""

import re
import shutil
import sys
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

CHAMPION_SUMMARY_URL = (
    "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/"
    "global/default/v1/champion-summary.json"
)

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("", NS)
# Le altre 4 namespace usate nel foglio (mc/xr/x14ac/r) - senza registrarle
# ElementTree le rinomina in prefissi generici auto-generati (ns0/ns1/ns2/...)
# al momento di riscrivere il file con ET.tostring() piu' sotto. BUG REALE
# TROVATO 2026-08-20 (l'utente non riusciva piu' ad aprire l'xlsx in Excel,
# "Si e' verificato un problema con una parte del contenuto... Parte
# /xl/worksheets/sheet1.xml con errore XML"): mancavano proprio queste 4
# registrazioni - un run precedente di QUESTO script (o di uno script simile
# usato per le colonne ruolo) aveva gia' rinominato tutto in ns1-ns4, e la
# corruzione sarebbe stata reintrodotta AD OGNI futuro rilancio (es. quando
# esce un nuovo campione) senza questo fix.
ET.register_namespace("mc", "http://schemas.openxmlformats.org/markup-compatibility/2006")
ET.register_namespace("xr", "http://schemas.microsoft.com/office/spreadsheetml/2014/revision")
ET.register_namespace("x14ac", "http://schemas.microsoft.com/office/spreadsheetml/2009/9/ac")
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")


def _tag(name: str) -> str:
    return f"{{{NS}}}{name}"


def fetch_champion_id_map() -> dict[str, int]:
    """Nome campione (esatto, stessa convenzione gia' usata nell'xlsx) -> ID Riot.

    BUG TROVATO in un test reale (2026-08-17): 61 campioni su 173 (tutti
    quelli con ID "classico" basso, es. Vayne=67, Heimerdinger=74, Annie=1)
    compaiono DUE VOLTE in questo file - una volta con l'ID vero, una volta
    con lo stesso ID + 60000 (es. 60067, 60074, 60001 - scopo della voce
    duplicata sconosciuto, forse dati per una modalita' di gioco diversa).
    Una prima versione di questa funzione (semplice dict comprehension)
    teneva l'ULTIMA voce incontrata per nome, che nella lista finiva quasi
    sempre per essere quella sbagliata (+60000) - i ban su drafter.lol
    letti tramite quell'ID (".../champion-icons/<id>.png") non trovavano
    piu' corrispondenza nell'xlsx per questi 61 campioni, sparendo dalla
    UI. Fix: a parita' di nome, tiene sempre l'ID PIU' BASSO.
    """
    import json

    # Senza uno User-Agent realistico CommunityDragon risponde 403 (stessa
    # protezione anti-bot generica gia' vista con op.gg in questo progetto).
    req = urllib.request.Request(
        CHAMPION_SUMMARY_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)

    id_by_name: dict[str, int] = {}
    for c in data:
        champ_id = c.get("id", -1)
        if champ_id <= 0:
            continue
        name = c["name"]
        if name not in id_by_name or champ_id < id_by_name[name]:
            id_by_name[name] = champ_id
    return id_by_name


def load_shared_strings(z: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    out = []
    for si in root.findall(_tag("si")):
        # una stringa condivisa puo' essere <t>...</t> diretto o piu' <r><t>...</t></r>
        t = si.find(_tag("t"))
        if t is not None:
            out.append(t.text or "")
        else:
            out.append("".join(r.findtext(_tag("t")) or "" for r in si.findall(_tag("r"))))
    return out


def cell_text(cell: ET.Element, shared: list[str]) -> str | None:
    if cell is None:
        return None
    t = cell.get("t")
    if t == "s":
        v = cell.findtext(_tag("v"))
        return shared[int(v)] if v is not None else None
    if t == "inlineStr":
        return cell.findtext(f"{_tag('is')}/{_tag('t')}")
    return cell.findtext(_tag("v"))


def col_letter(ref: str) -> str:
    return re.match(r"[A-Z]+", ref).group()


def sync(xlsx_path: Path, force: bool = False) -> None:
    if not xlsx_path.exists():
        raise SystemExit(f"File non trovato: {xlsx_path}")

    print("Scarico l'elenco campioni/ID da CommunityDragon...")
    id_by_name = fetch_champion_id_map()
    print(f"  {len(id_by_name)} campioni ricevuti.")

    backup_dir = Path(__file__).resolve().parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / f"tag DriftDraft - backup pre-id-sync {datetime.now():%Y%m%d-%H%M%S}.xlsx"
    shutil.copy2(xlsx_path, backup_path)
    print(f"Backup salvato in: {backup_path}")

    with zipfile.ZipFile(xlsx_path) as z:
        shared = load_shared_strings(z)
        sheet_xml = z.read("xl/worksheets/sheet1.xml")
        other_entries = [n for n in z.namelist() if n != "xl/worksheets/sheet1.xml"]
        other_data = {n: z.read(n) for n in other_entries}

    root = ET.fromstring(sheet_xml)
    sheet_data = root.find(_tag("sheetData"))

    rows = sheet_data.findall(_tag("row"))

    # BUG TROVATO in un test reale (2026-08-17): la versione precedente
    # calcolava sempre "l'ultima colonna presente + 1", senza controllare
    # se una colonna "ID" esistesse gia' - un secondo lancio (per
    # correggere dati sbagliati con --force) creava una colonna "ID"
    # DUPLICATA invece di aggiornare quella esistente. Fix: cerca prima nel
    # RIGA 1 una cella il cui testo sia gia' "ID" e riusa quella colonna;
    # solo se non esiste ne calcola una nuova (stessa logica di prima,
    # "ultima colonna + 1").
    header_row = next((row for row in rows if row.get("r") == "1"), None)
    new_col = None
    if header_row is not None:
        for cell in header_row.findall(_tag("c")):
            if cell_text(cell, shared) == "ID":
                new_col = col_letter(cell.get("r"))
                break

    if new_col is None:
        last_col_letter = "A"
        for row in rows:
            cells = row.findall(_tag("c"))
            if cells:
                last = col_letter(cells[-1].get("r"))
                if len(last) > len(last_col_letter) or (len(last) == len(last_col_letter) and last > last_col_letter):
                    last_col_letter = last
        # colonna successiva (assume A-Z poi AA-AZ, sufficiente per questo file)
        if len(last_col_letter) == 1:
            new_col = "A" + last_col_letter if last_col_letter == "Z" else chr(ord(last_col_letter) + 1)
        else:
            new_col = last_col_letter[0] + chr(ord(last_col_letter[1]) + 1)
        print(f"Nessuna colonna 'ID' trovata, ne creo una nuova in: {new_col}")
    else:
        print(f"Colonna 'ID' gia' esistente trovata in: {new_col} (verra' aggiornata, non duplicata)")

    matched, missing, already = 0, [], 0
    for row in rows:
        r = int(row.get("r"))
        cells = {c.get("r"): c for c in row.findall(_tag("c"))}
        existing_id_cell = cells.get(f"{new_col}{r}")

        if r == 1:
            if existing_id_cell is None:
                header = ET.SubElement(row, _tag("c"))
                header.set("r", f"{new_col}1")
                header.set("t", "inlineStr")
                is_el = ET.SubElement(header, _tag("is"))
                t_el = ET.SubElement(is_el, _tag("t"))
                t_el.text = "ID"
            continue

        name_cell = cells.get(f"B{r}")
        name = cell_text(name_cell, shared)
        if not name:
            continue

        if not force and existing_id_cell is not None and existing_id_cell.findtext(_tag("v")):
            already += 1
            continue  # gia' valorizzata, non sovrascrivere (salvo --force)

        champ_id = id_by_name.get(name)
        if champ_id is None:
            missing.append(name)
            continue

        if existing_id_cell is None:
            id_cell = ET.SubElement(row, _tag("c"))
            id_cell.set("r", f"{new_col}{r}")
        else:
            id_cell = existing_id_cell
            old_v = id_cell.find(_tag("v"))
            if old_v is not None:
                # --force su una cella gia' valorizzata: aggiorna il valore
                # esistente invece di aggiungerne un secondo (un <c> con due
                # <v> non e' un xlsx valido).
                old_v.text = str(champ_id)
                matched += 1
                continue
        v_el = ET.SubElement(id_cell, _tag("v"))
        v_el.text = str(champ_id)
        matched += 1

    # dimension + col width, cosi' Excel/openpyxl riconoscono subito la nuova colonna
    dim = root.find(_tag("dimension"))
    if dim is not None:
        dim.set("ref", re.sub(r"[A-Z]+(?=\d+$)", new_col, dim.get("ref")))
    cols_el = root.find(_tag("cols"))
    if cols_el is not None:
        col_idx = 0
        for ch in new_col:
            col_idx = col_idx * 26 + (ord(ch) - ord("A") + 1)
        new_col_def = ET.SubElement(cols_el, _tag("col"))
        new_col_def.set("min", str(col_idx))
        new_col_def.set("max", str(col_idx))
        new_col_def.set("width", "10")
        new_col_def.set("customWidth", "1")

    new_sheet_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n' + ET.tostring(
        root, encoding="unicode"
    ).encode("utf-8")

    tmp_path = xlsx_path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in other_data.items():
            out.writestr(name, data)
        out.writestr("xl/worksheets/sheet1.xml", new_sheet_xml)
    tmp_path.replace(xlsx_path)

    print(f"Righe aggiornate con un nuovo ID: {matched}")
    print(f"Righe gia' con ID (lasciate intatte): {already}")
    if missing:
        print(f"ATTENZIONE - campioni nell'xlsx senza corrispondenza su CommunityDragon: {missing}")
    print("Fatto.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv[1:]
    target = Path(args[0]) if args else Path(r"C:\Users\Tank\Desktop\tag DriftDraft.xlsx")
    sync(target, force=force)
