"""
1_backfill_from_excel.py — run this ONCE, before daily imports start.

Loads historical prescriptions from a single CSV: an export of the old
workbook's "Daily Log" sheet, which now carries the billing columns too
in one flat table:

    Name, Office, Claim Number, Drug, Qty, Date Billing, Amount Billed,
    Payment Received $, Balance Due, RX Number, Filled Date, Notes

"Claim Number" is ignored on purpose, so Expense Case Number stays blank
for hand entry. "RX Number" + "Filled Date" are the de-dup key.

Point BACKFILL_FILE in config.py at the export. Built-in Python only.
Safe to re-run: existing rows only get their still-blank columns filled.
"""

import sys

import config
import pharmacy_common as common


def main():
    if not config.BACKFILL_FILE.exists():
        print(f"could not find the backfill file at {config.BACKFILL_FILE}")
        print("Fix the BACKFILL_FILE path in config.py.")
        sys.exit(1)

    rows = common.read_backfill_csv(config.BACKFILL_FILE)
    if not rows:
        print("No rows to backfill.")
        print("Expected a header row with 'Name' plus the billing columns.")
        print("Check BACKFILL_COLUMN_MAP in config.py.")
        sys.exit(1)

    no_rx = sum(1 for r in rows if not r.get("rx_number"))
    no_date = sum(1 for r in rows if not r.get("filled_date"))

    conn = common.get_connection()
    common.ensure_schema(conn)
    new_count, filled_count = common.insert_backfill(
        conn, rows, source_file=config.BACKFILL_FILE.name
    )
    conn.close()

    print(f"Rows found: {len(rows)}  new: {new_count}  "
          f"blank fields filled on existing rows: {filled_count}")
    if no_rx or no_date:
        print(f"Note: {no_rx} row(s) had no RX Number and {no_date} had no Filled")
        print("Date. The de-dup key is (RX Number + Filled Date), so rows missing")
        print("both collapse into one — fill those in and re-run if the count looks low.")
    print("Backfill complete.")


if __name__ == "__main__":
    main()
