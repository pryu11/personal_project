"""California H-1B Sponsorship Dashboard -- Streamlit entry point.

Phase 4: sidebar filters (county, role, employer search, case status)
drive every section below from one shared filtered dataframe. Every chart
uses a single flat accent hue -- position (bar length, box placement,
x-axis) already carries category identity, so a multi-color categorical
palette would just be redundant ink. Palette is capped at 3 base colors
(ivory / terracotta / gunmetal); gridlines and muted text are opacity
tints of gunmetal rather than new hues, so nothing beyond those 3 is
ever introduced. See .streamlit/config.toml for the matching app theme.
"""

from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "lca_ca_tech_clean.csv"

IVORY = "#f6f7eb"
TERRACOTTA = "#e94f37"
GUNMETAL = "#393e41"

CHART_ACCENT = TERRACOTTA
GRID_COLOR = "rgba(57, 62, 65, 0.12)"
AXIS_COLOR = "rgba(57, 62, 65, 0.35)"
MUTED_TEXT = "rgba(57, 62, 65, 0.65)"

TOP_EMPLOYERS_SHOWN = 100


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(
        DATA_PATH, low_memory=False, parse_dates=["RECEIVED_DATE", "DECISION_DATE"]
    )


def style_chart(fig):
    """Apply the shared, recessive chart chrome (hairline gridlines, muted axes)."""
    fig.update_layout(
        plot_bgcolor=IVORY,
        paper_bgcolor=IVORY,
        font_color=MUTED_TEXT,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, linecolor=AXIS_COLOR, zeroline=False)
    fig.update_yaxes(gridcolor=GRID_COLOR, linecolor=AXIS_COLOR, zeroline=False)
    return fig


st.set_page_config(page_title="California H-1B Sponsorship Dashboard", layout="wide")
st.title("California H-1B Sponsorship Dashboard")
st.caption(
    "Exploring H-1B LCA filings for tech/data roles across California (FY2025 Q3 "
    "through FY2026 Q3), built from public DOL disclosure data."
)

df = load_data()

# --- Sidebar filters -- every section below reads from `filtered`, so the
# numbers everywhere on the page always agree with each other. ---
st.sidebar.header("Filters")

counties = sorted(df["WORKSITE_COUNTY_CLEAN"].dropna().unique())
selected_counties = st.sidebar.multiselect("County", counties, default=counties)

roles = sorted(df["role_category"].dropna().unique())
selected_roles = st.sidebar.multiselect("Role category", roles, default=roles)

statuses = sorted(df["CASE_STATUS"].dropna().unique())
selected_statuses = st.sidebar.multiselect("Case status", statuses, default=statuses)

experience_levels = sorted(df["experience_level"].dropna().unique())
selected_experience_levels = st.sidebar.multiselect(
    "Experience level", experience_levels, default=experience_levels
)

company_search = st.sidebar.text_input("Employer name contains")

