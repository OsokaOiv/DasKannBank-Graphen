# DasKannBank-Graphen

Pipeline zum Auswerten von DKB-Kontoauszügen (CSV/PDF) und Visualisieren der Ausgaben – als Tauri-Desktop-App (React + Rust), statische Diagramme (matplotlib) oder interaktives Dashboard (Streamlit + Plotly).

- [Architektur](architecture.md) – Datenfluss, Module (Rust dkb-core + Python Legacy), Datenmodell
- [Nutzung](usage.md) – Desktop-App, CLI-Befehle, Makefile-Targets, Streamlit-Dashboard
- [Konfiguration](configuration.md) – `categories.toml`, `pipeline.toml`
- [Entwicklung](development.md) – Code-Prinzipien, Tests (35 Rust + 5 Frontend + 29 Python), Workflow
