import argparse
import hashlib
from pathlib import Path
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # Python < 3.11
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
from datetime import datetime

CSV_DIR = Path(__file__).parent / "csv"
GRAPHS_DIR = Path(__file__).parent / "graphs"
CATEGORIES_FILE = Path(__file__).parent / "categories.toml"
CONFIG_FILE = Path(__file__).parent / "pipeline.toml"

COL_SENDER = "Zahlungspflichtige*r"
BAR_WIDTH_YEARLY = 0.6
COLOR_PROFIT = "#2ecc71"
COLOR_LOSS = "#e74c3c"
CATEGORY_OTHER = "Sonstige"


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


def _plot_pie_chart(labels: list[str], values: list[float], title: str, filename: str, cfg: dict) -> None:
    pc = cfg["charts"]["pie"]
    total = sum(values)
    fig, ax = plt.subplots(figsize=(pc["figure_width"], pc["figure_height"]))
    wedges, _, _ = ax.pie(
        values, labels=None, autopct="", startangle=90, textprops={"fontsize": 9},
    )
    ax.set_title(title, fontsize=14, fontweight="bold")
    legend_labels = [f"{l} — {v:.2f} € ({v/total*100:.1f}%)" for l, v in zip(labels, values)]
    ax.legend(wedges, legend_labels, title="Kategorien", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.tight_layout()
    out_path = GRAPHS_DIR / filename
    fig.savefig(out_path, dpi=cfg["display"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


def plot_pie(report: dict[str, float], cfg: dict) -> None:
    _plot_pie_chart(
        labels=list(report.keys()),
        values=list(report.values()),
        title=f"Ausgaben nach Kategorie (Gesamt: {sum(report.values()):.2f} €)",
        filename="ausgaben_nach_kategorie.png",
        cfg=cfg,
    )


def plot_monthly_stacked(monthly: pd.DataFrame, cfg: dict) -> None:
    bc = cfg["charts"]["monthly_bar"]
    pivot = monthly.pivot_table(
        index="Monat", columns="Kategorie", values="Betrag", aggfunc="sum", fill_value=0
    )
    pivot = pivot.sort_index()

    fig, ax = plt.subplots(figsize=(bc["figure_width"], bc["figure_height"]))
    categories_in_data = pivot.columns.tolist()
    bottom = None

    for cat in categories_in_data:
        vals = pivot[cat].values
        if bottom is None:
            ax.bar(pivot.index, vals, width=bc["bar_width_days"], label=cat)
            bottom = vals.copy()
        else:
            ax.bar(pivot.index, vals, width=bc["bar_width_days"], bottom=bottom, label=cat)
            bottom = bottom + vals

    ax.set_title("Ausgaben pro Monat nach Kategorie", fontsize=14, fontweight="bold")
    ax.set_ylabel("Betrag (€)")
    ax.set_xlabel("Monat")
    ax.legend(title="Kategorie", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()

    out_path = GRAPHS_DIR / "ausgaben_gestapelt_pro_monat.png"
    fig.savefig(out_path, dpi=cfg["display"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


def plot_monthly_lines(monthly: pd.DataFrame, cfg: dict) -> None:
    lc = cfg["charts"]["monthly_line"]
    pivot = monthly.pivot_table(
        index="Monat", columns="Kategorie", values="Betrag", aggfunc="sum", fill_value=0
    )
    pivot = pivot.sort_index()

    fig, ax = plt.subplots(figsize=(lc["figure_width"], lc["figure_height"]))
    categories_in_data = pivot.columns.tolist()

    for cat in categories_in_data:
        vals = pivot[cat].values
        ax.plot(pivot.index, vals, marker="o", label=cat, linewidth=2)
        for x, v in zip(pivot.index, vals):
            if v > 0:
                ax.text(x, v, f"{v:.2f}", fontsize=8, ha="center", va="bottom")

    ax.set_title("Ausgaben pro Monat nach Kategorie", fontsize=14, fontweight="bold")
    ax.set_ylabel("Betrag (€)")
    ax.set_xlabel("Monat")
    ax.legend(title="Kategorie", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.yaxis.set_major_formatter("{x:.0f} €")
    plt.xticks(rotation=45, ha="right")
    ax.set_ylim(bottom=0)
    fig.tight_layout()

    out_path = GRAPHS_DIR / "ausgaben_linien_pro_monat.png"
    fig.savefig(out_path, dpi=cfg["display"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


def plot_yearly_pies(expenses: pd.DataFrame, cfg: dict) -> None:
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
            cfg=cfg,
        )


def plot_monthly_pies(expenses: pd.DataFrame, cfg: dict) -> None:
    for month in sorted(expenses["Monat"].unique()):
        monthly = expenses[expenses["Monat"] == month]
        report = monthly.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False)
        if report.empty:
            continue
        _plot_pie_chart(
            labels=report.index.tolist(),
            values=report.values.tolist(),
            title=f"Ausgaben {month.strftime('%b %Y')} (Gesamt: {report.sum():.2f} €)",
            filename=f"ausgaben_{month.strftime('%Y-%m')}.png",
            cfg=cfg,
        )


def plot_income_monthly(income: pd.DataFrame, cfg: dict) -> None:
    if income.empty:
        return
    bc = cfg["charts"]["monthly_bar"]
    pivot = income.pivot_table(
        index="Monat", columns=COL_SENDER, values="Betrag", aggfunc="sum", fill_value=0
    ).sort_index()
    fig, ax = plt.subplots(figsize=(bc["figure_width"], bc["figure_height"]))
    bottom = None
    for sender in pivot.columns:
        vals = pivot[sender].values
        if bottom is None:
            ax.bar(pivot.index, vals, width=bc["bar_width_days"], label=sender)
            bottom = vals.copy()
        else:
            ax.bar(pivot.index, vals, width=bc["bar_width_days"], bottom=bottom, label=sender)
            bottom = bottom + vals
    ax.set_title("Einnahmen pro Monat", fontsize=14, fontweight="bold")
    ax.set_ylabel("Betrag (€)")
    ax.set_xlabel("Monat")
    ax.legend(title="Sender", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    out_path = GRAPHS_DIR / "einnahmen_pro_monat.png"
    fig.savefig(out_path, dpi=cfg["display"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


def plot_income_yearly(income: pd.DataFrame, cfg: dict) -> None:
    if income.empty:
        return
    bc = cfg["charts"]["monthly_bar"]
    pivot = income.pivot_table(
        index="Jahr", columns=COL_SENDER, values="Betrag", aggfunc="sum", fill_value=0
    ).sort_index()
    fig, ax = plt.subplots(figsize=(bc["figure_width"], bc["figure_height"]))
    bottom = None
    for sender in pivot.columns:
        vals = pivot[sender].values
        if bottom is None:
            ax.bar(pivot.index, vals, width=BAR_WIDTH_YEARLY, label=sender)
            bottom = vals.copy()
        else:
            ax.bar(pivot.index, vals, width=BAR_WIDTH_YEARLY, bottom=bottom, label=sender)
            bottom = bottom + vals
    ax.set_title("Einnahmen pro Jahr", fontsize=14, fontweight="bold")
    ax.set_ylabel("Betrag (€)")
    ax.set_xlabel("Jahr")
    ax.legend(title="Sender", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    out_path = GRAPHS_DIR / "einnahmen_pro_jahr.png"
    fig.savefig(out_path, dpi=cfg["display"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


def plot_income_pie(income: pd.DataFrame, cfg: dict) -> None:
    if income.empty:
        return
    pc = cfg["charts"]["pie"]
    report = income.groupby(COL_SENDER)["Betrag"].sum().sort_values(ascending=False)
    total = report.sum()
    fig, ax = plt.subplots(figsize=(pc["figure_width"], pc["figure_height"]))
    wedges, texts, autotexts = ax.pie(
        report.values,
        labels=report.index,
        autopct="%1.1f%%",
        startangle=140,
        textprops={"fontsize": pc.get("font_size", 10)},
    )
    ax.set_title(f"Einnahmen nach Sender (Gesamt: {total:.2f} €)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    out_path = GRAPHS_DIR / "einnahmen_kreis.png"
    fig.savefig(out_path, dpi=cfg["display"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


def plot_profit_loss(profit_loss: pd.DataFrame, cfg: dict) -> None:
    if profit_loss.empty:
        return
    bc = cfg["charts"]["monthly_bar"]
    fig, ax = plt.subplots(figsize=(bc["figure_width"], bc["figure_height"]))
    colors = [COLOR_PROFIT if x >= 0 else COLOR_LOSS for x in profit_loss["Differenz"]]
    ax.bar(profit_loss["Monat"], profit_loss["Differenz"], color=colors)
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=1)
    ax.set_title("Gewinn/Verlust pro Monat", fontsize=14, fontweight="bold")
    ax.set_ylabel("Differenz (€)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    out_path = GRAPHS_DIR / "gewinne_pro_monat.png"
    fig.savefig(out_path, dpi=cfg["display"]["dpi"], bbox_inches="tight")
    plt.close(fig)
    print(f"Diagramm gespeichert: {out_path}")


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


def plot_all_charts(expenses: pd.DataFrame, income: pd.DataFrame, profit_loss: pd.DataFrame, charts: set[str], cfg: dict) -> None:
    if "total" in charts:
        report = expenses.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).to_dict()
        plot_pie(report, cfg)
    if "monthly" in charts:
        plot_monthly_lines(expenses, cfg)
        plot_monthly_stacked(expenses, cfg)
    if "monthly-pies" in charts:
        plot_monthly_pies(expenses, cfg)
    if "yearly" in charts:
        plot_yearly_pies(expenses, cfg)
    if "income" in charts:
        plot_income_monthly(income, cfg)
        plot_income_yearly(income, cfg)
        plot_income_pie(income, cfg)
    if "income-pie" in charts:
        plot_income_pie(income, cfg)
    if "profit" in charts:
        plot_profit_loss(profit_loss, cfg)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ausgaben-Pipeline für DKB-Kontoauszüge")
    parser.add_argument(
        "charts", nargs="?", choices=["all", "total", "yearly", "monthly", "monthly-pies", "income", "income-pie", "profit"], default="all",
        help="Welche Diagramme erstellt werden sollen (default: all)",
    )
    args = parser.parse_args()

    chart_map = {
        "all": {"total", "yearly", "monthly", "monthly-pies", "income", "profit"},
        "total": {"total"},
        "yearly": {"yearly"},
        "monthly": {"monthly"},
        "monthly-pies": {"monthly-pies"},
        "income": {"income"},
        "income-pie": {"income-pie"},
        "profit": {"profit"},
    }

    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

    cfg = load_config()
    plt.rcParams["font.family"] = cfg["display"]["font_family"]

    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    categories = load_categories(CATEGORIES_FILE)
    df = load_transactions()

    if df.empty:
        print("Keine CSV-Dateien im Ordner 'csv/' gefunden.")
        return

    expenses = prepare_expenses(df, categories)
    income_data = prepare_income(df)
    profit_loss_data = prepare_profit_loss(expenses, income_data)
    print_all_tables(expenses)
    plot_all_charts(expenses, income_data, profit_loss_data, chart_map[args.charts], cfg)


if __name__ == "__main__":
    main()
