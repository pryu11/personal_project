"""Bay Area H-1B Sponsorship Dashboard -- Streamlit entry point.

Phase 3 skeleton: load the cleaned dataset, show a KPI row, and one
placeholder chart, just to prove the load -> render pipeline works end
to end. Sidebar filters and the rest of the dashboard sections come in
Phase 4.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "lca_bay_area_tech_clean.csv"


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, low_memory=False, parse_dates=["RECEIVED_DATE"])


st.set_page_config(page_title="Bay Area H-1B Sponsorship Dashboard", layout="wide")
st.title("Bay Area H-1B Sponsorship Dashboard")
st.caption(
    "Exploring FY2025 H-1B LCA filings for tech/data roles in the Bay Area, "
    "built from public DOL disclosure data."
)

df = load_data()
plausible_wages = df.loc[df["wage_is_plausible"], "ANNUAL_WAGE_FROM"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Filings", f"{len(df):,}")
col2.metric("Unique Employers", f"{df['EMPLOYER_NAME_CLEAN'].nunique():,}")
col3.metric("Median Annual Wage", f"${plausible_wages.median():,.0f}")
col4.metric(
    "Date Range",
    f"{df['RECEIVED_DATE'].min():%b %Y} - {df['RECEIVED_DATE'].max():%b %Y}",
)

st.subheader("Top Sponsoring Employers")
top_employers = df["EMPLOYER_NAME_CLEAN"].value_counts().head(15).reset_index()
top_employers.columns = ["Employer", "Filings"]
fig = px.bar(top_employers, x="Filings", y="Employer", orientation="h")
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, use_container_width=True)
