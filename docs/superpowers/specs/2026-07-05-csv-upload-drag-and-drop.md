# CSV-Upload per Drag-and-Drop im Streamlit-Dashboard

## Problemstellung

Das DKB-Ausgaben-Dashboard liest aktuell CSV-Dateien ausschließlich aus dem lokalen
`csv/`-Verzeichnis. Nutzer müssen Dateien manuell dorthin kopieren und die App
neu starten oder warten, bis die Dateien erkannt werden.

## Ziel

Ein sidebar-basierter CSV-Upload mit Drag-and-Drop-Unterstützung, der es erlaubt,
DKB-CSV-Exporte direkt im Browser hochzuladen, ohne auf das Dateisystem des Servers
zugreifen zu müssen.

## Architektur

Die Änderung erfolgt ausschließlich in `app.py`. Die Business-Logik in `pipeline.py`
bleibt unverändert — sie liest weiterhin alle `*.csv`-Dateien aus dem `csv/`-Verzeichnis.

```
[Browser]  --Drag&Drop-->  st.popover + st.file_uploader
                                   |
                                   v
                            csv/ -Verzeichnis (Speicher)
                                   |
                                   v
                         st.cache_data.clear() + st.rerun()
                                   |
                                   v
                        load_data() liest neu ein
```

## Komponenten-Design

### 1. Sidebar-Trigger

- Ein `st.sidebar.popover("📁 CSV hochladen")`-Button im Sidebar-Bereich.
- Position: Oberhalb der Filter (vor `render_sidebar()`), damit er immer sichtbar ist.

### 2. Popover-Inhalt

- **Drag-and-Drop-Zone** via `st.file_uploader("DKB-CSV-Dateien hier ablegen", type="csv", accept_multiple_files=True)`.
  - Der native Streamlit-File-Uploader bietet bereits HTML5-Drag-and-Drop.
  - Akzeptiert `.csv`-Dateien im DKB-Export-Format.
  - `accept_multiple_files=True` erlaubt Bulk-Upload.

- **Datei-Liste (optional)**: Zeigt die Namen der hochgeladenen Dateien.
  - via `session_state` gepuffert: `st.session_state["uploaded_files"]`

- **"Anwenden"-Button**: `st.button("Anwenden", type="primary", use_container_width=True)`.

### 3. Anwenden-Logik

```python
def _save_uploaded_files(uploaded_files: list) -> None:
    os.makedirs("csv", exist_ok=True)
    for f in uploaded_files:
        with open(os.path.join("csv", f.name), "wb") as out:
            out.write(f.getbuffer())
```

- Speichert jede Datei in das bestehende `csv/`-Verzeichnis.
- Überschreibt gleichnamige Dateien (kein Duplikat-Schutz nötig — DKB-Exporte haben unterschiedliche Dateinamen).
- Nach dem Speichern: `st.cache_data.clear()` → `st.rerun()`.

### 4. Zustandsmanagement

- `st.session_state["uploaded_files"]`: Liste der vom User ausgewählten Dateien.
- `st.session_state["upload_success"]`: Boolean/Message für Feedback.
- Keine dauerhafte Persistenz nötig — der Upload-Status lebt nur innerhalb der Session.

## Fehlerbehandlung

| Szenario | Reaktion |
|---|---|
| Keine Datei ausgewählt + "Anwenden" | `st.warning("Bitte wähle mindestens eine CSV-Datei aus.")` |
| Datei ist kein gültiges CSV | Keine serverseitige Validierung (wird von `load_transactions` abgefangen) |
| Datei-Schreibfehler | `st.error("Fehler beim Speichern: {msg}")` |
| `csv/`-Verzeichnis fehlt | Wird automatisch angelegt (`os.makedirs`) |

## Testing

Manuelle Tests:
1. Sidebar-Popover öffnen → Drag-and-drop einer CSV → Datei erscheint in der Liste
2. "Anwenden" klicken → Dashboard aktualisiert sich mit neuen Daten
3. Mehrere Dateien gleichzeitig hochladen → Alle werden gespeichert
4. Keine Datei ausgewählt + "Anwenden" → Warnmeldung erscheint
5. Ungültige Datei (kein CSV) → Uploader blockiert via `type="csv"`

## Offene Fragen / Nicht enthalten

- Keine persistente Upload-Historie
- Keine Löschfunktion für hochgeladene Dateien (könnte als Follow-Up kommen)
- Kein PDF-Upload (pdf2csv.py bleibt separater CLI-Pfad)

## Abhängigkeiten

- `streamlit>=1.29` (für `st.popover`)
- Keine neuen Python-Pakete erforderlich
