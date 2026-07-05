pub mod config;
pub mod csv_reader;
pub mod categorizer;
pub mod aggregator;
pub mod pdf_extractor;
pub mod util;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub buchungsdatum: String,
    pub wertstellung: String,
    pub status: Option<String>,
    #[serde(rename = "Zahlungspflichtige*r")]
    pub zahlungspflichtiger: Option<String>,
    #[serde(rename = "Zahlungsempfänger*in")]
    pub zahlungsempfaenger: Option<String>,
    pub verwendungszweck: Option<String>,
    pub umsatztyp: Option<String>,
    pub iban: Option<String>,
    #[serde(rename = "Betrag (€)")]
    pub betrag: f64,
    #[serde(rename = "Gläubiger-ID")]
    pub glaeubiger_id: Option<String>,
    pub mandatsreferenz: Option<String>,
    pub kundenreferenz: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpenseRecord {
    #[serde(rename = "Datum")]
    pub datum: String,
    #[serde(rename = "Monat")]
    pub monat: String,
    #[serde(rename = "Monat_Label")]
    pub monat_label: String,
    #[serde(rename = "Kategorie")]
    pub kategorie: String,
    #[serde(rename = "Betrag")]
    pub betrag: f64,
    #[serde(rename = "Zahlungsempfänger*in")]
    pub zahlungsempfaenger: Option<String>,
    pub verwendungszweck: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IncomeRecord {
    #[serde(rename = "Datum")]
    pub datum: String,
    #[serde(rename = "Monat")]
    pub monat: String,
    #[serde(rename = "Betrag")]
    pub betrag: f64,
    #[serde(rename = "Zahlungspflichtige*r")]
    pub zahlungspflichtiger: Option<String>,
    pub verwendungszweck: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProfitLossRecord {
    #[serde(rename = "Monat")]
    pub monat: String,
    #[serde(rename = "Einnahmen")]
    pub einnahmen: f64,
    #[serde(rename = "Ausgaben")]
    pub ausgaben: f64,
    #[serde(rename = "Differenz")]
    pub differenz: f64,
    #[serde(rename = "Status")]
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DashboardData {
    pub expenses: Vec<ExpenseRecord>,
    pub income: Vec<IncomeRecord>,
    pub profit_loss: Vec<ProfitLossRecord>,
    pub categories: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CategoryEntry {
    pub name: String,
    pub keywords: Vec<String>,
}
