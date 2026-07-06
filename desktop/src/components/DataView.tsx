import { useEffect, useState } from "react";
import { fetchDashboardData, fetchCategories, saveCategories, importFile, pickFile } from "../api";
import type { DashboardData, CategoryEntry } from "../types";
import DataTables from "./DataTables";
import Uncategorized from "./Uncategorized";

export default function DataView() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [categories, setCategories] = useState<CategoryEntry[]>([]);
  const [editing, setEditing] = useState(false);
  const [editEntries, setEditEntries] = useState<CategoryEntry[]>([]);
  const [saving, setSaving] = useState(false);
  const [importMsg, setImportMsg] = useState("");

  useEffect(() => {
    fetchDashboardData().then(setData).catch(() => {});
    fetchCategories().then(setCategories).catch(() => {});
  }, []);

  const startEditing = () => {
    setEditEntries(categories.map((c) => ({ name: c.name, keywords: [...c.keywords] })));
    setEditing(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveCategories(editEntries);
      setCategories(editEntries);
      setEditing(false);
    } catch (e) {
      console.error("Save failed", e);
    } finally {
      setSaving(false);
    }
  };

  const updateCategoryName = (idx: number, name: string) => {
    const next = [...editEntries];
    next[idx] = { ...next[idx], name };
    setEditEntries(next);
  };

  const updateKeyword = (catIdx: number, kwIdx: number, value: string) => {
    const next = [...editEntries];
    const kws = [...next[catIdx].keywords];
    kws[kwIdx] = value;
    next[catIdx] = { ...next[catIdx], keywords: kws };
    setEditEntries(next);
  };

  const addKeyword = (catIdx: number) => {
    const next = [...editEntries];
    next[catIdx] = { ...next[catIdx], keywords: [...next[catIdx].keywords, ""] };
    setEditEntries(next);
  };

  const removeKeyword = (catIdx: number, kwIdx: number) => {
    const next = [...editEntries];
    next[catIdx] = { ...next[catIdx], keywords: next[catIdx].keywords.filter((_, i) => i !== kwIdx) };
    setEditEntries(next);
  };

  const addCategory = () => {
    setEditEntries([...editEntries, { name: "", keywords: [""] }]);
  };

  const removeCategory = (idx: number) => {
    setEditEntries(editEntries.filter((_, i) => i !== idx));
  };

  const handleImport = async () => {
    const path = await pickFile();
    if (!path) return;
    setImportMsg("Importiere …");
    try {
      const msg = await importFile(path);
      setImportMsg(msg);
      const d = await fetchDashboardData();
      setData(d);
    } catch (e) {
      setImportMsg(e instanceof Error ? e.message : "Fehler beim Import");
    }
  };

  return (
    <div className="app-body" style={{ flexDirection: "column", overflow: "auto", padding: 24 }}>
      <div className="data-actions">
        <h2>Kategorie-Editor</h2>
        {!editing ? (
          <button className="data-btn" onClick={startEditing}>
            Kategorien bearbeiten
          </button>
        ) : (
          <div className="editor-actions">
            <button className="data-btn primary" onClick={handleSave} disabled={saving}>
              {saving ? "Speichert …" : "Speichern"}
            </button>
            <button className="data-btn" onClick={() => setEditing(false)}>
              Abbrechen
            </button>
          </div>
        )}
      </div>

      {editing && (
        <div className="category-editor">
          {editEntries.map((entry, ci) => (
            <div key={ci} className="cat-entry">
              <div className="cat-header">
                <input
                  className="cat-name-input"
                  value={entry.name}
                  onChange={(e) => updateCategoryName(ci, e.target.value)}
                  placeholder="Kategoriename"
                />
                <button className="data-btn small danger" onClick={() => removeCategory(ci)}>
                  ✕
                </button>
              </div>
              <div className="keyword-list">
                {entry.keywords.map((kw, ki) => (
                  <div key={ki} className="keyword-row">
                    <input
                      value={kw}
                      onChange={(e) => updateKeyword(ci, ki, e.target.value)}
                      placeholder="Keyword"
                    />
                    <button className="data-btn small" onClick={() => removeKeyword(ci, ki)}>
                      ✕
                    </button>
                  </div>
                ))}
                <button className="data-btn small" onClick={() => addKeyword(ci)}>
                  + Keyword
                </button>
              </div>
            </div>
          ))}
          <button className="data-btn" onClick={addCategory}>
            + Kategorie
          </button>
        </div>
      )}

      <div className="data-actions" style={{ marginTop: 24 }}>
        <h2>Dateien importieren</h2>
        <button className="data-btn" onClick={handleImport}>
          CSV/PDF auswählen
        </button>
        {importMsg && <span className="import-msg">{importMsg}</span>}
      </div>

      {data && (
        <div style={{ marginTop: 24 }}>
          <DataTables expenses={data.expenses} />
          <div style={{ marginTop: 16 }}>
            <Uncategorized expenses={data.expenses} />
          </div>
        </div>
      )}
    </div>
  );
}
