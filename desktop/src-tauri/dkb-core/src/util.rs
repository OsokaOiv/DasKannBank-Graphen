use std::fs;
use std::path::Path;

pub fn parse_amount(raw: &str) -> Option<f64> {
    let cleaned = raw.trim()
        .replace('.', "")
        .replace(',', ".")
        .replace("€", "")
        .replace('+', "")
        .trim()
        .to_string();
    cleaned.parse::<f64>().ok()
}

pub fn collect_files(dir: &Path, extension: &str) -> Vec<std::path::PathBuf> {
    if !dir.exists() {
        return Vec::new();
    }
    let mut paths: Vec<_> = match fs::read_dir(dir) {
        Ok(entries) => entries
            .filter_map(|e| e.ok())
            .map(|e| e.path())
            .filter(|p| p.extension().is_some_and(|ext| ext == extension))
            .collect(),
        Err(_) => return Vec::new(),
    };
    paths.sort();
    paths
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_amount_positive() {
        assert_eq!(parse_amount("1.234,56"), Some(1234.56));
    }

    #[test]
    fn test_parse_amount_negative() {
        assert_eq!(parse_amount("-58,23"), Some(-58.23));
    }

    #[test]
    fn test_parse_amount_no_thousands() {
        assert_eq!(parse_amount("3.450,00"), Some(3450.00));
    }

    #[test]
    fn test_parse_amount_empty() {
        assert!(parse_amount("").is_none());
    }

    #[test]
    fn test_parse_amount_invalid() {
        assert!(parse_amount("abc").is_none());
    }

    #[test]
    fn test_parse_amount_with_euro() {
        assert_eq!(parse_amount("1.234,56 €"), Some(1234.56));
    }

    #[test]
    fn test_parse_amount_with_plus() {
        assert_eq!(parse_amount("+290,87"), Some(290.87));
    }
}
