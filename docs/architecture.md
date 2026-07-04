# Architektur

## Datenfluss

```
pdf/           csv/             pipeline.toml       categories.toml
  │              │                   │                    │
  ▼              ▼                   ▼                    ▼
pdf2csv.py ──► *.csv ──► pipeline.py ──► graphs/*.png
                              │
                              ▼
                          app.py (Streamlit + Plotly)
```

1. **CSV-Quellen**: DKB-Exporte (`csv/*.csv`, semikolongetrennt, UTF-8 mit BOM, quoted header) oder per `pdf2csv.py` aus PDFs konvertiert
2. **Einlesen**: `load_transactions()` sucht die Header-Zeile `"Buchungsdatum"`, parst Beträge (deutsches Format) und Datum (`DD.MM.YY`), entfernt Dubletten via SHA256-Hash
3. **Filtern + Kategorisieren**: `prepare_expenses()` filtert Ausgaben (negative Beträge → Absolutbetrag), `assign_categories()` matched per Substring (Payee + Purpose, case-insensitive)
4. **Einnahmen**: `prepare_income()` filtert positive Beträge (Gehalt, Zinsen etc.) → kein Kategorisieren nötig
5. **Gewinn/Verlust**: `prepare_profit_loss()` vergleicht Einnahmen vs Ausgaben pro Monat
6. **Ausgabe**: Tabellen auf der Konsole + Diagramme via matplotlib (`pipeline.py`) **oder** interaktives Dashboard via Streamlit + Plotly (`app.py`)

## Module

### `pipeline.py` (CLI-Backend)
- `load_config()` – lädt `pipeline.toml`, falls vorhanden, sonst Defaults
- `load_categories()` – lädt `categories.toml`, normalisiert Keywords zu UPPERCASE
- `load_transactions()` – liest alle CSV, parst Beträge/Daten, entfernt Dubletten
- `prepare_expenses()` – filtert Ausgaben, kategorisiert, erzeugt Monat/Jahr-Spalten
- `prepare_income()` – filtert positive Beträge, erzeugt Monat/Jahr-Spalten
- `prepare_profit_loss()` – merge Einnahmen + Ausgaben pro Monat, berechnet Differenz
- `assign_categories()` – Keyword-Substring-Matching (Payee + Purpose)
- `_plot_pie_chart()` – generisches Pie-Chart (wiederverwendet von total/yearly/monthly)
- `plot_pie()` – Gesamt-Pie
- `plot_yearly_pies()` – ein Pie pro Jahr
- `plot_monthly_pies()` – ein Pie pro Monat
- `plot_monthly_lines()` – Liniendiagramm (monatlicher Verlauf pro Kategorie)
- `plot_monthly_stacked()` – gestapeltes Balkendiagramm
- `plot_income_monthly()` – Gestapelte Einnahmen-Balken pro Monat (farbcodiert nach Zahlungspflichtige*r)
- `plot_income_yearly()` – Gestapelte Einnahmen-Balken pro Jahr (farbcodiert nach Zahlungspflichtige*r)
- `plot_income_pie()` – Einnahmen-Kreisdiagramm (nach Zahlungspflichtige*r)
- `plot_profit_loss()` – Gewinn/Verlust-Balken pro Monat
- `print_table()` / `print_monthly_table()` / `print_uncategorized()` – Konsolen-Tabellen

