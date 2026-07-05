import argparse
import warnings
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from constants import (
    CSV_DIR,
    GRAPHS_DIR,
    CATEGORIES_FILE,
    COL_SENDER,
    BAR_WIDTH_YEARLY,
    COLOR_PROFIT,
    COLOR_LOSS,
    CATEGORY_OTHER,
)
from data import (
    load_config,
    load_categories,
    load_transactions,
    prepare_expenses,
    prepare_income,
    prepare_profit_loss,
    print_all_tables,
)


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
