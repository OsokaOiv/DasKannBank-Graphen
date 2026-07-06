# Nutzung

## Desktop-App (Tauri + React + Rust) ★

Die Desktop-App ist eine native Tauri-Anwendung mit React-Frontend und Rust-Backend (`dkb-core`).
Kein Python oder Streamlit nötig – die gesamte Datenverarbeitung läft in Rust.

### Voraussetzungen

- Node.js 20+
- Rust-Toolchain (siehe `docs/development.md`)
- Systemdependencies für Tauri (WebKit2GTK, etc. – siehe [Tauri-Doku](https://v2.tauri.app/start/prerequisites/))

### Build (produktionsfertiger Installer)

```bash
make build
# Erzeugt Installer in desktop/src-tauri/target/release/bundle/
```

Unter Windows wird `desktop/scripts/build-windows.ps1` empfohlen (auto-detektiert VS Build Tools, Rust, Node.js).

### Entwicklung (mit Hot-Reload)

```bash
make run
# Öffnet Tauri-Fenster mit Hot-Reload
```

Oder im Browser (ohne Tauri-Fenster):

```bash
cd desktop && npm run dev
# Öffnet http://localhost:5173
```

### Bedienung

| Element | Beschreibung |
|---|---|
| Tab "Dashboard" | Diagramme + Kennzahlen (8 Chart-Typen) |
| Tab "Daten" | Kategorie-Editor, Datei-Import, Transaktionstabellen |
| Design-Select | Themenauswahl: Standard (Hell/Dunkel), Terminal Pro (Cyan), Neon Finance (Smaragd), Cyber Dashboard (Bernstein) |
| 🌙/☀️ | Dark-Mode-Umschalter (nur im Standard-Theme) |

### Datenverzeichnis

Die App speichert Konfiguration und importierte Dateien unter `~/.config/dkb-finanz/`:

| Pfad | Inhalt |
|---|---|
| `categories.toml` | Kategorien mit Keywords (editierbar im Tab "Daten") |
| `csv/` | Importierte CSV-Kontoauszüge |
| `pdf/` | Importierte PDF-Kontoauszüge (werden beim Import automatisch konvertiert) |

### Tests

```bash
make test              # Rust + Frontend
make test-rust         # Nur Rust (35 Tests)
make test-frontend     # Nur Frontend (7 Tests)
```

### Windows-Build-Script

```powershell
.\desktop\scripts\build-windows.ps1
```

Auto-installiert Rust + Node.js falls nötig, lädt vcvars64.bat, erzeugt `.exe` + NSIS-Setup.

---

## Python-Prototyp (legacy/)

Die ursprüngliche Python-Implementierung lebt im Ordner `legacy/` als Referenz.
Sie wird nicht mehr aktiv weiterentwickelt, aber alle 29 Tests laufen weiterhin.

### Setup

```bash
make legacy-setup
```

### CLI (statische Diagramme)

```bash
make legacy-run                # Alle Diagramme → legacy/graphs/*.png
make legacy-pdf2csv            # PDFs → CSV konvertieren
```

### Dashboard (Streamlit)

```bash
make legacy-app
# Öffnet http://localhost:8501
```

### Tests

```bash
make legacy-test               # 29 Python-Tests
```

### Direkte Python-Befehle (Windows ohne make)

```powershell
legacy\.venv\Scripts\activate
python legacy/pipeline.py
streamlit run legacy/app.py
python -m pytest legacy/tests/ -v
```