### `app.py` (Streamlit-Dashboard)
- `load_data()` – cached Data Loading via `@st.cache_data`, gibt `(expenses, income, categories)` zurück
- `filter_expenses()` – filtert nach Monaten und Kategorien
- `filter_income()` – filtert Einnahmen nach Monaten
- `render_sidebar()` – Sidebar mit Steuerungselementen
- `render_summary()` – 5 Metrik-Kacheln (Ausgaben Gesamt, Einnahmen Gesamt, Anzahl, Kategorien, Monate)
- `render_total_pie()` / `render_yearly_pie()` / `render_monthly_pie()` – Plotly-Kreisdiagramme
- `render_monthly_line()` / `render_monthly_stacked()` – Plotly-Linien/Stacked-Bar
- `render_income_monthly_bar()` – Gestapelte Einnahmen-Balken (farbcodiert nach Zahlungspflichtige*r)
- `render_income_monthly_line()` – Einnahmen-Linien (eine pro Zahlungspflichtige*m)
- `render_income_yearly()` – Gestapelte Einnahmen-Jahresbalken (farbcodiert nach Zahlungspflichtige*r)
- `render_income_pie()` – Einnahmen-Kreisdiagramm (nach Zahlungspflichtige*r)
- `render_profit_loss()` – Gewinn/Verlust-Balken
- `render_tables()` – aufklappbare Daten-Tabs (Kategorie, Monatlich, Rohdaten)
- `render_uncategorized()` – Tabelle mit nicht kategorisierten Ausgaben

### `pdf2csv.py` (PDF-Konverter)
- Extrahiert Text aus PDF mittels `pdfplumber`
- Erkennt Tabellenzeilen per Regex (zwei Daten im Format `DD.MM.YY` getrennt durch Leerzeichen)
- Erkennt Detail-Zeilen (einzelnes Datum oder Text) als `Verwendungszweck`
- Footer-Erkennung (Kontostand, Gesamtumsatzsummen, Seitenzahlen)
- `--debug` speichert Roh-Text als `.txt` zum Debuggen
- Ausgabe als CSV mit `QUOTE_ALL` (kompatibel zum DKB-Export-Format)

### `tests/test_pipeline.py` (Unit-Tests)
- 22 Tests: `parse_amount` (5), `parse_date` (2), `assign_categories` (4), `transaction_hash` (2), `load_config` (2), `prepare_income` (2), `prepare_profit_loss` (3), `filter_data_by_year` (2)

### `tests/test_app.py` (Unit-Tests)
- 7 Tests: `filter_expenses` nach Kategorie, Monat, leerem Ergebnis + `filter_income` (2), `test_chart_functions` (2)

## Datenmodell

### Raw CSV (nach `load_transactions`)
| Spalte | Typ | Beispiel |
|---|---|---|
| Buchungsdatum | datetime | 2025-12-22 |
| Betrag (€) | str (original) | "-21,94" |
| Betrag | float | -21.94 |
| Zahlungsempfänger\*in | str | "REWE München" |
| Verwendungszweck | str | "VISA Einkauf" |

### Expenses (nach `prepare_expenses`)
| Spalte | Typ | Beispiel |
|---|---|---|
| Datum | datetime | 2025-12-22 |
| Betrag | float | 21.94 (abs) |
| Kategorie | str | "Lebensmittel" |
| Monat | timestamp | 2025-12-01 |
| Jahr | int | 2025 |
| Monat_Label | str | "Dec 2025" |

### Income (nach `prepare_income`)
| Spalte | Typ | Beispiel |
|---|---|---|
| Datum | datetime | 2025-12-01 |
| Betrag | float | 2500.00 |
| Monat | timestamp | 2025-12-01 |
| Jahr | int | 2025 |
| Monat_Label | str | "Dec 2025" |

### Profit/Loss (nach `prepare_profit_loss`)
| Spalte | Typ | Beispiel |
|---|---|---|
| Monat | timestamp | 2025-12-01 |
| Monat_Label | str | "Dec 2025" |
| Ausgaben | float | 1800.50 |
| Einnahmen | float | 3500.00 |
| Gewinn | float | 1699.50 |

## Schlüsselentscheidungen

- **Keyword-basierte Kategorisierung** (statt Regex/ML): einfacher, menschlich editierbar in `categories.toml`
- **SHA256-Dedup** (statt `drop_duplicates`): robuster gegen Whitespace-Unterschiede
- **`QUOTE_ALL` im CSV-Export**: DKB liefert quoted Header, Pipeline erwartet quoted Header
- **Konfiguration über TOML**: alle veränderbaren Werte in `.toml`, nicht im Code
- **Plotly statt matplotlib im Dashboard**: Interaktivität (Hover, Klick, Toggle)
