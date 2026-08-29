"""
1_backfill_from_excel.py — NOT USED in the NF Insurance workflow.

The old pipeline backfilled history from an Excel "Daily Log" tracker.
The current model is driven entirely by the NF Insurance CSV export
(name / drug / quantity) plus fields your team fills in by hand (office,
billing date, payment received, expense case number, discrepancy), so
there is no Excel source to load.

To load data, use:  python 2_daily_import.py
"""

import sys


def main():
    print(__doc__.strip())
    sys.exit(1)


if __name__ == "__main__":
    main()
