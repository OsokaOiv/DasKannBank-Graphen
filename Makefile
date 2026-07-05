VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

.PHONY: help install run run-total run-yearly run-monthly run-monthly-pies run-income run-income-pie run-profit pdf2csv test clean app api desktop-install desktop-dev

help:
	@echo "Verfügbare Befehle:"
	@echo "  make install           — Virtuelle Umgebung anlegen + Abhängigkeiten installieren"
	@echo "  make run               — Alle Diagramme erstellen"
	@echo "  make run-total         — Nur Gesamt-Kreisdiagramm"
	@echo "  make run-yearly        — Nur Kreisdiagramme pro Jahr"
	@echo "  make run-monthly       — Nur monatliche Diagramme (Linie + Balken)"
	@echo "  make run-monthly-pies  — Nur Kreisdiagramme pro Monat"
	@echo "  make run-income        — Nur Einnahmen-Diagramme"
	@echo "  make run-income-pie    — Nur Einnahmen-Kreisdiagramm"
	@echo "  make run-profit        — Nur Gewinn/Verlust-Diagramm"
	@echo "  make pdf2csv           — PDFs aus pdf/ in CSV konvertieren"
	@echo "  make app               — Streamlit-Dashboard starten (interaktiv)"
	@echo "  make api               — FastAPI-Backend starten (localhost:8765)"
	@echo "  make desktop-install   — npm-Abhängigkeiten für Desktop-App installieren"
	@echo "  make desktop-dev       — FastAPI + Vite dev server starten"
	@echo "  make test              — Tests ausführen (pytest)"
	@echo "  make clean             — Diagramme, venv und gecachte PDF-Daten löschen"

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install matplotlib pandas pdfplumber pytest streamlit plotly fastapi uvicorn[standard]

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

run-income: $(VENV)
	$(PYTHON) pipeline.py income

run-income-pie: $(VENV)
	$(PYTHON) pipeline.py income-pie

run-profit: $(VENV)
	$(PYTHON) pipeline.py profit

test: $(VENV)
	$(PYTHON) -m pytest tests/ -v

pdf2csv: $(VENV)
	$(PYTHON) pdf2csv.py

app: $(VENV)
	$(VENV)/bin/streamlit run app.py

api: $(VENV)
	$(PYTHON) api.py

desktop-install:
	cd desktop && npm install

desktop-dev:
	$(PYTHON) api.py &
	cd desktop && npm run dev

clean:
	rm -rf graphs/*.png
	rm -rf $(VENV)
