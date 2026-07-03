# Nutzung

## Setup

```bash
make install
```

Erzeugt eine virtuelle Umgebung (`.venv`) und installiert alle Abhängigkeiten.

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
```

Oder direkt mit Python:

```bash
python3 pipeline.py                 # alle
python3 pipeline.py total           # nur Gesamt
python3 pipeline.py yearly          # nur Jahr
python3 pipeline.py monthly         # nur Monatslinie + Balken
python3 pipeline.py monthly-pies    # nur Monatskreise
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

### Tabs unter dem Diagramm

- **Nach Kategorie**: Summen pro Kategorie
- **Monatlich**: Pivot-Tabelle Monat × Kategorie
- **Transaktionen**: Rohdaten (Datum, Empfänger, Betrag, Kategorie)
- **Nicht kategorisiert**: Ausgaben in "Sonstige" mit Empfänger + Zweck

## PDF → CSV

Anonymisierte PDF-Kontoauszüge in `pdf/` ablegen, dann:

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

Führt alle Unit-Tests aus (derzeit 19 Tests: 15 pipeline + 4 app).

## Aufräumen

```bash
make clean
```

Löscht `graphs/*.png` und die virtuelle Umgebung `.venv/`.
