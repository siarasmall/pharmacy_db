"""
config.py — the ONE file you normally need to edit.

Everything the scripts need to know about your folder layout and how the
"NF Insurance" report export lines up with the database lives here. If a
script prints an error about a missing file or a column it can't find,
this is the file to fix.

This version is built against the real NF-insurance export:
  - "NF Ins Test.csv" in sample_data/  (every row is one non-formulary
    prescription, prefixed by an "Ins.Code:" marker)
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

INBOX_DIR = BASE_DIR / "sample_data"      #TODO: switch back to inbox   # drop today's NF Insurance CSV export(s) here
ARCHIVE_DIR = BASE_DIR / "archive"     # processed CSVs are moved here automatically
SAMPLE_DIR = BASE_DIR / "sample_data"

DB_PATH = BASE_DIR / "pharmacy.db"                    # the database (back this up!)
EXPORT_CSV_PATH = BASE_DIR / "nf_insurance_export.csv"   # output of 3_export_for_powerbi.py

# =====================================================================
#  CSV COLUMN MAPPING  (used by 2_daily_import.py)
# =====================================================================
# The NF Insurance export is NOT a simple table with one header row.
# Every data line starts with the pharmacy's report letterhead, then an
# "Ins.Code:" marker, then that one prescription's data, then the
# report's running totals. (Confirmed against "NF Ins Test.csv": all 53
# rows share this exact layout.)
#
# Rather than counting columns from the start of the line (fragile if the
# letterhead ever changes width), the import script finds this marker
# text and reads a fixed sequence of fields that follows it:
#     Ins.Code:
CSV_DATA_MARKER = "ins.code"

# How many CSV fields after the marker field to skip before the real
# data starts. Layout after the marker cell (with the real report's
# spreadsheet column letters — the marker sits at column AA):
#   +0  AA  "Ins.Code:"    +1 AB NF     +2 AC "Ins.Name:"  +3 AD NF  +4 AE NF
#   +5  AF  store id       +6 AG Rx#    +7 AH refills       +8 AI status
#   +9  AJ  patient name  +10 AK drug  +11 AL fill date   +12 AM quantity
#  +13  AN  days          +14 AO --    +15 AP amount billed
#  +16  AQ  insurer paid $ +17 AR amount   <- this is "Insurance Paid"
CSV_MARKER_TO_DATA_OFFSET = 6

# The data fields, in the exact order they appear starting at the offset
# above. Names starting with "_" are read for positioning but dropped.
#   name           -> spreadsheet cell AJ in the full report
#   drug           -> cell AK
#   quantity       -> cell AM
#   insurance_paid -> cell AR
# "rx_number" and "filled_date" are NOT displayed columns — they're kept
# only as the de-duplication key so re-importing a file is always safe
# (two otherwise-identical rows can still be distinct prescriptions).
CSV_FIELD_SEQUENCE = [
    "rx_number", "_refills", "_status",
    "name", "drug", "filled_date", "quantity",
    "_days", "_unused", "_amount_billed", "_insurer_paid", "insurance_paid",
]

# =====================================================================
#  BACKFILL CSV MAPPING  (only used by 1_backfill_from_excel.py)
# =====================================================================
# The one-time backfill source is a CSV export of the OLD Excel tracker's
# "📋 Daily Log" sheet. It is a plain-ish table, not the marker format
# above. Layout:
#     row: "⬇ PRIME RX DAILY LOG ..."          <- banner, ignored
#     row: "Log Date:6/17/26 , ... "            <- separator; the date for
#                                                  the data rows below it
#     row: "Patient Name,RX #,Drug,Qty,DOA,..." <- header row
#     row: "SMITH, JOHN,6154,LIDOCAINE ...,..." <- one prescription
#     (repeat the Log Date / header / data block down the sheet)
# Stray rows that only have a Notes cell (no RX #) are ignored.
BACKFILL_FILE = SAMPLE_DIR / "PrimeRx_Patient_Tracker gaby copy.xlsx - 📋 Daily Log.csv"

# Header text (normalized: lowercased, only letters+digits) -> database
# column. Headers not listed here are dropped, so only the columns that
# exist in the current model are backfilled. "rx" and the "Log Date:"
# value become the hidden de-dup key (rx_number + filled_date).
BACKFILL_COLUMN_MAP = {
    "patientname": "name",
    "rx": "rx_number",
    "drug": "drug",
    "qty": "quantity",
    "officelocation": "office",
}

# A row whose first cell (normalized) starts with this is a "Log Date:"
# separator, not data. The text after the first ":" is the fill date for
# the rows that follow it.
BACKFILL_LOG_DATE_PREFIX = "log date"

# =====================================================================
#  DATABASE MODEL
# =====================================================================
# The table name.
TABLE_NAME = "nf_insurance_log"

# CSV_FIELDS are filled straight from the NF Insurance CSV on every
# import (name / drug / quantity / insurance_paid, read from cells
# AJ / AK / AM / AR respectively).
CSV_FIELDS = [
    ("name",           "Name"),
    ("drug",           "Drug"),
    ("quantity",       "Quantity"),
    ("insurance_paid", "Insurance Paid"),
]

# MANUAL_FIELDS start blank and are filled in later by your team in
# DB Browser for SQLite.
MANUAL_FIELDS = [
    ("office",              "Office"),
    ("billing_date",         "Billing Date"),
    ("payment_received",      "Payment Received"),
    ("expense_case_number",    "Expense Case Number"),
    ("payment_due",             "Payment Due"),
]

# ALL_FIELDS is the exact column order the table is created in and the
# order the export CSV is written in. Change this list to add, remove,
# rename, or re-order what the database holds.
ALL_FIELDS = [
    ("name",               "Name"),
    ("office",              "Office"),
    ("drug",               "Drug"),
    ("quantity",           "Quantity"),
    ("billing_date",       "Billing Date"),
    ("insurance_paid",     "Insurance Paid"),
    ("payment_received",   "Payment Received"),
    ("expense_case_number", "Expense Case Number"),
    ("payment_due",        "Payment Due"),
]

# Which of ALL_FIELDS are hand-entered (never written by the daily
# import; the backfill only fills them if it has a value and the cell is
# still blank).
MANUAL_FIELD_NAMES = {col for col, _ in MANUAL_FIELDS}
