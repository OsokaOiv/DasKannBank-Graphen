# Code-Prinzipien (Clean Code)

## Single Responsibility
Jede Funktion macht genau eine Sache. Eine Funktion zu plotten, zu rechnen und zu printen ist zu viel – aufteilen.

## DRY (Don't Repeat Yourself)
Gleiche Logik nicht kopieren. Gemeinsame Muster (z. B. Pie-Chart-Erstellung) in eine Hilfsfunktion auslagern.

## Aussagekräftige Namen
Variablen, Funktionen und Dateien sprechend benennen. Keine Abkürzungen (`df`, `vals`) außer bei offensichtlichen Standards (z. B. `df` für DataFrame in pandas). Da das Projekt auf Deutsch ist, werden auch Bezeichner auf Deutsch gewählt, sofern sie im Domain-Kontext auftauchen (Kategorien, Ausgaben, Monat).

## Kurze Funktionen
Funktionen sollten idealerweise unter 20–30 Zeilen bleiben. Wenn eine Funktion länger wird, fehlt vermutlich eine Abstraktionsebene.

## Keine Magic Numbers/Strings
Zahlen und Strings mit Bedeutung (z. B. `dpi=150`, `bar_width=20`) als benannte Konstante oder Parameter definieren, nicht hartkodiert im Funktionskörper.

## Kein Dead Code
Nicht mehr verwendete Imports, Variablen, Funktionen oder Parameter entfernen. Sie verwirren und täuschen vor, dass Funktionalität existiert, die es gar nicht gibt. Vor jedem Commit: kurz prüfen, ob alle Imports noch gebraucht werden.

## Fehler früh abfangen
Ungültige Daten (fehlende Spalten, NaT-Daten, leere DataFrames) so früh wie möglich erkennen und mit klarer Meldung abbrechen. Keine `except: pass`-Schlaufen.

## Typannotationen
Jede Funktion bekommt Typ-Hints für Parameter und Rückgabewert. Erhöht Lesbarkeit und ermöglicht statische Prüfung.

## Keine unnötigen Kommentare
Der Code soll selbsterklärend sein. Ein Kommentar darf nur erklären, **warum** etwas passiert – niemals **was** (das liest man aus dem Code).

## Konfiguration außerhalb des Codes
Alles, was sich ändern kann (Kategorie-Keywords, Schwellwerte, Format-Einstellungen), gehört in Konfigurationsdateien (`.toml`), nicht in den Python-Code.

## if __name__ == "__main__"
Das Hauptprogramm hat nur minimale Logik (Konstanten setzen, `main()` aufrufen). Die eigentliche Arbeit delegiert `main()` an spezialisierte Funktionen.

## Tests
Unit-Tests in `tests/` decken die Kernlogik ab (`parse_amount`, `parse_date`, `categorize`, `transaction_hash`). Änderungen an diesen Funktionen müssen die bestehenden Tests grün halten. Tests ausführen mit:
```bash
make test
```

## Pipeline-Workflow
Jede Änderung durchläuft diesen Zyklus:
1. **Planen** – Was ist das Ziel? (User-Frage verstehen, ggf. nachfragen)
2. **Todos setzen** – Arbeit in kleine Schritte zerlegen (`todowrite`)
3. **Implementieren** – Code schreiben (einzeln, testbar)
4. **Testen** – `python3 pipeline.py` ausführen, Output prüfen; `make test` für Unit-Tests
5. **Dokumentation aktualisieren** – README, Makefile-Help, code-principles.md bei Bedarf anpassen
6. **Code-Qualität prüfen** – Gegen diese Prinzipien reviewen (Dead Code, Typannotationen, …)
7. **Nochmal testen** – Sicherstellen, dass nichts kaputt ging
8. **Committen** – Sauberer Commit mit aussagekräftiger Nachricht
