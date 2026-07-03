# DasKannBank-Graphen

Pipeline zum Auswerten von DKB-Kontoauszügen (CSV) und Visualisieren der Ausgaben – als statische Diagramme (matplotlib) oder interaktives Dashboard (Streamlit + Plotly).

## Kurzstart

```bash
make install     # Setup + Abhängigkeiten
make run         # Alle Diagramme (PNG)
make app         # Interaktives Dashboard (Browser)
```

## Dokumentation

| Thema | Inhalt |
|---|---|
| [Architektur](docs/architecture.md) | Datenfluss, Module, Datenmodell |
| [Nutzung](docs/usage.md) | CLI-Befehle, Dashboard, PDF-Konvertierung, Tests |
| [Konfiguration](docs/configuration.md) | categories.toml, pipeline.toml |
| [Entwicklung](docs/development.md) | Code-Prinzipien, Projektstruktur, Workflow |


