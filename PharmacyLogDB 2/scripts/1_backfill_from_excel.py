"""
1_backfill_from_excel.py — run this ONCE, before daily imports start.

Loads historical prescriptions from a CSV export of the old Excel
tracker's "📋 Daily Log" sheet. Only the columns that exist in the
current database model are kept:
    Patient Name    -> name
    Drug            -> drug
    Qty             -> quantity
    Office Location  -> office
    RX #            -> de-dup key (hidden)
    Log Date:       -> de-dup key (hidden)
DOA / Insurance Carrier / Prescriber / Demo / Notes are not in the model
and are dropped.

Point BACKFILL_FILE in config.py at the export. Existing rows (e.g. from
a daily import) are never overwritten — only their blank columns get
filled. Built-in Python only.
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
        print("No prescription rows found in the backfill file.")
        print("Expected a header row containing 'Patient Name' and 'RX #',")
        print("with data rows beneath it. Check BACKFILL_COLUMN_MAP in config.py.")
        sys.exit(1)

    no_date = sum(1 for r in rows if not r.get("filled_date"))

    conn = common.get_connection()
    common.ensure_schema(conn)
    new_count, filled_count = common.insert_backfill(
        conn, rows, source_file=config.BACKFILL_FILE.name
    )
    conn.close()

    print(f"Rows found: {len(rows)}  new: {new_count}  "
          f"blank fields filled on existing rows: {filled_count}")
    if no_date:
        print(f"Warning: {no_date} row(s) had no preceding 'Log Date:' separator")
        print("and were imported with a blank fill date. Find them in DB Browser by")
        print("filtering filled_date = '' and set the correct date.")
    print("Backfill complete.")


if __name__ == "__main__":
    main()
