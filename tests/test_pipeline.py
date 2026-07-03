from pathlib import Path
import pandas as pd
import pytest

from pipeline import (
    parse_amount,
    parse_date,
    assign_categories,
    transaction_hash,
    load_config,
)


def test_parse_amount_german_negative():
    assert parse_amount("-21,94") == -21.94


def test_parse_amount_german_positive():
    assert parse_amount("290,87") == 290.87


def test_parse_amount_with_thousands_separator():
    assert parse_amount("1.234,56") == 1234.56


def test_parse_amount_empty():
    assert parse_amount("") is None


def test_parse_amount_invalid():
    assert parse_amount("abc") is None


def test_parse_date_two_digit_year():
    d = parse_date("22.12.25")
    assert d is not None
    assert d.year == 2025
    assert d.month == 12
    assert d.day == 22


def test_parse_date_invalid():
    assert parse_date("") is None
    assert parse_date("abc") is None
    assert parse_date("32.01.24") is None


def test_assign_categories_match_payee():
    categories = {"Lebensmittel": ["REWE", "LIDL"]}
    df = pd.DataFrame({
        "Zahlungsempfänger*in": ["REWE München"],
        "Verwendungszweck": ["VISA Einkauf"],
    })
    result = assign_categories(df, categories)
    assert result.iloc[0] == "Lebensmittel"


def test_assign_categories_match_purpose():
    categories = {"Transport": ["DB ", "MVG"]}
    df = pd.DataFrame({
        "Zahlungsempfänger*in": ["UNKNOWN SHOP"],
        "Verwendungszweck": ["DB Fahrkarte"],
    })
    result = assign_categories(df, categories)
    assert result.iloc[0] == "Transport"


def test_assign_categories_no_match():
    categories = {"Lebensmittel": ["REWE"]}
    df = pd.DataFrame({
        "Zahlungsempfänger*in": ["AMAZON"],
        "Verwendungszweck": ["PRIME"],
    })
    result = assign_categories(df, categories)
    assert result.iloc[0] == "Sonstige"


def test_assign_categories_case_insensitive():
    categories = {"Lebensmittel": ["rewe"]}
    df = pd.DataFrame({
        "Zahlungsempfänger*in": ["REWE Berlin"],
        "Verwendungszweck": [""],
    })
    result = assign_categories(df, categories)
    assert result.iloc[0] == "Lebensmittel"


def test_transaction_hash_consistent():
    df = pd.DataFrame({
        "Buchungsdatum": ["22.12.25"],
        "Betrag (€)": ["-21,94"],
        "Zahlungsempfänger*in": ["REWE"],
        "Verwendungszweck": ["Einkauf"],
    })
    h1 = transaction_hash(df.iloc[0])
    h2 = transaction_hash(df.iloc[0])
    assert h1 == h2


def test_transaction_hash_differs():
    df = pd.DataFrame({
        "Buchungsdatum": ["22.12.25", "23.12.25"],
        "Betrag (€)": ["-21,94", "-21,94"],
        "Zahlungsempfänger*in": ["REWE", "REWE"],
        "Verwendungszweck": ["Einkauf", "Einkauf"],
    })
    h1 = transaction_hash(df.iloc[0])
    h2 = transaction_hash(df.iloc[1])
    assert h1 != h2


def test_load_config_defaults():
    import pipeline
    pipeline.CONFIG_FILE = Path("nonexistent.toml")
    cfg = load_config()
    assert cfg["display"]["dpi"] == 150
    assert cfg["charts"]["monthly_bar"]["bar_width_days"] == 20


def test_load_config_nonexistent_file(tmp_path):
    cfg = load_config()
    assert cfg["display"]["font_family"] == "DejaVu Sans"
