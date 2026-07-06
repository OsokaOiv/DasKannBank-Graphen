use std::fs;
use std::io::Write;
use std::path::Path;

const FIELD_NAMES: &[&str] = &[
    "Buchungsdatum", "Wertstellung", "Status", "Zahlungspflichtige*r",
    "Zahlungsempfänger*in", "Verwendungszweck", "Umsatztyp", "IBAN",
    "Betrag (€)", "Gläubiger-ID", "Mandatsreferenz", "Kundenreferenz",
];

const FOOTER_PREFIXES: &[&str] = &[
    "Kontostand am", "Neuer Kontostand", "Gesamtumsatzsummen", "Summe Soll",
    "Summe Haben", "Deutsche Kreditbank", "Vorsitzender des Aufsichtsrats",
    "Seite", "Kontoauszug", "Saldo",
];

const SECTION_MARKERS: &[&str] = &["Kontoumsätze", "Umsatzliste"];

struct CsvRow {
    buchungsdatum: String,
    wertstellung: String,
    zahlungsempfaenger: String,
    verwendungszweck: String,
    umsatztyp: String,
    betrag: String,
}

pub fn convert_pdf(path: &Path) -> Result<(), String> {
    let bytes = fs::read(path).map_err(|e| format!("PDF lesen fehlgeschlagen: {}", e))?;
    let text = pdf_extract::extract_text_from_mem(&bytes)
        .map_err(|e| format!("PDF Text extrahieren fehlgeschlagen: {}", e))?;

    let rows = parse_pdf_text(&text);

    if rows.is_empty() {
        return Err("Keine Transaktionen in PDF gefunden".to_string());
    }

    let out_name = path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("export");
    let out_dir = path
        .parent()
        .ok_or_else(|| "Ungültiger PDF-Pfad".to_string())?;
    let out_path = out_dir.join(format!("{}.csv", out_name));

    write_csv(&rows, &out_path)
}

fn parse_pdf_text(text: &str) -> Vec<CsvRow> {
    let mut rows = Vec::new();
    let mut in_section = false;

    for raw_line in text.lines() {
        let line = raw_line.trim();
        if line.is_empty() {
            continue;
        }

        if is_section_marker(line) {
            in_section = true;
            continue;
        }

        if !in_section {
            continue;
        }

        if is_footer_line(raw_line) {
            in_section = false;
            continue;
        }

        if let Some(row) = try_parse_transaction(line) {
            rows.push(row);
        } else if let Some(last) = rows.last_mut() {
            append_to_last(last, line);
        }
    }

    rows
}

fn try_parse_transaction(line: &str) -> Option<CsvRow> {
    let (day, month, year, rest) = parse_date_prefix(line)?;
    let rest = rest.trim_start();
    let (vorzeichen, raw_amount) = extract_amount(rest)?;

    let normalized = raw_amount.replace('.', "").replace(',', ".");
    let parsed: f64 = normalized.parse().ok()?;
    let signed = if vorzeichen == "-" { -parsed } else { parsed };
    let display_amount = format!("{:+.2}", signed).replace('.', ",");
    let empfaenger = extract_purpose(rest, vorzeichen, raw_amount);

    Some(CsvRow {
        buchungsdatum: format!("{}.{}.{}", day, month, &year[2..]),
        wertstellung: format!("{}.{}.{}", day, month, &year[2..]),
        zahlungsempfaenger: empfaenger.clone(),
        verwendungszweck: empfaenger,
        umsatztyp: if signed < 0.0 { "Ausgang".to_string() } else { "Eingang".to_string() },
        betrag: display_amount,
    })
}

fn append_to_last(last: &mut CsvRow, line: &str) {
    if last.zahlungsempfaenger == last.verwendungszweck {
        last.zahlungsempfaenger = line.to_string();
    }
    last.verwendungszweck.push(' ');
    last.verwendungszweck.push_str(line);
}

