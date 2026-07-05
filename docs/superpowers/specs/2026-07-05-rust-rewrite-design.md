# Pure Rust Rewrite — DKB Finanz-Dashboard

**Date:** 2026-07-05  
**Status:** Draft

## Goal

Rewrite the Python data pipeline (`data.py`, `pipeline.py`, `pdf2csv.py`, `api.py`) in Rust and package the entire application as a single, self-contained Tauri desktop binary. Users should be able to download an installer and run the app without installing Python, Node.js, or any other dependency.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                  Tauri App                        │
│  ┌──────────────────────┐  ┌──────────────────┐  │
│  │   Rust Backend       │  │  React Frontend   │  │
│  │                      │  │                   │  │
│  │  dkb-core crate      │  │  Dashboard view   │  │
│  │  ┌────────────────┐  │  │  Data view        │  │
│  │  │ csv_reader     │──┼──│  (cat. editor +   │  │
│  │  │ pdf_extractor  │  │  │   tables)         │  │
│  │  │ categorizer    │  │  │                   │  │
│  │  │ aggregator     │  │  │  Dark mode toggle │  │
│  │  │ config         │  │  │  File import      │  │
│  │  └────────────────┘  │  └──────────────────┘  │
│  │         │            │         │               │
│  │  Tauri commands      │  invoke() / events     │
│  │  (get_data,          │                         │
│  │   save_categories,   │                         │
│  │   import_file)       │                         │
│  └──────────────────────┘  └──────────────────────┘
│                           │
│  User config dir:         │
│  ~/.config/dkb-finanz/    │
│  ├── categories.toml      │
│  └── csv/                 │
│      └── (imported files) │
└──────────────────────────────────────────────────┘
```

## Sub-projects

### 1. dkb-core (Rust library crate)

A single library crate at `desktop/src-tauri/dkb-core/` with five modules:

#### `csv_reader`
- Parse DKB semicolon-separated CSV files with German number format (`1.234,56`)
- Parse dates in `DD.MM.YYYY` format
- Extract fields: `Buchungstag`, `Wertstellung`, `Umsatzart`, `Zahlungspflichtige*r`, `Empfänger*in`, `Verwendungszweck`, `Betrag`
- Output: `Vec<Transaction>` where `Transaction` is a struct with typed fields (`f64` for Betrag, `NaiveDate` for dates)
- Handle BOM, encoding issues
- Reuse existing CSV test data from `tests/test_pipeline.py`

#### `pdf_extractor`
- Use `pdf-extract` crate to extract text from DKB PDF bank statements
- Parse the same `Transaction` fields from extracted text layout
- Match current `pdf2csv.py` behavior:
  - Detect "Kontoumsätze" section
  - Parse transaction blocks with date, type, payee, amount
  - Handle multi-line purposes
  - Write output as CSV or return as `Vec<Transaction>` directly

#### `categorizer`
- Load keyword rules from TOML (categories.toml)
- Case-insensitive substring matching against `Empfänger*in` and `Verwendungszweck`
- Same behavior as `pipeline.py:assign_categories()`
- Transactions that match no rule get category `"Sonstige"`
- Return `Vec<ExpenseRecord>` with category field filled
- Normalize income sender names (trim, uppercase, deduplicate whitespace)

#### `aggregator`
- Group expenses by month and category
- Calculate totals for pie charts
- Group income by month and normalized sender
- Calculate profit/loss per month (income − expenses)
- Same aggregation logic as `data.py`:
  - `prepare_expenses()`
  - `prepare_income()`
  - `prepare_profit_loss()`
- Return data structures matching the current JSON shape so the React frontend needs minimal changes

#### `config`
- Determine user config directory per platform:
  - Linux: `~/.config/dkb-finanz/`
  - macOS: `~/Library/Application Support/dkb-finanz/`
  - Windows: `%APPDATA%/dkb-finanz/`
- On first launch, copy default `categories.toml` and `pipeline.toml` from the app bundle
- Load/save `categories.toml` (serde + toml crate)
- Load `pipeline.toml` settings
- Create `csv/` subdirectory for imported files

### 2. Tauri Backend

Replace `api.py` with Tauri commands:

| Command | Input | Output | Description |
|---|---|---|---|
| `get_data` | — | `DashboardData` JSON | Run full pipeline: read CSVs → categorize → aggregate → return |
| `get_categories` | — | `Vec<CategoryEntry>` | Return current categories.toml as structured JSON |
| `save_categories` | `Vec<CategoryEntry>` | success/error | Write categories back to user config dir; re-process data |
| `import_file` | file path | success/error | Copy file to user `csv/` dir, re-process data |
| `pick_file` | — | file path (or None) | Open native file picker dialog for CSV/PDF selection |

The Rust `lib.rs` `run()` function registers these commands. No subprocess spawning, no HTTP server.

Data structures in the Tauri command outputs must match the current JSON shape from the FastAPI `/api/data` endpoint exactly so the frontend `api.ts` swap is mechanical.

### 3. Frontend Updates

#### `api.ts` replacement
- Replace `fetch()` calls with `invoke()` calls from `@tauri-apps/api`
- Keep all existing data types (`ExpenseRecord`, `IncomeRecord`, `ProfitLossRecord`, `FilterState`)
- The `useEffect` in `Dashboard.tsx` changes from `fetch(API_URL + "/api/data")` to `invoke("get_data")`

#### Dashboard view (unchanged)
- Same charts, summary cards, sidebar filters
- No visual changes

#### Data view (new)
- **Category editor**: Editable table of category names with keyword lists. Add/remove categories, add/remove keywords per category. Save button calls `save_categories`.
- **Transaction table**: Reuse the existing collapsible `DataTables` component (same as current)
- **Uncategorized table**: Reuse `Uncategorized` component
- Navigation between Dashboard and Data view via a tab bar or navbar

#### File import
- Drag-and-drop zone or native file picker button (using Tauri's dialog API)
- Accept `.csv` and `.pdf` files
- On drop/select, call `import_file(path)`, which copies to user config dir and triggers data reprocessing
- Progress indication during processing

#### Dark mode toggle
- Toggle switch in the header/sidebar
- Persist preference to `localStorage`
- CSS custom properties for light/dark theme
- Apply dark class to root element

### 4. Config Management

- First launch: copy bundled `categories.toml` and `pipeline.toml` to user config dir
- Subsequent launches: read from user config dir
- Category edits write back to user config dir only
- Imported CSV/PDF files go into user config dir's `csv/` subdirectory
- The bundled defaults serve as fallback if user deletes their config

### 5. Packaging

One command per platform:

```
# Linux
cargo tauri build --target x86_64-unknown-linux-gnu
# → .deb + .AppImage

