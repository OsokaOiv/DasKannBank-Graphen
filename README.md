# DasKannBank-Graphen

Pipeline zum Auswerten von DKB-Kontoauszügen (CSV) und Visualisieren der Ausgaben.

## Struktur

```
.
├── csv/                ← Kontoauszüge als CSV hier ablegen
├── pdf/                ← Anonymisierte PDFs zum Konvertieren
├── graphs/             ← generierte Diagramme
├── categories.toml     ← Keyword-Regeln für Kategorien
├── pipeline.py         ← Hauptskript (CSV → Diagramme)
├── pdf2csv.py          ← PDF → CSV Konverter
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
5. Erzeugt Diagramme in `graphs/`:
   - `ausgaben_nach_kategorie.png` – Kreisdiagramm (Gesamt)
   - `ausgaben_linien_pro_monat.png` – Liniendiagramm (monatlicher Verlauf pro Kategorie)
   - `ausgaben_gestapelt_pro_monat.png` – Gestapeltes Balkendiagramm (monatlich)
   - `ausgaben_YYYY.png` – Kreisdiagramm pro Jahr
   - `ausgaben_YYYY-MM.png` – Kreisdiagramm pro Monat

Selektive Ausführung über CLI-Argumente:
```bash
python3 pipeline.py total       # nur Gesamt-Kreisdiagramm
python3 pipeline.py yearly      # nur Jahres-Kreisdiagramme
python3 pipeline.py monthly     # nur Liniendiagramm
python3 pipeline.py monthly-pies  # nur Monats-Kreisdiagramme
```

## Kategorien anpassen

`categories.toml` bearbeiten – neue Kategorien oder Keywords ergänzen.
Nicht zugeordnete Ausgaben landen automatisch in **Sonstige**.

```toml
[Lebensmittel]
keywords = ["REWE", "Lidl", "EDEKA"]

["Essen & Trinken"]
keywords = ["RESTAURANT"]
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

## PDF-Konvertierung (optional)

Anonymisierte PDF-Kontoauszüge in `pdf/` ablegen, dann:
```bash
make pdf2csv              # normale Ausführung
python3 pdf2csv.py --debug  # mit Debug-Ausgabe (extrahierten Text als .txt speichern)
```
Erzeugt für jede PDF eine CSV in `csv/` im gleichen Format wie der DKB-Export. Anschließend wie gewohnt `make run`.
```


