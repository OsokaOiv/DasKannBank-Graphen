# Entwicklung

## Code-Prinzipien

Siehe [code-principles.md](../code-principles.md) im Projekt-Root.

Kernregeln:
- **Single Responsibility** – jede Funktion macht genau eine Sache
- **DRY** – keine Logik kopieren
- **Type Hints** – für alle Parameter und Rückgabewerte
- **Keine Magic Numbers** – alles in Konfigurationsdateien
- **Kein Dead Code** – ungenutzte Imports/Variablen vor Commit entfernen
- **Selbsterklärender Code** – Kommentare nur für "warum", nie für "was"

## Projektstruktur

```
.
├── desktop/              ★ Hauptprodukt – Tauri + React + Rust
│   ├── src/
│   │   ├── components/   ← UI-Komponenten (ChartView, DataTables, etc.)
│   │   ├── themes.ts     ← Theme-Definitionen (7 Themes)
│   │   ├── api.ts        ← Tauri IPC-Calls
│   │   └── __tests__/    ← 7 Frontend-Tests (Vitest)
│   ├── src-tauri/
│   │   ├── src/          ← Tauri-Backend (Rust)
│   │   └── dkb-core/
│   │       └── src/      ← 6 Module (config, csv_reader, categorizer,
│   │                          aggregator, util, pdf_to_csv) — 35 Tests
│   ├── scripts/build-windows.ps1
│   └── package.json
├── legacy/               ← Python-Prototyp (Referenz, unverändert)
│   ├── app.py / pipeline.py / pdf2csv.py / api.py / data.py / constants.py
│   ├── requirements.txt
│   ├── tests/            ← 29 Python-Tests
│   └── .venv/            ← Python venv (gitignored)
├── csv/                  ← DKB-CSV-Exporte (gitignored)
├── pdf/                  ← DKB-PDF-Kontoauszüge (gitignored)
├── docs/                 ← Dokumentation (Markdown)
├── categories.toml       ← Keyword-basierte Kategorien (geteilt)
├── code-principles.md    ← Clean Code Regeln
├── Makefile              ← Build-System (desktop-first)
└── README.md             ← Projekt-Übersicht
```

## Workflow

1. Änderung planen (Verständnis der Codebase, ggf. nachfragen)
2. Arbeit in kleine Schritte zerlegen
3. Implementieren (Clean Code beachten)
4. Tests ausführen
5. Dokumentation aktualisieren
6. Auf Dead Code prüfen
7. Nochmal testen
8. Committen

## Tests

### Rust (35 Tests — `cargo check` zero warnings)

```bash
cd desktop && cargo test
```

| Modul | Tests | Getestete Funktionen |
|---|---|---|
| `aggregator.rs` | 4 | `prepare_expenses`, `prepare_income`, `prepare_profit_loss`, `build_dashboard_data` |
| `categorizer.rs` | 4 | `from_toml`, `categorize`, `all_categories` |
| `csv_reader.rs` | 4 | `parse_date`, `read_csv`, `deduplicate` |
| `pdf_to_csv.rs` | 16 | `convert_pdf`, Zeilenerkennung, Footer-Filter |
| `util.rs` | 7 | `parse_amount`, `collect_files`, `format_currency`, `month_label` |

### Frontend (7 Tests — Vitest)

```bash
cd desktop && npm test
```

| Datei | Tests | Getestete Szenarien |
|---|---|---|
| `App.test.tsx` | 7 | Dashboard-Rendering, Tab-Wechsel, Dark-Mode-Toggle, Theme-Selector, Theme-Wechsel |

### Python (Legacy — 29 Tests)

```bash
make test
```

```bash
python3 -m pytest tests/ -v
python3 -m pytest tests/test_pipeline.py::test_parse_amount_german_negative -v  # einzelner Test
```

| Modul | Tests | Getestete Funktionen |
|---|---|---|
| `test_pipeline.py` | 22 | `parse_amount`, `parse_date`, `assign_categories`, `transaction_hash`, `load_config`, `prepare_income`, `prepare_profit_loss` |
| `test_app.py` | 7 | `filter_expenses`, `filter_income` |

### Neue Tests schreiben

**Python (Legacy):** Tests in `tests/` ablegen, Dateiname `test_*.py`. Funktionen mit `def test_*()`.
**Rust:** Tests mit `#[test]` im selben Modul oder in `tests/`-Integrationstests.
**Frontend:** Tests in `desktop/src/__tests__/` mit Vitest + Testing Library.

## Hinzufügen neuer Diagrammtypen

### In `pipeline.py` (matplotlib)
1. Neue Funktion schreiben (z. B. `plot_heatmap()`)
2. In `plot_all_charts()` aufrufen
3. Chart-Namen zum CLI-Argument (`chart_map`) hinzufügen

### In `app.py` (Streamlit + Plotly)
1. Neue Render-Funktion schreiben (z. B. `render_heatmap()`)
2. In `chart_map` registrieren
3. Name in `render_sidebar()` beim `selectbox`-Array ergänzen

## Deployment-Hinweise

- Zwei Arbeitskopien: `Projects/DasKannBank-Graphen` (Entwicklung) und `DKB/DasKannBank-Graphen` (echte Daten)
- Git Push/Pull manuell zwischen den Umgebungen
- Nach Pull immer `make install` (Linux/macOS) oder `pip install -r requirements.txt` (Windows)

## Theme-System

Das Theme-System verwendet CSS Custom Properties auf 4 Ebenen:

1. **`:root`** – Light-Mode-Farben (Standard-Theme)
2. **`.dark`** – Dark-Mode-Farben (Standard-Theme)
3. **`.theme-terminal-pro.dark`**, **`.theme-neon-finance.dark`**, **`.theme-cyber-dashboard.dark`** – Always-Dark-Theme-Farben
4. **`themes.ts`** – Steuert Persistenz (`localStorage`-Key `dkb-theme`) und Anwendung der Theme-Klassen auf `<html>`

Neue Themes hinzufügen:
1. In `themes.ts` neue `ThemeId` + `ThemeDef` eintragen
2. In `App.css` neue `.theme-*.dark`-CSS-Vars definieren
3. `applyTheme()` in `themes.ts` aktualisieren (für root-Klasse)

## Cross-Plattform-Hinweise

- **Pfade**: Alle Pfade im Code verwenden `pathlib.Path` (Python) oder `PathBuf` (Rust) – funktioniert auf Linux, macOS und Windows
- **Python-Version**: Beliebig ≥ 3.10
- **Makefile**: Nur für Linux/macOS; auf Windows `requirements.txt` + direkte Python-/Streamlit-Befehle verwenden (siehe [Nutzung](usage.md#windows-befehle-ohne-make))
- **Venv**: Windows nutzt `.venv\Scripts\activate` statt `.venv/bin/activate`
- **Encoding**: CSVs werden mit `utf-8-sig` gelesen – funktioniert auf allen Plattformen
- **Tauri-Build (Windows)**: `tauri.conf.json` verwendet `powershell -NoProfile -Command` für zuverlässige PATH-Auflösung bei `beforeDevCommand`/`beforeBuildCommand`
