"""
config.py — the ONE file you normally need to edit.

Everything the scripts need to know about your folder layout, your Excel
workbook, and how the PrimeRx export lines up lives here. If a script
prints an error about a missing file or a column it can't find, this is
the file to fix.

This version was rebuilt directly against your real files:
  - SAMPLE_primerx_daily_log.csv  (the actual PrimeRx "Daily Log Report" export)
  - PrimeRx_Patient_Tracker (gaby copy).xlsx  ("📋 Daily Log" tab, Excel Table
    named "DailyLogTable")
  - DailyLogAutomation Office Script.txt  (your old Office Script, used to
    cross-check column positions)
"""

from pathlib import Path

# =====================================================================
#  FOLDERS
# =====================================================================
# BASE_DIR is worked out automatically: it's the folder that CONTAINS the
# "scripts" folder this file lives in. So if config.py is at
#   <anywhere>\PharmacyLogDB\scripts\config.py
# then BASE_DIR is  <anywhere>\PharmacyLogDB  -- no matter where you copy
# the whole PharmacyLogDB folder or what it's called. Nothing to edit.
#
# Only override this if you deliberately keep the scripts somewhere other
# than a "scripts" subfolder of the data folder. To pin it to a fixed
# path instead, replace the line below with e.g.:
#   BASE_DIR = Path(r"C:\PharmacyLogDB")
BASE_DIR = Path(__file__).resolve().parent.parent

HISTORY_DIR = BASE_DIR / "history"     # current/old Excel tracker lives here
INBOX_DIR = BASE_DIR / "sample_data"      #TODO: switch back to inbox   # drop today's PrimeRx CSV export(s) here
ARCHIVE_DIR = BASE_DIR / "archive"     # processed CSVs are moved here automatically
SAMPLE_DIR = BASE_DIR / "sample_data"

DB_PATH = BASE_DIR / "pharmacy.db"                    # the database (back this up!)
EXPORT_CSV_PATH = BASE_DIR / "daily_log_export.csv"   # output of 3_export_for_powerbi.py

# =====================================================================
#  EXCEL BACKFILL SETTINGS  (only used by 1_backfill_from_excel.py)
# =====================================================================
EXCEL_FILE = SAMPLE_DIR / "SAMPLE_PrimeRx_Patient_Tracker.xlsx" #TODO: switch back to history
EXCEL_DAILY_LOG_SHEET = "📋 Daily Log"

# Your Daily Log tab is a real Excel Table (Insert > Table), named below.
# We read its column headers straight from the table definition — that's
# more reliable than guessing at header text — and use its column order
# to know which cell is which. If your real workbook's table has a
# different name, update it here (Excel: click any cell in the table,
# check the "Table Name" box on the Table Design ribbon tab).
EXCEL_TABLE_NAME = "DailyLogTable"

# Maps each table column header (lowercased, punctuation ignored) to a
# database field. Add an entry here if your real header text differs
# from what's listed (e.g. if a header is "Rx Number" instead of "RX #").
EXCEL_COLUMN_ALIASES = {
    "patientname": "patient",
    "patient": "patient",
    "rx": "rx_number",
    "rxnumber": "rx_number",
    "drug": "drug",
    "qty": "qty",
    "quantity": "qty",
    "doa": "doa",
    "insurancecarrier": "insurance_carrier",
    "prescriber": "prescriber",
    "officelocation": "office_location",
    "office": "office_location",
    "demo": "demo",
    "notes": "notes",
    "note": "notes",
}

# Your old Office Script inserts a row like "Log Date:6/17/26" every time
# the date changes, styled in blue/italic, to visually separate each
# day's batch (see DailyLogAutomation Office Script.txt). Those rows
# don't have their own Rx #, so the backfill script uses them to figure
# out which date each data row underneath belongs to. This is the text
# it looks for at the start of the "Patient Name" cell.
EXCEL_LOG_DATE_PREFIX = "log date"

# =====================================================================
#  CSV COLUMN MAPPING  (only used by 2_daily_import.py)
# =====================================================================
# The real PrimeRx "Daily Log Report" CSV export is NOT a simple table
# with one header row — every single line repeats the pharmacy's full
# letterhead and the report's column-title text, then the actual data
# for that one prescription. (Confirmed against your real
# SAMPLE_primerx_daily_log.csv — every one of its 19 rows has this exact
# layout, and the field positions match your old Office Script's
# COL_PATIENT / COL_RX / COL_DRUG / COL_QTY / COL_PRESCRIBER / COL_LOGDATE
# constants exactly.)
#
# Rather than counting columns from the start of the line (fragile if
# the letterhead ever changes), the import script looks for this marker
# text, which sits right before each row's real data:
#     *** Daily Log For : 8/25/2026 ***
CSV_DATA_MARKER = "daily log for"

# How many CSV fields after the marker field to skip before the real
# data starts (there's one blank field between the marker and Rx #).
CSV_MARKER_TO_DATA_OFFSET = 2

# The real data fields, in the exact order they appear after the marker.
# "_date_raw" and "_time_raw" get combined into date_time_filled.
# "_unused" is a spacer column PrimeRx always leaves blank.
CSV_FIELD_SEQUENCE = [
    "rx_number", "status", "ref", "_date_raw", "_time_raw",
    "patient", "address", "prescriber", "drug", "qty", "days",
    "_unused", "copay", "ins", "ph_tech",
]

# =====================================================================
#  DATABASE FIELDS
# =====================================================================
# AUTO_FIELDS are filled straight from the PrimeRx CSV every day.
# (status and ref are extra fields your real export includes beyond
# what the original setup guide listed — kept because the data's
# already there for free.)
AUTO_FIELDS = [
    ("rx_number",        "Rx #"),
    ("status",            "Status"),
    ("ref",                "Ref"),
    ("date_time_filled",    "Date/Time Filled"),
    ("patient",              "Patient"),
    ("address",                "Address"),
    ("prescriber",               "Prescriber"),
    ("drug",                       "Drug"),
    ("qty",                          "Qty"),
    ("days",                          "Days"),
    ("copay",                          "CoPay"),
    ("ins",                              "Ins"),
    ("ph_tech",                           "PH/Tech"),
]

# MANUAL_FIELDS start blank and are filled in later by your team in
# DB Browser for SQLite. The backfill script pulls these straight from
# the matching columns in the DailyLogTable Excel table.
MANUAL_FIELDS = [
    ("doa",               "DOA"),
    ("insurance_carrier",  "Insurance Carrier"),
    ("office_location",     "Office Location"),
    ("demo",                 "Demo"),
    ("notes",                 "Notes"),
]

ALL_FIELDS = AUTO_FIELDS + MANUAL_FIELDS
