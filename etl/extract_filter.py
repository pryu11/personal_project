"""Filter one fiscal year of raw LCA disclosure data down to California tech/data roles.

Streams rows directly from the raw Excel file instead of loading it into a
pandas DataFrame first -- a fiscal year has 500k+ rows, but only a small
fraction are both in California and in a target SOC code, so filtering
row-by-row keeps memory usage low regardless of the source file's size.
"""

import sys
from pathlib import Path

import openpyxl
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reference.tech_soc_codes import TECH_SOC_CODES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET_STATE = "CA"
TARGET_SOC_PREFIXES = tuple(TECH_SOC_CODES.keys())


def extract_filter(raw_path: Path) -> pd.DataFrame:
    wb = openpyxl.load_workbook(raw_path, read_only=True)
    ws = wb[wb.sheetnames[0]]

    rows = ws.iter_rows(values_only=True)
    header = list(next(rows))
    col_index = {name: i for i, name in enumerate(header)}
    state_i = col_index["WORKSITE_STATE"]
    soc_i = col_index["SOC_CODE"]

    matched = []
    total = 0
    for row in rows:
        total += 1
        state = row[state_i]
        soc = row[soc_i]
        if state != TARGET_STATE:
            continue
        if not soc or not soc.startswith(TARGET_SOC_PREFIXES):
            continue
        matched.append(row)

    wb.close()

    print(f"{total:,} total rows -> {len(matched):,} rows after CA + tech SOC filter")
    return pd.DataFrame(matched, columns=header)


def main():
    fiscal_year = sys.argv[1] if len(sys.argv) > 1 else "FY2025"
    raw_dir = PROJECT_ROOT / "data" / "raw" / fiscal_year
    raw_files = list(raw_dir.glob("*.xlsx"))
    if not raw_files:
        raise FileNotFoundError(f"No .xlsx file found in {raw_dir}")

    out_path = PROJECT_ROOT / "data" / "interim" / f"lca_{fiscal_year}_ca_tech.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = extract_filter(raw_files[0])
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
