use std::process::{Command, Child};
use std::sync::Mutex;
use tauri::Manager;

struct PythonBackend(Mutex<Option<Child>>);

fn start_python_backend() -> Option<Child> {
    let child = Command::new(".venv/bin/python")
        .arg("api.py")
        .spawn();
    match child {
        Ok(c) => {
            println!("Python backend started with PID {}", c.id());
            Some(c)
        }
        Err(e) => {
            eprintln!("Failed to start Python backend: {}", e);
            None
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let backend = start_python_backend();
    std::thread::sleep(std::time::Duration::from_secs(2));

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(PythonBackend(Mutex::new(backend)))
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Some(state) = window.try_state::<PythonBackend>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            let _ = child.kill();
                            println!("Python backend stopped");
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
