# Nutzung

## Setup

### Linux / macOS

```bash
make install
```

Erzeugt eine virtuelle Umgebung (`.venv`) und installiert alle Abhängigkeiten.

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Ohne `make` (nicht vorinstalliert) kommt `requirements.txt` zum Einsatz – die enthält dieselben Pakete.

## CLI (statische Diagramme)

### Alle Diagramme

```bash
make run
```

### Selektiv

```bash
make run-total          # Nur Gesamt-Kreisdiagramm
make run-yearly         # Nur Kreisdiagramme pro Jahr
make run-monthly        # Nur Linien- + Balkendiagramm
make run-monthly-pies   # Nur Kreisdiagramme pro Monat
make run-income         # Nur Einnahmen-Diagramme
make run-income-pie     # Nur Einnahmen-Kreisdiagramm
make run-profit         # Nur Gewinn/Verlust-Diagramm
```

Oder direkt mit Python:

```bash
python3 pipeline.py                 # alle (inkl. Einnahmen + Gewinn/Verlust)
python3 pipeline.py total           # nur Gesamt
python3 pipeline.py yearly          # nur Jahr
python3 pipeline.py monthly         # nur Monatslinie + Balken
python3 pipeline.py monthly-pies    # nur Monatskreise
python3 pipeline.py income          # nur Einnahmen
python3 pipeline.py income-pie      # nur Einnahmen-Kreis
python3 pipeline.py profit          # nur Gewinn/Verlust
```

### Ausgabe

Diagramme landen als PNGs in `graphs/`:

| Datei | Inhalt |
|---|---|
| `ausgaben_nach_kategorie.png` | Gesamt-Kreisdiagramm |
| `ausgaben_YYYY.png` | Kreisdiagramm pro Jahr |
| `ausgaben_YYYY-MM.png` | Kreisdiagramm pro Monat |
| `ausgaben_linien_pro_monat.png` | Liniendiagramm (monatlich) |
| `ausgaben_gestapelt_pro_monat.png` | Gestapeltes Balkendiagramm (monatlich) |
| `einnahmen_pro_monat.png` | Einnahmen pro Monat (gestapelt, farbcodiert nach Zahlungspflichtige*r) |
| `einnahmen_pro_jahr.png` | Einnahmen pro Jahr (gestapelt, farbcodiert nach Zahlungspflichtige*r) |
| `gewinne_pro_monat.png` | Gewinn/Verlust-Balken pro Monat |

## Dashboard (interaktiv – Streamlit)

```bash
make app
```

Öffnet Streamlit-Dashboard im Browser (Standard: `http://localhost:8501`).

### Steuerung

| Element | Beschreibung |
|---|---|
| Sidebar – Monate | "Alle" oder einzelne Monate auswählen |
| Sidebar – Kategorien | "Alle" oder einzelne Kategorien filtern |
| Sidebar – Diagrammtyp | Umschalten zwischen 10 Diagrammarten |
| Diagramm – Hover | Zeigt Betrag + Prozent |
| Diagramm – Legende | Klick zum Ein-/Ausblenden einzelner Kategorien |

### Diagrammtypen

| Typ | Beschreibung |
|---|---|
| Kreis (Gesamt) | Alle Ausgaben in einem Pie-Chart |
| Kreis (Jahr) | Pie-Chart für ein ausgewähltes Jahr |
| Kreis (Monat) | Pie-Chart für einen ausgewählten Monat |
| Linien (Monat) | Liniendiagramm – Verlauf pro Kategorie |
| Gestapelte Balken (Monat) | Gestapelte Balken pro Monat |
| Einnahmen (Balken) | Einnahmen pro Monat (gestapelt, farbcodiert nach Zahlungspflichtige*r) |
| Einnahmen (Linie) | Einnahmen-Verlauf pro Monat (eine Linie pro Zahlungspflichtige*m) |
| Einnahmen (Jahr) | Einnahmen pro Jahr (gestapelt, farbcodiert nach Zahlungspflichtige*r) |
| Einnahmen (Kreis) | Einnahmen nach Sender in einem Kreisdiagramm |
| Gewinn/Verlust (Monat) | Differenz Einnahmen − Ausgaben pro Monat |

### Tabs unter dem Diagramm

- **Nach Kategorie**: Summen pro Kategorie
- **Monatlich**: Pivot-Tabelle Monat × Kategorie
- **Transaktionen**: Rohdaten (Datum, Empfänger, Betrag, Kategorie)
- **Nicht kategorisiert**: Ausgaben in "Sonstige" mit Empfänger + Zweck

