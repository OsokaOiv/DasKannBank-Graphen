# Architektur

## Datenfluss

### Tauri Desktop App (aktuell)

```
pdf/             csv/            categories.toml
  │               │                   │
  ▼               ▼                   ▼
pdf_to_csv.rs ──► *.csv ──► dkb-core (Rust)
  (bei Import)              │
                           ▼
                       Tauri IPC (get_data)
                           │
                           ▼
                     React + Plotly (Dashboard)
```

1. **Import**: Datei (CSV oder PDF) wird via Dateidialog ausgewählt und per `import_file`-Kommando verarbeitet
2. **CSV**: Wird direkt ins `csv/`-Verzeichnis kopiert
3. **PDF**: Wird sofort via `pdf_to_csv::convert_pdf()` in CSV konvertiert und ins `csv/`-Verzeichnis geschrieben (keine PDF-Verarbeitung zur Abfragezeit)
4. **Abfrage**: `get_data` liest nur CSVs via `csv_reader::read_all_csvs()` – kein PDF-Dekodieren zur Laufzeit
5. **Kategorisierung**: `categorizer` matched per Substring (Payee + Purpose, case-insensitive)
6. **Aggregation**: `aggregator` berechnet Ausgaben, Einnahmen, Gewinn/Verlust
7. **Ausgabe**: JSON-Strukturen via Tauri IPC an React, Visualisierung mit Plotly (Dark-Mode-Unterstützung via `paper_bgcolor`/`plot_bgcolor`/`font.color`)

### Python-Pipeline (Legacy)

```
pdf/           csv/             pipeline.toml       categories.toml
  │              │                   │                    │
  ▼              ▼                   ▼                    ▼
pdf2csv.py ──► *.csv ──► pipeline.py ──► graphs/*.png
                              │
                              ▼
                          app.py (Streamlit + Plotly)
```

## Module (dkb-core – Rust)

6 Module in `desktop/src-tauri/dkb-core/src/`:

### `config.rs`
- `app_dir()` – Basisverzeichnis `~/.config/dkb-finanz/`
- `csv_dir()` / `pdf_dir()` – Unterverzeichnisse für CSV/PDF
- `categories_path()` – Pfad zu `categories.toml`
- `load_category_entries()` – lädt Kategorien aus TOML
- `save_category_entries()` – schreibt Kategorien zurück
- `copy_defaults_if_missing()` – initiale Konfiguration anlegen

### `csv_reader.rs`
- `read_csv()` – parst eine semikolongetrennte CSV (UTF-8 mit BOM), extrahiert 12 Spalten (Buchungsdatum, Wertstellung, Status, Zahlungspflichtige\*r, Zahlungsempfänger\*in, Verwendungszweck, Umsatztyp, IBAN, Betrag, Gläubiger-ID, Mandatsreferenz, Kundenreferenz)
- `read_all_csvs()` – sammelt alle CSV in `csv/`, dedupliziert via Hash
- Kein Herausfiltern von `Verwendungszweck`-leeren Zeilen

### `categorizer.rs`
- `Categorizer`-Struct: hält Keyword-Listen pro Kategorie
- `from_toml()` – lädt Keyword-Mappings aus `categories.toml`
- `categorize()` – Substring-Matching (case-insensitive) über Payee + Purpose
- `all_categories()` – gibt alle Kategorienamen zurück

### `aggregator.rs`
- `build_dashboard_data()` – zentrale Aggregation: Expenses, Income, Profit/Loss
- `prepare_expenses()` – filtert negative Beträge, kategorisiert, Monat/Jahr-Spalten
- `prepare_income()` – filtert positive Beträge
- `prepare_profit_loss()` – merge Einnahmen + Ausgaben pro Monat

