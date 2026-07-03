VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

.PHONY: help install run run-total run-yearly run-monthly clean

help:
	@echo "Verfügbare Befehle:"
	@echo "  make install       — Virtuelle Umgebung anlegen + Abhängigkeiten installieren"
	@echo "  make run           — Alle Diagramme erstellen"
	@echo "  make run-total     — Nur Gesamt-Kreisdiagramm"
	@echo "  make run-yearly    — Nur Kreisdiagramme pro Jahr"
	@echo "  make run-monthly   — Nur monatliche Diagramme (Linie + Kreis)"
	@echo "  make clean         — Diagramme und venv löschen"

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install matplotlib pandas

run: $(VENV)
	$(PYTHON) pipeline.py

run-total: $(VENV)
	$(PYTHON) pipeline.py total

run-yearly: $(VENV)
	$(PYTHON) pipeline.py yearly

run-monthly: $(VENV)
	$(PYTHON) pipeline.py monthly

clean:
	rm -rf graphs/*.png
	rm -rf $(VENV)
