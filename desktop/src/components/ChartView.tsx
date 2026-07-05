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

function normalizeSender(raw: string | undefined | null): string {
  if (!raw || raw === "0") return "Unbekannt";
  return raw.trim().replace(/\s+/g, " ").toUpperCase();
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
          font: { family: "-apple-system, BlinkMacSystemFont, sans-serif" },
          margin: { t: 40, r: 20, b: 60, l: 60 },
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: "100%", height: 420 }}
        useResizeHandler
      />
    </div>
  );
}

function buildTotalPie(expenses: ExpenseRecord[]): ChartFigure {
  const grouped: Record<string, number> = {};
  for (const e of expenses) {
    grouped[e.Kategorie] = (grouped[e.Kategorie] || 0) + e.Betrag;
  }
  const labels = Object.keys(grouped);
  const values = Object.values(grouped);
  const total = values.reduce((a, b) => a + b, 0);

  return {
    data: [
      {
        type: "pie" as const,
        labels,
        values,
        textinfo: "label+percent" as const,
        textposition: "outside" as const,
        hovertemplate: "%{label}<br>%{value:.2f} \u20ac (%{percent})<extra></extra>",
      } as Data,
    ],
    layout: {
      title: { text: `Ausgaben nach Kategorie (Gesamt: ${total.toFixed(2)} \u20ac)` },
    },
  };
}

function fmtMonth(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("de-DE", { month: "short", year: "numeric" });
}

function buildMonthlyLine(expenses: ExpenseRecord[]): ChartFigure {
  const grouped: Record<string, number> = {};
  for (const e of expenses) {
    grouped[e.Monat] = (grouped[e.Monat] || 0) + e.Betrag;
  }
  const months = Object.keys(grouped).sort();
  const labels = months.map(fmtMonth);
  const values = months.map((m) => grouped[m]);

  return {
    data: [
      {
        type: "scatter" as const,
        mode: "lines+markers" as const,
        x: labels,
        y: values,
        line: { color: "#e53935", width: 2 },
        marker: { color: "#e53935", size: 6 },
        hovertemplate: "%{x}<br>%{y:.2f} \u20ac<extra></extra>",
        name: "Ausgaben",
      } as Data,
    ],
    layout: {
      title: { text: "Monatliche Ausgaben" },
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: "Betrag (\u20ac)" }, separatethousands: true },
    },
  };
}

function buildMonthlyStacked(expenses: ExpenseRecord[]): ChartFigure {
  const byMonth: Record<string, Record<string, number>> = {};
  for (const e of expenses) {
    if (!byMonth[e.Monat]) byMonth[e.Monat] = {};
    byMonth[e.Monat][e.Kategorie] =
      (byMonth[e.Monat][e.Kategorie] || 0) + e.Betrag;
  }
  const months = Object.keys(byMonth).sort();
  const labels = months.map(fmtMonth);
  const categories = [...new Set(expenses.map((e) => e.Kategorie))];
  const colors = [
    "#e53935", "#1e88e5", "#43a047", "#fb8c00", "#8e24aa",
    "#00acc1", "#f4511e", "#3949ab", "#c0ca33", "#6d4c41",
  ];

  const traces: Data[] = categories.map((cat, i) => ({
    type: "bar" as const,
    name: cat,
    x: labels,
    y: months.map((m) => byMonth[m][cat] || 0),
    marker: { color: colors[i % colors.length] },
    hovertemplate: `%{x}<br>${cat}: %{y:.2f} \u20ac<extra></extra>`,
  } as Data));

  return {
    data: traces,
    layout: {
      title: { text: "Monatliche Ausgaben nach Kategorie" },
      barmode: "stack" as const,
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: "Betrag (\u20ac)" }, separatethousands: true },
      legend: { orientation: "h" as const, y: -0.2 },
    },
  };
}

function buildIncomeBar(income: IncomeRecord[]): ChartFigure {
  const byMonth: Record<string, Record<string, number>> = {};
  const senders = new Set<string>();
  for (const i of income) {
    const sender = normalizeSender(i["Zahlungspflichtige*r"]);
    senders.add(sender);
    if (!byMonth[i.Monat]) byMonth[i.Monat] = {};
    byMonth[i.Monat][sender] = (byMonth[i.Monat][sender] || 0) + i.Betrag;
  }
  const months = Object.keys(byMonth).sort();
  const labels = months.map(fmtMonth);
  const colors = ["#43a047", "#1e88e5", "#fb8c00", "#8e24aa", "#e53935", "#00acc1"];

  const traces: Data[] = [...senders].map((sender, i) => ({
    type: "bar" as const,
    name: sender,
    x: labels,
    y: months.map((m) => byMonth[m][sender] || 0),
    marker: { color: colors[i % colors.length] },
    hovertemplate: `${sender}<br>%{x}<br>%{y:.2f} \u20ac<extra></extra>`,
  } as Data));

  return {
    data: traces,
    layout: {
      title: { text: "Monatliche Einnahmen nach Sender" },
      barmode: "stack" as const,
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: "Betrag (\u20ac)" }, separatethousands: true },
      legend: { orientation: "h" as const, y: -0.2 },
    },
  };
}