fn extract_purpose(rest: &str, vorzeichen: &str, raw_amount: &str) -> String {
    let bereinigt = rest.trim_end();
    let end = if vorzeichen.is_empty() {
        bereinigt.len().saturating_sub(raw_amount.len())
    } else {
        let amount_with_sign = format!("{}{}", vorzeichen, raw_amount);
        bereinigt.rfind(&amount_with_sign).unwrap_or(bereinigt.len())
    };
    bereinigt[..end.min(bereinigt.len())].trim().to_string()
}

fn parse_date_prefix(s: &str) -> Option<(&str, &str, &str, &str)> {
    let s = s.trim_start();
    if s.len() < 10 {
        return None;
    }
    let day = &s[..2];
    if s.as_bytes()[2] != b'.' {
        return None;
    }
    let month = &s[3..5];
    if s.as_bytes()[5] != b'.' {
        return None;
    }
    let year = &s[6..10];
    if !year.as_bytes().iter().all(|b| b.is_ascii_digit()) {
        return None;
    }
    Some((day, month, year, &s[10..]))
}

fn extract_amount(s: &str) -> Option<(&str, &str)> {
    let s = s.trim_end();
    let bytes = s.as_bytes();
    let mut i = bytes.len();

    while i > 0 && bytes[i - 1].is_ascii_whitespace() {
        i -= 1;
    }
    let end = i;

    while i > 0 && (bytes[i - 1].is_ascii_digit() || bytes[i - 1] == b',' || bytes[i - 1] == b'.') {
        i -= 1;
    }
    let num_part = &s[i..end];
    if num_part.is_empty() {
        return None;
    }

    if i > 0 && (bytes[i - 1] == b'-' || bytes[i - 1] == b'+') {
        let vorzeichen = if bytes[i - 1] == b'-' { "-" } else { "+" };
        i -= 1;
        while i > 0 && bytes[i - 1].is_ascii_whitespace() {
            i -= 1;
        }
        Some((vorzeichen, num_part))
    } else {
        Some(("", num_part))
    }
}

fn is_section_marker(line: &str) -> bool {
    let trimmed = line.trim();
    for marker in SECTION_MARKERS {
        if trimmed.contains(marker) {
            return true;
        }
    }
    false
}

fn is_footer_line(line: &str) -> bool {
    let trimmed = line.trim_start();
    for prefix in FOOTER_PREFIXES {
        if trimmed.starts_with(prefix) {
            return true;
        }
    }
    false
}

