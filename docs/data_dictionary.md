# Data Dictionary — `data/processed/lca_ca_tech_clean.csv`

Source: U.S. Department of Labor, Office of Foreign Labor Certification (OFLC),
LCA (Labor Condition Application) disclosure data. Three raw quarterly files are
currently loaded (DOL's fiscal year runs Oct–Sep):

- FY2025 Q3 (decisions Apr–Jun 2025) and FY2025 Q4 (decisions Jul–Sep 2025) —
  FY2025 is a completed fiscal year, so each quarterly file covers only that quarter.
- FY2026 Q3 (decisions Oct 2025–Jun 2026) — FY2026 is still in progress, and DOL
  publishes the current fiscal year's quarterly file as cumulative year-to-date,
  so this single file already covers all of FY2026 Q1–Q3, not just Q3 alone.

`RECEIVED_DATE` on these rows can go back much further than any of the above,
since a case can be decided long after it was filed — use `DECISION_DATE` (or
the derived `DECISION_FISCAL_YEAR` column) for anything tied to "what fiscal
period this data covers."

Each row is one LCA filing (one job/worksite/wage combination an employer
submitted as part of sponsoring an H-1B worker). This file has already been
filtered to California worksites in tech/data SOC codes (see
`etl/extract_filter.py`) — it is not the full national dataset. It is not
limited to the Bay Area; `is_bay_area` (see below) flags the subset that is.

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
| `WORKSITE_CITY` / `WORKSITE_COUNTY` / `WORKSITE_STATE` | Worksite location as reported. Raw `WORKSITE_COUNTY` is ~88% populated statewide but has inconsistent formatting (e.g. "SANTA CLARA COUNTY" vs. "SANTA CLARA" as separate raw values) — see `WORKSITE_COUNTY_CLEAN` below for the normalized version this dashboard actually uses. |
| `WAGE_RATE_OF_PAY_FROM` / `WAGE_RATE_OF_PAY_TO` | Wage as reported, in whatever unit `WAGE_UNIT_OF_PAY` specifies |
| `WAGE_UNIT_OF_PAY` | `Year`, `Hour`, `Week`, `Bi-Weekly`, or `Month` |
| `PREVAILING_WAGE` | DOL's benchmark wage for the role/location, for comparison |
| `PW_WAGE_LEVEL` | OES wage level (`I`–`IV`) backing the prevailing wage, DOL's standard seniority proxy — Level I is entry-level, IV is fully competent/expert. `NaN` when the employer used a non-OES wage source instead (see `experience_level` below). |

## Derived columns (added by `etl/clean.py`)

| Column | Description |
|---|---|
| `WORKSITE_COUNTY_CLEAN` | Statewide county field: raw `WORKSITE_COUNTY` normalized (whitespace/case standardized, trailing "COUNTY" suffix stripped), falling back to a city->county lookup (`reference/bay_area_cities.py`, Bay Area cities only) for the ~12% of rows with no raw county. `"Unknown"` (not dropped) if neither source resolves it — about 2.7% of rows. |
| `is_bay_area` | `True` if `WORKSITE_COUNTY_CLEAN` is one of the 9 Bay Area counties. |
| `EMPLOYER_NAME_CLEAN` | Standardized employer name: legal-entity suffixes (Inc., LLC, Corp., PBC, etc.) stripped, then a manual override applied for stylized brand names (e.g. `PayPal`, `TikTok`, `IBM`) that generic casing rules can't guess. See `reference/employer_name_map.py`. Not exhaustive — unmapped names pass through as generically-cleaned title case. |
| `ANNUAL_WAGE_FROM` / `ANNUAL_WAGE_TO` | `WAGE_RATE_OF_PAY_FROM`/`TO` annualized using `WAGE_UNIT_OF_PAY` (Hour ×2080, Week ×52, Bi-Weekly ×26, Month ×12, Year ×1). |
| `wage_is_plausible` | `False` if `ANNUAL_WAGE_FROM` falls outside a $20,000–$1,000,000 plausibility band — almost always an employer picking the wrong `WAGE_UNIT_OF_PAY` at filing time (e.g. a $200,000 annual salary mistakenly tagged as hourly). **Flagged, not dropped** — the raw values are preserved either way so nothing is silently discarded. |
| `role_category` | Human-readable role name mapped from `SOC_CODE`'s 7-character prefix via `reference/tech_soc_codes.py` (e.g. `15-2051` → "Data Scientists"). |
| `DECISION_FISCAL_YEAR` | DOL fiscal year (Oct–Sep) the filing was decided in, derived from `DECISION_DATE` via `add_fiscal_year()` in `etl/clean.py`. Used to group the Top Sponsoring Employers table and other year-based views; note that the FY2026 bucket is a partial year to date (see Known limitations). |
| `experience_level` | Human-readable label for `PW_WAGE_LEVEL` (e.g. `"Level I - Entry"`), with `NaN` mapped to `"Unknown"` rather than dropped, via `add_experience_level()` in `etl/clean.py`. There's no dedicated field for internships — H-1B LCA filings are specialty-occupation employment, not internships (those go through F-1 OPT/CPT and don't file an LCA), so this can only approximate "entry-level," not "internship." |
| `ANNUAL_PREVAILING_WAGE` | `PREVAILING_WAGE` annualized using `PW_UNIT_OF_PAY` (same multipliers as `ANNUAL_WAGE_FROM`/`TO`) — needed because the prevailing wage's pay-period unit can differ from the offered wage's `WAGE_UNIT_OF_PAY`. |
| `wage_premium_pct` | `(ANNUAL_WAGE_FROM - ANNUAL_PREVAILING_WAGE) / ANNUAL_PREVAILING_WAGE * 100` — how far above (+) or below (-) DOL's prevailing wage benchmark the offered wage is. Computed for all rows; aggregate it only over `wage_is_plausible == True` rows, same as any other use of `ANNUAL_WAGE_FROM`. |

