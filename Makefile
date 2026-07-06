VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
CARGO = cargo
NPM = npm

.PHONY: help install install-rust install-frontend \
        run run-total run-yearly run-monthly run-monthly-pies \
        run-income run-income-pie run-profit \
        pdf2csv app api \
        desktop-install desktop-dev desktop-build \
        test test-rust test-frontend test-python \
        check clean

help:
	@echo "Verfügbare Befehle:"
	@echo ""
	@echo "  Python (Legacy):"
	@echo "    make install           — venv + Abhängigkeiten installieren"
	@echo "    make run               — Alle Diagramme erstellen"
	@echo "    make pdf2csv           — PDFs aus pdf/ in CSV konvertieren"
	@echo "    make app               — Streamlit-Dashboard starten"
	@echo "    make api               — FastAPI-Backend starten (localhost:8765)"
	@echo ""
	@echo "  Rust + Frontend (Desktop):"
	@echo "    make install-rust      — Rust-Toolchain prüfen"
	@echo "    make install-frontend  — npm-Abhängigkeiten installieren"
	@echo "    make desktop-dev       — Web-Server + Vite dev server"
	@echo "    make desktop-build     — Tauri-Produktionbuild"
	@echo ""
	@echo "  Tests:"
	@echo "    make test              — Alle Tests (Rust + Frontend + Python)"
	@echo "    make test-rust         — Nur Rust-Tests (cargo test)"
	@echo "    make test-frontend     — Nur Frontend-Tests (vitest)"
	@echo "    make test-python       — Nur Python-Tests (pytest)"
	@echo ""
	@echo "  Sonstiges:"
	@echo "    make check             — cargo check (Rust)"
	@echo "    make clean             — venv, node_modules löschen"

# ---- Python (Legacy) ----
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

pdf2csv: $(VENV)
	$(PYTHON) pdf2csv.py

app: $(VENV)
	$(VENV)/bin/streamlit run app.py

api: $(VENV)
	$(PYTHON) api.py

# ---- Rust + Frontend (Desktop) ----
install-rust:
	rustup target add x86_64-unknown-linux-gnu 2>/dev/null || true
	rustup target add aarch64-apple-darwin 2>/dev/null || true

install-frontend:
	cd desktop && $(NPM) install

desktop-install: install-frontend

desktop-dev:
	cd desktop/src-tauri && cargo run --bin web-server &
	cd desktop && $(NPM) run dev

desktop-build:
	cd desktop && $(NPM) run tauri build

# ---- Tests ----
test-rust:
	cd desktop/src-tauri && $(CARGO) test -p dkb-core

test-frontend:
	cd desktop && $(NPM) test

test-python: $(VENV)
	$(PYTHON) -m pytest tests/ -v

test: test-rust test-frontend

# ---- Checks ----
check:
	cd desktop/src-tauri && $(CARGO) check

# ---- Clean ----
clean:
	rm -rf graphs/*.png
	rm -rf $(VENV)
	rm -rf desktop/node_modules
	rm -rf desktop/src-tauri/target