fn write_csv(rows: &[CsvRow], path: &Path) -> Result<(), String> {
    let mut file = fs::File::create(path).map_err(|e| format!("CSV erstellen fehlgeschlagen: {}", e))?;

    let header = FIELD_NAMES
        .iter()
        .map(|n| format!("\"{}\"", n))
        .collect::<Vec<_>>()
        .join(";");
    writeln!(file, "{}", header).map_err(|e| format!("CSV schreiben fehlgeschlagen: {}", e))?;

    for row in rows {
        let values = [
            format!("\"{}\"", row.buchungsdatum),
            format!("\"{}\"", row.wertstellung),
            "\"Gebucht\"".to_string(),
            "\"\"".to_string(),
            format!("\"{}\"", row.zahlungsempfaenger),
            format!("\"{}\"", row.verwendungszweck),
            format!("\"{}\"", row.umsatztyp),
            "\"\"".to_string(),
            format!("\"{}\"", row.betrag),
            "\"\"".to_string(),
            "\"\"".to_string(),
            "\"\"".to_string(),
        ];
        writeln!(file, "{}", values.join(";"))
            .map_err(|e| format!("CSV schreiben fehlgeschlagen: {}", e))?;
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_date_prefix_valid() {
        let result = parse_date_prefix("22.12.2025 REWE Muenchen -21,94");
        assert_eq!(result, Some(("22", "12", "2025", " REWE Muenchen -21,94")));
    }

    #[test]
    fn test_parse_date_prefix_short() {
        assert!(parse_date_prefix("short").is_none());
    }

    #[test]
    fn test_parse_date_prefix_no_dots() {
        assert!(parse_date_prefix("22122025 REWE").is_none());
    }

    #[test]
    fn test_extract_amount_negative() {
        let result = extract_amount("REWE Muenchen -21,94");
        assert_eq!(result, Some(("-", "21,94")));
    }

    #[test]
    fn test_extract_amount_positive() {
        let result = extract_amount("Gehalt Januar +3.450,00");
        assert_eq!(result, Some(("+", "3.450,00")));
    }

    #[test]
    fn test_extract_amount_no_sign() {
        let result = extract_amount("Test 123,45");
        assert_eq!(result, Some(("", "123,45")));
    }

    #[test]
    fn test_extract_amount_thousands() {
        let result = extract_amount("Miete 1.234,56");
        assert_eq!(result, Some(("", "1.234,56")));
    }

    #[test]
    fn test_extract_amount_no_number() {
        assert!(extract_amount("Just text").is_none());
    }

    #[test]
    fn test_is_footer_line() {
        assert!(is_footer_line("Kontostand am 31.12.2025: 1.234,56 €"));
        assert!(is_footer_line("Seite 1 von 2"));
        assert!(is_footer_line("Deutsche Kreditbank AG"));
        assert!(is_footer_line("Saldo EUR 1.234,56"));
        assert!(is_footer_line("Saldo"));
        assert!(!is_footer_line("22.12.2025 REWE Muenchen -21,94"));
    }

    #[test]
    fn test_is_section_marker() {
        assert!(is_section_marker("Kontoumsätze"));
        assert!(is_section_marker("Umsatzliste"));
        assert!(!is_section_marker("22.12.2025 REWE -21,94"));
    }

    #[test]
    fn test_parse_pdf_text_single() {
        let text = "Kontoumsätze\n22.12.2025 REWE Muenchen -21,94\nSaldo";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
        assert!(rows[0].zahlungsempfaenger.contains("REWE"));
        assert_eq!(rows[0].betrag, "-21,94");
        assert_eq!(rows[0].umsatztyp, "Ausgang");
    }

    #[test]
    fn test_parse_pdf_text_multi_line() {
        let text = "Kontoumsätze\n22.12.2025 VISA -21,94\nREWE Muenchen\nSaldo";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
        assert!(rows[0].zahlungsempfaenger.contains("REWE"));
        assert!(rows[0].verwendungszweck.contains("VISA REWE Muenchen"));
        assert_eq!(rows[0].betrag, "-21,94");
    }

    #[test]
    fn test_parse_pdf_text_multiple_transactions() {
        let text = "Kontoumsätze\n22.12.2025 REWE -21,94\n23.12.2025 Gehalt +3.450,00\nSaldo";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].betrag, "-21,94");
        assert_eq!(rows[1].betrag, "+3450,00");
        assert_eq!(rows[1].umsatztyp, "Eingang");
    }

    #[test]
    fn test_parse_pdf_text_footer_stops_parsing() {
        let text = "Kontoumsätze\n22.12.2025 REWE -21,94\nKontostand am 31.12.2025\n23.12.2025 Gehalt +3.450,00";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
    }

    #[test]
    fn test_parse_pdf_text_no_section_marker() {
        let text = "22.12.2025 REWE -21,94\n";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 0);
    }

    #[test]
    fn test_write_csv_basic() {
        let rows = vec![CsvRow {
            buchungsdatum: "22.12.25".to_string(),
            wertstellung: "22.12.25".to_string(),
            zahlungsempfaenger: "REWE Muenchen".to_string(),
            verwendungszweck: "REWE Muenchen".to_string(),
            umsatztyp: "Ausgang".to_string(),
            betrag: "-21,94".to_string(),
        }];

        let dir = std::env::temp_dir().join("dkb_test_pdf_csv");
        let _ = std::fs::create_dir_all(&dir);
        let path = dir.join("test.csv");
        write_csv(&rows, &path).unwrap();

        let content = std::fs::read_to_string(&path).unwrap();
        let _ = std::fs::remove_dir_all(&dir);

        assert!(content.contains("Buchungsdatum"));
        assert!(content.contains("REWE Muenchen"));
        assert!(content.contains("-21,94"));
        assert!(content.contains("Ausgang"));
    }
}
