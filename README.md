# DasKannBank-Graphen

Pipeline zum Auswerten von DKB-Kontoauszügen (CSV) und Visualisieren der Ausgaben.

## Struktur

```
.
├── csv/                ← Kontoauszüge als CSV hier ablegen
├── graphs/             ← generierte Diagramme
├── categories.toml     ← Keyword-Regeln für Kategorien
├── pipeline.py         ← Hauptskript
├── Makefile            ← Hilfsbefehle
└── .venv/              ← virtuelle Python-Umgebung
```

## Setup

```bash
make install
```

## Nutzung

```bash
make run
```

Die Pipeline:
1. Liest **alle** `csv/*.csv` ein (beliebig viele, z. B. mehrere Jahre)
2. Filtert Ausgaben (negative Beträge)
3. Kategorisiert anhand der Regeln in `categories.toml`
4. Zeigt eine Gesamt-Tabelle + monatliche Aufschlüsselung
5. Erzeugt zwei Diagramme in `graphs/`:
   - `ausgaben_nach_kategorie.png` – Kreisdiagramm (Gesamt)
   - `ausgaben_pro_monat.png` – Gestapeltes Balkendiagramm (monatlich)

## Kategorien anpassen

`categories.toml` bearbeiten – neue Kategorien oder Keywords ergänzen.
Nicht zugeordnete Ausgaben landen automatisch in **Sonstige**.

```toml
[groceries]
keywords = ["REWE", "Lidl", "EDEKA"]

[dining]
keywords = ["RESTAURANT", "MCDONALD"]
```

Keyword-Vergleich erfolgt **Groß-/Kleinschreibungsunabhängig** (alles wird in Großbuchstaben geprüft).

## Datenformat

Erwartet werden semikolongetrennte CSVs im DKB-Format mit Blattkopf
und einer Zeile `"Buchungsdatum";"Wertstellung";...;"Betrag (€)";...`.
Beträge im deutschen Format (Komma als Dezimaltrenner).
Datum im Format `DD.MM.YY`.

Aufruf ohne venv:
```bash
source .venv/bin/activate && python3 pipeline.py
```
