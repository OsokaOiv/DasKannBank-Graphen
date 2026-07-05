import hashlib
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import pandas as pd
import warnings
from datetime import datetime
from constants import (
    CSV_DIR,
    CONFIG_FILE,
    CATEGORY_OTHER,
)


def load_config() -> dict:
    defaults = {
        "display": {"dpi": 150, "font_family": "DejaVu Sans"},
        "charts": {
            "pie": {"figure_width": 10, "figure_height": 7},
            "monthly_bar": {"figure_width": 14, "figure_height": 7, "bar_width_days": 20},
            "monthly_line": {"figure_width": 14, "figure_height": 7},
        },
    }
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            user = tomllib.load(f)
        for section, values in user.items():
            if section in defaults:
                defaults[section].update(values)
            else:
                defaults[section] = values
    return defaults


def load_categories(path: Path) -> dict[str, list[str]]:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return {name: [k.upper() for k in entry["keywords"]] for name, entry in data.items()}


def parse_amount(raw: str) -> float | None:
    raw = raw.strip().replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_date(raw: str) -> datetime | None:
    try:
        return datetime.strptime(raw.strip(), "%d.%m.%y")
    except (ValueError, AttributeError):
        return None


def transaction_hash(row: pd.Series) -> str:
    raw = f"{row['Buchungsdatum']}|{row['Betrag (€)']}|{row.get('Zahlungsempfänger*in', '')}|{row.get('Verwendungszweck', '')}"
    return hashlib.sha256(raw.encode()).hexdigest()


def load_transactions() -> pd.DataFrame:
    rows = []
    for csv_path in sorted(CSV_DIR.glob("*.csv")):
        with open(csv_path, encoding="utf-8-sig") as f:
            lines = f.readlines()

        header_idx = None
        for i, line in enumerate(lines):
            if line.startswith('"Buchungsdatum"'):
                header_idx = i
                break

        if header_idx is None:
            warnings.warn(f"{csv_path.name}: Keine Spaltenüberschrift gefunden, überspringe")
            continue

        df = pd.read_csv(
            pd.io.common.StringIO("".join(lines[header_idx:])),
            delimiter=";",
            dtype=str,
        )

        if "Betrag (€)" not in df.columns:
            print(f"Warnung: {csv_path.name} enthält keine 'Betrag (€)'-Spalte – übersprungen")
            continue
        invalid = df["Betrag (€)"].apply(parse_amount).isna()
        if invalid.any():
            warnings.warn(f"{csv_path.name}: {invalid.sum()} Zeile(n) mit ungültigem Betrag übersprungen")
            df = df[~invalid]

        rows.append(df)

    if not rows:
        return pd.DataFrame()

    df = pd.concat(rows, ignore_index=True)
    n_before = len(df)

    df["_hash"] = df.apply(transaction_hash, axis=1)
    dups = df.duplicated(subset="_hash", keep="first")
    if dups.any():
        warnings.warn(f"{dups.sum()} Dubletten entfernt")
        df = df[~dups]
    df = df.drop(columns=["_hash"])

    df["Betrag"] = df["Betrag (€)"].apply(parse_amount)
    df["Datum"] = df["Buchungsdatum"].apply(parse_date)

    no_date = df["Datum"].isna()
    if no_date.any():
        warnings.warn(f"{no_date.sum()} Zeile(n) mit ungültigem Datum übersprungen")
        df = df[~no_date]

    return df


def assign_categories(df: pd.DataFrame, categories: dict[str, list[str]]) -> pd.Series:
    upper_cats = {cat: [k.upper() for k in kw] for cat, kw in categories.items()}
    def categorize(row: pd.Series) -> str:
        text = f"{str(row.get('Zahlungsempfänger*in', '')).upper()} {str(row.get('Verwendungszweck', '')).upper()}"
        for cat, keywords in upper_cats.items():
            for kw in keywords:
                if kw in text:
                    return cat
        return CATEGORY_OTHER

    return df.apply(categorize, axis=1)


def prepare_expenses(df: pd.DataFrame, categories: dict[str, list[str]]) -> pd.DataFrame:
    if "Betrag" not in df.columns:
        raise ValueError("prepare_expenses: Spalte 'Betrag' fehlt")
    if "Datum" not in df.columns:
        raise ValueError("prepare_expenses: Spalte 'Datum' fehlt")
    expenses = df[df["Betrag"] < 0].copy()
    expenses["Betrag"] = expenses["Betrag"].abs()
    expenses["Kategorie"] = assign_categories(expenses, categories)
    expenses["Monat"] = expenses["Datum"].dt.to_period("M").dt.to_timestamp()
    expenses["Jahr"] = expenses["Datum"].dt.year
    return expenses


