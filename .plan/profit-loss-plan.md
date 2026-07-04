# Plan: Gewinn/Verlust (Einnahmen − Ausgaben) ✅ Implementiert

## Ziel
Monatliche Differenz aus Einnahmen und Ausgaben als eigenes Diagramm – zeigt auf einen Blick, ob ein Monat im Plus oder Minus war.

**Abhängigkeit:** Income-Graphs müssen zuerst implementiert sein (`.plan/income-graph-plan.md`).

---

## 1. Datenberechnung

Aus den bestehenden DataFrames `expenses` und `income`:

```python
def prepare_profit_loss(expenses: pd.DataFrame, income: pd.DataFrame) -> pd.DataFrame:
    monthly_expenses = expenses.groupby("Monat")["Betrag"].sum().rename("Ausgaben")
    monthly_income = income.groupby("Monat")["Betrag"].sum().rename("Einnahmen")
    merged = pd.merge(monthly_income, monthly_expenses, left_index=True, right_index=True, how="outer").fillna(0)
    merged["Differenz"] = merged["Einnahmen"] - merged["Ausgaben"]
    merged["Status"] = merged["Differenz"].apply(lambda x: "Gewinn" if x >= 0 else "Verlust")
    return merged.reset_index()
```

Ergebnis pro Monat: Einnahmen, Ausgaben, Differenz, Status (Gewinn/Verlust).

Beispiel:

| Monat | Einnahmen | Ausgaben | Differenz | Status |
|---|---|---|---|---|
| 2025-01 | 3.450,00 | 398,10 | 3.051,90 | Gewinn |
| 2025-02 | 3.450,00 | 303,81 | 3.146,19 | Gewinn |

---

## 2. Diagramm-Typen

### Matplotlib (`pipeline.py`)

| Diagramm | Dateiname | Beschreibung |
|---|---|---|
| Differenz-Balken | `gewinne_pro_monat.png` | Ein Balken pro Monat, grün = Gewinn, rot = Verlust, Null-Linie markiert |
| Einnahmen vs Ausgaben | `einnahmen_vs_ausgaben_monat.png` | Gruppierte Balken Einnahmen vs Ausgaben pro Monat |

### Streamlit (`app.py`)

| Diagramm-Typ | Beschreibung |
|---|---|
| Gewinn/Verlust Balken | Farbcodiert (grün/rot), Hover zeigt Einnahmen + Ausgaben + Differenz |
| Einnahmen vs Ausgaben | Gruppierte Balken zum Vergleichen |

---

## 3. Visualisierungs-Details

### Farbcodierung

- **Gewinn (Differenz ≥ 0):** grün (`#2ecc71`)
- **Verlust (Differenz < 0):** rot (`#e74c3c`)
- **Referenzlinie bei 0** – horizontal, gestrichelt, grau

### Hover-Informationen (Streamlit/Plotly)

```
Januar 2025
Einnahmen:  3.450,00 €
Ausgaben:    398,10 €
Differenz:  3.051,90 € ✅ Gewinn
```

---

## 4. Platzierung

Eigenes CLI-Argument `"profit"` in `pipeline.py`:

```python
"profit" in charts → plot_profit_loss(...)
```

Eigener Sidebar-Eintrag in `app.py`:

```
"Gewinn/Verlust (Monat)"
"Einnahmen vs Ausgaben (Monat)"
```

---

## 5. Tests

### Neue Tests in `tests/test_pipeline.py`

- `test_prepare_profit_loss_basic()` – korrekte Berechnung bei Standarddaten
- `test_prepare_profit_loss_profit()` – Einnahmen > Ausgaben → Gewinn
- `test_prepare_profit_loss_loss()` – Ausgaben > Einnahmen → Verlust
- `test_prepare_profit_loss_equal()` – Einnahmen = Ausgaben → Gewinn (≥ 0)
- `test_prepare_profit_loss_empty_income()` – Monat ohne Einnahmen
- `test_prepare_profit_loss_empty_expenses()` – Monat ohne Ausgaben

### Neue Tests in `tests/test_app.py`

- `test_render_profit_loss_colors()` – grüne/rote Balken je nach Vorzeichen

---

## 6. Umsetzungsschritte

1. `prepare_profit_loss()` in `pipeline.py` schreiben + testen
2. Matplotlib-Charts: `plot_profit_loss()` + `plot_income_vs_expenses()`
3. `"profit"` in CLI + `chart_map` + `plot_all_charts()` aufnehmen
4. Streamlit: Render-Funktion + Sidebar-Eintrag + `chart_map`
5. Tests schreiben
6. Docs ergänzen
