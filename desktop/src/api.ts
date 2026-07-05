import type { DashboardData, CategoryEntry } from "./types";

const API_BASE = "http://127.0.0.1:8765";

function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

async function tauriInvoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<T>(cmd, args);
}

export async function fetchDashboardData(): Promise<DashboardData> {
  if (isTauri()) {
    return tauriInvoke<DashboardData>("get_data");
  }
  const res = await fetch(`${API_BASE}/api/data`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchCategories(): Promise<CategoryEntry[]> {
  if (isTauri()) {
    return tauriInvoke<CategoryEntry[]>("get_categories");
  }
  const res = await fetch(`${API_BASE}/api/categories`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function saveCategories(entries: CategoryEntry[]): Promise<void> {
  if (isTauri()) {
    return tauriInvoke<void>("save_categories", { entries });
  }
  const res = await fetch(`${API_BASE}/api/categories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entries),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
}

export async function importFile(path: string): Promise<string> {
  if (isTauri()) {
    return tauriInvoke<string>("import_file", { path });
  }
  const formData = new FormData();
  const response = await fetch(path);
  const blob = await response.blob();
  const file = new File([blob], path.split("/").pop() || "file.csv");
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload error: ${res.status}`);
  const data = await res.json();
  return data.saved;
}

export async function pickFile(): Promise<string | null> {
  if (isTauri()) {
    return tauriInvoke<string | null>("pick_file");
  }
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv,.pdf";
    input.onchange = () => {
      if (input.files && input.files[0]) {
        resolve(input.files[0].name);
      } else {
        resolve(null);
      }
    };
    input.click();
  });
}
