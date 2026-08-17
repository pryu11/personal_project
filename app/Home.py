"""Bay Area H-1B Sponsorship Dashboard -- Streamlit entry point.

Phase 4: sidebar filters (county, role, employer search, case status)
drive every section below from one shared filtered dataframe, per the
dataviz skill's guidance every chart here uses a single flat hue --
position (bar length, box placement, x-axis) already carries category
identity, so a multi-color categorical palette would just be redundant
ink. Blue (#2a78d6) is the skill's default sequential/single-series hue,
reused everywhere for a consistent look.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "lca_bay_area_tech_clean.csv"

CHART_BLUE = "#2a78d6"
GRID_COLOR = "#e1e0d9"
AXIS_COLOR = "#c3c2b7"
MUTED_TEXT = "#898781"


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(
        DATA_PATH, low_memory=False, parse_dates=["RECEIVED_DATE", "DECISION_DATE"]
    )


def style_chart(fig):
    """Apply the shared, recessive chart chrome (hairline gridlines, muted axes)."""
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color=MUTED_TEXT,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, linecolor=AXIS_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, linecolor=AXIS_COLOR, zeroline=False)
    return fig


st.set_page_config(page_title="Bay Area H-1B Sponsorship Dashboard", layout="wide")
st.title("Bay Area H-1B Sponsorship Dashboard")
st.caption(
    "Exploring FY2025 H-1B LCA filings for tech/data roles in the Bay Area, "
    "built from public DOL disclosure data."
)

df = load_data()

# --- Sidebar filters -- every section below reads from `filtered`, so the
# numbers everywhere on the page always agree with each other. ---
st.sidebar.header("Filters")

counties = sorted(df["WORKSITE_COUNTY_INFERRED"].dropna().unique())
selected_counties = st.sidebar.multiselect("County", counties, default=counties)

roles = sorted(df["role_category"].dropna().unique())
selected_roles = st.sidebar.multiselect("Role category", roles, default=roles)

statuses = sorted(df["CASE_STATUS"].dropna().unique())
selected_statuses = st.sidebar.multiselect("Case status", statuses, default=statuses)

company_search = st.sidebar.text_input("Employer name contains")

filtered = df[
    df["WORKSITE_COUNTY_INFERRED"].isin(selected_counties)
    & df["role_category"].isin(selected_roles)
    & df["CASE_STATUS"].isin(selected_statuses)
]
if company_search:
    filtered = filtered[
        filtered["EMPLOYER_NAME_CLEAN"].str.contains(
            company_search, case=False, na=False, regex=False
        )
    ]

if filtered.empty:
    st.warning("No filings match the current filters.")
    st.stop()

plausible_wages = filtered.loc[filtered["wage_is_plausible"], "ANNUAL_WAGE_FROM"]

# --- KPI row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Filings", f"{len(filtered):,}")
col2.metric("Unique Employers", f"{filtered['EMPLOYER_NAME_CLEAN'].nunique():,}")
col3.metric("Median Annual Wage", f"${plausible_wages.median():,.0f}")
col4.metric(
    "Decision Date Range",
    f"{filtered['DECISION_DATE'].min():%b %Y} - {filtered['DECISION_DATE'].max():%b %Y}",
)

# --- Top sponsoring employers ---
st.subheader("Top Sponsoring Employers")
top_employers = filtered["EMPLOYER_NAME_CLEAN"].value_counts().head(15).reset_index()
top_employers.columns = ["Employer", "Filings"]
fig = px.bar(top_employers, x="Filings", y="Employer", orientation="h")
fig.update_traces(marker_color=CHART_BLUE)
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(style_chart(fig), use_container_width=True)

# --- Salary distribution by role category ---
st.subheader("Salary Distribution by Role")
st.caption("Excludes filings flagged as implausible wages (likely unit-entry errors).")
wage_df = filtered[filtered["wage_is_plausible"]]
role_order = (
    wage_df.groupby("role_category")["ANNUAL_WAGE_FROM"].median().sort_values(ascending=False).index
)
fig = px.box(wage_df, x="role_category", y="ANNUAL_WAGE_FROM", category_orders={"role_category": list(role_order)})
fig.update_traces(marker_color=CHART_BLUE, line_color=CHART_BLUE)
fig.update_layout(xaxis_title=None, yaxis_title="Annual Wage ($)", xaxis_tickangle=-30)
st.plotly_chart(style_chart(fig), use_container_width=True)

# --- Monthly filing volume ---
st.subheader("Monthly Filing Volume")
st.caption(
    "By decision date. Only FY2025 Q4 (Jul-Sep 2025) is loaded so far -- "
    "this chart will extend automatically as more fiscal quarters/years are added."
)
monthly = (
    filtered.assign(month=filtered["DECISION_DATE"].dt.to_period("M").dt.to_timestamp())
    .groupby("month")
    .size()
    .reset_index(name="Filings")
)
fig = px.line(monthly, x="month", y="Filings", markers=True)
fig.update_traces(line_color=CHART_BLUE, line_width=2, marker=dict(color=CHART_BLUE, size=8))
fig.update_layout(xaxis_title=None)
st.plotly_chart(style_chart(fig), use_container_width=True)

# --- Geographic breakdown ---
st.subheader("Filings by County")
county_counts = (
    filtered["WORKSITE_COUNTY_INFERRED"].value_counts().reset_index()
)
county_counts.columns = ["County", "Filings"]
fig = px.bar(county_counts, x="Filings", y="County", orientation="h")
fig.update_traces(marker_color=CHART_BLUE)
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(style_chart(fig), use_container_width=True)
