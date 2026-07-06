use std::fs;
use std::path::Path;

use crate::util;
use crate::Transaction;

const BOM_SKIP: usize = 3;
const DATE_MIN_LEN: usize = 8;

fn parse_date(raw: &str) -> Option<String> {
    let raw = raw.trim();
    if raw.len() < DATE_MIN_LEN {
        return None;
    }
    let day = &raw[0..2];
    let month = &raw[3..5];
    let year = &raw[6..8];
    Some(format!("20{}-{}-{}", year, month, day))
}

fn normalize_header(col: &str) -> String {
    col.trim_matches('"').trim().to_string()
}

pub fn read_csv<P: AsRef<Path>>(path: P) -> Vec<Transaction> {
    let path = path.as_ref();
    let content = match fs::read_to_string(path) {
        Ok(c) => c,
        Err(_) => return Vec::new(),
    };

    let content = if content.starts_with('\u{feff}') {
        content[BOM_SKIP..].to_string()
    } else {
        content
    };

    let lines: Vec<&str> = content.lines().collect();
    let header_idx = lines.iter().position(|l| l.contains("Buchungsdatum"));

    let header_idx = match header_idx {
        Some(i) => i,
        None => return Vec::new(),
    };

    let csv_content = lines[header_idx..].join("\n");
    let mut reader = csv::ReaderBuilder::new()
        .delimiter(b';')
        .flexible(true)
        .from_reader(csv_content.as_bytes());

    let headers: Vec<String> = match reader.headers() {
        Ok(h) => h.iter().map(normalize_header).collect(),
        Err(_) => return Vec::new(),
    };

    let mut transactions = Vec::new();

    for result in reader.records() {
        let record = match result {
            Ok(r) => r,
            Err(_) => continue,
        };

        let get = |name: &str| -> Option<String> {
            headers.iter().position(|h| h == name)
                .and_then(|i| record.get(i))
                .map(|s| s.trim_matches('"').trim().to_string())
        };

        let betrag_raw = get("Betrag (€)").or_else(|| get("Betrag"));
        let betrag = match betrag_raw.and_then(|r| util::parse_amount(&r)) {
            Some(b) => b,
            None => continue,
        };

        let raw_date = get("Buchungsdatum").unwrap_or_default();
        transactions.push(Transaction {
            buchungsdatum: parse_date(&raw_date).unwrap_or(raw_date),
            wertstellung: parse_date(&get("Wertstellung").unwrap_or_default()).unwrap_or_default(),
            status: get("Status"),
            zahlungspflichtiger: get("Zahlungspflichtige*r"),
            zahlungsempfaenger: get("Zahlungsempfänger*in"),
            verwendungszweck: get("Verwendungszweck"),
            umsatztyp: get("Umsatztyp"),
            iban: get("IBAN"),
            betrag,
            glaeubiger_id: get("Gläubiger-ID"),
            mandatsreferenz: get("Mandatsreferenz"),
            kundenreferenz: get("Kundenreferenz"),
        });
    }

    transactions
}

pub fn read_all_csvs(dir: &Path) -> Vec<Transaction> {
    let mut all: Vec<Transaction> = util::collect_files(dir, "csv")
        .iter()
        .flat_map(|path| read_csv(path))
        .collect();
    deduplicate(&mut all);
    all
}

fn transaction_hash(t: &Transaction) -> String {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    let mut hasher = DefaultHasher::new();
    t.buchungsdatum.hash(&mut hasher);
    t.betrag.to_bits().hash(&mut hasher);
    t.zahlungsempfaenger.hash(&mut hasher);
    t.verwendungszweck.hash(&mut hasher);
    format!("{:x}", hasher.finish())
}

fn deduplicate(transactions: &mut Vec<Transaction>) {
    let mut seen = std::collections::HashSet::new();
    transactions.retain(|t| seen.insert(transaction_hash(t)));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_date_valid() {
        assert_eq!(parse_date("22.12.25"), Some("2025-12-22".to_string()));
    }

    #[test]
    fn test_parse_date_invalid() {
        assert!(parse_date("").is_none());
    }

    #[test]
    fn test_read_csv_real_format() {
        let csv_data = r#""Girokonto";"DE00000000000000000000"
"Zeitraum:";"24.06.2024 - 22.12.2025"
"Kontostand vom 03.07.2026:";"138,28 €"

"Buchungsdatum";"Wertstellung";"Status";"Zahlungspflichtige*r";"Zahlungsempfänger*in";"Verwendungszweck";"Umsatztyp";"IBAN";"Betrag (€)";"Gläubiger-ID";"Mandatsreferenz";"Kundenreferenz"
"22.12.25";"22.12.25";"Gebucht";"ISSUER";"REWE Muenchen";"VISA Einkauf";"Ausgang";"DE00000000000000000000";"-21,94";"";"";"ref123"
"22.12.25";"22.12.25";"Gebucht";"COMPANY GMBH";"";"LOHN GEHALT 12/25";"Eingang";"DE00000000000000000000";"290,87";"";"";"ref456""#;

        let dir = std::env::temp_dir().join("dkb_test_csv");
        let _ = std::fs::create_dir_all(&dir);
        let path = dir.join("test.csv");
        std::fs::write(&path, csv_data).unwrap();

        let txns = read_csv(&path);
        let _ = std::fs::remove_dir_all(&dir);

        assert_eq!(txns.len(), 2);
        assert_eq!(txns[0].zahlungsempfaenger.as_deref(), Some("REWE Muenchen"));
        assert!((txns[0].betrag - (-21.94)).abs() < 0.001);
        assert_eq!(txns[1].betrag, 290.87);
        assert_eq!(txns[1].umsatztyp.as_deref(), Some("Eingang"));
    }

    #[test]
    fn test_read_csv_simple_format() {
        let csv_data = r#""Buchungsdatum";"Wertstellung";"Zahlungsempfänger*in";"Verwendungszweck";"Betrag (€)"
"02.01.25";"02.01.25";"Firma GmbH";"Gehalt Januar 2025";"3.450,00"
"03.01.25";"03.01.25";"REWE München";"VISA Einkauf";"-58,23""#;

        let dir = std::env::temp_dir().join("dkb_test_csv_simple");
        let _ = std::fs::create_dir_all(&dir);
        let path = dir.join("test2.csv");
        std::fs::write(&path, csv_data).unwrap();

        let txns = read_csv(&path);
        let _ = std::fs::remove_dir_all(&dir);

        assert_eq!(txns.len(), 2);
        assert_eq!(txns[0].betrag, 3450.00);
        assert_eq!(txns[1].betrag, -58.23);
    }
}
