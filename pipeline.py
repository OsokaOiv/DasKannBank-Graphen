from pathlib import Path
import tomllib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
from datetime import datetime
from matplotlib.patheffects import withStroke

CSV_DIR = Path(__file__).parent / "csv"
GRAPHS_DIR = Path(__file__).parent / "graphs"
CATEGORIES_FILE = Path(__file__).parent / "categories.toml"

plt.rcParams["font.family"] = "DejaVu Sans"


def load_categories(path: Path) -> dict[str, list[str]]:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return {name: [k.upper() for k in entry["keywords"]] for name, entry in data.items()}


def parse_amount(raw: str) -> float:
    raw = raw.strip().replace(".", "").replace(",", ".")
    return float(raw) if raw else 0.0


def parse_date(raw: str) -> datetime | None:
    try:
        return datetime.strptime(raw.strip(), "%d.%m.%y")
    except (ValueError, AttributeError):
        return None


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
            continue

        df = pd.read_csv(
            pd.io.common.StringIO("".join(lines[header_idx:])),
            delimiter=";",
            dtype=str,
        )
        rows.append(df)

    if not rows:
        return pd.DataFrame()

    df = pd.concat(rows, ignore_index=True)
    df["Betrag"] = df["Betrag (€)"].apply(parse_amount)
    df["Datum"] = df["Buchungsdatum"].apply(parse_date)
    return df


def assign_categories(df: pd.DataFrame, categories: dict[str, list[str]]) -> pd.Series:
    def categorize(row):
        text = f"{str(row.get('Zahlungsempfänger*in', '')).upper()} {str(row.get('Verwendungszweck', '')).upper()}"
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in text:
                    return cat
        return "Sonstige"

    return df.apply(categorize, axis=1)


def _plot_pie_chart(labels: list[str], values: list[float], title: str, filename: str):
    total = sum(values)
    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct="", startangle=90, textprops={"fontsize": 9},
    )
    ax.set_title(title, fontsize=14, fontweight="bold")
    legend_labels = [f"{l} — {v:.2f} € ({v/total*100:.1f}%)" for l, v in zip(labels, values)]
    ax.legend(wedges, legend_labels, title="Kategorien", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.tight_layout()
    out_path = GRAPHS_DIR / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


def plot_pie(report: dict[str, float]):
    _plot_pie_chart(
        labels=list(report.keys()),
        values=list(report.values()),
        title=f"Ausgaben nach Kategorie (Gesamt: {sum(report.values()):.2f} €)",
        filename="ausgaben_nach_kategorie.png",
    )


def plot_monthly_stacked(monthly: pd.DataFrame):

    pivot = monthly.pivot_table(
        index="Monat", columns="Kategorie", values="Betrag", aggfunc="sum", fill_value=0
    )
    pivot = pivot.sort_index()

    fig, ax = plt.subplots(figsize=(14, 7))
    categories_in_data = pivot.columns.tolist()
    bottom = None
    bar_width = 20

    for cat in categories_in_data:
        vals = pivot[cat].values
        if bottom is None:
            bars = ax.bar(pivot.index, vals, width=bar_width, label=cat)
            bottom = vals.copy()
        else:
            bars = ax.bar(pivot.index, vals, width=bar_width, bottom=bottom, label=cat)
            bottom = bottom + vals

        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{v:.2f}",
                    ha="center", va="center",
                    fontsize=8, fontweight="bold", color="white",
                    path_effects=[withStroke(linewidth=2, foreground="black")],
                )

    ax.set_title("Ausgaben pro Monat nach Kategorie", fontsize=14, fontweight="bold")
    ax.set_ylabel("Betrag (€)")
    ax.set_xlabel("Monat")
    ax.legend(title="Kategorie", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()

    out_path = GRAPHS_DIR / "ausgaben_pro_monat.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


def plot_yearly_pies(expenses: pd.DataFrame):
    for year in sorted(expenses["Jahr"].unique()):
        yearly = expenses[expenses["Jahr"] == year]
        report = yearly.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False)
        if report.empty:
            continue
        _plot_pie_chart(
            labels=report.index.tolist(),
            values=report.values.tolist(),
            title=f"Ausgaben {year} (Gesamt: {report.sum():.2f} €)",
            filename=f"ausgaben_{year}.png",
        )


def print_table(report: dict[str, float], title: str = ""):
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


def print_monthly_table(monthly: pd.DataFrame):
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


def prepare_expenses(df: pd.DataFrame, categories: dict) -> pd.DataFrame:
    expenses = df[df["Betrag"] < 0].copy()
    expenses["Betrag"] = expenses["Betrag"].abs()
    expenses = expenses.dropna(subset=["Datum"])
    expenses["Kategorie"] = assign_categories(expenses, categories)
    expenses["Monat"] = expenses["Datum"].dt.to_period("M").dt.to_timestamp()
    expenses["Jahr"] = expenses["Datum"].dt.year
    return expenses


def print_uncategorized(expenses: pd.DataFrame) -> None:
    sonstige = expenses[expenses["Kategorie"] == "Sonstige"]
    if sonstige.empty:
        return
    grouped = sonstige.groupby("Zahlungsempfänger*in").agg(
        Betrag=("Betrag", "sum"),
        Anzahl=("Betrag", "count"),
    ).sort_values("Betrag", ascending=False)

    print("\nNicht kategorisierte Ausgaben (Sonstige)")
    print("=" * 60)
    print(f"{'Empfänger':<45} {'Betrag':>8} {'#':>4}")
    print("-" * 60)
    for name, row in grouped.iterrows():
        print(f"{str(name).upper()[:44]:<45} {row['Betrag']:>7.2f} € {int(row['Anzahl']):>3}")
    print("=" * 60)
    print("Tipp: Namen oben als keyword in categories.toml eintragen.")


def print_all_tables(expenses: pd.DataFrame):
    report = expenses.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).to_dict()
    print_table(report, "Gesamtausgaben")
    print_monthly_table(expenses)
    for year in sorted(expenses["Jahr"].unique()):
        yearly = expenses[expenses["Jahr"] == year]
        yr = yearly.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).to_dict()
        print_table(yr, f"Ausgaben {year}")
    print_uncategorized(expenses)


def plot_all_charts(expenses: pd.DataFrame):
    report = expenses.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).to_dict()
    plot_pie(report)
    plot_monthly_stacked(expenses)
    plot_yearly_pies(expenses)


def main():
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    categories = load_categories(CATEGORIES_FILE)
    df = load_transactions()

    if df.empty:
        print("Keine CSV-Dateien im Ordner 'csv/' gefunden.")
        return

    expenses = prepare_expenses(df, categories)
    print_all_tables(expenses)
    plot_all_charts(expenses)


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
    main()