# macOS
cargo tauri build --target x86_64-apple-darwin
# → .dmg

# Windows (cross-compile from Linux with mingw)
cargo tauri build --target x86_64-pc-windows-msvc
# → .msi
```

## Implementation Order

1. **dkb-core: config** — user config directory logic, TOML serde models (no dependencies on other modules)
2. **dkb-core: csv_reader** — parse CSVs, write tests
3. **dkb-core: categorizer** — load rules, match transactions, write tests
4. **dkb-core: aggregator** — group/aggregate, write tests
5. **dkb-core: pdf_extractor** — PDF text extraction, write tests
6. **Tauri integration** — wire up commands in `lib.rs`, test with `tauri dev`
7. **Frontend: api.ts swap** — replace fetch with invoke, verify Dashboard still works
8. **Frontend: Data view** — category editor + tables + file import
9. **Frontend: Dark mode** — CSS variables + toggle
10. **Packaging** — build for all platforms, test installers

## Testing Strategy

- Unit tests for each `dkb-core` module (Rust `#[cfg(test)]`)
- Integration test: run full pipeline on sample CSV, compare output shape to Python pipeline output
- Tauri test: use `tauri::test` to call commands and verify JSON shapes match current API
- Frontend: visual inspection (no test framework currently); manual test of invoke calls

## Success Criteria

- [ ] `make test` passes all Rust tests
- [ ] `cargo tauri build` produces a working installer
- [ ] Fresh install: app starts without Python/Node, shows dashboard
- [ ] Category editor: can add/remove categories, save persists, data re-processes
- [ ] File import: drag PDF or CSV, data updates immediately
- [ ] Dark mode: toggle works, preference persists across restarts
- [ ] Data view: transaction table + uncategorized table render correctly
- [ ] All 8 chart types render with same data as current app
