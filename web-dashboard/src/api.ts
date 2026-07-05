import type { DashboardData } from "./types";

const API_BASE = "http://127.0.0.1:8765";

export async function fetchDashboardData(): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/api/data`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
