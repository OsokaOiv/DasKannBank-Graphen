import { useMemo, useState } from "react";
import Plot from "react-plotly.js";
import type { ExpenseRecord, IncomeRecord, ProfitLossRecord } from "../types";
import type * as Plotly from "plotly.js";

type Data = Plotly.Data;
type Layout = Partial<Plotly.Layout>;

interface ChartFigure {
  data: Data[];
  layout: Layout;
}

interface Props {
  expenses: ExpenseRecord[];
  income: IncomeRecord[];
  profitLoss: ProfitLossRecord[];
}

function cssVar(name: string): string {
  if (typeof document === "undefined") return "";
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

const COLOR_EXPENSE = "#e53935";
const COLOR_INCOME = "#43a047";
const COLOR_POSITIVE = "#2e7d32";
const COLOR_NEGATIVE = "#c62828";
const COLORS_CATEGORY = [
  "#e53935", "#1e88e5", "#43a047", "#fb8c00", "#8e24aa",
  "#00acc1", "#f4511e", "#3949ab", "#c0ca33", "#6d4c41",
];
const COLORS_SENDER = ["#43a047", "#1e88e5", "#fb8c00", "#8e24aa", "#e53935", "#00acc1"];
const LAYOUT_MARGIN = { t: 40, r: 20, b: 60, l: 60 };
const CHART_HEIGHT = 420;
const EURO = "\u20ac";

const HOVER_TEMPLATE = "%{x}<br>%{y:.2f} " + EURO + "<extra></extra>";
const HOVER_PIE = "%{label}<br>%{value:.2f} " + EURO + " (%{percent})<extra></extra>";

function normalizeSender(raw: string | undefined | null): string {
  if (!raw || raw === "0") return "Unbekannt";
  return raw.trim().replace(/\s+/g, " ").toUpperCase();
}

function fmtMonat(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("de-DE", { month: "short", year: "numeric" });
}

function groupByCategory(records: ExpenseRecord[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of records) {
    out[r.Kategorie] = (out[r.Kategorie] || 0) + r.Betrag;
  }
  return out;
}

function groupBySender(records: IncomeRecord[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of records) {
    const sender = normalizeSender(r["Zahlungspflichtige*r"]);
    out[sender] = (out[sender] || 0) + r.Betrag;
  }
  return out;
}

function groupMonthlyByCategory(records: ExpenseRecord[]): {
  months: string[];
  categories: string[];
  data: Record<string, Record<string, number>>;
} {
  const byMonth: Record<string, Record<string, number>> = {};
  for (const r of records) {
    if (!byMonth[r.Monat]) byMonth[r.Monat] = {};
    byMonth[r.Monat][r.Kategorie] = (byMonth[r.Monat][r.Kategorie] || 0) + r.Betrag;
  }
  const months = Object.keys(byMonth).sort();
  const categories = [...new Set(records.map((r) => r.Kategorie))];
  return { months, categories, data: byMonth };
}

function groupMonthlyBySender(records: IncomeRecord[]): {
  months: string[];
  senders: string[];
  data: Record<string, Record<string, number>>;
} {
  const byMonth: Record<string, Record<string, number>> = {};
  const senders = new Set<string>();
  for (const r of records) {
    const sender = normalizeSender(r["Zahlungspflichtige*r"]);
    senders.add(sender);
    if (!byMonth[r.Monat]) byMonth[r.Monat] = {};
    byMonth[r.Monat][sender] = (byMonth[r.Monat][sender] || 0) + r.Betrag;
  }
  const months = Object.keys(byMonth).sort();
  return { months, senders: [...senders], data: byMonth };
}

function buildPieFigure(
  labels: string[],
  values: number[],
  total: number,
  title: string,
): ChartFigure {
  return {
    data: [
      {
        type: "pie" as const,
        labels,
        values,
        textinfo: "label+percent" as const,
        textposition: "outside" as const,
        hovertemplate: HOVER_PIE,
      } as Data,
    ],
    layout: {
      title: { text: `${title} (Gesamt: ${total.toFixed(2)} ${EURO})` },
    },
  };
}

function buildBarTraces(
  months: string[],
  labels: string[],
  groups: string[],
  data: Record<string, Record<string, number>>,
  colors: string[],
): Data[] {
  return groups.map((g, i) => ({
    type: "bar" as const,
    name: g,
    x: labels,
    y: months.map((m) => data[m][g] || 0),
    marker: { color: colors[i % colors.length] },
    hovertemplate: `%{x}<br>${g}: %{y:.2f} ${EURO}<extra></extra>`,
  } as Data));
}

function buildScatterTraces(
  months: string[],
  labels: string[],
  groups: string[],
  data: Record<string, Record<string, number>>,
  colors: string[],
): Data[] {
  return groups.map((g, i) => ({
    type: "scatter" as const,
    mode: "lines+markers" as const,
    name: g,
    x: labels,
    y: months.map((m) => data[m][g] || 0),
    line: { color: colors[i % colors.length], width: 2 },
    marker: { color: colors[i % colors.length], size: 6 },
    hovertemplate: `%{x}<br>${g}: %{y:.2f} ${EURO}<extra></extra>`,
  } as Data));
}

type ChartType =
  | "Ausgaben \u2013 Kreis (Gesamt)"
  | "Ausgaben \u2013 Linie (Monat)"
  | "Ausgaben \u2013 Balken (Monat)"
  | "Einnahmen \u2013 Balken (Monat)"
  | "Einnahmen \u2013 Linie (Monat)"
  | "Einnahmen \u2013 Kreis"
  | "G/V \u2013 Saldo (Monat)"
  | "G/V \u2013 Vergleich (Monat)";

const CHART_TYPES: ChartType[] = [
  "Ausgaben \u2013 Kreis (Gesamt)",
  "Ausgaben \u2013 Linie (Monat)",
  "Ausgaben \u2013 Balken (Monat)",
  "Einnahmen \u2013 Balken (Monat)",
  "Einnahmen \u2013 Linie (Monat)",
  "Einnahmen \u2013 Kreis",
  "G/V \u2013 Saldo (Monat)",
  "G/V \u2013 Vergleich (Monat)",
];

export default function ChartView({ expenses, income, profitLoss }: Props) {
  const [chartType, setChartType] = useState<ChartType>("Ausgaben \u2013 Kreis (Gesamt)");

  const figure: ChartFigure = useMemo(() => {
    switch (chartType) {
      case "Ausgaben \u2013 Kreis (Gesamt)":
        return buildTotalPie(expenses);
      case "Ausgaben \u2013 Linie (Monat)":
        return buildMonthlyLine(expenses);
      case "Ausgaben \u2013 Balken (Monat)":
        return buildMonthlyStacked(expenses);
      case "Einnahmen \u2013 Balken (Monat)":
        return buildIncomeBar(income);
      case "Einnahmen \u2013 Linie (Monat)":
        return buildIncomeLine(income);
      case "Einnahmen \u2013 Kreis":
        return buildIncomePie(income);
      case "G/V \u2013 Saldo (Monat)":
        return buildSaldo(profitLoss);
      case "G/V \u2013 Vergleich (Monat)":
        return buildIncomeVsExpenses(profitLoss);
      default:
        return buildTotalPie(expenses);
    }
  }, [chartType, expenses, income, profitLoss]);

  return (
    <div className="chart-area">
      <div className="chart-header">
        <h3 id="chart-select-label">Diagramm</h3>
        <select aria-labelledby="chart-select-label" value={chartType} onChange={(event) => setChartType(event.target.value as ChartType)}>
          {CHART_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>
      <Plot
        data={figure.data || []}
        layout={{
          ...figure.layout,
          autosize: true,
          paper_bgcolor: cssVar("--bg-card") || "#fff",
          plot_bgcolor: cssVar("--bg-card") || "#fff",
          font: { color: cssVar("--text") || "#1a202c", family: "Inter, -apple-system, BlinkMacSystemFont, sans-serif" },
          margin: LAYOUT_MARGIN,
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: "100%", height: CHART_HEIGHT }}
        useResizeHandler
      />
    </div>
  );
}

function buildTotalPie(expenses: ExpenseRecord[]): ChartFigure {
  const grouped = groupByCategory(expenses);
  const labels = Object.keys(grouped);
  const values = Object.values(grouped);
  const total = values.reduce((a, b) => a + b, 0);
  return buildPieFigure(labels, values, total, "Ausgaben nach Kategorie");
}

function buildMonthlyLine(expenses: ExpenseRecord[]): ChartFigure {
  const grouped: Record<string, number> = {};
  for (const e of expenses) grouped[e.Monat] = (grouped[e.Monat] || 0) + e.Betrag;
  const months = Object.keys(grouped).sort();
  const labels = months.map(fmtMonat);
  const values = months.map((m) => grouped[m]);

  return {
    data: [
      {
        type: "scatter" as const,
        mode: "lines+markers" as const,
        x: labels,
        y: values,
        line: { color: COLOR_EXPENSE, width: 2 },
        marker: { color: COLOR_EXPENSE, size: 6 },
        hovertemplate: HOVER_TEMPLATE,
        name: "Ausgaben",
      } as Data,
    ],
    layout: {
      title: { text: "Monatliche Ausgaben" },
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: `Betrag (${EURO})` }, separatethousands: true },
    },
  };
}

