# Data Dictionary — `data/processed/lca_bay_area_tech_clean.csv`

Source: U.S. Department of Labor, Office of Foreign Labor Certification (OFLC),
LCA (Labor Condition Application) disclosure data, FY2025 Q4 (decisions dated
Jul–Sep 2025 — DOL's fiscal year runs Oct–Sep, so Q4 is the final quarter,
not the whole year). `RECEIVED_DATE` on these rows goes back much further
(to April 2022) since a case can be decided long after it was filed —
use `DECISION_DATE` for anything tied to "what FY2025 Q4 covers."

Each row is one LCA filing (one job/worksite/wage combination an employer
submitted as part of sponsoring an H-1B worker). This file has already been
filtered to California worksites in tech/data SOC codes (see
`etl/extract_filter.py`) and then to Bay Area worksites only (see
`is_bay_area` below) — it is not the full national dataset.

## Key original columns (kept as-is from the raw DOL file)

| Column | Description |
|---|---|
| `CASE_NUMBER` | DOL's unique identifier for the filing |
| `CASE_STATUS` | `Certified`, `Certified - Withdrawn`, `Withdrawn`, or `Denied`. **Not filtered** — all four are kept so a dashboard can let users choose what to include. |
| `RECEIVED_DATE` / `DECISION_DATE` | Filing and decision dates |
| `VISA_CLASS` | Visa program (e.g. H-1B) |
| `JOB_TITLE` | Employer-provided job title (free text, inconsistent — use `role_category` instead for grouping) |
| `SOC_CODE` / `SOC_TITLE` | Standard Occupational Classification code/title as reported by the employer |
| `EMPLOYER_NAME` | Employer name as originally reported (unstandardized — use `EMPLOYER_NAME_CLEAN`) |
| `WORKSITE_CITY` / `WORKSITE_COUNTY` / `WORKSITE_STATE` | Worksite location as reported. `WORKSITE_COUNTY` is only ~15% populated in the raw data, so it is **not** used for Bay Area filtering (see `WORKSITE_COUNTY_INFERRED` below). |
| `WAGE_RATE_OF_PAY_FROM` / `WAGE_RATE_OF_PAY_TO` | Wage as reported, in whatever unit `WAGE_UNIT_OF_PAY` specifies |
| `WAGE_UNIT_OF_PAY` | `Year`, `Hour`, `Week`, `Bi-Weekly`, or `Month` |
| `PREVAILING_WAGE` | DOL's benchmark wage for the role/location, for comparison |

## Derived columns (added by `etl/clean.py`)

| Column | Description |
|---|---|
| `WORKSITE_COUNTY_INFERRED` | County inferred from `WORKSITE_CITY` via `reference/bay_area_cities.py`, since raw `WORKSITE_COUNTY` is too sparse to use directly. `NaN` if the city isn't a recognized Bay Area city. |
| `is_bay_area` | `True` if `WORKSITE_COUNTY_INFERRED` matched one of the 9 Bay Area counties. This file already contains only `is_bay_area == True` rows — the column is kept for transparency/re-filtering. |
| `EMPLOYER_NAME_CLEAN` | Standardized employer name: legal-entity suffixes (Inc., LLC, Corp., PBC, etc.) stripped, then a manual override applied for stylized brand names (e.g. `PayPal`, `TikTok`, `IBM`) that generic casing rules can't guess. See `reference/employer_name_map.py`. Not exhaustive — unmapped names pass through as generically-cleaned title case. |
| `ANNUAL_WAGE_FROM` / `ANNUAL_WAGE_TO` | `WAGE_RATE_OF_PAY_FROM`/`TO` annualized using `WAGE_UNIT_OF_PAY` (Hour ×2080, Week ×52, Bi-Weekly ×26, Month ×12, Year ×1). |
| `wage_is_plausible` | `False` if `ANNUAL_WAGE_FROM` falls outside a $20,000–$1,000,000 plausibility band — almost always an employer picking the wrong `WAGE_UNIT_OF_PAY` at filing time (e.g. a $200,000 annual salary mistakenly tagged as hourly). **Flagged, not dropped** — the raw values are preserved either way so nothing is silently discarded. |
| `role_category` | Human-readable role name mapped from `SOC_CODE`'s 7-character prefix via `reference/tech_soc_codes.py` (e.g. `15-2051` → "Data Scientists"). |

## Known limitations

- Employer names are self-reported and only partially standardized — a long tail of rare variants remains uncleaned by design (see plan rationale in `reference/employer_name_map.py`).
- Bay Area membership is inferred from city name, not a direct county field, and covers 77.7% of the CA-tech-filtered rows; the rest are genuinely outside the 9-county Bay Area (LA, San Diego, Sacramento, Central Valley, Santa Cruz County, etc.).
- Only one fiscal quarter (FY2025 Q4, Jul–Sep 2025 decisions) is included so far — trend charts will be thin until more quarters/years are added.
- `role_category` reflects the employer's self-reported SOC code, which can be inconsistent with the actual job duties.
