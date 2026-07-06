use std::path::PathBuf;
use std::fs;
use directories::ProjectDirs;

pub fn project_dirs() -> Option<ProjectDirs> {
    ProjectDirs::from("com", "dkb", "dkb-finanz")
}

pub fn config_dir() -> PathBuf {
    let base = project_dirs()
        .map(|d| d.config_dir().to_path_buf())
        .unwrap_or_else(|| {
            let home = std::env::var("HOME")
                .or_else(|_| std::env::var("USERPROFILE"))
                .unwrap_or_else(|_| ".".to_string());
            PathBuf::from(home).join(".config").join("dkb-finanz")
        });
    base
}

pub fn csv_dir() -> PathBuf {
    config_dir().join("csv")
}

pub fn pdf_dir() -> PathBuf {
    config_dir().join("pdf")
}

pub fn categories_path() -> PathBuf {
    config_dir().join("categories.toml")
}

pub fn ensure_dirs() -> std::io::Result<()> {
    fs::create_dir_all(config_dir())?;
    fs::create_dir_all(csv_dir())?;
    fs::create_dir_all(pdf_dir())?;
    Ok(())
}

pub fn copy_defaults_if_missing(bundle_dir: &PathBuf) -> std::io::Result<()> {
    ensure_dirs()?;
    if !categories_path().exists() {
        let src = bundle_dir.join("categories.toml");
        if src.exists() {
            fs::copy(&src, categories_path())?;
        }
    }
    Ok(())
}

pub fn save_category_entries(entries: &[crate::CategoryEntry]) -> std::io::Result<()> {
    let mut output = String::new();
    for entry in entries {
        output.push_str(&format!("[{}]\n", entry.name));
        output.push_str("keywords = [\n");
        for kw in &entry.keywords {
            output.push_str(&format!("    {:?},\n", kw));
        }
        output.push_str("]\n\n");
    }
    fs::write(categories_path(), &output)
}

pub fn load_category_entries() -> Vec<crate::CategoryEntry> {
    let content = fs::read_to_string(categories_path()).unwrap_or_default();
    parse_category_toml(&content)
}

pub fn parse_category_toml(content: &str) -> Vec<crate::CategoryEntry> {
    let parsed: Result<toml::Value, _> = content.parse();
    let parsed = match parsed {
        Ok(v) => v,
        Err(_) => return Vec::new(),
    };
    let table = match parsed.as_table() {
        Some(t) => t,
        None => return Vec::new(),
    };

    let mut entries = Vec::new();
    for (name, value) in table {
        let keywords = value.get("keywords")
            .and_then(|k| k.as_array())
            .map(|a| a.iter()
                .filter_map(|v| v.as_str().map(String::from))
                .collect::<Vec<_>>())
            .unwrap_or_default();
        entries.push(crate::CategoryEntry { name: name.clone(), keywords });
    }
    entries.sort_by(|a, b| a.name.cmp(&b.name));
    entries
}
