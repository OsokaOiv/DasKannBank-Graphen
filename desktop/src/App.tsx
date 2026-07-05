import { useState, useEffect } from "react";
import Dashboard from "./components/Dashboard";
import DataView from "./components/DataView";
import "./App.css";

type View = "dashboard" | "data";

function App() {
  const [view, setView] = useState<View>("dashboard");
  const [dark, setDark] = useState(() => localStorage.getItem("dkb-dark") === "true");

  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("dkb-dark", String(dark));
  }, [dark]);

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
        <button
          className="dark-toggle"
          onClick={() => setDark(!dark)}
          aria-label={dark ? "☀️" : "🌙"}
        >
          {dark ? "☀️" : "🌙"}
        </button>
      </nav>
      {view === "dashboard" ? <Dashboard /> : <DataView />}
    </div>
  );
}

export default App;
