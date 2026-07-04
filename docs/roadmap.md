# Roadmap

Ideen für die Weiterentwicklung, grob sortiert nach Aufwand/Nutzen.

---

## Klein / Sofort nutzbar

- **CSV-Upload im Dashboard** – per Drag-and-drop in Streamlit, kein manuelles Kopieren nach `csv/` mehr nötig
- ~~**Einnahmen-Tab** – Gehalt, Zinsen, Rückerstattungen sichtbar machen (separater Tab im Dashboard)~~ ✅
- **Responsive Layout** – optimized für Tablets und Handy-Bildschirme

## Mittel

- **Budget-Tracking** – Monatslimits pro Kategorie in `pipeline.toml`, Dashboard zeigt Fortschritt mit Farbampel
- **Automatisches Lernen** – bereits kategorisierte Payees merken, Neuzugänge automatisch zuordnen
- **Jahresvergleich** – zwei Jahre im selben Liniendiagramm (z. B. 2025 vs 2026)
- **Export-Funktion** – Dashboard als PDF oder PNG speichern

## Größer / Architektur

- **Docker** – Container mit `docker compose up`, keine händische venv-Einrichtung
- **SQLite statt CSV** – persistentes Speichern von Transaktionen + gelernten Regeln
- **Monatsbericht als PDF** – automatisierter PDF-Report mit Chart + Tabelle
- **Monatliche Erinnerung** – E-Mail- oder Desktop-Notification "Neuen Kontoauszug importieren"
