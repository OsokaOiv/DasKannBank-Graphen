VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

.PHONY: help install run run-total run-yearly run-monthly run-monthly-pies pdf2csv test clean app

help:
	@echo "Verfügbare Befehle:"
	@echo "  make install           — Virtuelle Umgebung anlegen + Abhängigkeiten installieren"
	@echo "  make run               — Alle Diagramme erstellen"
	@echo "  make run-total         — Nur Gesamt-Kreisdiagramm"
	@echo "  make run-yearly        — Nur Kreisdiagramme pro Jahr"
	@echo "  make run-monthly       — Nur monatliche Diagramme (Linie + Balken)"
	@echo "  make run-monthly-pies  — Nur Kreisdiagramme pro Monat"
	@echo "  make pdf2csv           — PDFs aus pdf/ in CSV konvertieren (benötigt anonymisierte PDFs)"
	@echo "  make app               — Streamlit-Dashboard starten (interaktiv)"
	@echo "  make test              — Tests ausführen (pytest)"
	@echo "  make clean             — Diagramme, venv und gecachte PDF-Daten löschen"

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install matplotlib pandas pdfplumber pytest streamlit plotly

run: $(VENV)
	$(PYTHON) pipeline.py

run-total: $(VENV)
	$(PYTHON) pipeline.py total

run-yearly: $(VENV)
	$(PYTHON) pipeline.py yearly

run-monthly: $(VENV)
	$(PYTHON) pipeline.py monthly

run-monthly-pies: $(VENV)
	$(PYTHON) pipeline.py monthly-pies

test: $(VENV)
	$(PYTHON) -m pytest tests/ -v

pdf2csv: $(VENV)
	$(PYTHON) pdf2csv.py

app: $(VENV)
	$(VENV)/bin/streamlit run app.py

clean:
	rm -rf graphs/*.png
	rm -rf $(VENV)
