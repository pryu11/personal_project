"""Run the full pipeline: raw Excel -> CA/tech filter -> cleaned Bay Area dataset.

Thin orchestrator over extract_filter.py and clean.py so the whole
pipeline can be re-run with one command as new fiscal years are added.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from etl.clean import main as clean_main
from etl.extract_filter import main as extract_filter_main


def main():
    extract_filter_main()
    clean_main()


if __name__ == "__main__":
    main()
