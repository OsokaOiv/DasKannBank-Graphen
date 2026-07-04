# Plan: Einnahmen-Visualisierung ✅ Implementiert

## Ziel
Einnahmen (positive Beträge in der CSV) analog zu den Ausgaben visualisieren – in `pipeline.py` (matplotlib, statisch) und `app.py` (Plotly, interaktiv).  
Keine Kategorien nötig – Einnahmen sind typischerweise Gehalt + wenige andere Quellen.

---

## 1. Datenvorbereitung

### Neue Funktion: `prepare_income()`

Analog zu `prepare_expenses()`, aber filtert `Betrag > 0` statt `< 0` und absolutiert nicht.

```python
def prepare_income(df: pd.DataFrame) -> pd.DataFrame:
    income = df[df["Betrag"] > 0].copy()
    income["Monat"] = income["Datum"].dt.to_period("M").dt.to_timestamp()
    income["Jahr"] = income["Datum"].dt.year
    return income
```

### Integration in `load_data()`

`app.py`'s `load_data()` muss zusätzlich `prepare_income(df)` zurückgeben.  
`pipeline.py`'s `main()` ruft `prepare_income(df)` parallel zu `prepare_expenses()`.

### CLI-Argumente

Neues Chart-Set `"income"` in `chart_map`:

```python
"income": {"income"}
"all": {"total", "yearly", "monthly", "monthly-pies", "income"}
```

---

## 2. Diagramm-Typen

### Matplotlib (`pipeline.py`)

| Diagramm | Dateiname | Beschreibung |
|---|---|---|
| Monatliche Balken | `einnahmen_pro_monat.png` | Ein Balken pro Monat, Höhe = Summe Einnahmen |
| Monatliche Linie | `einnahmen_linie_pro_monat.png` | Linienchart mit Markern |
| Jährliche Balken | `einnahmen_pro_jahr.png` | Ein Balken pro Jahr |
| Einnahmen vs Ausgaben | `einnahmen_vs_ausgaben.png` | Vergleich nebeneinander |

#### Neue Funktionen in `pipeline.py`

- `plot_income_monthly(income, cfg)` – Balken + Linie
- `plot_income_yearly(income, cfg)` – Jahresbalken
- `plot_income_vs_expenses(income, expenses, cfg)` – gruppierte Balken

### Streamlit (`app.py`)

| Diagramm-Typ | Beschreibung |
|---|---|
| Balken (Monat) | Plotly Express bar chart |
| Linie (Monat) | Plotly Express line chart |
| Balken (Jahr) | Jahresübersicht |
| Vergleich | Einnahmen vs Ausgaben overlay |

#### Neue Render-Funktionen

- `render_income_monthly_bar(filtered_income)`
- `render_income_monthly_line(filtered_income)`
- `render_income_yearly(filtered_income)`
- `render_income_vs_expenses(filtered_income, filtered_expenses)`

### Sidebar-Einträge

Neue Chart-Typen in `render_sidebar()`:

```
"Einnahmen (Balken)",
"Einnahmen (Linie)",
"Einnahmen vs Ausgaben"
```

---

## 3. Filter

Einnahmen haben dieselben Filter wie Ausgaben (Monate). Kategoriefilter entfällt (keine Kategorisierung nötig).

---

## 4. Datenstruktur

```
Raw CSV → Betrag > 0 → prepare_income()
                               ↓
                   ┌─────────────────────┐
                   │ Datum  | Betrag |   │
                   │ Monat  | Jahr   |   │
                   └─────────────────────┘
```

Keine `Kategorie`-Spalte, kein `assign_categories()`.

---

## 5. Tests

### Neue Tests in `tests/test_pipeline.py`

- `test_prepare_income_filters_positive()` – nur positive Beträge
- `test_prepare_income_creates_monat()` – Monatsspalte korrekt
- `test_prepare_income_creates_jahr()` – Jahrespalte korrekt
- `test_prepare_income_empty()` – leeres Ergebnis bei nur Ausgaben

### Neue Tests in `tests/test_app.py`

- `test_filter_income_by_month()` – Monatsfilter auf Einnahmen

---

## 6. Umsetzungsschritte

1. `prepare_income()` in `pipeline.py` schreiben + testen
2. Matplotlib-Charts in `pipeline.py`: 3 neue Funktionen + `"income"` in `chart_map` + CLI
3. `load_data()` erweitern (income parallel zu expenses laden)
4. Plotly-Charts in `app.py`: 3 neue Render-Funktionen + Sidebar-Einträge
5. `plot_income_vs_expenses()` für beide Module
6. Tests schreiben + alte Tests grün halten
7. Docs ergänzen
8. Dashboard-Screenshot mit beiden Modi aktualisieren
