use std::sync::Mutex;

use dkb_core::aggregator::build_dashboard_data;
use dkb_core::categorizer::Categorizer;
use dkb_core::config;
use dkb_core::csv_reader;
use dkb_core::pdf_extractor;
use dkb_core::{CategoryEntry, DashboardData};

struct AppState {
    categories: Categorizer,
}

#[tauri::command]
fn get_data(state: tauri::State<Mutex<AppState>>) -> Result<DashboardData, String> {
    let cat = state.lock().map_err(|e| e.to_string())?;
    let csv_transactions = csv_reader::read_all_csvs(&config::csv_dir());
    let pdf_transactions = pdf_extractor::process_pdfs(&config::pdf_dir());

    let mut all = csv_transactions;
    all.extend(pdf_transactions);

    Ok(build_dashboard_data(&all, &cat.categories))
}

#[tauri::command]
fn get_categories() -> Result<Vec<CategoryEntry>, String> {
    Ok(config::load_category_entries())
}

#[tauri::command]
fn save_categories(
    state: tauri::State<Mutex<AppState>>,
    entries: Vec<CategoryEntry>,
) -> Result<(), String> {
    config::save_category_entries(&entries).map_err(|e| e.to_string())?;

    let mut cat = state.lock().map_err(|e| e.to_string())?;
    cat.categories = Categorizer::from_toml(config::categories_path());
    Ok(())
}

#[tauri::command]
fn import_file(path: String) -> Result<String, String> {
    let src = std::path::PathBuf::from(&path);
    if !src.exists() {
        return Err("Datei nicht gefunden".to_string());
    }

    let ext = src.extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_lowercase();

    let dest_dir = match ext.as_str() {
        "csv" => config::csv_dir(),
        "pdf" => config::pdf_dir(),
        _ => return Err("Nur CSV- und PDF-Dateien unterstützt".to_string()),
    };

    let file_name = src.file_name()
        .ok_or_else(|| "Ungültiger Dateiname".to_string())?;
    let dest = dest_dir.join(file_name);

    std::fs::copy(&src, &dest).map_err(|e| e.to_string())?;
    Ok(format!("{} importiert", file_name.to_string_lossy()))
}

#[tauri::command]
fn pick_file() -> Result<Option<String>, String> {
    let dialog = rfd::FileDialog::new()
        .add_filter("CSV/PDF", &["csv", "pdf"])
        .set_title("Kontoauszug importieren")
        .pick_file();
    Ok(dialog.map(|p| p.to_string_lossy().to_string()))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    if let Err(e) = config::copy_defaults_if_missing(
        &std::env::current_dir().unwrap_or_default().join("..").join(".."),
    ) {
        eprintln!("Warnung: Konnte Standard-Konfiguration nicht kopieren: {}", e);
    }

    let categories = Categorizer::from_toml(config::categories_path());
    let state = Mutex::new(AppState { categories });

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(state)
        .invoke_handler(tauri::generate_handler![
            get_data,
            get_categories,
            save_categories,
            import_file,
            pick_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
