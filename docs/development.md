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
├── .venv/                ← Virtuelle Python-Umgebung (gitignored)
├── csv/                  ← DKB-CSV-Exporte (gitignored)
├── pdf/                  ← Anonymisierte PDFs (gitignored)
├── graphs/               ← Generierte PNG-Diagramme (gitignored)
├── docs/                 ← Dokumentation (Markdown)
├── tests/
│   ├── test_pipeline.py  ← 15 Tests
│   └── test_app.py       ← 4 Tests
├── app.py                ← Streamlit-Dashboard
├── pipeline.py           ← CLI-Backend (Daten + matplotlib)
├── pdf2csv.py            ← PDF-Konverter
├── categories.toml       ← Keyword-basierte Kategorien
├── pipeline.toml         ← Diagramm-Konfiguration
├── code-principles.md    ← Clean Code Regeln
├── Makefile              ← Build/Run/Test-Befehle
└── README.md             ← Projekt-Übersicht
```

## Workflow

1. Änderung planen (Verständnis der Codebase, ggf. nachfragen)
2. Arbeit in kleine Schritte zerlegen
3. Implementieren (Clean Code beachten)
4. Tests ausführen: `make test`
5. Dokumentation aktualisieren
6. Auf Dead Code prüfen
7. Nochmal testen
8. Committen

## Tests

### Ausführen

```bash
make test
```

Oder direkt:

```bash
python3 -m pytest tests/ -v
python3 -m pytest tests/test_pipeline.py::test_parse_amount_german_negative -v  # einzelner Test
```

### Testabdeckung

| Modul | Tests | Getestete Funktionen |
|---|---|---|
| `test_pipeline.py` | 15 | `parse_amount`, `parse_date`, `assign_categories`, `transaction_hash`, `load_config` |
| `test_app.py` | 4 | `filter_expenses` |

### Neue Tests schreiben

Tests in `tests/` ablegen, Dateiname `test_*.py`. Funktionen mit `def test_*()`.

Verfügbare Module importieren:

```python
from pipeline import parse_amount, assign_categories
from app import filter_expenses
```

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
- Nach Pull immer `make install` (falls neue Abhängigkeiten)
