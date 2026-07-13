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
    "Seite", "Kontoauszug",
];

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

    let out_name = path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("export");
    let out_dir = path
        .parent()
        .ok_or_else(|| "Ungültiger PDF-Pfad".to_string())?;

    // Debug: save raw extracted text for inspection
    let txt_path = out_dir.join(format!("{}.txt", out_name));
    let _ = fs::write(&txt_path, &text);

    let rows = parse_pdf_text(&text);

    if rows.is_empty() {
        let line_count = text.lines().filter(|l| !l.trim().is_empty()).count();
        return Err(format!(
            "Keine Transaktionen in PDF gefunden ({} nicht-leere Zeilen)",
            line_count
        ));
    }

    let out_path = out_dir.join(format!("{}.csv", out_name));

    write_csv(&rows, &out_path)
}

fn find_date_prefix_position(s: &str) -> Option<usize> {
    let bytes = s.as_bytes();
    let len = s.len();
    if len < 10 {
        return None;
    }
    let mut i = 0;
    while i + 10 <= len {
        if bytes[i + 2] == b'.'
            && bytes[i + 5] == b'.'
            && bytes[i..i + 2].iter().all(|b| b.is_ascii_digit())
            && bytes[i + 3..i + 5].iter().all(|b| b.is_ascii_digit())
            && bytes[i + 6..i + 10].iter().all(|b| b.is_ascii_digit())
        {
            return Some(i);
        }
        i += 1;
    }
    None
}

struct PendingTx {
    day: String,
    month: String,
    year: String,
    purpose: String,
}

fn finalize_pending(rows: &mut Vec<CsvRow>, p: PendingTx) {
    if let Some((sign, raw_amount, amount_end)) = find_last_amount(&p.purpose) {
        let purpose_end = amount_end - raw_amount.len()
            - if sign.is_empty() { 0 } else { sign.len() };
        let purpose = p.purpose[..purpose_end].trim();

        let normalized = raw_amount.replace('.', "").replace(',', ".");
        if let Ok(parsed) = normalized.parse::<f64>() {
            let signed = if sign == "-" { -parsed } else { parsed };
            let display_amount = format!("{:+.2}", signed).replace('.', ",");
            let date_str = format!("{}.{}.{}", p.day, p.month, &p.year[2..]);

            rows.push(CsvRow {
                buchungsdatum: date_str.clone(),
                wertstellung: date_str,
                zahlungsempfaenger: purpose.to_string(),
                verwendungszweck: purpose.to_string(),
                umsatztyp: if signed < 0.0 { "Ausgang".to_string() } else { "Eingang".to_string() },
                betrag: display_amount,
            });
        }
    }
}

fn find_last_amount(s: &str) -> Option<(&str, &str, usize)> {
    let bytes = s.as_bytes();
    let len = s.len();
    let mut last_match: Option<(usize, &str, &str)> = None;
    let mut i = 0;

    while i < len {
        if bytes[i].is_ascii_digit() {
            if let Some((amount_str, end)) = match_german_amount(s, i) {
                let sign = find_preceding_sign(s, i);
                last_match = Some((i, sign, amount_str));
                i = end;
                continue;
            }
        }
        i += 1;
    }

    last_match.map(|(start, sign, amount)| {
        let end = start + amount.len();
        (sign, amount, end)
    })
}

fn parse_pdf_text(text: &str) -> Vec<CsvRow> {
    let mut rows = Vec::new();
    let mut pending: Option<PendingTx> = None;

    for raw_line in text.lines() {
        let trimmed = raw_line.trim();
        if trimmed.is_empty() {
            continue;
        }

        if is_footer_line(raw_line) {
            if let Some(p) = pending.take() {
                finalize_pending(&mut rows, p);
            }
            if !rows.is_empty() { break; }
            continue;
        }

        let date_line = if has_date_prefix(trimmed) {
            Some(trimmed)
        } else if pending.is_none() {
            find_date_prefix_position(trimmed).map(|pos| &trimmed[pos..])
        } else {
            None
        };

        match date_line {
            Some(line) => {
                if let Some(p) = pending.take() {
                    finalize_pending(&mut rows, p);
                }

                let mut remaining = line;
                let mut found_any = false;

                loop {
                    match try_parse_first_transaction(remaining) {
                        Some((row, consumed)) => {
                            rows.push(row);
                            found_any = true;
                            if consumed < remaining.len() {
                                remaining = remaining[consumed..].trim_start();
                                if remaining.is_empty() || !has_date_prefix(remaining) {
                                    break;
                                }
                            } else {
                                break;
                            }
                        }
                        None => {
                            if !found_any {
                                if let Some((day, month, year, rest)) = parse_date_prefix(line) {
                                    pending = Some(PendingTx {
                                        day: day.to_string(),
                                        month: month.to_string(),
                                        year: year.to_string(),
                                        purpose: rest.trim().to_string(),
                                    });
                                }
                            } else if !remaining.trim().is_empty() {
                                if let Some(last) = rows.last_mut() {
                                    append_to_last(last, remaining.trim());
                                }
                            }
                            break;
                        }
                    }
                }
            }
            None => {
                if let Some(p) = &mut pending {
                    if !p.purpose.is_empty() {
                        p.purpose.push(' ');
                    }
                    p.purpose.push_str(trimmed);
                } else if let Some(last) = rows.last_mut() {
                    append_to_last(last, trimmed);
                }
            }
        }
    }

    if let Some(p) = pending {
        finalize_pending(&mut rows, p);
    }

    rows
}

