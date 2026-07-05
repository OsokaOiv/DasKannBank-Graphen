use std::fs;
use std::path::Path;

use crate::util;
use crate::Transaction;

pub fn extract_pdf<P: AsRef<Path>>(path: P) -> Vec<Transaction> {
    let path = path.as_ref();
    let bytes = match fs::read(path) {
        Ok(b) => b,
        Err(_) => return Vec::new(),
    };

    let text = match pdf_extract::extract_text_from_mem(&bytes) {
        Ok(t) => t,
        Err(_) => return Vec::new(),
    };

    parse_pdf_text(&text)
}

fn parse_pdf_text(text: &str) -> Vec<Transaction> {
    let mut transactions = Vec::new();
    let mut in_umsatze = false;

    for line in text.lines() {
        let line = line.trim();

        if line.contains("Kontoumsätze") || line.contains("Umsatzliste") {
            in_umsatze = true;
            continue;
        }

        if !in_umsatze {
            continue;
        }

        if line.contains("Saldo") || line.contains("Summe") || line.is_empty() {
            continue;
        }

        if let Some(t) = try_parse_transaction_line(line) {
            transactions.push(t);
        }
    }

    transactions
}

fn try_parse_transaction_line(line: &str) -> Option<Transaction> {
    let parts: Vec<&str> = line.split_whitespace().collect();
    if parts.len() < 3 {
        return None;
    }

    let date_str = parts[0];
    if date_str.len() != 8 || date_str.chars().filter(|&c| c == '.').count() != 2 {
        return None;
    }

    let last = parts.last()?;
    let betrag = util::parse_amount(last)?;

    let second_to_last = parts[parts.len() - 2];
    let amount_end_idx = if second_to_last.starts_with('-') || second_to_last.starts_with('+') {
        parts.len() - 2
    } else {
        parts.len() - 1
    };

    let payee = if amount_end_idx > 1 {
        Some(parts[1..amount_end_idx].join(" "))
    } else {
        None
    };

    Some(Transaction {
        buchungsdatum: date_str.to_string(),
        wertstellung: String::new(),
        status: Some("Gebucht".to_string()),
        zahlungspflichtiger: None,
        zahlungsempfaenger: payee,
        verwendungszweck: None,
        umsatztyp: if betrag < 0.0 { Some("Ausgang".to_string()) } else { Some("Eingang".to_string()) },
        iban: None,
        betrag,
        glaeubiger_id: None,
        mandatsreferenz: None,
        kundenreferenz: None,
    })
}

pub fn process_pdfs(dir: &Path) -> Vec<Transaction> {
    util::collect_files(dir, "pdf")
        .iter()
        .flat_map(|path| extract_pdf(path))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_try_parse_transaction_line() {
        let line = "22.12.25 REWE Muenchen VISA Einkauf -21,94";
        let t = try_parse_transaction_line(line).unwrap();
        assert_eq!(t.buchungsdatum, "22.12.25");
        assert!(t.zahlungsempfaenger.as_deref().unwrap_or("").contains("REWE"));
        assert!((t.betrag - (-21.94)).abs() < 0.001);
    }

    #[test]
    fn test_try_parse_income_line() {
        let line = "01.01.25 FIRMA Gehalt 3.450,00";
        let t = try_parse_transaction_line(line).unwrap();
        assert_eq!(t.betrag, 3450.00);
        assert_eq!(t.umsatztyp.as_deref(), Some("Eingang"));
    }

    #[test]
    fn test_try_parse_invalid_date() {
        assert!(try_parse_transaction_line("abc REWE -21,94").is_none());
    }

    #[test]
    fn test_try_parse_invalid_amount() {
        assert!(try_parse_transaction_line("22.12.25 REWE abc").is_none());
    }
}
