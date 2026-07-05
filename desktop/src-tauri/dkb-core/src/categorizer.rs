use std::collections::HashMap;
use std::fs;
use std::path::Path;

use crate::Transaction;

const CATEGORY_OTHER: &str = "Sonstige";

#[derive(Debug, Clone)]
pub struct Categorizer {
    rules: HashMap<String, Vec<String>>,
}

impl Categorizer {
    pub fn new(rules: HashMap<String, Vec<String>>) -> Self {
        Self { rules }
    }

    pub fn from_toml<P: AsRef<Path>>(path: P) -> Self {
        let content = match fs::read_to_string(path.as_ref()) {
            Ok(c) => c,
            Err(_) => return Self { rules: HashMap::new() },
        };
        let parsed: Result<toml::Value, _> = content.parse();
        let parsed = match parsed {
            Ok(v) => v,
            Err(_) => return Self { rules: HashMap::new() },
        };

        let table = match parsed.as_table() {
            Some(t) => t,
            None => return Self { rules: HashMap::new() },
        };

        let mut rules = HashMap::new();
        for (cat_name, value) in table {
            let keywords = match value.get("keywords") {
                Some(k) => k.as_array(),
                None => None,
            };
            if let Some(kws) = keywords {
                let kws: Vec<String> = kws.iter()
                    .filter_map(|v| v.as_str())
                    .map(|s| s.to_uppercase())
                    .collect();
                rules.insert(cat_name.clone(), kws);
            }
        }

        Self { rules }
    }

    pub fn categorize(&self, t: &Transaction) -> String {
        let text_parts: Vec<String> = vec![
            t.zahlungsempfaenger.clone().unwrap_or_default(),
            t.zahlungspflichtiger.clone().unwrap_or_default(),
            t.verwendungszweck.clone().unwrap_or_default(),
        ];
        let text = text_parts.join(" ").to_uppercase();

        for (category, keywords) in &self.rules {
            for kw in keywords {
                if text.contains(kw.as_str()) {
                    return category.clone();
                }
            }
        }
        CATEGORY_OTHER.to_string()
    }

    pub fn all_category_names(&self) -> Vec<String> {
        let mut names: Vec<String> = self.rules.keys().cloned().collect();
        names.sort();
        names
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_categorize_match_payee() {
        let mut rules = HashMap::new();
        rules.insert("Lebensmittel".to_string(), vec!["REWE".to_string(), "LIDL".to_string()]);
        let cat = Categorizer::new(rules);

        let t = Transaction {
            buchungsdatum: "22.12.25".to_string(),
            wertstellung: "22.12.25".to_string(),
            status: Some("Gebucht".to_string()),
            zahlungspflichtiger: None,
            zahlungsempfaenger: Some("REWE Muenchen".to_string()),
            verwendungszweck: Some("VISA Einkauf".to_string()),
            umsatztyp: Some("Ausgang".to_string()),
            iban: None,
            betrag: -21.94,
            glaeubiger_id: None,
            mandatsreferenz: None,
            kundenreferenz: None,
        };

        assert_eq!(cat.categorize(&t), "Lebensmittel");
    }

    #[test]
    fn test_categorize_match_purpose() {
        let mut rules = HashMap::new();
        rules.insert("Strom".to_string(), vec!["ABSCHLAG".to_string()]);
        let cat = Categorizer::new(rules);

        let t = Transaction {
            buchungsdatum: "22.12.25".to_string(),
            wertstellung: "22.12.25".to_string(),
            status: None,
            zahlungspflichtiger: None,
            zahlungsempfaenger: Some("STADTWERKE".to_string()),
            verwendungszweck: Some("Abschlag Strom Januar".to_string()),
            umsatztyp: None,
            iban: None,
            betrag: -85.00,
            glaeubiger_id: None,
            mandatsreferenz: None,
            kundenreferenz: None,
        };

        assert_eq!(cat.categorize(&t), "Strom");
    }

    #[test]
    fn test_categorize_no_match() {
        let rules = HashMap::new();
        let cat = Categorizer::new(rules);

        let t = Transaction {
            buchungsdatum: "22.12.25".to_string(),
            wertstellung: "22.12.25".to_string(),
            status: None,
            zahlungspflichtiger: None,
            zahlungsempfaenger: Some("SOME SHOP".to_string()),
            verwendungszweck: Some("Purchase".to_string()),
            umsatztyp: None,
            iban: None,
            betrag: -10.00,
            glaeubiger_id: None,
            mandatsreferenz: None,
            kundenreferenz: None,
        };

        assert_eq!(cat.categorize(&t), CATEGORY_OTHER);
    }

    #[test]
    fn test_categorize_case_insensitive() {
        let mut rules = HashMap::new();
        rules.insert("Lebensmittel".to_string(), vec!["REWE".to_string()]);
        let cat = Categorizer::new(rules);

        let t = Transaction {
            buchungsdatum: "22.12.25".to_string(),
            wertstellung: "22.12.25".to_string(),
            status: None,
            zahlungspflichtiger: None,
            zahlungsempfaenger: Some("REWE Muenchen".to_string()),
            verwendungszweck: None,
            umsatztyp: None,
            iban: None,
            betrag: -10.00,
            glaeubiger_id: None,
            mandatsreferenz: None,
            kundenreferenz: None,
        };

        assert_eq!(cat.categorize(&t), "Lebensmittel");
    }

}
