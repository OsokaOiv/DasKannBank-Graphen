from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pipeline import (
    load_categories,
    load_transactions,
    prepare_expenses,
    prepare_income,
    prepare_profit_loss,
    CATEGORIES_FILE,
    CATEGORY_OTHER,
    COLOR_PROFIT,
    COLOR_LOSS,
)

FONT_FAMILY = "DejaVu Sans"
FMT_EUR = ":.2f €"
MONTH_LABEL_FMT = "%b %Y"
AXIS_MONAT = "Monat"
AXIS_BETRAG = "Betrag (€)"
FMT_EUR_THOUSANDS = ":,.2f €"
FMT_PCT = ":.1f%"


def _filter_by_months(df: pd.DataFrame, selected_months: list[str]) -> pd.DataFrame:
    if selected_months and "Monat_Label" in df.columns:
        return df[df["Monat_Label"].isin(selected_months)]
    return df


def filter_expenses(
    expenses: pd.DataFrame,
    selected_months: list[str] | None = None,
    selected_categories: list[str] | None = None,
) -> pd.DataFrame:
    if selected_months is None:
        selected_months = []
    if selected_categories is None:
        selected_categories = []
    filtered = _filter_by_months(expenses, selected_months)
    if selected_categories and "Kategorie" in filtered.columns:
        filtered = filtered[filtered["Kategorie"].isin(selected_categories)]
    return filtered


def filter_income(
    income: pd.DataFrame,
    selected_months: list[str] | None = None,
) -> pd.DataFrame:
    if selected_months is None:
        selected_months = []
    return _filter_by_months(income, selected_months)


COL_SENDER = "Zahlungspflichtige*r"
AXIS_JAHR = "Jahr"