filtered = df[
    df["WORKSITE_COUNTY_CLEAN"].isin(selected_counties)
    & df["role_category"].isin(selected_roles)
    & df["CASE_STATUS"].isin(selected_statuses)
    & df["experience_level"].isin(selected_experience_levels)
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
st.caption(
    f"Top {TOP_EMPLOYERS_SHOWN} by total filings, broken out by fiscal year. "
    "FY2026 is a partial year to date (through Jun 2026) -- more year columns "
    "will appear automatically as more fiscal quarters/years are added. "
    "Certified % is certified filings as a share of this employer's total filings "
    "shown here. Wage vs. Prevailing is the median percent by which this employer's "
    "offered wage is above (+) or below (-) DOL's prevailing wage benchmark for the "
    "role, excluding filings flagged as implausible wages. Careers links to a search "
    "for that company's job postings, not a verified official page."
)
by_year = (
    filtered.groupby(["EMPLOYER_NAME_CLEAN", "DECISION_FISCAL_YEAR"])
    .size()
    .reset_index(name="Filings")
)
employer_table = by_year.pivot(
    index="EMPLOYER_NAME_CLEAN", columns="DECISION_FISCAL_YEAR", values="Filings"
).fillna(0).astype(int)
fiscal_year_cols = sorted(employer_table.columns)
employer_table["Total"] = employer_table.sum(axis=1)
employer_table = employer_table.sort_values("Total", ascending=False).head(TOP_EMPLOYERS_SHOWN)
employer_table = employer_table.reset_index().rename(columns={"EMPLOYER_NAME_CLEAN": "Company"})
employer_table.insert(0, "Rank", range(1, len(employer_table) + 1))

certified_counts = (
    filtered[filtered["CASE_STATUS"] == "Certified"].groupby("EMPLOYER_NAME_CLEAN").size()
)
employer_table["Certified %"] = (
    employer_table["Company"].map(certified_counts).fillna(0) / employer_table["Total"] * 100
).map(lambda pct: f"{pct:.1f}%")

wage_premium_by_employer = (
    filtered[filtered["wage_is_plausible"]]
    .groupby("EMPLOYER_NAME_CLEAN")["wage_premium_pct"]
    .median()
)
employer_table["Wage vs. Prevailing"] = employer_table["Company"].map(wage_premium_by_employer).map(
    lambda pct: "—" if pd.isna(pct) else f"{pct:+.1f}%"
)

employer_table["Careers"] = employer_table["Company"].map(
    lambda name: f"https://www.google.com/search?q={quote_plus(name + ' careers')}"
)

employer_table = employer_table[
    ["Rank", "Company"] + fiscal_year_cols + ["Total", "Certified %", "Wage vs. Prevailing", "Careers"]
]
st.dataframe(
    employer_table,
    hide_index=True,
    column_config={"Careers": st.column_config.LinkColumn("Careers", display_text="🔍 Search")},
)

# --- Top job titles ---
st.subheader("Top Job Titles")
st.caption(
    "Top 15 employer-reported job titles within the current filters, shown as "
    "reported. Free text, not standardized -- the same role can appear under many "
    "different titles (see role_category above for a standardized grouping)."
)
job_title_counts = (
    filtered.assign(JOB_TITLE=filtered["JOB_TITLE"].str.strip())
    .groupby(["JOB_TITLE", "role_category"])
    .size()
    .reset_index(name="Filings")
    .sort_values("Filings", ascending=False)
    .head(15)
    .rename(columns={"JOB_TITLE": "Job Title", "role_category": "Category"})
)[["Job Title", "Category", "Filings"]]
st.dataframe(job_title_counts, hide_index=True)

# --- Salary distribution by role category ---
st.subheader("Salary Distribution by Role")
st.caption("Excludes filings flagged as implausible wages (likely unit-entry errors).")
wage_df = filtered[filtered["wage_is_plausible"]]
role_order = (
    wage_df.groupby("role_category")["ANNUAL_WAGE_FROM"].median().sort_values(ascending=False).index
)
fig = px.box(wage_df, x="role_category", y="ANNUAL_WAGE_FROM", category_orders={"role_category": list(role_order)})
fig.update_traces(marker_color=CHART_ACCENT, line_color=CHART_ACCENT)
fig.update_layout(xaxis_title=None, yaxis_title="Annual Wage ($)", xaxis_tickangle=-30)
st.plotly_chart(style_chart(fig))

# --- Salary by experience level ---
st.subheader("Salary by Experience Level")
st.caption(
    "Annual wage quartiles by DOL wage level (the closest proxy this data has "
    "to seniority). Excludes filings flagged as implausible wages."
)
level_order = [
    "Level I - Entry",
    "Level II - Qualified",
    "Level III - Experienced",
    "Level IV - Fully Competent",
    "Unknown",
]
salary_by_level = (
    wage_df.groupby("experience_level")["ANNUAL_WAGE_FROM"]
    .quantile([0.25, 0.5, 0.75])
    .unstack()
    .rename(columns={0.25: "25th Percentile", 0.5: "Median", 0.75: "75th Percentile"})
)
salary_by_level = salary_by_level.reindex(
    [lvl for lvl in level_order if lvl in salary_by_level.index]
)
salary_by_level = salary_by_level.reset_index().rename(columns={"experience_level": "Experience Level"})
for col in ["25th Percentile", "Median", "75th Percentile"]:
    salary_by_level[col] = salary_by_level[col].map(lambda v: f"${v:,.0f}")
st.dataframe(salary_by_level, hide_index=True)

# --- Salary by company ---
st.subheader("Salary by Company")
st.caption(
    "Annual wage quartiles for the top 15 employers by filing count within the "
    "current filters. Excludes filings flagged as implausible wages. Base offered "
    "wage only -- DOL's LCA data doesn't capture bonus, equity, or other total "
    "compensation."
)
top_companies_by_filings = filtered["EMPLOYER_NAME_CLEAN"].value_counts().head(15).index
salary_by_company = (
    wage_df[wage_df["EMPLOYER_NAME_CLEAN"].isin(top_companies_by_filings)]
    .groupby("EMPLOYER_NAME_CLEAN")["ANNUAL_WAGE_FROM"]
    .quantile([0.25, 0.5, 0.75])
    .unstack()
    .rename(columns={0.25: "25th Percentile", 0.5: "Median", 0.75: "75th Percentile"})
    .reindex(top_companies_by_filings)
    .dropna(how="all")
)
salary_by_company = salary_by_company.sort_values("Median", ascending=False)
salary_by_company = salary_by_company.reset_index().rename(columns={"EMPLOYER_NAME_CLEAN": "Company"})
for col in ["25th Percentile", "Median", "75th Percentile"]:
    salary_by_company[col] = salary_by_company[col].map(lambda v: f"${v:,.0f}")
st.dataframe(salary_by_company, hide_index=True)

# --- Monthly filing volume by outcome ---
st.subheader("Monthly Filing Volume by Outcome")
st.caption(
    "By decision date, Apr 2025 through Jun 2026. Certified (bars, left axis) and "
    "Denied (line, right axis) use separate scales since Denied volume is far "
    "smaller -- compare their shapes over time, not their heights against each "
    "other. Labels above each bar are the certified rate: certified filings as a "
    "percent of all filings that month, regardless of status. This will extend "
    "automatically as more fiscal quarters/years are added."
)
outcome_df = filtered[filtered["CASE_STATUS"].isin(["Certified", "Denied"])]
monthly_outcome = (
    outcome_df.assign(month=outcome_df["DECISION_DATE"].dt.to_period("M").dt.to_timestamp())
    .groupby(["month", "CASE_STATUS"])
    .size()
    .reset_index(name="Filings")
)
certified_monthly = monthly_outcome[monthly_outcome["CASE_STATUS"] == "Certified"]
denied_monthly = monthly_outcome[monthly_outcome["CASE_STATUS"] == "Denied"]

monthly_total = (
    filtered.assign(month=filtered["DECISION_DATE"].dt.to_period("M").dt.to_timestamp())
    .groupby("month")
    .size()
    .reset_index(name="TotalFilings")
)
certified_monthly = certified_monthly.merge(monthly_total, on="month", how="left")
certified_monthly["CertifiedRatePct"] = (
    certified_monthly["Filings"] / certified_monthly["TotalFilings"] * 100
)

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Bar(
        x=certified_monthly["month"],
        y=certified_monthly["Filings"],
        name="Certified",
        marker_color=CHART_ACCENT,
        text=certified_monthly["CertifiedRatePct"].map(lambda pct: f"{pct:.1f}%"),
        textposition="outside",
        textfont=dict(color=GUNMETAL),
    ),
    secondary_y=False,
)
fig.update_yaxes(
    range=[0, certified_monthly["Filings"].max() * 1.15], secondary_y=False
)
fig.add_trace(
    go.Scatter(
        x=denied_monthly["month"],
        y=denied_monthly["Filings"],
        name="Denied",
        mode="lines+markers",
        line=dict(color=GUNMETAL, width=2),
        marker=dict(size=8),
    ),
    secondary_y=True,
)
fig.update_yaxes(title_text="Certified filings", secondary_y=False)
fig.update_yaxes(title_text="Denied filings", secondary_y=True)
fig.update_layout(xaxis_title=None, legend_title_text=None)
fig = style_chart(fig)
fig.update_yaxes(showgrid=False, secondary_y=True)
st.plotly_chart(fig)

