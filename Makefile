CARGO = cargo
NPM = npm

.PHONY: help build run test check \
        test-rust test-frontend \
        legacy-setup legacy-run legacy-pdf2csv legacy-app legacy-api legacy-test \
        clean

help:
	@echo "╔═══════════════════════════════════════╗"
	@echo "║     DKB Finanz — Build System         ║"
	@echo "╚═══════════════════════════════════════╝"
	@echo ""
	@echo "★ Desktop App (Tauri + React + Rust):"
	@echo "    make build        — Produktionbuild (Tauri)"
	@echo "    make run          — Entwicklung (Tauri dev)"
	@echo "    make test         — Rust + Frontend Tests"
	@echo "    make test-rust    — Nur Rust (cargo test)"
	@echo "    make test-frontend— Nur Frontend (vitest)"
	@echo "    make check        — cargo check (Rust, keine Tests)"
	@echo ""
	@echo "○ Python-Prototyp (legacy/):"
	@echo "    make legacy-setup    — venv + Abhängigkeiten"
	@echo "    make legacy-run      — Alle Diagramme (pipeline.py)"
	@echo "    make legacy-pdf2csv  — PDFs → CSV konvertieren"
	@echo "    make legacy-app      — Streamlit-Dashboard starten"
	@echo "    make legacy-api      — FastAPI-Backend (localhost:8765)"
	@echo "    make legacy-test     — Python-Tests (pytest)"
	@echo ""
	@echo "◇ Sonstiges:"
	@echo "    make clean           — node_modules, target löschen"
	@echo "    make help            — Diese Hilfe"

# ============================================================
# ★ Desktop App (Tauri + React + Rust) — das Hauptprodukt
# ============================================================

build:
	cd desktop && $(NPM) run tauri build

run:
	cd desktop && $(NPM) run tauri dev

test: test-rust test-frontend

test-rust:
	cd desktop/src-tauri && $(CARGO) test -p dkb-core

test-frontend:
	cd desktop && $(NPM) test

check:
	cd desktop/src-tauri && $(CARGO) check

# ============================================================
# ○ Python-Prototyp (legacy/) — historische Referenz
# ============================================================

LEGACY_VENV = legacy/.venv
LEGACY_PYTHON = $(LEGACY_VENV)/bin/python3
LEGACY_PIP = $(LEGACY_VENV)/bin/pip

$(LEGACY_VENV):
	python3 -m venv $(LEGACY_VENV)

legacy-setup: $(LEGACY_VENV)
	$(LEGACY_PIP) install -r legacy/requirements.txt fastapi uvicorn httpx2
	@echo ""
	@echo "Python-Prototyp einsatzbereit. Verwende 'make legacy-run' usw."

legacy-run: $(LEGACY_VENV)
	$(LEGACY_PYTHON) legacy/pipeline.py

legacy-pdf2csv: $(LEGACY_VENV)
	$(LEGACY_PYTHON) legacy/pdf2csv.py

legacy-app: $(LEGACY_VENV)
	$(LEGACY_VENV)/bin/streamlit run legacy/app.py

legacy-api: $(LEGACY_VENV)
	$(LEGACY_PYTHON) legacy/api.py

legacy-test: $(LEGACY_VENV)
	cd legacy && ../$(LEGACY_VENV)/bin/python -m pytest tests/ -v

# ============================================================
# ◇ Aufräumen
# ============================================================

clean:
	rm -rf desktop/node_modules
	rm -rf desktop/src-tauri/target
	rm -rf desktop/dist
	@echo "Desktop-Build-Artefakte entfernt."
	@echo "Python-Prototyp: legacy/.venv manuell löschen falls gewünscht."
