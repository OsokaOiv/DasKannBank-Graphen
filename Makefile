VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

.PHONY: help install run clean

help:
	@echo "Verfügbare Befehle:"
	@echo "  make install   — Virtuelle Umgebung anlegen + Abhängigkeiten installieren"
	@echo "  make run       — Pipeline ausführen (CSV → Auswertung + Diagramm)"
	@echo "  make clean     — Plots und ggf. Cache löschen"

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV)
	$(PIP) install matplotlib pandas

run: $(VENV)
	$(PYTHON) pipeline.py

clean:
	rm -rf graphs/*.png
	rm -rf $(VENV)
