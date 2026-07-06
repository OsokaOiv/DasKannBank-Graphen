<div align="center">

# DasKannBank-Graphen
  
**Ausgabenvisualisierung für DKB-Kontoauszüge**


[![CI](https://img.shields.io/github/actions/workflow/status/OsokaOiv/DasKannBank-Graphen/ci.yml?branch=main&label=CI&logo=github)](https://github.com/OsokaOiv/DasKannBank-Graphen/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10--3.13-blue?logo=python)](https://www.python.org)
[![Rust](https://img.shields.io/badge/Rust-1.85+-orange?logo=rust)](https://www.rust-lang.org)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)](docs/usage.md#windows-befehle-ohne-make)
[![Python tests](https://img.shields.io/badge/Python%20tests-29%20passed-brightgreen)](tests/)
[![Rust tests](https://img.shields.io/badge/Rust%20tests-35%20passed-brightgreen)](desktop/src-tauri/dkb-core/)
[![Frontend tests](https://img.shields.io/badge/Frontend%20tests-5%20passed-brightgreen)](desktop/src/__tests__/)

<br>

<img src="docs/screenshot.png" alt="Dashboard Screenshot" width="700"/>

<br>

Pipeline to analyse DKB bank statement CSVs and visualise expenses – as static <b>matplotlib</b> charts (PNG), an interactive <b>Streamlit</b> dashboard with <b>Plotly</b>, or a <b>Tauri</b> desktop app (<b>React + Rust</b>) with native file dialogs and no Python dependency.

</div>

---

## Features

- **Automatic CSV import** – reads all `csv/*.csv` files (semicolon-separated, German number format)
- **Keyword-based categorisation** – editable `categories.toml`, case-insensitive substring matching
- **Deduplication** – SHA256-based duplicate detection across multiple files
- **10 chart types** – total/yearly/monthly pie charts, monthly line + stacked bars, income (stacked by payer), income line per payer, income (pie by payer), yearly income (stacked by payer), profit/loss
- **Interactive dashboard** – Streamlit + Plotly with hover data, clickable legends, category/month/chart-type filters
- **PDF converter** – Rust `pdf_to_csv` module extracts tables from DKB PDF statements (via `pdf_extract`); Python `pdf2csv.py` also available
- **Cross-platform** – Linux, macOS, and Windows

---

## Quick Start

### Linux / macOS

```bash
make install
make run              # all static charts → graphs/*.png
make run-income       # income charts only
make run-profit       # profit/loss chart only
make app              # interactive dashboard → http://localhost:8501
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python pipeline.py
streamlit run app.py
```

---

## Documentation

| Topic | Content |
|---|---|
| [Architecture](docs/architecture.md) | Data flow, modules, data model |
| [Usage](docs/usage.md) | CLI commands, dashboard, PDF conversion, tests |
| [Configuration](docs/configuration.md) | categories.toml, pipeline.toml |
| [Development](docs/development.md) | Code principles, structure, workflow |

---

## Tests

### Python (Legacy — 29 Tests)

```bash
make test
```

### Rust (35 Tests — `cargo check` passes with zero warnings)

```bash
cd desktop && cargo test
```

### Frontend (5 Tests)

```bash
cd desktop && npm test
```

CI runs Python tests on every push across Python 3.10–3.13 on Linux, macOS, and Windows (Rust + Frontend CI planned).

---

## Contributing

Contributions are welcome.  

1. Open an [issue](https://github.com/OsokaOiv/DasKannBank-Graphen/issues) to discuss changes
2. Follow the [code principles](code-principles.md)
3. Ensure all tests pass: `make test`
4. Submit a pull request

---

## License

[GNU General Public License v3.0](LICENSE)


