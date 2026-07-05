export interface ExpenseRecord {
  Datum: string;
  Monat: string;
  Monat_Label: string;
  Kategorie: string;
  Betrag: number;
  "Zahlungsempfänger*in"?: string;
  Verwendungszweck?: string;
}

export interface IncomeRecord {
  Datum: string;
  Monat: string;
  Betrag: number;
  "Zahlungspflichtige*r"?: string;
  Verwendungszweck?: string;
}

export interface ProfitLossRecord {
  Monat: string;
  Einnahmen: number;
  Ausgaben: number;
  Differenz: number;
  Status: string;
}

export interface DashboardData {
  expenses: ExpenseRecord[];
  income: IncomeRecord[];
  profit_loss: ProfitLossRecord[];
  categories: string[];
}

export interface FilterState {
  dateFrom: string;
  dateTo: string;
  categories: string[];
}
