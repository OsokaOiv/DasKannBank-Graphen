import type { ExpenseRecord, IncomeRecord } from "../types";

interface Props {
  expenses: ExpenseRecord[];
  income: IncomeRecord[];
}

function sum(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0);
}

const numFmt = new Intl.NumberFormat("de-DE", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function formatCurrency(value: number): string {
  return `${numFmt.format(value)} \u20ac`;
}

export default function SummaryCards({ expenses, income }: Props) {
  const totalExpenses = sum(expenses.map((e) => e.Betrag));
  const totalIncome = sum(income.map((i) => i.Betrag));
  const balance = totalIncome - totalExpenses;

  return (
    <div className="summary-row">
      <div className="summary-card">
        <div className="label">Ausgaben Gesamt</div>
        <div className="value negative">{formatCurrency(totalExpenses)}</div>
      </div>
      <div className="summary-card">
        <div className="label">Einnahmen Gesamt</div>
        <div className="value positive">{formatCurrency(totalIncome)}</div>
      </div>
      <div className="summary-card">
        <div className="label">Bilanz</div>
        <div className={`value ${balance >= 0 ? "positive" : "negative"}`}>
          {formatCurrency(balance)}
        </div>
      </div>
      <div className="summary-card">
        <div className="label">Transaktionen</div>
        <div className="value">{expenses.length + income.length}</div>
      </div>
      <div className="summary-card">
        <div className="label">Kategorien</div>
        <div className="value">
          {new Set(expenses.map((e) => e.Kategorie)).size}
        </div>
      </div>
    </div>
  );
}
