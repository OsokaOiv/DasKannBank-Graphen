# Konfiguration

## `categories.toml` – Kategorie-Definitionen

Jede Kategorie hat eine Liste von **Keywords**. Eine Transaktion wird kategorisiert, wenn eines der Keywords im Payee oder Purpose (case-insensitive) vorkommt.

```toml
[Lebensmittel]
keywords = ["REWE", "Lidl", "EDEKA"]

["Essen & Trinken"]
keywords = ["RESTAURANT", "MCDONALD"]
```

**Regeln:**
- Vergleich erfolgt per **Substring** (nicht exakt): "REWE München" matched auf "REWE"
- Groß-/Kleinschreibung irrelevant (Pipeline normalisiert alles zu UPPERCASE intern)
- Erste passende Kategorie gewinnt (Reihenfolge in der Datei)
- Kein Match → Kategorie **"Sonstige"**

### Kategorien mit Sonderzeichen

Wenn der Kategoriename Leerzeichen oder Sonderzeichen enthält, in Anführungszeichen setzen:

```toml
["Essen & Trinken"]
keywords = ["RESTAURANT"]
```

## `pipeline.toml` – Diagramm-Einstellungen

Steuert DPI, Schriftart und Diagrammgrößen für die matplotlib-Ausgabe (`pipeline.py`).

```toml
[display]
dpi = 150
font_family = "DejaVu Sans"

[charts.pie]
figure_width = 10
figure_height = 7

[charts.monthly_bar]
figure_width = 14
figure_height = 7
bar_width_days = 20

[charts.monthly_line]
figure_width = 14
figure_height = 7
```

Kann weggelassen werden – dann gelten Defaults (DPI 150, DejaVu Sans, Breite 10/14, Höhe 7).

### Default-Werte

| Pfad | Default |
|---|---|
| `display.dpi` | 150 |
| `display.font_family` | "DejaVu Sans" |
| `charts.pie.figure_width` | 10 |
| `charts.pie.figure_height` | 7 |
| `charts.monthly_bar.figure_width` | 14 |
| `charts.monthly_bar.figure_height` | 7 |
| `charts.monthly_bar.bar_width_days` | 20 |
| `charts.monthly_line.figure_width` | 14 |
| `charts.monthly_line.figure_height` | 7 |

## `~/.streamlit/config.toml` – Streamlit-Konfiguration

Zum Deaktivieren des Streamlit-Telemetrie-Trackings:

```toml
[browser]
gatherUsageStats = false
```

Datei anlegen unter `~/.streamlit/config.toml`.
