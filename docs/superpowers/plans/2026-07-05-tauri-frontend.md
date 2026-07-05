# Tauri Desktop Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Streamlit UI with a Tauri desktop app (React + Plotly.js frontend, Python FastAPI backend).

**Architecture:** Keep all existing Python data processing code untouched. Add a FastAPI server (`api.py`) that serves the same data as JSON. Build a React frontend with identical charts/filters. Wrap everything in Tauri — the Rust shell spawns the Python backend as a subprocess and renders the React frontend in a native webview. Result: single `.exe`.

**Tech Stack:** Tauri v2 (Rust), React + Vite + TypeScript, Plotly.js, Python + FastAPI + uvicorn

## Prerequisites

- Rust toolchain (`rustup` + `cargo`)
- Node.js v20+ with npm
- Python 3.10+ with venv (already exists in `.venv/`)
- On Windows: WebView2 runtime (pre-installed on Win10+)

## File Structure (all new, none removed)

```
/desktop/
├── src-tauri/
│   ├── src/
│   │   ├── main.rs        # Tauri entry: window + sidecar launch
│   │   └── lib.rs
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── build.rs
│   └── icons/
├── src/                   # React frontend
│   ├── App.tsx            # Main component
│   ├── main.tsx           # React entry
│   ├── components/
│   │   ├── Sidebar.tsx    # Month/category filters, chart selector
│   │   ├── SummaryCards.tsx  # Metrics row
│   │   ├── ChartView.tsx  # Renders selected Plotly chart
│   │   ├── DataTables.tsx # Collapsible tables
│   │   └── Uncategorized.tsx  # Sonstige table
│   ├── api.ts             # HTTP calls to FastAPI
│   ├── types.ts           # TypeScript interfaces
│   └── vite-env.d.ts
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
api.py                     # FastAPI backend (project root)
requirements-api.txt       # FastAPI + uvicorn deps
```

## Global Constraints

