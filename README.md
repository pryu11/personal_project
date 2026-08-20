# California H-1B Sponsorship Dashboard

An exploratory dashboard of H-1B visa sponsorship for tech/data roles across California, built from the U.S. Department of Labor's public LCA (Labor Condition Application) disclosure data.

This is a personal learning project — first solo app, first time using Cursor and Claude Code, and a chance to practice real-world data cleaning and visualization as a Data Science student new to the Bay Area.

## Status

✅ Deployed, built in phases:

- [x] Phase 0 — environment, git, and GitHub setup
- [x] Phase 1 — raw data acquisition and first filter
- [x] Phase 2 — data cleaning and county / role standardization
- [x] Phase 3 — dashboard skeleton
- [x] Phase 4 — full dashboard
- [x] Phase 5 — polish, deploy, and publish

**Live app:** https://personalproject-bayareah1bdashboard.streamlit.app/

## Data Source

U.S. Department of Labor, Office of Foreign Labor Certification (OFLC) — public LCA disclosure data.

Currently loaded:
- **FY2025 Q3 + Q4** (decisions Apr–Sep 2025) — each a single-quarter file, since FY2025 is a completed fiscal year.
- **FY2026 Q3** (decisions Oct 2025–Jun 2026) — DOL publishes the current, in-progress fiscal year's quarterly file as cumulative year-to-date, so this one file already covers all of FY2026 Q1–Q3, not just Q3 alone.

Filtered to California worksites in tech/data SOC codes (not just the Bay Area — an `is_bay_area` flag marks the ~79% of rows that are). More fiscal quarters/years will be added over time — see `docs/data_dictionary.md` for the full column reference and current known limitations.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/Home.py
```

The dashboard reads from `data/processed/lca_ca_tech_clean.csv`, which is committed to the repo. To regenerate it from raw data, see `etl/build_dataset.py`.

## Built With

Python, pandas, and Streamlit — developed using [Cursor](https://cursor.com) and [Claude Code](https://claude.com/product/claude-code) as a hands-on way to learn both tools.
