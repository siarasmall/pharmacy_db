"""
1_backfill_from_excel.py — run this ONCE, before daily imports start.

Backfills history by combining TWO CSV exports of the old workbook:
  - "📋 Daily Log" sheet  -> RX # and Notes for each prescription
  - "💰 Billing" sheet    -> name, office, drug, quantity, billing date,
                             amount billed, payment received, claim
                             number, balance due

The two sheets have no shared key column, so their data rows are paired
row-by-row in file order (Nth Daily Log row = Nth Billing row). Keep the
exports aligned. Point BACKFILL_DAILY_LOG_FILE / BACKFILL_BILLING_FILE in
config.py at them. Built-in Python only.

Safe to re-run: existing rows only get their still-blank columns filled.
"""

import sys

import config
import pharmacy_common as common


def main():
    missing = [
        p for p in (config.BACKFILL_DAILY_LOG_FILE, config.BACKFILL_BILLING_FILE)
        if not p.exists()
    ]
    if missing:
        for p in missing:
            print(f"could not find backfill file: {p}")
        print("Fix BACKFILL_DAILY_LOG_FILE / BACKFILL_BILLING_FILE in config.py.")
        sys.exit(1)

    rows, meta = common.read_backfill(
        config.BACKFILL_DAILY_LOG_FILE, config.BACKFILL_BILLING_FILE
    )

    if meta["daily"] != meta["billing"]:
        print(f"Warning: Daily Log has {meta['daily']} prescription row(s), Billing "
              f"has {meta['billing']}. Paired the first {meta['paired']} of each — "
              f"check that the two sheets line up row-for-row before trusting this.")

    if not rows:
        print("No rows to backfill.")
        print("The Daily Log needs a header row with 'RX #'; the Billing sheet needs")
        print("a header row with 'Patient Name'. Check BACKFILL_*_MAP in config.py.")
        sys.exit(1)

    no_date = sum(1 for r in rows if not r.get("filled_date"))

    conn = common.get_connection()
    common.ensure_schema(conn)
    new_count, filled_count = common.insert_backfill(
        conn, rows, source_file=config.BACKFILL_BILLING_FILE.name
    )
    conn.close()

    print(f"Paired rows: {len(rows)}  new: {new_count}  "
          f"blank fields filled on existing rows: {filled_count}")
    if no_date:
        print(f"Note: {no_date} row(s) had no preceding 'Log Date:' in the Daily Log")
        print("and were imported with a blank fill date. Find them in DB Browser by")
        print("filtering filled_date = '' and set the correct date.")
    print("Backfill complete.")


if __name__ == "__main__":
    main()