- Do NOT modify, delete, or rename any existing files (`app.py`, `pipeline.py`, `data.py`, `constants.py`, `pdf2csv.py`, `categories.toml`, `pipeline.toml`, etc.)
- All existing Python tests must continue to pass
- The Tauri desktop frontend must replicate the same charts and filters as the current Streamlit app
- Plotly.js should be used for charts (same visual appearance as Streamlit's plotly)
- The `csv/` directory is the single source of data (same as before)
- No new Python dependencies beyond FastAPI + uvicorn

---

### Task 1: Install Rust + Tauri CLI

- [ ] **Step 1: Install Rust via rustup**

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
```

Expected: `rustc --version` and `cargo --version` print version numbers.

- [ ] **Step 2: Install Tauri CLI**

```bash
cargo install tauri-cli --version "^2"
```

Expected: `cargo tauri --version` prints a version.

- [ ] **Step 3: Install FastAPI dependencies**

Add to `requirements.txt` (or create `requirements-api.txt`):
```
fastapi>=0.110
uvicorn>=0.29
```

Install:
```bash
.venv/bin/pip install fastapi uvicorn
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add fastapi + uvicorn dependencies"
```

---

### Task 2: Create FastAPI Backend (`api.py`)

**Files:**
- Create: `api.py`

**Interfaces:**
- Produces: `GET /api/data` → JSON with expenses, income, categories
- Produces: `POST /api/upload` → saves CSV, returns success
- Produces: `GET /api/health` → health check
- Consumes: `data.py`, `constants.py` (existing)

- [ ] **Step 1: Write `api.py`**

```python
"""FastAPI backend serving the existing data pipeline as JSON."""

from pathlib import Path
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from data import (
    load_categories,
    load_transactions,
    prepare_expenses,
    prepare_income,
    prepare_profit_loss,
)
from constants import CATEGORIES_FILE

app = FastAPI(title="DKB Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize(df):
    """Convert DataFrame to JSON-serializable dict."""
    if df.empty:
        return []
    return df.to_dict(orient="records")


def _convert_dates(records, date_fields=None):
    """Convert datetime objects to ISO strings."""
    if date_fields is None:
        date_fields = ["Datum", "Monat"]
    for rec in records:
        for field in date_fields:
            if field in rec and rec[field] is not None:
                if hasattr(rec[field], "isoformat"):
                    rec[field] = rec[field].isoformat()
    return records


def _build_response():
    """Load all data and return as JSON-serializable dict."""
    categories = load_categories(CATEGORIES_FILE)
    df = load_transactions()
    if df.empty:
        return {"expenses": [], "income": [], "profit_loss": [], "categories": list(categories.keys())}

    expenses = prepare_expenses(df, categories)
    expenses["Monat_Label"] = expenses["Monat"].dt.strftime("%b %Y")
    income = prepare_income(df)
    profit_loss = prepare_profit_loss(expenses, income)

    exp_data = _convert_dates(_serialize(expenses))
    inc_data = _convert_dates(_serialize(income))
    pl_data = _convert_dates(_serialize(profit_loss))

    return {
        "expenses": exp_data,
        "income": inc_data,
        "profit_loss": pl_data,
        "categories": sorted(expenses["Kategorie"].unique().tolist()) if not expenses.empty else [],
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/data")
def get_data():
    return _build_response()


@app.post("/api/upload")
async def upload_csv(file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Nur CSV-Dateien erlaubt")
    csv_dir = Path("csv")
    csv_dir.mkdir(exist_ok=True)
    content = await file.read()
    (csv_dir / file.filename).write_bytes(content)
    return {"saved": file.filename}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
```

- [ ] **Step 2: Start the API and verify it works**

```bash
.venv/bin/python api.py &
sleep 3
curl http://127.0.0.1:8765/api/health
curl http://127.0.0.1:8765/api/data | .venv/bin/python -m json.tool | head -20
kill %1
```

Expected: health returns `{"status":"ok"}`, data returns JSON with expenses/income/profit_loss.

- [ ] **Step 3: Commit**

```bash
git add api.py
git commit -m "feat: add FastAPI backend serving data pipeline as JSON"
```

---

### Task 3: Scaffold Tauri + React Project

**Files:**
- Create: `desktop/` directory with full Tauri project

- [ ] **Step 1: Create Tauri project**

```bash
cd /mnt/c/Users/Fokus/Documents/Projects/DasKannBank-Graphen
mkdir -p desktop && cd desktop
npm create vite@latest . -- --template react-ts
npm install
npm install plotly.js-dist-min react-plotly.js
cargo tauri init
```

Choose:
- App name: `DKB Dashboard`
- Window title: `DKB Ausgaben-Dashboard`
- Dev server URL: `http://localhost:5173`
- Frontend dev command: `npm run dev`
- Frontend build command: `npm run build`
- Dev command: `cargo tauri dev`

- [ ] **Step 2: Configure Tauri for sidecar and window**

Edit `desktop/src-tauri/tauri.conf.json`:
```json
{
  "$schema": "https://raw.githubusercontent.com/tauri-apps/tauri/dev/crates/tauri-config-schema/schema.json",
  "productName": "DKB Dashboard",
  "version": "0.1.0",
  "identifier": "com.dkb-dashboard.app",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:5173",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "app": {
    "windows": [
      {
        "title": "DKB Ausgaben-Dashboard",
        "width": 1280,
        "height": 800,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
}
```

- [ ] **Step 3: Add shell plugin to Cargo.toml for sidecar support**

Edit `desktop/src-tauri/Cargo.toml`:
```toml
[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"

[build-dependencies]
tauri-build = { version = "2", features = [] }
```

- [ ] **Step 4: Register shell plugin in `lib.rs`**

```rust
#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

- [ ] **Step 5: Commit**

```bash
git add desktop/
git commit -m "feat: scaffold Tauri + React project"
```

---

### Task 4: Build React Frontend Components

**Files:**
- Modify: `desktop/src/App.tsx`
- Create: `desktop/src/api.ts`, `desktop/src/types.ts`
- Create: `desktop/src/components/Sidebar.tsx`
- Create: `desktop/src/components/SummaryCards.tsx`
- Create: `desktop/src/components/ChartView.tsx`
- Create: `desktop/src/components/DataTables.tsx`
- Create: `desktop/src/components/Uncategorized.tsx`

**Interfaces:**
- Consumes: `GET /api/data` from Task 2
- Consumes: `POST /api/upload` from Task 2

- [ ] **Step 1: Create types**

`desktop/src/types.ts`:
```typescript
export interface Transaction {
  Datum: string;
  Betrag: number;
  Kategorie: string;
  Monat: string;
  Monat_Label: string;
  Jahr: number;
  Zahlungsempfänger?: string;
  Verwendungszweck?: string;
}

export interface IncomeRecord {
  Datum: string;
  Betrag: number;
  Monat: string;
  Monat_Label: string;
  Jahr: number;
  "Zahlungspflichtige*r"?: string;
}

export interface ProfitLoss {
  Monat: string;
  Einnahmen: number;
  Ausgaben: number;
  Differenz: number;
  Status: string;
}

export interface DashboardData {
  expenses: Transaction[];
  income: IncomeRecord[];
  profit_loss: ProfitLoss[];
  categories: string[];
}
```

- [ ] **Step 2: Create API client**

`desktop/src/api.ts`:
```typescript
const API_BASE = "http://127.0.0.1:8765";

export async function fetchDashboardData() {
  const res = await fetch(`${API_BASE}/api/data`);
  if (!res.ok) throw new Error("Failed to fetch data");
  return res.json();
}

export async function uploadCsv(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.ok;
}
```

- [ ] **Step 3: Create Sidebar component**

`desktop/src/components/Sidebar.tsx`:
```tsx
interface SidebarProps {
  months: string[];
  categories: string[];
  selectedMonths: string[];
  selectedCategories: string[];
  chartType: string;
  onMonthsChange: (m: string[]) => void;
  onCategoriesChange: (c: string[]) => void;
  onChartTypeChange: (t: string) => void;
}

const CHART_TYPES = [
  "Kreis (Gesamt)",
  "Kreis (Jahr)",
  "Kreis (Monat)",
  "Linien (Monat)",
  "Gestapelte Balken (Monat)",
  "Einnahmen (Balken)",
  "Einnahmen (Linie)",
  "Einnahmen (Jahr)",
  "Einnahmen (Kreis)",
  "Gewinn/Verlust (Monat)",
];

export function Sidebar({
  months, categories, selectedMonths, selectedCategories,
  chartType, onMonthsChange, onCategoriesChange, onChartTypeChange,
}: SidebarProps) {
  return (
    <aside style={{ width: 260, padding: 16, borderRight: "1px solid #ddd" }}>
      <h2>Filter</h2>
      <div>
        <label>Monate</label>
        <select multiple value={selectedMonths} onChange={e =>
          onMonthsChange(Array.from(e.target.selectedOptions, o => o.value))
        }>
          {months.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
      <div>
        <label>Kategorien</label>
        <select multiple value={selectedCategories} onChange={e =>
          onCategoriesChange(Array.from(e.target.selectedOptions, o => o.value))
        }>
          {categories.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <div>
        <label>Diagramm</label>
        <select value={chartType} onChange={e => onChartTypeChange(e.target.value)}>
          {CHART_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>
    </aside>
  );
}
```

- [ ] **Step 4: Create SummaryCards component**

`desktop/src/components/SummaryCards.tsx`:
```tsx
export function SummaryCards({ totalExpenses, totalIncome, count, categories, months }: {
  totalExpenses: number; totalIncome: number; count: number;
  categories: number; months: number;
}) {
  return (
    <div style={{ display: "flex", gap: 16, padding: "12px 0" }}>
      {[
        ["Ausgaben Gesamt", `${totalExpenses.toFixed(2)} €`],
        ["Einnahmen Gesamt", `${totalIncome.toFixed(2)} €`],
        ["Anzahl Transaktionen", String(count)],
        ["Kategorien", String(categories)],
        ["Monate", String(months)],
      ].map(([label, value]) => (
        <div key={label} style={{
          flex: 1, padding: 12, borderRadius: 8, background: "#f5f5f5",
          textAlign: "center",
        }}>
          <div style={{ fontSize: 12, color: "#666" }}>{label}</div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 5: Create ChartView component** (wraps Plotly charts)

`desktop/src/components/ChartView.tsx`:
```tsx
import Plot from "react-plotly.js";

interface ChartViewProps {
  chartType: string;
  expenses: any[];
  income: any[];
  profitLoss: any[];
}

function buildPie(data: any[], labelField: string, valueField: string, title: string) {
  return {
    data: [{
      type: "pie" as const,
      labels: data.map(d => d[labelField]),
      values: data.map(d => d[valueField]),
      textinfo: "label+percent",
      hovertemplate: `%{label}<br>%{value:.2f} €<extra></extra>`,
    }],
    layout: { title, width: undefined, height: 450 },
  };
}

function buildMonthlyLine(data: any[], title: string) {
  const categories = [...new Set(data.map(d => d.Kategorie))];
  const months = [...new Set(data.map(d => d.Monat_Label))].sort();
  const traces = categories.map(cat => {
    const catData = data.filter(d => d.Kategorie === cat);
    return {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: cat,
      x: months,
      y: months.map(m => {
        const match = catData.find(d => d.Monat_Label === m);
        return match ? match.Betrag : 0;
      }),
      hovertemplate: `${cat}<br>%{x}<br>%{y:.2f} €<extra></extra>`,
    };
  });
  return { data: traces, layout: { title, xaxis: { title: "Monat" }, yaxis: { title: "Betrag (€)" } } };
}

function buildStackedBar(data: any[], title: string) {
  const categories = [...new Set(data.map(d => d.Kategorie))];
  const months = [...new Set(data.map(d => d.Monat_Label))].sort();
  const traces = categories.map(cat => {
    const catData = data.filter(d => d.Kategorie === cat);
    return {
      type: "bar" as const,
      name: cat,
      x: months,
      y: months.map(m => {
        const match = catData.find(d => d.Monat_Label === m);
        return match ? match.Betrag : 0;
      }),
      hovertemplate: `${cat}<br>%{x}<br>%{y:.2f} €<extra></extra>`,
    };
  });
  return {
    data: traces,
    layout: { barmode: "stack", title, xaxis: { title: "Monat" }, yaxis: { title: "Betrag (€)" } },
  };
}

function buildIncomeBar(data: any[], title: string) {
  const senders = [...new Set(data.map(d => d["Zahlungspflichtige*r"]))];
  const months = [...new Set(data.map(d => d.Monat_Label))].sort();
  const traces = senders.map(s => {
    const sData = data.filter(d => d["Zahlungspflichtige*r"] === s);
    return {
      type: "bar" as const,
      name: s,
      x: months,
      y: months.map(m => {
        const match = sData.find(d => d.Monat_Label === m);
        return match ? match.Betrag : 0;
      }),
      hovertemplate: `${s}<br>%{x}<br>%{y:.2f} €<extra></extra>`,
    };
  });
  return {
    data: traces,
    layout: { barmode: "stack", title, xaxis: { title: "Monat" }, yaxis: { title: "Betrag (€)" } },
  };
}

function buildIncomeLine(data: any[], title: string) {
  const senders = [...new Set(data.map(d => d["Zahlungspflichtige*r"]))];
  const months = [...new Set(data.map(d => d.Monat_Label))].sort();
  const traces = senders.map(s => {
    const sData = data.filter(d => d["Zahlungspflichtige*r"] === s);
    return {
      type: "scatter" as const,
      mode: "lines+markers" as const,
      name: s,
      x: months,
      y: months.map(m => {
        const match = sData.find(d => d.Monat_Label === m);
        return match ? match.Betrag : 0;
      }),
      text: months.map(m => {
        const match = sData.find(d => d.Monat_Label === m);
        return match ? `${match.Betrag.toFixed(2)} €` : "";
      }),
      textposition: "top center" as const,
      textfont: { size: 9 },
      hovertemplate: `${s}<br>%{x}<br>%{y:.2f} €<extra></extra>`,
    };
  });
  return {
    data: traces,
    layout: {
      title, xaxis: { title: "Monat" }, yaxis: { title: "Betrag (€)", rangemode: "tozero" },
    },
  };
}

function buildIncomeYearly(data: any[], title: string) {
  const senders = [...new Set(data.map(d => d["Zahlungspflichtige*r"]))];
  const years = [...new Set(data.map(d => d.Jahr))].sort();
  const traces = senders.map(s => {
    const sData = data.filter(d => d["Zahlungspflichtige*r"] === s);
    return {
      type: "bar" as const,
      name: s,
      x: years,
      y: years.map(y => {
        const match = sData.find(d => d.Jahr === y);
        return match ? match.Betrag : 0;
      }),
      hovertemplate: `${s}<br>%{x}<br>%{y:.2f} €<extra></extra>`,
    };
  });
  return {
    data: traces,
    layout: { barmode: "stack", title, xaxis: { title: "Jahr" }, yaxis: { title: "Betrag (€)" } },
  };
}

function buildProfitLoss(data: any[]) {
  const colors = data.map(d => d.Differenz >= 0 ? "#2ecc71" : "#e74c3c");
  return {
    data: [{
      type: "bar" as const,
      x: data.map(d => d.Monat),
      y: data.map(d => d.Differenz),
      marker: { color: colors },
      hovertemplate: `%{x}<br>Differenz: %{y:.2f} €<extra></extra>`,
    }],
    layout: { title: "Gewinn/Verlust pro Monat", yaxis: { title: "Differenz (€)" }, shapes: [{
      type: "line", xref: "paper", yref: "y", x0: 0, y0: 0, x1: 1, y1: 0,
      line: { color: "gray", dash: "dash" },
    }] },
  };
}

export function ChartView({ chartType, expenses, income, profitLoss }: ChartViewProps) {
  let fig: any;

  switch (chartType) {
    case "Kreis (Gesamt)":
      fig = buildPie(expenses, "Kategorie", "Betrag", "Ausgaben nach Kategorie");
      break;
    case "Kreis (Jahr)":
      fig = buildPie(expenses, "Kategorie", "Betrag", "Ausgaben pro Jahr (Wähle ein Jahr)");
      break;
    case "Kreis (Monat)":
      fig = buildPie(expenses, "Kategorie", "Betrag", "Ausgaben pro Monat (Wähle einen Monat)");
      break;
    case "Linien (Monat)":
      fig = buildMonthlyLine(expenses, "Ausgaben pro Monat nach Kategorie");
      break;
    case "Gestapelte Balken (Monat)":
      fig = buildStackedBar(expenses, "Ausgaben pro Monat nach Kategorie");
      break;
    case "Einnahmen (Balken)":
      fig = buildIncomeBar(income, "Einnahmen pro Monat");
      break;
    case "Einnahmen (Linie)":
      fig = buildIncomeLine(income, "Einnahmen pro Monat (Verlauf)");
      break;
    case "Einnahmen (Jahr)":
      fig = buildIncomeYearly(income, "Einnahmen pro Jahr");
      break;
    case "Einnahmen (Kreis)":
      fig = buildPie(income, "Zahlungspflichtige*r", "Betrag", "Einnahmen nach Sender");
      break;
    case "Gewinn/Verlust (Monat)":
      fig = buildProfitLoss(profitLoss);
      break;
    default:
      fig = { data: [], layout: { title: chartType } };
  }

  return (
    <Plot
      data={fig.data}
      layout={{ ...fig.layout, font: { family: "DejaVu Sans" }, hovermode: "x unified", width: undefined }}
      useResizeHandler
      style={{ width: "100%", height: "100%" }}
      config={{ responsive: true }}
    />
  );
}
```

- [ ] **Step 6: Create DataTables component**

`desktop/src/components/DataTables.tsx`:
```tsx
export function DataTables({ expenses }: { expenses: any[] }) {
  const byCategory = Object.entries(
    expenses.reduce((acc: Record<string, number>, d) => {
      acc[d.Kategorie] = (acc[d.Kategorie] || 0) + d.Betrag;
      return acc;
    }, {})
  ).sort((a, b) => b[1] - a[1]);

  return (
    <details>
      <summary>Tabellarische Übersicht</summary>
      <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead><tr><th>Kategorie</th><th>Betrag (€)</th></tr></thead>
        <tbody>
          {byCategory.map(([cat, val]) => (
            <tr key={cat}><td>{cat}</td><td>{val.toFixed(2)}</td></tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
```

- [ ] **Step 7: Create Uncategorized component**

`desktop/src/components/Uncategorized.tsx`:
```tsx
export function Uncategorized({ expenses }: { expenses: any[] }) {
  const sonstige = expenses.filter(d => d.Kategorie === "Sonstige");
  if (sonstige.length === 0) return <p>Alle Ausgaben sind kategorisiert!</p>;
  const grouped = Object.entries(
    sonstige.reduce((acc: Record<string, { total: number; count: number }>, d: any) => {
      const key = `${d.Zahlungsempfänger}|${d.Verwendungszweck}`;
      if (!acc[key]) acc[key] = { total: 0, count: 0 };
      acc[key].total += d.Betrag;
      acc[key].count += 1;
      return acc;
    }, {})
  ).sort((a, b) => b[1].total - a[1].total);

  return (
    <details>
      <summary>Nicht kategorisierte Ausgaben ({grouped.length} Gruppen)</summary>
      <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead><tr><th>Empfänger</th><th>Betrag (€)</th><th>Anzahl</th></tr></thead>
        <tbody>
          {grouped.map(([key, val]) => (
            <tr key={key}><td>{key}</td><td>{val.total.toFixed(2)}</td><td>{val.count}</td></tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
```

- [ ] **Step 8: Assemble main App component**

`desktop/src/App.tsx`:
```tsx
import { useEffect, useState } from "react";
import { fetchDashboardData } from "./api";
import type { DashboardData } from "./types";
import { Sidebar } from "./components/Sidebar";
import { SummaryCards } from "./components/SummaryCards";
import { ChartView } from "./components/ChartView";
import { DataTables } from "./components/DataTables";
import { Uncategorized } from "./components/Uncategorized";

function filterMonths(data: any[], months: string[]) {
  if (months.length === 0) return data;
  return data.filter(d => months.includes(d.Monat_Label));
}

function filterCategories(data: any[], cats: string[]) {
  if (cats.length === 0) return data;
  return data.filter(d => cats.includes(d.Kategorie));
}

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedMonths, setSelectedMonths] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [chartType, setChartType] = useState("Kreis (Gesamt)");

  useEffect(() => {
    fetchDashboardData().then(setData);
  }, []);

  if (!data) return <div style={{ padding: 40 }}>Lade Daten...</div>;

  const months = [...new Set(data.expenses.map(d => d.Monat_Label))].sort();
  const filteredExpenses = filterCategories(filterMonths(data.expenses, selectedMonths), selectedCategories);
  const filteredIncome = filterMonths(data.income, selectedMonths);
  const totalExpenses = filteredExpenses.reduce((s, d) => s + d.Betrag, 0);
  const totalIncome = filteredIncome.reduce((s, d) => s + d.Betrag, 0);

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "DejaVu Sans" }}>
      <Sidebar
        months={months}
        categories={data.categories}
        selectedMonths={selectedMonths}
        selectedCategories={selectedCategories}
        chartType={chartType}
        onMonthsChange={setSelectedMonths}
        onCategoriesChange={setSelectedCategories}
        onChartTypeChange={setChartType}
      />
      <main style={{ flex: 1, padding: 16, overflowY: "auto" }}>
        <h1>DKB Ausgaben-Dashboard</h1>
        <SummaryCards
          totalExpenses={totalExpenses}
          totalIncome={totalIncome}
          count={filteredExpenses.length}
          categories={new Set(filteredExpenses.map(d => d.Kategorie)).size}
          months={new Set(filteredExpenses.map(d => d.Monat_Label)).size}
        />
        <ChartView
          chartType={chartType}
          expenses={filteredExpenses}
          income={filteredIncome}
          profitLoss={data.profit_loss}
        />
        <DataTables expenses={filteredExpenses} />
        <Uncategorized expenses={filteredExpenses} />
      </main>
    </div>
  );
}
```

- [ ] **Step 9: Verify the frontend builds**

```bash
cd desktop && npm run build
```

Expected: Vite builds the React app to `desktop/dist/`.

- [ ] **Step 10: Commit**

```bash
git add desktop/src/
git commit -m "feat: add React frontend components with Plotly.js"
```

---

### Task 5: Start Python Backend from Tauri

**Files:**
- Create: `desktop/src-tauri/src/main.rs`

- [ ] **Step 1: Write main.rs with sidecar launch**

`desktop/src-tauri/src/main.rs` (if not already created by `cargo tauri init`):

```rust
// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Child};
use std::sync::Mutex;

struct PythonBackend(Mutex<Option<Child>>);

fn start_python_backend() -> Option<Child> {
    let child = Command::new(".venv/bin/python")
        .arg("api.py")
        .spawn();
    match child {
        Ok(c) => {
            println!("Python backend started with PID {}", c.id());
            Some(c)
        }
        Err(e) => {
            eprintln!("Failed to start Python backend: {}", e);
            None
        }
    }
}

fn main() {
    let backend = start_python_backend();
    // Wait a moment for the server to start
    std::thread::sleep(std::time::Duration::from_secs(2));

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(PythonBackend(Mutex::new(backend)))
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Some(state) = window.try_state::<PythonBackend>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            let _ = child.kill();
                            println!("Python backend stopped");
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

Also update `main.rs` to call `run()` from `lib.rs`:

```rust
fn main() {
    app_lib::run();
}
```

And in `lib.rs`:
```rust
pub fn run() {
    // ... same Builder code
}
```

- [ ] **Step 2: Verify the project compiles**

```bash
cd desktop && cargo tauri build
```

Expected: Rust compiles, frontend builds, Tauri packages everything.

- [ ] **Step 3: Commit**

```bash
git add desktop/src-tauri/src/main.rs
git commit -m "feat: launch Python backend from Tauri on startup"
```

---

### Task 6: Package and Distribute

- [ ] **Step 1: Bundle Python with PyInstaller (optional — for standalone .exe)**

If distributing without requiring Python installation:

```bash
.venv/bin/pip install pyinstaller
.venv/bin/pyinstaller --onefile --name dkb-backend api.py
```

Move the resulting binary: `mv dist/dkb-backend desktop/src-tauri/binaries/`

Update `tauri.conf.json` to reference the external binary instead of running Python directly.

- [ ] **Step 2: Build the Tauri desktop app**

```bash
cd desktop
cargo tauri build
```

Expected: A platform-specific installer in `desktop/src-tauri/target/release/bundle/`:
- Windows: `.msi` and `.exe`
- macOS: `.dmg`
- Linux: `.deb`, `.AppImage`

- [ ] **Step 3: Commit final build config**

```bash
git add desktop/src-tauri/tauri.conf.json desktop/src-tauri/Cargo.toml
git commit -m "chore: finalize Tauri build configuration"
```