function buildMonthlyStacked(expenses: ExpenseRecord[]): ChartFigure {
  const { months, categories, data } = groupMonthlyByCategory(expenses);
  const labels = months.map(fmtMonat);
  const traces = buildBarTraces(months, labels, categories, data, COLORS_CATEGORY);

  return {
    data: traces,
    layout: {
      title: { text: "Monatliche Ausgaben nach Kategorie" },
      barmode: "stack" as const,
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: `Betrag (${EURO})` }, separatethousands: true },
      legend: { orientation: "h" as const, y: -0.2 },
    },
  };
}

function buildIncomeBar(income: IncomeRecord[]): ChartFigure {
  const { months, senders, data } = groupMonthlyBySender(income);
  const labels = months.map(fmtMonat);
  const traces = buildBarTraces(months, labels, senders, data, COLORS_SENDER);

  return {
    data: traces,
    layout: {
      title: { text: "Monatliche Einnahmen nach Sender" },
      barmode: "stack" as const,
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: `Betrag (${EURO})` }, separatethousands: true },
      legend: { orientation: "h" as const, y: -0.2 },
    },
  };
}

function buildIncomeLine(income: IncomeRecord[]): ChartFigure {
  const { months, senders, data } = groupMonthlyBySender(income);
  const labels = months.map(fmtMonat);
  const traces = buildScatterTraces(months, labels, senders, data, COLORS_SENDER);

  return {
    data: traces,
    layout: {
      title: { text: "Monatliche Einnahmen nach Sender" },
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: `Betrag (${EURO})` }, separatethousands: true },
      legend: { orientation: "h" as const, y: -0.25 },
    },
  };
}

