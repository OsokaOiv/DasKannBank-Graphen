import io
import os
import pandas as pd
from app import filter_expenses, filter_income, _save_uploaded_files


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


def test_filter_income_by_month():
    df = pd.DataFrame({
        "Betrag": [10.0, 20.0],
        "Monat_Label": ["Jan 2025", "Feb 2025"],
    })
    result = filter_income(df, ["Jan 2025"])
    assert len(result) == 1
    assert result.iloc[0]["Monat_Label"] == "Jan 2025"


def test_filter_income_all_when_none():
    df = pd.DataFrame({
        "Betrag": [10.0, 20.0],
        "Monat_Label": ["Jan 2025", "Feb 2025"],
    })
    result = filter_income(df)
    assert len(result) == 2


def test_filter_income_empty():
    df = pd.DataFrame({
        "Betrag": [10.0],
        "Monat_Label": ["Jan 2025"],
    })
    result = filter_income(df, ["Feb 2025"])
    assert result.empty


class _FakeUploadedFile:
    """Duck-typed mock of streamlit's UploadedFile that only provides what _save_uploaded_files uses."""
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._buf = io.BytesIO(data)

    def getbuffer(self):
        return self._buf.getbuffer()


def test_save_uploaded_files_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fake = _FakeUploadedFile("test.csv", b"a,b,c\n1,2,3")
    saved, errors = _save_uploaded_files([fake])
    assert saved == 1
    assert errors == []
    assert os.path.exists("csv/test.csv")
    with open("csv/test.csv") as f:
        assert f.read() == "a,b,c\n1,2,3"


def test_save_uploaded_files_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with open("csv", "w") as f:
        f.write("not a directory")
    fake = _FakeUploadedFile("test.csv", b"data")
    saved, errors = _save_uploaded_files([fake])
    assert saved == 0
    assert len(errors) >= 1


def test_save_uploaded_files_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    saved, errors = _save_uploaded_files([])
    assert saved == 0
    assert errors == []