## Known limitations

- Employer names are self-reported and only partially standardized — a long tail of rare variants remains uncleaned by design (see plan rationale in `reference/employer_name_map.py`).
- This dataset covers all of California, not just the Bay Area; `is_bay_area` flags the 79.0% of rows in the 9-county Bay Area, the rest are genuinely elsewhere in the state (LA, San Diego, Sacramento, Central Valley, etc.).
- Three fiscal quarters are included so far — FY2025 Q3, FY2025 Q4, and FY2026 Q3 (the last of which is cumulative Oct 2025–Jun 2026, not a single quarter). FY2025 is a complete fiscal year; FY2026 is still in progress, so any FY2025-vs-FY2026 comparison (e.g. in the Top Sponsoring Employers table) is comparing a full year against a partial year to date.
- `role_category` reflects the employer's self-reported SOC code, which can be inconsistent with the actual job duties.
- `experience_level` is `"Unknown"` for ~23% of rows (19,343 of 83,169) — filings that used a non-OES prevailing wage source have no `PW_WAGE_LEVEL` at all, so they can't be bucketed as entry-level or not.
- `wage_premium_pct` is never negative in this dataset — H-1B law requires the offered wage to be at or above the prevailing wage benchmark for an LCA to be filed at all, and about a third of plausible-wage filings are filed at exactly that floor (0%). This is expected, not a data quality issue.
- Wage fields are base offered wage only (`WAGE_RATE_OF_PAY_FROM`/`TO`) — DOL's LCA data has no field for bonus, equity, or other total compensation, so this dataset can't answer "total comp" questions regardless of dashboard scope.
- There's no remote-work indicator anywhere in DOL's disclosure data — LCA filings only require a physical worksite address (`WORKSITE_CITY`/`WORKSITE_COUNTY`/`WORKSITE_POSTAL_CODE`), so whether a filed role is actually remote can't be determined from this data.