fn try_parse_first_transaction(s: &str) -> Option<(CsvRow, usize)> {
    let (day, month, year, rest_orig) = parse_date_prefix(s)?;
    let rest = rest_orig.trim_start();
    let leading_ws = rest_orig.len() - rest.len();
    let (vorzeichen, raw_amount, amount_end) = find_first_amount(rest)?;

    let purpose_end = amount_end - raw_amount.len() - if vorzeichen.is_empty() { 0 } else { vorzeichen.len() };
    let purpose = rest[..purpose_end].trim();

    let normalized = raw_amount.replace('.', "").replace(',', ".");
    let parsed: f64 = normalized.parse().ok()?;
    let signed = if vorzeichen == "-" { -parsed } else { parsed };
    let display_amount = format!("{:+.2}", signed).replace('.', ",");

    let date_str = format!("{}.{}.{}", day, month, &year[2..]);
    let total_consumed = 10 + leading_ws + amount_end;

    Some((
        CsvRow {
            buchungsdatum: date_str.clone(),
            wertstellung: date_str,
            zahlungsempfaenger: purpose.to_string(),
            verwendungszweck: purpose.to_string(),
            umsatztyp: if signed < 0.0 { "Ausgang".to_string() } else { "Eingang".to_string() },
            betrag: display_amount,
        },
        total_consumed,
    ))
}

fn find_first_amount(s: &str) -> Option<(&str, &str, usize)> {
    let bytes = s.as_bytes();
    let len = s.len();
    let mut i = 0;

    while i < len {
        if bytes[i].is_ascii_digit() {
            if let Some((amount_str, end)) = match_german_amount(s, i) {
                let sign = find_preceding_sign(s, i);
                return Some((sign, amount_str, end));
            }
            i += 1;
        } else {
            i += 1;
        }
    }

    None
}

fn find_preceding_sign(s: &str, digit_start: usize) -> &str {
    let bytes = s.as_bytes();
    let mut j = digit_start;

    while j > 0 && bytes[j - 1].is_ascii_whitespace() {
        j -= 1;
    }
    if j > 0 && (bytes[j - 1] == b'-' || bytes[j - 1] == b'+') {
        if bytes[j - 1] == b'-' { "-" } else { "+" }
    } else {
        ""
    }
}

fn match_german_amount(s: &str, start: usize) -> Option<(&str, usize)> {
    let bytes = s.as_bytes();
    let len = s.len();
    let mut i = start;

    if i >= len || !bytes[i].is_ascii_digit() {
        return None;
    }

    let mut digit_count = 0;
    while i < len && bytes[i].is_ascii_digit() && digit_count < 3 {
        i += 1;
        digit_count += 1;
    }

    loop {
        if i >= len || bytes[i] != b'.' {
            break;
        }
        if i + 3 >= len
            || !bytes[i + 1].is_ascii_digit()
            || !bytes[i + 2].is_ascii_digit()
            || !bytes[i + 3].is_ascii_digit()
        {
            return None;
        }
        i += 4;
        if i < len && bytes[i].is_ascii_digit() {
            return None;
        }
    }

    if i + 2 >= len
        || bytes[i] != b','
        || !bytes[i + 1].is_ascii_digit()
        || !bytes[i + 2].is_ascii_digit()
    {
        return None;
    }
    let end = i + 3;

    if i + 3 < len && bytes[i + 3].is_ascii_digit() {
        return None;
    }

    let num_part = &s[start..end];
    Some((num_part, end))
}

