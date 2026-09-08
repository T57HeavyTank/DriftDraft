; Installer Windows per DriftDraft — Inno Setup 6.
;
; Si costruisce con scripts/build_installer.py, che legge la versione da
; main.py e la passa qui: NON scriverla a mano in questo file, altrimenti
; diventa il secondo posto da ricordarsi di aggiornare ad ogni release.
;
;   python scripts/build_installer.py
;
; Prima serve il pacchetto: pyinstaller driftdraft.spec

#ifndef MyAppVersion
  #define MyAppVersion "0.0"
#endif

#define MyAppName "DriftDraft"
#define MyAppExeName "DriftDraft.exe"

[Setup]
AppId={{7C1B5E42-3F8A-4C6D-9E21-DD1F0A5B7C33}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=T57HeavyTank
AppSupportURL=https://github.com/T57HeavyTank/DriftDraft
VersionInfoVersion={#MyAppVersion}

; PER-UTENTE, non in Program Files, e non e' una scorciatoia per evitare
; l'UAC: l'applicazione SCRIVE nella propria cartella (data/roster.json,
; data/saved_drafts.json, le tabelle Leaguepedia e le immagini dei campioni
; che scarica al primo avvio). In Program Files un utente senza privilegi
; non puo' scrivere, e l'app si romperebbe al primo salvataggio invece che
; all'installazione - il tipo di guasto peggiore, perche' si manifesta dopo.
; Stessa scelta di VS Code e Discord.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

; La GPL-3 va mostrata a chi installa: e' il momento in cui riceve il
; programma.
LicenseFile=..\LICENSE
InfoAfterFile=..\THIRD-PARTY.md

OutputDir=..\dist
OutputBaseFilename=DriftDraft-v{#MyAppVersion}-setup
SetupIconFile=..\assets\icon.ico

; Il grosso del pacchetto e' il Chromium di Playwright: senza compressione
; forte l'installer sarebbe enorme quanto la cartella.
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "italiano"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop"; GroupDescription: "Collegamenti:"

[Files]
; Tutto il contenuto di dist/DriftDraft, cioe' quello che produce PyInstaller.
; Le immagini dei campioni NON ci sono e non devono esserci: le scarica l'app
; al primo avvio (vedi driftdraft/champion_art.py e THIRD-PARTY.md).
Source: "..\dist\{#MyAppName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Roba che l'app si e' scaricata da sola dopo l'installazione: Inno non la
; conosce (non l'ha installata lei) e la lascerebbe li' per sempre.
Type: filesandordirs; Name: "{app}\assets\icons"
Type: filesandordirs; Name: "{app}\assets\splash"
Type: files; Name: "{app}\data\leaguepedia_drafts.json"
Type: files; Name: "{app}\data\leaguepedia_tables.json"

; NON si cancellano data\roster.json e data\saved_drafts.json: sono il lavoro
; di chi usa l'app - nomi dei suoi giocatori, tier list, draft salvate - e una
; disinstallazione non deve buttarlo via senza chiedere. Restano nella
; cartella, che percio' sopravvive alla disinstallazione: e' voluto, ed e'
; scritto nel messaggio qui sotto.

[Messages]
italiano.FinishedLabel=Installazione completata.%n%nAl primo avvio DriftDraft scarichera' le immagini dei campioni (circa 21 MB): serve una connessione a Internet, e si fa una volta sola.
