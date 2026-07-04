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
| `einnahmen_pro_monat.png` | Einnahmen-Balken pro Monat |
| `einnahmen_pro_jahr.png` | Einnahmen-Balken pro Jahr |
| `gewinne_pro_monat.png` | Gewinn/Verlust-Balken pro Monat |

## Dashboard (interaktiv)

```bash
make app
```

Öffnet Streamlit-Dashboard im Browser (Standard: `http://localhost:8501`).

### Steuerung

| Element | Beschreibung |
|---|---|
| Sidebar – Monate | "Alle" oder einzelne Monate auswählen |
| Sidebar – Kategorien | "Alle" oder einzelne Kategorien filtern |
| Sidebar – Diagrammtyp | Umschalten zwischen 5 Diagrammarten |
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
| Einnahmen (Balken) | Einnahmen pro Monat |
| Einnahmen (Linie) | Einnahmen-Verlauf pro Monat |
| Gewinn/Verlust (Monat) | Differenz Einnahmen − Ausgaben pro Monat |

### Tabs unter dem Diagramm

- **Nach Kategorie**: Summen pro Kategorie
- **Monatlich**: Pivot-Tabelle Monat × Kategorie
- **Transaktionen**: Rohdaten (Datum, Empfänger, Betrag, Kategorie)
- **Nicht kategorisiert**: Ausgaben in "Sonstige" mit Empfänger + Zweck

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

Führt alle Unit-Tests aus (derzeit 29 Tests: 22 pipeline + 7 app).

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
| Pipeline (profit) | `make run-profit` | `.venv\Scripts\activate` + `python pipeline.py profit` |
| Dashboard | `make app` | `.venv\Scripts\activate` + `streamlit run app.py` |
| PDF → CSV | `make pdf2csv` | `.venv\Scripts\activate` + `python pdf2csv.py` |
| Tests | `make test` | `.venv\Scripts\activate` + `python -m pytest tests/ -v` |
| Aufräumen | `make clean` | `Remove-Item graphs\*.png -Force; Remove-Item .venv -Recurse -Force` |

**Hinweis:** Das venv muss vor jedem Befehl aktiviert werden (`.venv\Scripts\activate`).
Wer `make` auf Windows nutzen möchte, installiert es z. B. via Chocolatey: `choco install make`.
