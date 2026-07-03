import pandas as pd
from app import filter_expenses


def test_filter_expenses_by_category():
    df = pd.DataFrame({
        "Betrag": [10.0, 20.0, 30.0],
        "Monat_Label": ["Jan 2025", "Jan 2025", "Jan 2025"],
        "Kategorie": ["A", "B", "C"],
    })
    result = filter_expenses(df, selected_categories=["A", "B"])
    assert len(result) == 2
    assert list(result["Kategorie"]) == ["A", "B"]


def test_filter_expenses_all_with_none():
    df = pd.DataFrame({
        "Betrag": [10.0, 20.0],
        "Monat_Label": ["Jan 2025", "Feb 2025"],
        "Kategorie": ["A", "B"],
    })
    result = filter_expenses(df)
    assert len(result) == 2


def test_filter_expenses_by_month():
    df = pd.DataFrame({
        "Betrag": [10.0, 20.0],
        "Monat_Label": ["Jan 2025", "Feb 2025"],
        "Kategorie": ["A", "B"],
    })
    result = filter_expenses(df, selected_months=["Jan 2025"])
    assert len(result) == 1
    assert result.iloc[0]["Monat_Label"] == "Jan 2025"


def test_filter_expenses_empty_result():
    df = pd.DataFrame({
        "Betrag": [10.0],
        "Monat_Label": ["Jan 2025"],
        "Kategorie": ["A"],
    })
    result = filter_expenses(df, selected_months=[], selected_categories=["B"])
    assert result.empty
