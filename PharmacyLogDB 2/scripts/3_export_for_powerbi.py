"""
3_export_for_powerbi.py — optional. Dumps the whole daily_log table to
a plain CSV so Power BI or Excel can read it (Get Data -> Text/CSV).

Re-run this any time you want fresh numbers, then hit Refresh in
Power BI / Excel.
"""

import csv
import sys

import config
import pharmacy_common as common


def main():
    if not config.DB_PATH.exists():
        print(f"could not find the database at {config.DB_PATH}")
        print("Run 1_backfill_from_excel.py and/or 2_daily_import.py first.")
        sys.exit(1)

    conn = common.get_connection()
    common.ensure_schema(conn)

    columns = [col for col, _ in config.ALL_FIELDS] + [
        "date_filled", "source_file", "imported_at",
    ]
    labels = [label for _, label in config.ALL_FIELDS] + [
        "Date Filled", "Source File", "Imported At",
    ]

    rows = conn.execute(
        f"SELECT {', '.join(columns)} FROM daily_log ORDER BY date_filled, rx_number"
    ).fetchall()
    conn.close()

    with open(config.EXPORT_CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(labels)
        for row in rows:
            writer.writerow([row[c] for c in columns])

    print(f"Exported {len(rows)} rows to {config.EXPORT_CSV_PATH}")


if __name__ == "__main__":
    main()