function buildIncomePie(income: IncomeRecord[]): ChartFigure {
  const grouped: Record<string, number> = {};
  for (const i of income) {
    const sender = normalizeSender(i["Zahlungspflichtige*r"]);
    grouped[sender] = (grouped[sender] || 0) + i.Betrag;
  }
  const labels = Object.keys(grouped);
  const values = Object.values(grouped);
  const total = values.reduce((a, b) => a + b, 0);

  return {
    data: [
      {
        type: "pie" as const,
        labels,
        values,
        textinfo: "label+percent" as const,
        textposition: "outside" as const,
        hovertemplate: "%{label}<br>%{value:.2f} \u20ac (%{percent})<extra></extra>",
      } as Data,
    ],
    layout: {
      title: { text: `Einnahmen nach Sender (Gesamt: ${total.toFixed(2)} \u20ac)` },
    },
  };
}

function buildIncomeLine(income: IncomeRecord[]): ChartFigure {
  const byMonth: Record<string, Record<string, number>> = {};
  const senders = new Set<string>();
  for (const i of income) {
    const sender = normalizeSender(i["Zahlungspflichtige*r"]);
    senders.add(sender);
    if (!byMonth[i.Monat]) byMonth[i.Monat] = {};
    byMonth[i.Monat][sender] = (byMonth[i.Monat][sender] || 0) + i.Betrag;
  }
  const months = Object.keys(byMonth).sort();
  const labels = months.map(fmtMonth);
  const colors = ["#43a047", "#1e88e5", "#fb8c00", "#8e24aa", "#e53935", "#00acc1"];

  const traces: Data[] = [...senders].map((sender, i) => ({
    type: "scatter" as const,
    mode: "lines+markers" as const,
    name: sender,
    x: labels,
    y: months.map((m) => byMonth[m][sender] || 0),
    line: { color: colors[i % colors.length], width: 2 },
    marker: { color: colors[i % colors.length], size: 6 },
    hovertemplate: `${sender}<br>%{x}<br>%{y:.2f} \u20ac<extra></extra>`,
  } as Data));

  return {
    data: traces,
    layout: {
      title: { text: "Monatliche Einnahmen nach Sender" },
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: "Betrag (\u20ac)" }, separatethousands: true },
      legend: { orientation: "h" as const, y: -0.25 },
    },
  };
}

function buildSaldo(profitLoss: ProfitLossRecord[]): ChartFigure {
  const months = profitLoss.map((p) => p.Monat);
  const labels = months.map(fmtMonth);
  const values = profitLoss.map((p) => p.Differenz);
  const colors = values.map((v) => v >= 0 ? "#2e7d32" : "#c62828");

  return {
    data: [
      {
        type: "bar" as const,
        x: labels,
        y: values,
        marker: { color: colors },
        hovertemplate: "%{x}<br>%{y:.2f} \u20ac<extra></extra>",
        name: "Saldo",
      } as Data,
    ],
    layout: {
      title: { text: "Gewinn / Verlust pro Monat" },
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: "Saldo (\u20ac)" }, separatethousands: true },
    },
  };
}

function buildIncomeVsExpenses(profitLoss: ProfitLossRecord[]): ChartFigure {
  const months = profitLoss.map((p) => p.Monat);
  const labels = months.map(fmtMonth);

  return {
    data: [
      {
        type: "bar" as const,
        name: "Einnahmen",
        x: labels,
        y: profitLoss.map((p) => p.Einnahmen),
        marker: { color: "#43a047" },
        hovertemplate: "%{x}<br>%{y:.2f} \u20ac<extra></extra>",
      } as Data,
      {
        type: "bar" as const,
        name: "Ausgaben",
        x: labels,
        y: profitLoss.map((p) => p.Ausgaben),
        marker: { color: "#e53935" },
        hovertemplate: "%{x}<br>%{y:.2f} \u20ac<extra></extra>",
      } as Data,
    ],
    layout: {
      title: { text: "Einnahmen vs. Ausgaben pro Monat" },
      barmode: "group" as const,
      xaxis: { title: { text: "Monat" } },
      yaxis: { title: { text: "Betrag (\u20ac)" }, separatethousands: true },
      legend: { orientation: "h" as const, y: -0.2 },
    },
  };
}