def render_income_monthly_bar(income_filtered: pd.DataFrame) -> None:
    pivot = income_filtered.pivot_table(
        index="Monat", columns=COL_SENDER, values="Betrag", aggfunc="sum", fill_value=0
    ).sort_index()
    fig = go.Figure()
    for sender in pivot.columns:
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=pivot[sender],
            name=sender,
            hovertemplate=f"{sender}<br>%{{x|%b %Y}}<br>%{{y:.2f}} €<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        title="Einnahmen pro Monat",
        xaxis_title=AXIS_MONAT,
        yaxis_title=AXIS_BETRAG,
        legend_title="Sender",
        font=dict(family=FONT_FAMILY),
        hovermode="x unified",
        xaxis=dict(dtick="M1", tickformat="%b %Y"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_income_monthly_line(income_filtered: pd.DataFrame) -> None:
    pivot = income_filtered.pivot_table(
        index="Monat", columns=COL_SENDER, values="Betrag", aggfunc="sum", fill_value=0
    ).sort_index()
    fig = go.Figure()
    for sender in pivot.columns:
        fig.add_trace(go.Scatter(
            x=pivot.index,
            y=pivot[sender],
            mode="lines+markers+text",
            name=sender,
            text=[f"{v:.2f} €" if v > 0 else "" for v in pivot[sender]],
            textposition="top center",
            textfont=dict(size=9),
            hovertemplate=f"{sender}<br>%{{x|%b %Y}}<br>%{{y:.2f}} €<extra></extra>",
        ))
    fig.update_layout(
        title="Einnahmen pro Monat (Verlauf)",
        xaxis_title=AXIS_MONAT,
        yaxis_title=AXIS_BETRAG,
        legend_title="Sender",
        font=dict(family=FONT_FAMILY),
        hovermode="x unified",
        xaxis=dict(dtick="M1", tickformat="%b %Y"),
        yaxis=dict(rangemode="tozero"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_income_yearly(income_filtered: pd.DataFrame) -> None:
    pivot = income_filtered.pivot_table(
        index="Jahr", columns=COL_SENDER, values="Betrag", aggfunc="sum", fill_value=0
    ).sort_index()
    fig = go.Figure()
    for sender in pivot.columns:
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=pivot[sender],
            name=sender,
            hovertemplate=f"{sender}<br>%{{x}}<br>%{{y:.2f}} €<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        title="Einnahmen pro Jahr",
        xaxis_title=AXIS_JAHR,
        yaxis_title=AXIS_BETRAG,
        legend_title="Sender",
        font=dict(family=FONT_FAMILY),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_profit_loss(profit_loss: pd.DataFrame) -> None:
    color_map = {"Gewinn": COLOR_PROFIT, "Verlust": COLOR_LOSS}
    fig = px.bar(
        profit_loss,
        x="Monat",
        y="Differenz",
        color="Status",
        color_discrete_map=color_map,
        title="Gewinn/Verlust pro Monat",
        hover_data={"Einnahmen": FMT_EUR, "Ausgaben": FMT_EUR, "Differenz": FMT_EUR},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        xaxis_title=AXIS_MONAT,
        yaxis_title=AXIS_BETRAG,
        font=dict(family=FONT_FAMILY),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    categories = load_categories(CATEGORIES_FILE)
    df = load_transactions()
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), categories
    expenses = prepare_expenses(df, categories)
    expenses["Monat_Label"] = expenses["Monat"].dt.strftime(MONTH_LABEL_FMT)
    income = prepare_income(df)
    return expenses, income, categories


def render_sidebar(expenses: pd.DataFrame) -> tuple:
    st.sidebar.title("Filter")
    if expenses.empty or "Monat_Label" not in expenses.columns:
        return "Kreis (Gesamt)", [], []
    months = sorted(expenses["Monat_Label"].unique(), key=lambda x: datetime.strptime(x, MONTH_LABEL_FMT))
    all_months = st.sidebar.checkbox("Alle Monate", value=True)
    if all_months:
        selected_months = months
    else:
        selected_months = st.sidebar.multiselect("Monate", months, default=months)

    categories = sorted(expenses["Kategorie"].unique()) if not expenses.empty else []
    all_cats = st.sidebar.checkbox("Alle Kategorien", value=True)
    if all_cats:
        selected_categories = categories
    else:
        selected_categories = st.sidebar.multiselect("Kategorien", categories, default=categories)

    chart_type = st.sidebar.selectbox(
        "Diagramm",
        [
            "Kreis (Gesamt)",
            "Kreis (Jahr)",
            "Kreis (Monat)",
            "Linien (Monat)",
            "Gestapelte Balken (Monat)",
            "Einnahmen (Balken)",
            "Einnahmen (Linie)",
            "Einnahmen (Jahr)",
            "Gewinn/Verlust (Monat)",
        ],
    )

    return chart_type, selected_months, selected_categories


def render_summary(expenses_filtered: pd.DataFrame) -> None:
    total = expenses_filtered["Betrag"].sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ausgaben gesamt", f"{total:.2f} €")
    col2.metric("Anzahl Transaktionen", len(expenses_filtered))
    col3.metric("Kategorien", expenses_filtered["Kategorie"].nunique())
    col4.metric("Monate", expenses_filtered["Monat_Label"].nunique())


def render_total_pie(expenses_filtered: pd.DataFrame) -> None:
    report = expenses_filtered.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).reset_index()
    total = report["Betrag"].sum()
    report["Anteil"] = report["Betrag"] / total * 100
    report["Label"] = report.apply(
        lambda r: f"{r['Kategorie']}<br>{r['Betrag']:.2f} € ({r['Anteil']:.1f}%)", axis=1
    )
    fig = px.pie(
        report,
        values="Betrag",
        names="Kategorie",
        title=f"Ausgaben nach Kategorie (Gesamt: {total:.2f} €)",
        hover_data={"Betrag": FMT_EUR_THOUSANDS, "Anteil": FMT_PCT},
    )
    fig.update_traces(textinfo="label+percent", textposition="outside")
    fig.update_layout(
        legend_title="Kategorie",
        font=dict(family=FONT_FAMILY),
        hoverlabel=dict(font_size=12),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_monthly_line(expenses_filtered: pd.DataFrame) -> None:
    pivot = expenses_filtered.pivot_table(
        index="Monat", columns="Kategorie", values="Betrag", aggfunc="sum", fill_value=0
    ).sort_index()
    fig = go.Figure()
    for cat in pivot.columns:
        fig.add_trace(go.Scatter(
            x=pivot.index,
            y=pivot[cat],
            mode="lines+markers+text",
            name=cat,
            text=[f"{v:.2f} €" if v > 0 else "" for v in pivot[cat]],
            textposition="top center",
            textfont=dict(size=9),
            hovertemplate=f"{cat}<br>%{{x|%b %Y}}<br>%{{y:.2f}} €<extra></extra>",
        ))
    fig.update_layout(
        title="Ausgaben pro Monat nach Kategorie",
        xaxis_title=AXIS_MONAT,
        yaxis_title=AXIS_BETRAG,
        legend_title="Kategorie",
        font=dict(family=FONT_FAMILY),
        hovermode="x unified",
        xaxis=dict(dtick="M1", tickformat="%b %Y"),
        yaxis=dict(rangemode="tozero"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_monthly_stacked(expenses_filtered: pd.DataFrame) -> None:
    pivot = expenses_filtered.pivot_table(
        index="Monat", columns="Kategorie", values="Betrag", aggfunc="sum", fill_value=0
    ).sort_index()
    fig = go.Figure()
    categories_in_data = pivot.columns.tolist()
    for cat in categories_in_data:
        fig.add_trace(go.Bar(
            x=pivot.index,
            y=pivot[cat],
            name=cat,
            hovertemplate=f"{cat}<br>%{{x|%b %Y}}<br>%{{y:.2f}} €<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        title="Ausgaben pro Monat nach Kategorie",
        xaxis_title=AXIS_MONAT,
        yaxis_title=AXIS_BETRAG,
        legend_title="Kategorie",
        font=dict(family=FONT_FAMILY),
        hovermode="x unified",
        xaxis=dict(dtick="M1", tickformat="%b %Y"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_yearly_pie(expenses_filtered: pd.DataFrame) -> None:
    years = sorted(expenses_filtered["Jahr"].unique())
    if not years:
        st.info("Keine Daten verfügbar.")
        return
    selected = st.selectbox("Jahr wählen", years, key="year_pie")
    yearly = expenses_filtered[expenses_filtered["Jahr"] == selected]
    if yearly.empty:
        st.info(f"Keine Daten für {selected}")
        return
    report = yearly.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).reset_index()
    total = report["Betrag"].sum()
    fig = px.pie(
        report,
        values="Betrag",
        names="Kategorie",
        title=f"Ausgaben {selected} (Gesamt: {total:.2f} €)",
        hover_data={"Betrag": FMT_EUR_THOUSANDS},
    )
    fig.update_traces(textinfo="label+percent", textposition="outside")
    fig.update_layout(legend_title="Kategorie", font=dict(family=FONT_FAMILY))
    st.plotly_chart(fig, use_container_width=True)


def render_monthly_pie(expenses_filtered: pd.DataFrame) -> None:
    months = sorted(
        expenses_filtered["Monat_Label"].unique(),
        key=lambda x: datetime.strptime(x, MONTH_LABEL_FMT),
    )
    if not months:
        st.info("Keine Daten verfügbar.")
        return
    selected = st.selectbox("Monat wählen", months, key="month_pie")
    monthly = expenses_filtered[expenses_filtered["Monat_Label"] == selected]
    if monthly.empty:
        st.info(f"Keine Daten für {selected}")
        return
    report = monthly.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).reset_index()
    total = report["Betrag"].sum()
    fig = px.pie(
        report,
        values="Betrag",
        names="Kategorie",
        title=f"Ausgaben {selected} (Gesamt: {total:.2f} €)",
        hover_data={"Betrag": FMT_EUR_THOUSANDS},
    )
    fig.update_traces(textinfo="label+percent", textposition="outside")
    fig.update_layout(legend_title="Kategorie", font=dict(family=FONT_FAMILY))
    st.plotly_chart(fig, use_container_width=True)


def render_tables(expenses_filtered: pd.DataFrame) -> None:
    with st.expander("Tabellarische Übersicht", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Nach Kategorie", "Monatlich", "Transaktionen"])
        with tab1:
            report = expenses_filtered.groupby("Kategorie")["Betrag"].sum().sort_values(ascending=False).reset_index()
            report.columns = ["Kategorie", "Betrag (€)"]
            report["Betrag (€)"] = report["Betrag (€)"].apply(lambda x: f"{x:.2f}")
            st.dataframe(report, use_container_width=True, hide_index=True)
        with tab2:
            pivot = expenses_filtered.pivot_table(
                index="Monat", columns="Kategorie", values="Betrag", aggfunc="sum", fill_value=0
            ).sort_index()
            pivot["Gesamt"] = pivot.sum(axis=1)
            pivot.index = pivot.index.strftime(MONTH_LABEL_FMT)
            st.dataframe(pivot.style.format("{:.2f}"), use_container_width=True)
        with tab3:
            cols = ["Datum", "Zahlungsempfänger*in", "Verwendungszweck", "Betrag", "Kategorie"]
            raw = expenses_filtered[cols].sort_values("Datum").reset_index(drop=True)
            raw["Betrag"] = raw["Betrag"].apply(lambda x: f"{x:.2f} €")
            raw["Datum"] = raw["Datum"].dt.strftime("%d.%m.%Y")
            st.dataframe(raw, use_container_width=True, hide_index=True)


def render_uncategorized(expenses_filtered: pd.DataFrame) -> None:
    sonstige = expenses_filtered[expenses_filtered["Kategorie"] == CATEGORY_OTHER]
    if sonstige.empty:
        st.success("Alle Ausgaben sind kategorisiert! 🎉")
        return
    with st.expander(f"Nicht kategorisierte Ausgaben ({len(sonstige)} Transaktionen)", expanded=False):
        grouped = sonstige.groupby(["Zahlungsempfänger*in", "Verwendungszweck"], as_index=False).agg(
            Betrag=("Betrag", "sum"),
            Anzahl=("Betrag", "count"),
        ).sort_values("Betrag", ascending=False)
        grouped.columns = ["Empfänger", "Verwendungszweck", "Betrag (€)", "Anzahl"]
        grouped["Betrag (€)"] = grouped["Betrag (€)"].apply(lambda x: f"{x:.2f}")
        st.dataframe(grouped, use_container_width=True, hide_index=True)
        st.info("Tipp: Empfänger oder Verwendungszweck als keyword in categories.toml eintragen.")


def main() -> None:
    st.set_page_config(page_title="DKB Ausgaben-Dashboard", layout="wide")
    st.title("📊 DKB Ausgaben-Dashboard")

    expenses, income, _ = load_data()

    if expenses.empty:
        st.warning("Keine CSV-Dateien im Ordner 'csv/' gefunden. Lege dort DKB-Exporte ab.")
        return

    st.sidebar.header("Steuerung")
    chart_type, selected_months, selected_categories = render_sidebar(expenses)

    filtered_expenses = filter_expenses(expenses, selected_months, selected_categories)
    filtered_income = filter_income(income, selected_months)
    profit_loss = prepare_profit_loss(filtered_expenses, filtered_income)

    if filtered_expenses.empty:
        st.info("Keine Daten für die ausgewählten Filter.")
        return

    render_summary(filtered_expenses)

    st.divider()

    chart_map = {
        "Kreis (Gesamt)": lambda: render_total_pie(filtered_expenses),
        "Kreis (Jahr)": lambda: render_yearly_pie(filtered_expenses),
        "Kreis (Monat)": lambda: render_monthly_pie(filtered_expenses),
        "Linien (Monat)": lambda: render_monthly_line(filtered_expenses),
        "Gestapelte Balken (Monat)": lambda: render_monthly_stacked(filtered_expenses),
        "Einnahmen (Balken)": lambda: render_income_monthly_bar(filtered_income),
        "Einnahmen (Linie)": lambda: render_income_monthly_line(filtered_income),
        "Einnahmen (Jahr)": lambda: render_income_yearly(filtered_income),
        "Gewinn/Verlust (Monat)": lambda: render_profit_loss(profit_loss),
    }
    chart_map[chart_type]()

    render_tables(filtered_expenses)
    render_uncategorized(filtered_expenses)


if __name__ == "__main__":
    main()