# --- City breakdown ---
st.subheader("Filings by City")
st.caption(
    "Top 15 worksite cities by filing count within the current filters. LCA "
    "filings only report a physical worksite address -- there's no field "
    "indicating whether a role is remote."
)
city_counts = (
    filtered["WORKSITE_CITY"].str.strip().str.title().value_counts().head(15).reset_index()
)
city_counts.columns = ["City", "Filings"]
fig = px.bar(city_counts, x="Filings", y="City", orientation="h")
fig.update_traces(marker_color=CHART_ACCENT)
fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(style_chart(fig))

# --- Resources ---
st.subheader("Resources")
st.caption("Official sources for the H-1B process and the data behind this dashboard.")
st.markdown(
    "- [USCIS: H-1B Specialty Occupations]"
    "(https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations) "
    "— program overview and eligibility\n"
    "- [USCIS: H-1B Cap Season]"
    "(https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/h-1b-cap-season) "
    "— registration windows and cap details\n"
    "- [USCIS: H-1B Electronic Registration Process]"
    "(https://www.uscis.gov/working-in-the-united-states/temporary-workers/h-1b-specialty-occupations/h-1b-electronic-registration-process) "
    "— how to register for the cap\n"
    "- [DOL OFLC: Performance Data]"
    "(https://www.dol.gov/agencies/eta/foreign-labor/performance) "
    "— the official LCA disclosure data source behind this dashboard\n"
)
