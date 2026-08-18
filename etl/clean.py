"""Clean the CA tech-role interim data into a final Bay Area analysis dataset.

Takes the interim CSV(s) produced by extract_filter.py and:
  - flags Bay Area worksites via reference/bay_area_cities.py
  - standardizes employer names (generic suffix-stripping + manual overrides)
  - annualizes wages to a common yearly figure, flagging implausible values
  - adds a human-readable role_category from the SOC code

CASE_STATUS is left untouched -- Certified/Withdrawn/Denied are all kept
so a future dashboard filter can decide what to show, rather than this
cleaning step silently deciding for it.
"""

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reference.bay_area_cities import BAY_AREA_CITY_TO_COUNTY, normalize_city
from reference.employer_name_map import EMPLOYER_NAME_OVERRIDES
from reference.tech_soc_codes import TECH_SOC_CODES

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Legal-entity suffixes to strip, plus PBC (Public Benefit Corporation,
# e.g. "Anthropic, Pbc") and a trailing lone "&" left behind when a suffix
# like "Co." is stripped from "Jpmorgan Chase & Co." -> "Jpmorgan Chase &".
SUFFIX_RE = re.compile(
    r"[,\.]?\s*\b(INC|INCORPORATED|LLC|L\.L\.C|CORP|CORPORATION|CO|COMPANY|"
    r"LTD|LIMITED|LLP|PLLC|P\.C|PC|PBC)\b\.?\s*$",
    re.IGNORECASE,
)
TRAILING_CONNECTOR_RE = re.compile(r"[,&]+\s*$")

# Annualization multipliers for WAGE_UNIT_OF_PAY values seen in the raw data.
WAGE_UNIT_MULTIPLIERS = {
    "Year": 1,
    "Hour": 2080,
    "Week": 52,
    "Bi-Weekly": 26,
    "Month": 12,
}

# Plausibility bounds for annualized wages -- outside this range is almost
# certainly a unit-selection data-entry error, not a real salary.
PLAUSIBLE_WAGE_MIN = 20_000
PLAUSIBLE_WAGE_MAX = 1_000_000


def standardize_employer_name(raw: str) -> str:
    name = str(raw).strip().upper()
    name = re.sub(r"[,\.]+$", "", name)
    prev = None
    while prev != name:
        prev = name
        name = SUFFIX_RE.sub("", name).strip()
    name = TRAILING_CONNECTOR_RE.sub("", name).strip()
    name = name.title()
    return EMPLOYER_NAME_OVERRIDES.get(name, name)


def add_bay_area_flag(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df["WORKSITE_CITY"].apply(normalize_city)
    df["WORKSITE_COUNTY_INFERRED"] = normalized.map(BAY_AREA_CITY_TO_COUNTY)
    df["is_bay_area"] = df["WORKSITE_COUNTY_INFERRED"].notna()
    return df


def add_employer_standardization(df: pd.DataFrame) -> pd.DataFrame:
    df["EMPLOYER_NAME_CLEAN"] = df["EMPLOYER_NAME"].apply(standardize_employer_name)
    return df


def add_annual_wage(df: pd.DataFrame) -> pd.DataFrame:
    multiplier = df["WAGE_UNIT_OF_PAY"].map(WAGE_UNIT_MULTIPLIERS)

    df["ANNUAL_WAGE_FROM"] = df["WAGE_RATE_OF_PAY_FROM"] * multiplier
    df["ANNUAL_WAGE_TO"] = df["WAGE_RATE_OF_PAY_TO"] * multiplier

    df["wage_is_plausible"] = df["ANNUAL_WAGE_FROM"].between(
        PLAUSIBLE_WAGE_MIN, PLAUSIBLE_WAGE_MAX
    )
    return df


def add_role_category(df: pd.DataFrame) -> pd.DataFrame:
    soc_prefix = df["SOC_CODE"].str.slice(0, 7)
    df["role_category"] = soc_prefix.map(TECH_SOC_CODES)
    return df


def add_fiscal_year(df: pd.DataFrame) -> pd.DataFrame:
    """DOL's fiscal year runs Oct-Sep, so Oct-Dec belongs to the *next* year's FY."""
    decision_date = pd.to_datetime(df["DECISION_DATE"])
    fiscal_year = decision_date.dt.year + (decision_date.dt.month >= 10).astype(int)
    df["DECISION_FISCAL_YEAR"] = "FY" + fiscal_year.astype(str)
    return df


WAGE_LEVEL_LABELS = {
    "I": "Level I - Entry",
    "II": "Level II - Qualified",
    "III": "Level III - Experienced",
    "IV": "Level IV - Fully Competent",
}


def add_experience_level(df: pd.DataFrame) -> pd.DataFrame:
    """PW_WAGE_LEVEL (DOL's OES-based prevailing wage level) is the closest proxy
    LCA data has to seniority -- Level I is defined as entry-level. Filings that
    used a non-OES wage survey have no level at all, so those are labeled
    Unknown rather than dropped.
    """
    df["experience_level"] = df["PW_WAGE_LEVEL"].map(WAGE_LEVEL_LABELS).fillna("Unknown")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = add_bay_area_flag(df)
    df = add_employer_standardization(df)
    df = add_annual_wage(df)
    df = add_role_category(df)
    df = add_fiscal_year(df)
    df = add_experience_level(df)
    return df


def main():
    interim_dir = PROJECT_ROOT / "data" / "interim"
    interim_files = sorted(interim_dir.glob("lca_*_ca_tech.csv"))
    if not interim_files:
        raise FileNotFoundError(f"No interim files found in {interim_dir}")

    frames = [pd.read_csv(f) for f in interim_files]
    df = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(df):,} rows from {len(interim_files)} interim file(s)")

    df = clean(df)

    bay_area_df = df[df["is_bay_area"]].copy()
    print(f"{len(bay_area_df):,} rows are in the Bay Area (of {len(df):,} CA tech rows)")

    out_path = PROJECT_ROOT / "data" / "processed" / "lca_bay_area_tech_clean.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bay_area_df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