function buildIncomePie(income: IncomeRecord[]): ChartFigure {
  const grouped = groupBySender(income);
  const labels = Object.keys(grouped);
  const values = Object.values(grouped);
  const total = values.reduce((a, b) => a + b, 0);
  return buildPieFigure(labels, values, total, "Einnahmen nach Sender");
}

function buildSaldo(profitLoss: ProfitLossRecord[]): ChartFigure {
  const labels = profitLoss.map((p) => fmtMonat(p.Monat));
  const values = profitLoss.map((p) => p.Differenz);
  const colors = values.map((v) => v >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE);

  return {
    data: [
      {
        type: "bar" as const,
        x: labels,
        y: values,
        marker: { color: colors },
        hovertemplate: HOVER_TEMPLATE,
        name: "Saldo",
      } as Data,
    ],
    layout: {
      title: { text: "Gewinn / Verlust pro Monat" },
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: `Saldo (${EURO})` }, separatethousands: true },
    },
  };
}

function buildIncomeVsExpenses(profitLoss: ProfitLossRecord[]): ChartFigure {
  const labels = profitLoss.map((p) => fmtMonat(p.Monat));

  return {
    data: [
      {
        type: "bar" as const,
        name: "Einnahmen",
        x: labels,
        y: profitLoss.map((p) => p.Einnahmen),
        marker: { color: COLOR_INCOME },
        hovertemplate: HOVER_TEMPLATE,
      } as Data,
      {
        type: "bar" as const,
        name: "Ausgaben",
        x: labels,
        y: profitLoss.map((p) => p.Ausgaben),
        marker: { color: COLOR_EXPENSE },
        hovertemplate: HOVER_TEMPLATE,
      } as Data,
    ],
    layout: {
      title: { text: "Einnahmen vs. Ausgaben pro Monat" },
      barmode: "group" as const,
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: `Betrag (${EURO})` }, separatethousands: true },
      legend: { orientation: "h" as const, y: -0.2 },
    },
  };
}
