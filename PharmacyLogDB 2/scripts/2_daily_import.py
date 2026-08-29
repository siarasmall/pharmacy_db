"""
2_daily_import.py — run this every day (about 30 seconds).

Loads every PrimeRx Daily Log Report CSV sitting in the inbox folder,
skips anything already imported, and moves processed files to archive.

Only uses Python's built-in libraries — nothing to install for this one.
"""

import shutil
import sys
from datetime import datetime
from pathlib import Path

import config
import pharmacy_common as common


def process_file(conn, csv_path):
    try:
        rows = common.read_primerx_csv(csv_path)
    except Exception as exc:
        print(f"  ERROR reading {csv_path.name}: {exc}")
        print("  Left in inbox — fix the issue and re-run.")
        return None

    if not rows:
        print(f"  {csv_path.name}: No prescription rows detected.")
        print("  The CSV isn't the PrimeRx Daily Log Report format, or it's empty.")
        print("  Re-export from PrimeRx. (File left in inbox.)")
        return None

    new_count = common.insert_auto_only(conn, rows, source_file=csv_path.name)
    print(f"  {csv_path.name}: Rows found: {len(rows)}  new: {new_count}")
    return len(rows)


def main():
    config.INBOX_DIR.mkdir(parents=True, exist_ok=True)
    config.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(config.INBOX_DIR.glob("*.csv"))
    if not csv_files:
        print("No new CSV files found.")
        print(f"(Looked in: {config.INBOX_DIR})")
        return

    conn = common.get_connection()
    common.ensure_schema(conn)

    print(f"Found {len(csv_files)} CSV file(s) in inbox:")
    processed = 0
    for csv_path in csv_files:
        ok = process_file(conn, csv_path)
        if ok is not None:
            processed += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = config.ARCHIVE_DIR / f"{csv_path.stem}_{timestamp}{csv_path.suffix}"
            shutil.move(str(csv_path), str(dest))

    conn.close()
    print(f"\nDone. {processed} of {len(csv_files)} file(s) processed and archived.")
    if processed < len(csv_files):
        print("Files with errors were left in inbox — see messages above.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        sys.exit(1)