### `pdf_to_csv.rs`
- `convert_pdf()` – extrahiert Text via `pdf_extract`, erkennt Tabellenzeilen an zwei Datumsfeldern (`DD.MM.YY`), erkennt Detail-Zeilen als `Verwendungszweck`, Footer-Erkennung (Kontostand, Gesamtumsatzsummen, Seitenzahlen)
- Algorithmus entspricht dem Python `pdf2csv.py` (gleiche Regex-Logik, gleiche Feldnamen)
- Gibt CSV mit `QUOTE_ALL` aus (kompatibel zum DKB-Export-Format)

### `util.rs`
- `parse_amount()` – deutsches Zahlenformat → f64
- `collect_files()` – sammelt Dateien nach Extension
- `format_currency()` – f64 → deutscher Währungsstring
- `month_label()` – Datum → "Monat Jahr"-Label

### `lib.rs`
- Definiert Datenstrukturen: `Transaction`, `ExpenseRecord`, `IncomeRecord`, `ProfitLossRecord`, `DashboardData`, `CategoryEntry`
- Exportiert alle Module

## Datenmodell

### `Transaction` (Raw CSV – Rust)
| Feld | Typ | Beispiel |
|---|---|---|
| buchungsdatum | String | "2025-12-22" |
| wertstellung | String | "2025-12-21" |
| status | Option\<String\> | "Gebucht" |
| zahlungspflichtiger | Option\<String\> | "Max Mustermann" |
| zahlungsempfaenger | Option\<String\> | "REWE München" |
| verwendungszweck | Option\<String\> | "VISA Einkauf" |
| umsatztyp | Option\<String\> | "Lastschrift" |
| iban | Option\<String\> | "DE12..." |
| betrag | f64 | -21.94 |
| glaeubiger_id | Option\<String\> | "DE..." |
| mandatsreferenz | Option\<String\> | "..." |
| kundenreferenz | Option\<String\> | "..." |

### `ExpenseRecord` (aggregiert)
| Feld | Typ | Beispiel |
|---|---|---|
| Datum | String | "2025-12-22" |
| Monat | String | "2025-12-01" |
| Monat_Label | String | "Dec 2025" |
| Kategorie | String | "Lebensmittel" |
| Betrag | f64 | 21.94 |
| Zahlungsempfänger\*in | Option\<String\> | "REWE München" |
| verwendungszweck | Option\<String\> | "VISA Einkauf" |

### `IncomeRecord` (aggregiert)
| Feld | Typ | Beispiel |
|---|---|---|
| Datum | String | "2025-12-01" |
| Monat | String | "2025-12-01" |
| Betrag | f64 | 2500.00 |
| Zahlungspflichtige\*r | Option\<String\> | "Arbeitgeber" |
| verwendungszweck | Option\<String\> | "Gehalt" |

### `ProfitLossRecord` (aggregiert)
| Feld | Typ | Beispiel |
|---|---|---|
| Monat | String | "2025-12-01" |
| Einnahmen | f64 | 3500.00 |
| Ausgaben | f64 | 1800.50 |
| Differenz | f64 | 1699.50 |
| Status | String | "Gewinn" |

## Schlüsselentscheidungen

- **Keyword-basierte Kategorisierung** (statt Regex/ML): einfacher, menschlich editierbar in `categories.toml`
- **Hash-Dedup** (statt `retain`/`HashSet`): robuster gegen Whitespace-Unterschiede
- **PDF-Konvertierung bei Import**: PDF → CSV sofort beim Import, `get_data` nur CSV-Lese-Zugriff
- **Konfiguration über TOML**: alle veränderbaren Werte in `.toml`, nicht im Code
- **Plotly im React-Frontend**: interaktive Diagramme mit Dark-Mode-Unterstützung
- **Theme-System**: 4 Themes (Standard, Terminal Pro, Neon Finance, Cyber Dashboard) über CSS Custom Properties; Design-Switcher in der Navigationsleiste; `themes.ts` steuert Persistenz und Anwendung der Theme-Klassen auf `<html>`
