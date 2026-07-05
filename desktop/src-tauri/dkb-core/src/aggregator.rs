use std::collections::HashMap;

use crate::{
    categorizer::Categorizer,
    DashboardData, ExpenseRecord, IncomeRecord, ProfitLossRecord, Transaction,
};

const FIRST_DAY: &str = "01";

fn month_key(date_str: &str) -> String {
    if date_str.len() >= 7 {
        format!("{}-{}", &date_str[..7], FIRST_DAY)
    } else {
        date_str.to_string()
    }
}

fn month_label(date_str: &str) -> String {
    if date_str.len() < 10 {
        return date_str.to_string();
    }
    let month_num: u32 = date_str[5..7].parse().unwrap_or(1);
    let year = &date_str[2..4];
    let month_name = match month_num {
        1 => "Jan", 2 => "Feb", 3 => "Mär", 4 => "Apr",
        5 => "Mai", 6 => "Jun", 7 => "Jul", 8 => "Aug",
        9 => "Sep", 10 => "Okt", 11 => "Nov", 12 => "Dez",
        _ => "???",
    };
    format!("{} {}", month_name, year)
}

pub fn build_dashboard_data(
    transactions: &[Transaction],
    categorizer: &Categorizer,
) -> DashboardData {
    let mut expenses: Vec<ExpenseRecord> = Vec::new();
    let mut income: Vec<IncomeRecord> = Vec::new();

    for t in transactions {
        if t.betrag < 0.0 {
            let abs_betrag = t.betrag.abs();
            let datum = t.buchungsdatum.clone();
            let monat = month_key(&datum);
            let monat_label = month_label(&datum);
            let kategorie = categorizer.categorize(t);

            expenses.push(ExpenseRecord {
                datum: datum.clone(),
                monat,
                monat_label,
                kategorie,
                betrag: abs_betrag,
                zahlungsempfaenger: t.zahlungsempfaenger.clone(),
                verwendungszweck: t.verwendungszweck.clone(),
            });
        } else if t.betrag > 0.0 {
            let datum = t.buchungsdatum.clone();
            let monat = month_key(&datum);

            income.push(IncomeRecord {
                datum: datum.clone(),
                monat,
                betrag: t.betrag,
                zahlungspflichtiger: t.zahlungspflichtiger.clone(),
                verwendungszweck: t.verwendungszweck.clone(),
            });
        }
    }

    let categories = extract_categories(&expenses, categorizer);
    let profit_loss = compute_profit_loss(&expenses, &income);

    DashboardData {
        expenses,
        income,
        profit_loss,
        categories,
    }
}

fn extract_categories(expenses: &[ExpenseRecord], categorizer: &Categorizer) -> Vec<String> {
    let mut cats: Vec<String> = expenses.iter()
        .map(|e| e.kategorie.clone())
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect();
    if cats.is_empty() {
        cats = categorizer.all_category_names();
    }
    cats
}

pub fn compute_profit_loss(
    expenses: &[ExpenseRecord],
    income: &[IncomeRecord],
) -> Vec<ProfitLossRecord> {
    let mut monthly_expenses: HashMap<String, f64> = HashMap::new();
    let mut monthly_income: HashMap<String, f64> = HashMap::new();

    for e in expenses {
        *monthly_expenses.entry(e.monat.clone()).or_insert(0.0) += e.betrag;
    }
    for i in income {
        *monthly_income.entry(i.monat.clone()).or_insert(0.0) += i.betrag;
    }

    let all_months: std::collections::BTreeSet<String> = monthly_expenses.keys()
        .chain(monthly_income.keys())
        .cloned()
        .collect();

    let mut result: Vec<ProfitLossRecord> = all_months.iter()
        .map(|monat| {
            let ausgaben = monthly_expenses.get(monat).copied().unwrap_or(0.0);
            let einnahmen = monthly_income.get(monat).copied().unwrap_or(0.0);
            let differenz = einnahmen - ausgaben;
            let status = if differenz >= 0.0 { "Gewinn" } else { "Verlust" };
            ProfitLossRecord {
                monat: monat.clone(),
                einnahmen,
                ausgaben,
                differenz,
                status: status.to_string(),
            }
        })
        .collect();

    result.sort_by(|a, b| a.monat.cmp(&b.monat));
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_tx(betrag: f64, date: &str, payee: Option<&str>) -> Transaction {
        Transaction {
            buchungsdatum: date.to_string(),
            wertstellung: date.to_string(),
            status: None,
            zahlungspflichtiger: None,
            zahlungsempfaenger: payee.map(|s| s.to_string()),
            verwendungszweck: None,
            umsatztyp: None,
            iban: None,
            betrag,
            glaeubiger_id: None,
            mandatsreferenz: None,
            kundenreferenz: None,
        }
    }

    #[test]
    fn test_month_key() {
        assert_eq!(month_key("2025-01-15"), "2025-01-01");
        assert_eq!(month_key("2025-12-01"), "2025-12-01");
    }

    #[test]
    fn test_profit_loss_basic() {
        let expenses = vec![
            ExpenseRecord { datum: "2025-01-01".into(), monat: "2025-01-01".into(), monat_label: "Jan 2025".into(), kategorie: "Food".into(), betrag: 100.0, zahlungsempfaenger: None, verwendungszweck: None },
        ];
        let income = vec![
            IncomeRecord { datum: "2025-01-01".into(), monat: "2025-01-01".into(), betrag: 500.0, zahlungspflichtiger: None, verwendungszweck: None },
        ];
        let pl = compute_profit_loss(&expenses, &income);
        assert_eq!(pl.len(), 1);
        assert_eq!(pl[0].einnahmen, 500.0);
        assert_eq!(pl[0].ausgaben, 100.0);
        assert_eq!(pl[0].differenz, 400.0);
        assert_eq!(pl[0].status, "Gewinn");
    }

    #[test]
    fn test_profit_loss_verlust() {
        let expenses = vec![
            ExpenseRecord { datum: "2025-01-01".into(), monat: "2025-01-01".into(), monat_label: "Jan 2025".into(), kategorie: "Food".into(), betrag: 500.0, zahlungsempfaenger: None, verwendungszweck: None },
        ];
        let income = vec![
            IncomeRecord { datum: "2025-01-01".into(), monat: "2025-01-01".into(), betrag: 100.0, zahlungspflichtiger: None, verwendungszweck: None },
        ];
        let pl = compute_profit_loss(&expenses, &income);
        assert_eq!(pl[0].status, "Verlust");
        assert!((pl[0].differenz - (-400.0)).abs() < 0.001);
    }

    #[test]
    fn test_build_dashboard_data() {
        use std::collections::HashMap;
        let rules = HashMap::new();
        let categorizer = Categorizer::new(rules);

        let txns = vec![
            make_tx(-50.0, "22.12.25", Some("REWE")),
            make_tx(3450.0, "02.01.25", Some("Firma GmbH")),
        ];

        let data = build_dashboard_data(&txns, &categorizer);
        assert_eq!(data.expenses.len(), 1);
        assert_eq!(data.income.len(), 1);
        assert_eq!(data.profit_loss.len(), 2);
        assert_eq!(data.expenses[0].betrag, 50.0);
        assert_eq!(data.income[0].betrag, 3450.0);
    }
}
