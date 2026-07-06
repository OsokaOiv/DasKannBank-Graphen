import { useState, useEffect, useCallback, type JSX } from "react";
import Dashboard from "./components/Dashboard";
import DataView from "./components/DataView";
import "./App.css";
import type { ThemeId } from "./themes";
import { THEMES, loadTheme, saveTheme, applyTheme } from "./themes";

const STORAGE_DARK_KEY = "dkb-dark";

type View = "dashboard" | "data";

function App(): JSX.Element {
  const [view, setView] = useState<View>("dashboard");
  const [theme, setTheme] = useState<ThemeId>(loadTheme);
  const [dark, setDark] = useState(() => {
    const t = loadTheme();
    return t !== "standard" || localStorage.getItem(STORAGE_DARK_KEY) === "true";
  });

  const syncTheme = useCallback((t: ThemeId, d: boolean) => {
    applyTheme(t, d);
    saveTheme(t);
    if (t === "standard") localStorage.setItem(STORAGE_DARK_KEY, String(d));
  }, []);

  const handleThemeChange = useCallback((t: ThemeId) => {
    setTheme(t);
    const isDark = t !== "standard" || dark;
    setDark(isDark);
    syncTheme(t, isDark);
  }, [dark, syncTheme]);

  const handleDarkToggle = useCallback(() => {
    const next = !dark;
    setDark(next);
    syncTheme(theme, next);
  }, [dark, theme, syncTheme]);

  useEffect(() => {
    syncTheme(theme, dark);
  }, []);

  const currentTheme = THEMES.find((t) => t.id === theme) ?? THEMES[0];

  return (
    <div className="app-layout">
      <nav className="app-nav">
        <button
          className={`nav-btn ${view === "dashboard" ? "active" : ""}`}
          onClick={() => setView("dashboard")}
        >
          Dashboard
        </button>
        <button
          className={`nav-btn ${view === "data" ? "active" : ""}`}
          onClick={() => setView("data")}
        >
          Daten
        </button>
        <div className="nav-spacer" />
        <select
          className="theme-select"
          value={theme}
          onChange={(e) => handleThemeChange(e.target.value as ThemeId)}
          aria-label="Design wählen"
        >
          {THEMES.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label}
            </option>
          ))}
        </select>
        {currentTheme.alwaysDark ? (
          <span className="dark-indicator">🌙</span>
        ) : (
          <button
            className="dark-toggle"
            onClick={handleDarkToggle}
            aria-label={dark ? "Helles Design" : "Dunkles Design"}
          >
            {dark ? "☀️" : "🌙"}
          </button>
        )}
      </nav>
      {view === "dashboard" ? <Dashboard dark={dark || currentTheme.alwaysDark} /> : <DataView />}
    </div>
  );
}

export default App;