def prepare_income(df: pd.DataFrame) -> pd.DataFrame:
    if not {"Datum", "Betrag"}.issubset(df.columns):
        raise ValueError("prepare_income: Spalten 'Datum' und 'Betrag' erforderlich")
    income = df[df["Betrag"] > 0].copy()
    income["Monat"] = income["Datum"].dt.to_period("M").dt.to_timestamp()
    income["Jahr"] = income["Datum"].dt.year
    income["Monat_Label"] = income["Monat"].dt.strftime("%b %Y")
    return income


def prepare_profit_loss(expenses: pd.DataFrame, income: pd.DataFrame) -> pd.DataFrame:
    if "Monat" not in expenses.columns:
        raise ValueError("prepare_profit_loss: Spalte 'Monat' in expenses fehlt")
    if "Monat" not in income.columns:
        raise ValueError("prepare_profit_loss: Spalte 'Monat' in income fehlt")
    monthly_expenses = expenses.groupby("Monat")["Betrag"].sum().rename("Ausgaben")
    monthly_income = income.groupby("Monat")["Betrag"].sum().rename("Einnahmen")
    merged = pd.merge(monthly_income, monthly_expenses, left_index=True, right_index=True, how="outer").fillna(0)
    merged["Differenz"] = merged["Einnahmen"] - merged["Ausgaben"]
    merged["Status"] = merged["Differenz"].apply(lambda x: "Gewinn" if x >= 0 else "Verlust")
    return merged.reset_index()


def print_table(report: dict[str, float], title: str = "") -> None:
    total = sum(report.values())
    if title:
        print(f"\n{title}")
        print("=" * len(title))
    print(f"{'Kategorie':<25} {'Betrag (€)':>12} {'Anteil':>8}")
    print("-" * 47)
    for cat, amount in report.items():
        pct = amount / total * 100
        print(f"{cat:<25} {amount:>10.2f} €  {pct:>6.1f} %")
    print("-" * 47)
    print(f"{'Gesamt':<25} {total:>10.2f} €  {'100.0 %':>8}")


def print_monthly_table(monthly: pd.DataFrame) -> None:
    pivot = monthly.pivot_table(
        index="Monat", columns="Kategorie", values="Betrag", aggfunc="sum", fill_value=0
    )
    pivot["Gesamt"] = pivot.sum(axis=1)
    pivot = pivot.sort_index()
    pivot.index = pivot.index.strftime("%b %Y")

    print("\nAusgaben pro Monat (€)")
    print("=" * 60)
    print(pivot.to_string(float_format=lambda x: f"{x:>8.2f}"))
    print("=" * 60)


def print_uncategorized(expenses: pd.DataFrame) -> None:
    sonstige = expenses[expenses["Kategorie"] == CATEGORY_OTHER]
    if sonstige.empty:
        return
    grouped = sonstige.groupby(["Zahlungsempfänger*in", "Verwendungszweck"], as_index=False).agg(
        Betrag=("Betrag", "sum"),
        Anzahl=("Betrag", "count"),
    ).sort_values("Betrag", ascending=False)

    print("\nNicht kategorisierte Ausgaben (Sonstige)")
    print("=" * 100)
    print(f"{'Empfänger':<40} {'Verwendungszweck':<40} {'Betrag':>8} {'#':>4}")
    print("-" * 100)
    for _, row in grouped.iterrows():
        empfaenger = str(row["Zahlungsempfänger*in"])[:39]
        zweck = str(row["Verwendungszweck"])[:39]
        print(f"{empfaenger:<40} {zweck:<40} {row['Betrag']:>7.2f} € {int(row['Anzahl']):>3}")
    print("=" * 100)
    print("Tipp: Namen oder Zweck oben als keyword in categories.toml eintragen.")


def print_all_tables(expenses: pd.DataFrame) -> None:
    report = expenses.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).to_dict()
    print_table(report, "Gesamtausgaben")
    print_monthly_table(expenses)
    for year in sorted(expenses["Jahr"].unique()):
        yearly = expenses[expenses["Jahr"] == year]
        yr = yearly.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).to_dict()
        print_table(yr, f"Ausgaben {year}")
    print_uncategorized(expenses)