fn append_to_last(last: &mut CsvRow, line: &str) {
    if last.zahlungsempfaenger == last.verwendungszweck {
        last.zahlungsempfaenger = line.to_string();
    }
    last.verwendungszweck.push(' ');
    last.verwendungszweck.push_str(line);
}

fn has_date_prefix(s: &str) -> bool {
    let bytes = s.trim_start().as_bytes();
    bytes.len() >= 10
        && bytes[2] == b'.'
        && bytes[5] == b'.'
        && bytes[..2].iter().all(|b| b.is_ascii_digit())
        && bytes[3..5].iter().all(|b| b.is_ascii_digit())
        && bytes[6..10].iter().all(|b| b.is_ascii_digit())
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
    fn test_match_german_amount_simple() {
        let (amount, end) = match_german_amount(" -21,94", 2).unwrap();
        assert_eq!(amount, "21,94");
        assert_eq!(end, 7);
    }

    #[test]
    fn test_match_german_amount_thousands() {
        let (amount, end) = match_german_amount(" 1.234,56€", 1).unwrap();
        assert_eq!(amount, "1.234,56");
        assert_eq!(end, 9);
    }

    #[test]
    fn test_match_german_amount_no_match_no_comma() {
        assert!(match_german_amount(" 57300000", 1).is_none());
    }

    #[test]
    fn test_match_german_amount_no_match_wrong_decimals() {
        assert!(match_german_amount(" 7,12345678", 1).is_none());
    }

    #[test]
    fn test_find_first_amount_negative() {
        let result = find_first_amount("REWE Muenchen -21,94 text");
        assert_eq!(result, Some(("-", "21,94", 20)));
    }

    #[test]
    fn test_find_first_amount_positive() {
        let result = find_first_amount("Gehalt +3.450,00");
        assert_eq!(result, Some(("+", "3.450,00", 16)));
    }

    #[test]
    fn test_find_first_amount_no_sign() {
        let result = find_first_amount("Test 123,45");
        assert_eq!(result, Some(("", "123,45", 11)));
    }

    #[test]
    fn test_find_first_amount_thousands() {
        let result = find_first_amount("Miete 1.234,56");
        assert_eq!(result, Some(("", "1.234,56", 14)));
    }

    #[test]
    fn test_find_first_amount_no_number() {
        assert!(find_first_amount("Just text").is_none());
    }

    #[test]
    fn test_find_first_amount_skips_wrong_decimals() {
        let result = find_first_amount("Preis 8,12345678 EUR Stück 4,5000 -51,50");
        assert_eq!(result, Some(("-", "51,50", 41)));
    }

    #[test]
    fn test_is_footer_line() {
        assert!(is_footer_line("Kontostand am 31.12.2025: 1.234,56 €"));
        assert!(is_footer_line("Seite 1 von 2"));
        assert!(is_footer_line("Deutsche Kreditbank AG"));
        assert!(is_footer_line("Kontoauszug 8/"));
        assert!(!is_footer_line("22.12.2025 REWE Muenchen -21,94"));
    }

    #[test]
    fn test_parse_pdf_text_single() {
        let text = "Kontoumsätze\n22.12.2025 REWE Muenchen -21,94\nKontostand am";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
        assert!(rows[0].zahlungsempfaenger.contains("REWE"));
        assert_eq!(rows[0].betrag, "-21,94");
        assert_eq!(rows[0].umsatztyp, "Ausgang");
    }

    #[test]
    fn test_find_date_prefix_position_found() {
        assert_eq!(find_date_prefix_position("Auszug Nr. 7 05.07.2023Text"), Some(13));
    }

    #[test]
    fn test_find_date_prefix_position_start() {
        assert_eq!(find_date_prefix_position("05.07.2023Text"), Some(0));
    }

    #[test]
    fn test_find_date_prefix_position_not_found() {
        assert_eq!(find_date_prefix_position("Kein Datum"), None);
    }

    #[test]
    fn test_find_date_prefix_position_short() {
        assert_eq!(find_date_prefix_position("123"), None);
    }

    #[test]
    fn test_parse_pdf_text_header_before_date() {
        let text = "Kontoumsätze\nAuszug Nr. 7 05.07.2023 FLUG AIRLINE -152,00 06.07.2023 Depot -75,30\nKontostand am";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].betrag, "-152,00");
        assert_eq!(rows[0].buchungsdatum, "05.07.23");
        assert_eq!(rows[1].betrag, "-75,30");
        assert_eq!(rows[1].buchungsdatum, "06.07.23");
    }

    #[test]
    fn test_parse_pdf_text_all_one_line_with_header() {
        let text = "Kontoumsätze\nAuszug Nr. 7 05.07.2023Kartenzahlung onl FLUG AIRLINE -152,00 06.07.2023Wertpapierabrechnung / Wert: 07.07.2023 Depot -75,30\nKontostand am";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].betrag, "-152,00");
        assert_eq!(rows[0].buchungsdatum, "05.07.23");
        assert_eq!(rows[1].betrag, "-75,30");
        assert_eq!(rows[1].buchungsdatum, "06.07.23");
    }

    #[test]
    fn test_parse_pdf_text_single_line_no_newlines() {
        let text = "Kontoumsätze Auszug Nr. 7 05.07.2023Kartenzahlung onl FLUG AIRLINE -152,00 06.07.2023Wertpapierabrechnung / Wert: 07.07.2023 Depot -75,30 10.07.2023Zahlungseingang Taschengeld 300,00";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 3);
        assert_eq!(rows[0].betrag, "-152,00");
        assert_eq!(rows[1].betrag, "-75,30");
        assert_eq!(rows[2].betrag, "+300,00");
    }

    #[test]
    fn test_parse_pdf_text_multi_line() {
        let text = "Kontoumsätze\n22.12.2025 VISA -21,94\nREWE Muenchen\nKontostand am";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
        assert!(rows[0].zahlungsempfaenger.contains("REWE"));
        assert!(rows[0].verwendungszweck.contains("VISA REWE Muenchen"));
        assert_eq!(rows[0].betrag, "-21,94");
    }

    #[test]
    fn test_parse_pdf_text_multiple_transactions() {
        let text = "Kontoumsätze\n22.12.2025 REWE -21,94\n23.12.2025 Gehalt +3.450,00\nKontostand am";
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
    fn test_parse_pdf_text_ignores_non_date_lines() {
        let text = "22.12.2025 REWE -21,94\n";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
    }

    #[test]
    fn test_parse_pdf_text_concatenated_lines() {
        let text = "Kontoumsätze\n05.07.2023 FLUG AIRLINE -152,00 06.07.2023 Depot -75,30\nKontostand am";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].betrag, "-152,00");
        assert_eq!(rows[1].betrag, "-75,30");
    }

    #[test]
    fn test_parse_pdf_text_concatenated_with_embedded_date() {
        let text = "Kontoumsätze\n05.07.2023 FLUG AIRLINE -152,00 06.07.2023 Wertp.Abrechn. 07.07.2023 XYZ -75,30\nKontostand am";
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 2);
        assert_eq!(rows[0].betrag, "-152,00");
        assert_eq!(rows[0].buchungsdatum, "05.07.23");
        assert_eq!(rows[1].betrag, "-75,30");
        assert_eq!(rows[1].buchungsdatum, "06.07.23");
    }

    #[test]
    fn test_parse_pdf_text_concatenated_full_example() {
        let text = concat!(
            "Kontoumsätze\n",
            "05.07.2023 Kartenzahlung onl FLUG AIRLINE -152,00 ",
            "06.07.2023 Depot Wertp.Abrechn. 07.07.2023 XYZ -75,30 ",
            "10.07.2023 Zahlungseingang Taschengeld 300,00 ",
            "12.07.2023 Zahlungseingang Beitrag 80,00\n",
            "Kontostand am",
        );
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 4);
        assert_eq!(rows[0].betrag, "-152,00");
        assert_eq!(rows[1].betrag, "-75,30");
        assert_eq!(rows[2].betrag, "+300,00");
        assert_eq!(rows[3].betrag, "+80,00");
    }

    #[test]
    fn test_parse_pdf_text_skips_wrong_decimal_amounts() {
        let text = concat!(
            "Kontoumsätze\n",
            "06.07.2023 Depot Preis 8,12345678 Stück 4,5000 -51,50\n",
            "Kontostand am",
        );
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].betrag, "-51,50");
        assert_eq!(rows[0].buchungsdatum, "06.07.23");
    }

    #[test]
    fn test_find_last_amount_simple() {
        let (sign, amount, end) = find_last_amount("Kartenzahlung onl FLUG AIRLINE -152,00").unwrap();
        assert_eq!(sign, "-");
        assert_eq!(amount, "152,00");
        assert_eq!(end, 38);
    }

    #[test]
    fn test_find_last_amount_skips_embedded() {
        let s = "Basislastschrift VERSICHERUNG EUR 120,59 . BEITRAG 0123 -120,59";
        let (sign, amount, end) = find_last_amount(s).unwrap();
        assert_eq!(sign, "-");
        assert_eq!(amount, "120,59");
        assert_eq!(end, s.len());
    }

    #[test]
    fn test_find_last_amount_no_match() {
        assert!(find_last_amount("Keine Zahlen hier").is_none());
    }

    #[test]
    fn test_parse_pdf_text_multi_line_amount_on_separate_line() {
        let text = concat!(
            "Kontoumsätze\n",
            "05.07.2023Kartenzahlung onl\n",
            "FLUG AIRLINE XXXXXXXXXX/KOLN//DE 2023-07-03T21:00\n",
            "Debitk.89 2099-12 Zahl.System VISA Debit\n",
            "              -152,00\n",
            "Kontostand am",
        );
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].betrag, "-152,00");
        assert!(rows[0].verwendungszweck.contains("Kartenzahlung onl FLUG AIRLINE"));
    }

    #[test]
    fn test_parse_pdf_text_multi_line_with_embedded_amount_in_purpose() {
        let text = concat!(
            "Kontoumsätze\n",
            "17.07.2023Basislastschrift\n",
            "VERSICHERUNG XYZ - Die Krankenkasse 1234567890\n",
            "OB-XXXXXXXXXX EUR 120,59 . BEITRAG 0123 - 0456\n",
            "Gläubiger-ID: DE00VERSXXXXXXXXXX\n",
            "              -120,59\n",
            "Kontostand am",
        );
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].betrag, "-120,59");
        assert!(rows[0].verwendungszweck.contains("EUR 120,59"));
    }

    #[test]
    fn test_parse_pdf_text_full_pdf_simulation() {
        let text = concat!(
            "Kontoauszug 8/2023\n",
            "  Kontostand am 04.07.2023, Auszug Nr.    7                5.000,00\n",
            "05.07.2023Kartenzahlung onl\n",
            "FLUG AIRLINE XXXXXXXXXX/KOLN//DE\n",
            "Debitk.89 2099-12 Zahl.System VISA Debit\n",
            "              -152,00\n",
            "\n",
            "06.07.2023Wertpapierabrechnung / Wert: 07.07.2023\n",
            "Depot XXXXXXXXXX Wertp.Abrechn. 05.07.2023\n",
            "ETF WORLD SRI U.EOA ISIN XXXXXXXXXX\n",
            "Preis 8,12345678 EUR Stück 4,5000\n",
            "               -75,30\n",
            "\n",
            "10.07.2023Zahlungseingang\n",
            "Familie Mustermann               300,00\n",
            "\n",
            "12.07.2023Zahlungseingang\n",
            "Familie Beispiel               80,00\n",
            "\n",
            "17.07.2023Basislastschrift\n",
            "VERSICHERUNG XYZ - Die Krankenkasse 1234567890\n",
            "OB-XXXXXXXXXX EUR 120,59 . BEITRAG 0123 - 0456\n",
            "Gläubiger-ID: DE00VERSXXXXXXXXXX\n",
            "              -120,59\n",
            "\n",
            "01.08.2023Überweisung\n",
            "ZAHLDIENST EUROPE S.A R.L. ET CIE, S. DATUM 31.07.2023\n",
            "               -11,50\n",
            "\n",
            "04.08.2023Kartenzahlung\n",
            "RESTAURANT MUC/Munchen//DE\n",
            "Debitk.89 2099-12 Zahl.System VISA Debit\n",
            "                -7,00\n",
            "\n",
            "  Kontostand am 04.08.2023 um 18:03 Uhr                5.000,00\n",
        );
        let rows = parse_pdf_text(text);
        assert_eq!(rows.len(), 7);
        assert_eq!(rows[0].betrag, "-152,00");
        assert_eq!(rows[0].buchungsdatum, "05.07.23");
        assert_eq!(rows[1].betrag, "-75,30");
        assert_eq!(rows[1].buchungsdatum, "06.07.23");
        assert_eq!(rows[2].betrag, "+300,00");
        assert_eq!(rows[2].buchungsdatum, "10.07.23");
        assert_eq!(rows[2].umsatztyp, "Eingang");
        assert_eq!(rows[3].betrag, "+80,00");
        assert_eq!(rows[3].buchungsdatum, "12.07.23");
        assert_eq!(rows[3].umsatztyp, "Eingang");
        assert_eq!(rows[4].betrag, "-120,59");
        assert_eq!(rows[4].buchungsdatum, "17.07.23");
        assert_eq!(rows[5].betrag, "-11,50");
        assert_eq!(rows[5].buchungsdatum, "01.08.23");
        assert_eq!(rows[6].betrag, "-7,00");
        assert_eq!(rows[6].buchungsdatum, "04.08.23");
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
