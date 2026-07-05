use std::sync::Mutex;

use axum::{
    Router,
    routing::get,
    Json,
    response::IntoResponse,
    http::Method,
};
use tower_http::cors::{CorsLayer, Any};
use dkb_core::aggregator::build_dashboard_data;
use dkb_core::categorizer::Categorizer;
use dkb_core::config;
use dkb_core::csv_reader;
use dkb_core::pdf_extractor;

struct AppState {
    categories: Mutex<Categorizer>,
}

async fn get_data_handler(
    axum::extract::State(state): axum::extract::State<std::sync::Arc<AppState>>,
) -> impl IntoResponse {
    let cat = state.categories.lock().unwrap();
    let csv_transactions = csv_reader::read_all_csvs(&config::csv_dir());
    let pdf_transactions = pdf_extractor::process_pdfs(&config::pdf_dir());

    let mut all = csv_transactions;
    all.extend(pdf_transactions);

    let data = build_dashboard_data(&all, &cat);
    Json(data)
}

async fn health_handler() -> impl IntoResponse {
    Json(serde_json::json!({"status": "ok"}))
}

#[tokio::main]
async fn main() {
    let _ = config::copy_defaults_if_missing(&std::env::current_dir().unwrap_or_default());
    let categories = Categorizer::from_toml(config::categories_path());

    let state = std::sync::Arc::new(AppState {
        categories: Mutex::new(categories),
    });

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([Method::GET, Method::POST])
        .allow_headers(Any);

    let app = Router::new()
        .route("/api/health", get(health_handler))
        .route("/api/data", get(get_data_handler))
        .layer(cors)
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:8765").await.unwrap();
    println!("Web server listening on http://127.0.0.1:8765");
    axum::serve(listener, app).await.unwrap();
}
