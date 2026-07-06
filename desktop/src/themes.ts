export type ThemeId = "standard" | "terminal-pro" | "neon-finance" | "cyber-dashboard";

export interface ThemeDef {
  id: ThemeId;
  label: string;
  description: string;
  alwaysDark: boolean;
}

export const THEMES: ThemeDef[] = [
  {
    id: "standard",
    label: "Standard",
    description: "Hell/Dunkel umschaltbar",
    alwaysDark: false,
  },
  {
    id: "terminal-pro",
    label: "Terminal Pro",
    description: "Cyan-Akzente, monospace, CRT-Glow",
    alwaysDark: true,
  },
  {
    id: "neon-finance",
    label: "Neon Finance",
    description: "Smaragd + elektrisches Blau, Glas-Karten",
    alwaysDark: true,
  },
  {
    id: "cyber-dashboard",
    label: "Cyber Dashboard",
    description: "Bernstein-Akzente, warmes Terminal-Glühen",
    alwaysDark: true,
  },
];

const STORAGE_THEME_KEY = "dkb-theme";

export function loadTheme(): ThemeId {
  return (localStorage.getItem(STORAGE_THEME_KEY) as ThemeId) || "standard";
}

export function saveTheme(id: ThemeId): void {
  localStorage.setItem(STORAGE_THEME_KEY, id);
}

export function applyTheme(id: ThemeId, dark: boolean): void {
  const root = document.documentElement;
  root.classList.remove("theme-standard", "theme-terminal-pro", "theme-neon-finance", "theme-cyber-dashboard");
  root.classList.add(`theme-${id}`);
  if (dark || id !== "standard") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}
