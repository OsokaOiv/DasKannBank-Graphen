import { useEffect, useState, useMemo, useCallback } from "react";
import { fetchDashboardData } from "../api";
import type { DashboardData, FilterState, ExpenseRecord, IncomeRecord } from "../types";
import Sidebar from "./Sidebar";
import SummaryCards from "./SummaryCards";
import ChartView from "./ChartView";
import DataTables from "./DataTables";
import Uncategorized from "./Uncategorized";

interface DashboardProps {
  dark?: boolean;
}

export default function Dashboard({ dark }: DashboardProps) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filter, setFilter] = useState<FilterState>({
    dateFrom: "",
    dateTo: "",
    categories: [],
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await fetchDashboardData();
      setData(d);

      const dates = [...d.expenses, ...d.income]
        .map((r) => r.Datum)
        .filter(Boolean)
        .sort();
      const dateFrom = dates[0] || "";
      const dateTo = dates[dates.length - 1] || "";

      setFilter({
        dateFrom,
        dateTo,
        categories: d.categories,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler beim Laden");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const { filteredExpenses, filteredIncome, filteredProfitLoss } = useMemo(() => {
    if (!data) return { filteredExpenses: [], filteredIncome: [], filteredProfitLoss: [] };

    let expenses: ExpenseRecord[] = data.expenses;
    let income: IncomeRecord[] = data.income;

    if (filter.dateFrom) {
      expenses = expenses.filter((e) => e.Datum >= filter.dateFrom);
      income = income.filter((i) => i.Datum >= filter.dateFrom);
    }
    if (filter.dateTo) {
      expenses = expenses.filter((e) => e.Datum <= filter.dateTo);
      income = income.filter((i) => i.Datum <= filter.dateTo);
    }
    if (filter.categories.length > 0) {
      expenses = expenses.filter((e) => filter.categories.includes(e.Kategorie));
    }

    const profitLoss = data.profit_loss.filter((p) => {
      const monthStart = p.Monat + "-01";
      if (filter.dateFrom && monthStart < filter.dateFrom) return false;
      if (filter.dateTo && monthStart > filter.dateTo) return false;
      return true;
    });

    return { filteredExpenses: expenses, filteredIncome: income, filteredProfitLoss: profitLoss };
  }, [data, filter]);

  if (loading) {
    return <div className="loading" role="status" aria-live="polite">Lade Daten …</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>Fehler: {error}</p>
        <p style={{ fontSize: 14, color: "#888" }}>
          Stelle sicher, dass der API-Server unter http://127.0.0.1:8765 läuft.
        </p>
        <button onClick={loadData}>Erneut versuchen</button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="app-body">
      <Sidebar
        categories={data.categories}
        filter={filter}
        onFilterChange={setFilter}
      />
      <main className="main-content">
        <h1>DKB Finanz-Dashboard</h1>
        <SummaryCards expenses={filteredExpenses} income={filteredIncome} />
        <ChartView
          dark={dark}
          expenses={filteredExpenses}
          income={filteredIncome}
          profitLoss={filteredProfitLoss}
        />
        <DataTables expenses={filteredExpenses} />
        <Uncategorized expenses={filteredExpenses} />
      </main>
    </div>
  );
}