## Desktop-App (Tauri + React)

Die neue Desktop-App ersetzt das Streamlit-Dashboard durch eine native Tauri-Anwendung mit React-Frontend und Python-FastAPI-Backend.

### Voraussetzungen

- Node.js 20+
- Rust-Toolchain (siehe `docs/development.md`)
- Python `.venv` mit Abhängigkeiten (`make install`)

### Starten (Entwicklung)

```bash
# 1. API-Server starten (ein Terminal)
.venv/bin/python api.py
# Läuft auf http://127.0.0.1:8765

# 2. Frontend starten (zweites Terminal)
cd desktop
npm run dev
# Öffnet http://localhost:5173 im Browser
```

Oder mit Tauri-Fenster:

```bash
cd desktop
npm run tauri dev
```

### Bauen

```bash
cd desktop
npm run tauri build
# Erzeugt Installer in desktop/src-tauri/target/release/bundle/
```

### Bedienung

| Element | Beschreibung |
|---|---|
| Sidebar – Zeitraum | Datumsauswahl Von/Bis zur Filterung |
| Sidebar – Kategorien | Multi-Select zum Filtern nach Kategorien |
| Diagrammauswahl | Dropdown zum Wechseln zwischen 8 Diagrammtypen |
| Tabelle | Sortierbare Transaktionsliste (Klick auf Spaltenkopf) |
| Nicht kategorisiert | Aufklappbare Liste der "Sonstige"-Transaktionen |

### Diagrammtypen (Desktop)

| Name | Beschreibung |
|---|---|
| Ausgaben – Kreis (Gesamt) | Alle Ausgaben im Pie-Chart |
| Ausgaben – Linie (Monat) | Liniendiagramm – monatlicher Verlauf |
| Ausgaben – Balken (Monat) | Gestapelte Balken pro Monat nach Kategorie |
| Einnahmen – Balken (Monat) | Einnahmen pro Monat, gestapelt nach Sender |
| Einnahmen – Linie (Monat) | Einnahmen pro Monat, Linien nach Sender |
| Einnahmen – Kreis | Einnahmen nach Sender im Pie-Chart |
| G/V – Saldo (Monat) | Gewinn/Verlust (Saldo) pro Monat |
| G/V – Vergleich (Monat) | Einnahmen vs. Ausgaben pro Monat |

## PDF → CSV

DKB-PDF-Kontoauszüge in `pdf/` ablegen, dann:

```bash
make pdf2csv
```

Erzeugt für jede PDF eine CSV in `csv/`. Mit Debug-Output:

```bash
python3 pdf2csv.py --debug
```

Speichert Roh-Text als `.txt`-Datei zum Prüfen der Erkennung.

## Tests

```bash
make test
```

Führt alle Unit-Tests aus (derzeit 34 Tests: 22 pipeline + 12 app).

## Aufräumen

```bash
make clean
```

Löscht `graphs/*.png` und die virtuelle Umgebung `.venv/`.

## Windows: Befehle ohne `make`

Alle Python-Befehle funktionieren identisch – nur der Aufruf unterscheidet sich:

| Aufgabe | Linux/macOS (make) | Windows (PowerShell) |
|---|---|---|
| Setup | `make install` | `.venv\Scripts\activate` + `pip install -r requirements.txt` |
| Pipeline (alle) | `make run` | `.venv\Scripts\activate` + `python pipeline.py` |
| Pipeline (total) | `make run-total` | `.venv\Scripts\activate` + `python pipeline.py total` |
| Pipeline (income) | `make run-income` | `.venv\Scripts\activate` + `python pipeline.py income` |
| Pipeline (income-pie) | `make run-income-pie` | `.venv\Scripts\activate` + `python pipeline.py income-pie` |
| Pipeline (profit) | `make run-profit` | `.venv\Scripts\activate` + `python pipeline.py profit` |
| Dashboard | `make app` | `.venv\Scripts\activate` + `streamlit run app.py` |
| PDF → CSV | `make pdf2csv` | `.venv\Scripts\activate` + `python pdf2csv.py` |
| Tests | `make test` | `.venv\Scripts\activate` + `python -m pytest tests/ -v` |
| Aufräumen | `make clean` | `Remove-Item graphs\*.png -Force; Remove-Item .venv -Recurse -Force` |

**Hinweis:** Das venv muss vor jedem Befehl aktiviert werden (`.venv\Scripts\activate`).
Wer `make` auf Windows nutzen möchte, installiert es z. B. via Chocolatey: `choco install make`.
