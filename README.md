# Bay Area H-1B Sponsorship Dashboard

An exploratory dashboard of H-1B visa sponsorship for tech/data roles in the San Francisco Bay Area, built from the U.S. Department of Labor's public LCA (Labor Condition Application) disclosure data.

This is a personal learning project — first solo app, first time using Cursor and Claude Code, and a chance to practice real-world data cleaning and visualization as a Data Science student new to the Bay Area.

## Status

🚧 Work in progress, built in phases:

- [x] Phase 0 — environment, git, and GitHub setup
- [x] Phase 1 — raw data acquisition and first filter
- [x] Phase 2 — data cleaning and Bay Area / role standardization
- [x] Phase 3 — dashboard skeleton
- [x] Phase 4 — full dashboard
- [ ] Phase 5 — polish, deploy, and publish

## Data Source

U.S. Department of Labor, Office of Foreign Labor Certification (OFLC) — public LCA disclosure data.

Currently loaded: **FY2025 Q4** (decisions from July–September 2025), filtered to California worksites in tech/data SOC codes, then to Bay Area worksites only. More fiscal quarters/years will be added over time — see `docs/data_dictionary.md` for the full column reference and current known limitations.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/Home.py
```

The dashboard reads from `data/processed/lca_bay_area_tech_clean.csv`, which is committed to the repo. To regenerate it from raw data, see `etl/build_dataset.py`.

## Built With

Python, pandas, and Streamlit — developed using [Cursor](https://cursor.com) and [Claude Code](https://claude.com/product/claude-code) as a hands-on way to learn both tools.
