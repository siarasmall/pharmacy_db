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
#  BACKFILL MAPPING  (only used by 1_backfill_from_excel.py)
# =====================================================================
# The one-time backfill combines TWO CSV exports of the OLD workbook:
#   - "📋 Daily Log" sheet  -> RX # and Notes for each prescription
#   - "💰 Billing" sheet    -> everything else (name, office, drug, qty,
#                              billing date, amount, payment, claim #,
#                              balance due)
# The two sheets are paired ROW BY ROW in file order: the Nth data row of
# the Daily Log is the same prescription as the Nth data row of Billing.
# Keep the two exports aligned. There is no shared key column between
# them, so if their row counts differ the script pairs the first N of
# each and warns.
BACKFILL_DAILY_LOG_FILE = SAMPLE_DIR / "PrimeRx_Patient_Tracker gaby copy.xlsx - 📋 Daily Log.csv"
BACKFILL_BILLING_FILE = SAMPLE_DIR / "PrimeRx_Patient_Tracker gaby copy.xlsx - 💰 Billing.csv"

# Daily Log: header text (normalized to letters+digits) -> db column.
# Only these are taken from that sheet; "rx" is also the de-dup key.
BACKFILL_DAILY_LOG_MAP = {
    "rx": "rx_number",
    "notes": "notes",
}

# A Daily Log row whose first cell (normalized) starts with this is a
# "Log Date:" separator, not data. Text after the first ":" dates the
# rows beneath it (the other half of the de-dup key).
BACKFILL_LOG_DATE_PREFIX = "log date"

# Billing: header text -> db column. Normalized keeping "$" so that
# "Payment Received" and "Payment Received $" stay distinct. Headers not
# listed here are ignored (Insurance Carrier, Date of Accident, Billing
# SENT are not in the model).
BACKFILL_BILLING_MAP = {
    "patientname": "name",
    "office": "office",
    "drug": "drug",
    "quantity": "quantity",
    "claimnumber": "expense_case_number",
    "datesenttobilling": "billing_date",
    "amountbilled$": "insurance_paid",
    "paymentreceived$": "payment_received",
    "balancedue$": "payment_due",
}

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

# MANUAL_FIELDS are everything the daily NF import does NOT fill. The
# backfill populates most of them from the Billing sheet; anything still
# blank is typed in later in DB Browser for SQLite.
MANUAL_FIELDS = [
    ("office",              "Office"),
    ("billing_date",         "Billing Date"),
    ("payment_received",      "Payment Received"),
    ("expense_case_number",    "Expense Case Number"),
    ("payment_due",             "Payment Due"),
    ("notes",                    "Notes"),
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
    ("notes",              "Notes"),
]

# Which of ALL_FIELDS are hand-entered (never written by the daily
# import; the backfill only fills them if it has a value and the cell is
# still blank).
MANUAL_FIELD_NAMES = {col for col, _ in MANUAL_FIELDS}
