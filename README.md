# NF Insurance Prescription Log

A small, self-contained pipeline that turns the pharmacy's **NF Insurance
report** CSV export into a fast **local SQLite database**, then lets the team
fill in a few billing/tracking fields by hand.

**Everything stays on one computer.** Nothing syncs to the cloud. That is
deliberate: the data is PHI and there is **no Business Associate Agreement
(BAA)** in place, so cloud storage is off the table.

---

## The big picture

```
NF Insurance CSV  ->  drop in "inbox/"  ->  run 2_daily_import.py  ->  pharmacy.db (SQLite)
                                                                          |
       fill in Office / Billing Date / Payment Received /   <--  DB Browser for SQLite
                Expense Case Number / Payment Due
                                                                          |
                            reports / dashboards  <--  Power BI or Excel (3_export_for_powerbi.py)
```

Re-importing the same file is always safe: prescriptions already in the database
are skipped, and hand-entered values are never overwritten.

---

## Data model

One table, **`nf_insurance_log`**, created automatically on first run. Every
column is stored as `TEXT`. These are the **only** columns the database holds,
in this display order:

Each column is filled by the **daily import** (NF Insurance CSV), the **one-time
backfill** (a single CSV export of the old workbook's "Daily Log" sheet, which
now carries the billing columns too), or **by hand** later.

| # | Column | Label | Daily import | Backfill CSV header |
|---|---|---|---|---|
| 1 | `name` | Name | NF CSV cell **AJ** | Name |
| 2 | `office` | Office | — | Office |
| 3 | `drug` | Drug | NF CSV cell **AK** | Drug |
| 4 | `quantity` | Quantity | NF CSV cell **AM** | Qty |
| 5 | `billing_date` | Billing Date | — | Date Billing |
| 6 | `insurance_paid` | Insurance Paid | NF CSV cell **AR** (text, e.g. `1,892.20`) | Amount Billed |
| 7 | `payment_received` | Payment Received | — | Payment Received $ |
| 8 | `expense_case_number` | Expense Case Number | — | — (Claim Number not mapped; hand-entered later) |
| 9 | `payment_due` | Payment Due | **derived** | **derived** |
| 10 | `notes` | Notes | — | Notes |

A `—` means that source leaves the column blank; anything still blank after both
runs is typed in later in DB Browser. The backfill also reads **RX Number** and
**Filled Date** into the hidden de-dup key; if a backfill row has no RX Number it
gets a content-hash key instead (see below) so it isn't lost.

**`payment_due` is a derived column — don't hand-edit it.** It always equals
`insurance_paid − payment_received`, formatted to 2 decimals. `read_backfill_csv()`
computes it at load time, and two SQLite triggers keep it current: one fills it
on insert, the other recomputes it whenever `insurance_paid` or `payment_received`
changes — no matter what makes the change (a script, DB Browser, plain SQL). The
"Balance Due" column in the backfill file is ignored.

### Hidden bookkeeping columns

The table also carries four columns that are **not** part of the model and are
not exported: `id` (primary key), `rx_number` and `filled_date` (together the
de-duplication key — two rows can otherwise look identical but be distinct
prescriptions), and `source_file` / `imported_at` (provenance). The unique
constraint is `UNIQUE(rx_number, filled_date)`.

The daily import always has a real `rx_number` + `filled_date` (NF report cells
AG / AL), so re-running it is idempotent. The backfill file's **RX Number** is
*not* guaranteed — when it's missing, `read_backfill_csv()` fills `rx_number`
with `BF-<hash>` derived from `config.BACKFILL_HASH_FIELDS` (name, drug,
quantity, billing date, amount, notes). That keeps distinct prescriptions in
distinct rows and keeps a backfill re-run idempotent; the only rows that merge
are ones identical across every hashed field.

The column list lives in [`config.py`](PharmacyLogDB 2/scripts/config.py) as
`ALL_FIELDS` (display order + schema), with `CSV_FIELDS` (what the daily import
writes) and `MANUAL_FIELDS` (everything else) splitting it. Edit `ALL_FIELDS` to
add, remove, rename, or re-order what the database holds — every script follows
it. `ensure_schema()` **adds** any new `ALL_FIELDS` column to an existing
`pharmacy.db` on the next run; SQLite can't drop or rename, so a removed/renamed
column just lingers unused (or delete `pharmacy.db` and reload for a clean
table).

---

## Input format: the NF Insurance report CSV

The export is **not** a plain table. Every data line repeats the report
letterhead, then an `Ins.Code:` marker, then that one prescription's data, then
the report's running totals. Example (one line, trimmed):

```
... letterhead ... ,Ins.Code:,NF,Ins.Name:,NF,NF,12345,61623,0,B,"SMITH, JOHN",DICLOFENAC SODIUM 3% GEL ,8/28/2026,200,30, ... totals ...
```

The importer finds the `Ins.Code:` marker on each line and reads a fixed
sequence of fields after it (configured by `CSV_DATA_MARKER`,
`CSV_MARKER_TO_DATA_OFFSET`, and `CSV_FIELD_SEQUENCE` in `config.py`):

| Offset from marker | Report cell | Field | Used as |
|---|---|---|---|
| +6 | AG | Rx number | de-dup key (hidden) |
| +9 | AJ | patient name | `name` |
| +10 | AK | drug | `drug` |
| +11 | AL | fill date | de-dup key (hidden) |
| +12 | AM | quantity | `quantity` |
| +17 | AR | amount | `insurance_paid` |

Lines without the marker (or without an Rx number — e.g. a totals-only row) are
skipped. Because the parser keys off the marker rather than counting from the
start of the line, extra letterhead columns don't break it.

---

## Repository layout

```
pharmacy_db/
├── README.md                     <- this file
├── START_HERE_Setup_Guide.md     <- step-by-step Windows setup for non-technical staff
└── PharmacyLogDB 2/              <- the project folder (this is "BASE_DIR")
    ├── START_HERE_Setup_Guide.md
    ├── scripts/
    │   ├── config.py                 <- the only file you normally edit
    │   ├── pharmacy_common.py        <- shared engine — do not edit
    │   ├── 1_backfill_from_excel.py  <- run ONCE to load history from the old "Daily Log" sheet CSV
    │   ├── 2_daily_import.py         <- run to load NF Insurance CSV exports
    │   └── 3_export_for_powerbi.py   <- optional — dump the 10 columns to a flat CSV
    ├── inbox/           <- drop NF Insurance CSV export(s) here
    ├── archive/         <- processed CSVs are moved here automatically, timestamped
    ├── sample_data/     <- "NF Ins Test.csv" (daily import) + "…Daily Log.csv" (backfill)
    ├── pharmacy.db      <- the SQLite database — THIS is what you back up (created on first run)
    └── nf_insurance_export.csv  <- output of 3_export_for_powerbi.py (regenerated on demand)
```

> **`BASE_DIR` is auto-detected.** `config.py` sets it to the parent of its own
> `scripts/` folder, so the whole `PharmacyLogDB` folder can be copied anywhere,
> on any drive, under any name, and every path still resolves. On the pharmacy
> PC the folder lives at `C:\PharmacyLogDB\`; in this repo it is
> `PharmacyLogDB 2/`.

---

## Component reference

### `scripts/config.py` — the settings file

The one file you normally touch:

- **Folders** — `BASE_DIR` (auto-detected) plus derived `INBOX_DIR`,
  `ARCHIVE_DIR`, `SAMPLE_DIR`, `DB_PATH`, `EXPORT_CSV_PATH`.
- **CSV column mapping** (daily import) — `CSV_DATA_MARKER` (`ins.code`),
  `CSV_MARKER_TO_DATA_OFFSET` (`6`), and `CSV_FIELD_SEQUENCE` (the field order
  after the offset; `_`-prefixed names are read for positioning then dropped).
  `name` / `drug` / `quantity` / `insurance_paid` map to report cells
  AJ / AK / AM / AR.
- **Backfill mapping** (one-time) — `BACKFILL_FILE` (the single "Daily Log" sheet
  CSV), `BACKFILL_COLUMN_MAP` (header text → db column, normalized keeping `$`
  so `Payment Received` ≠ `Payment Received $`; unlisted headers such as `Claim
  Number` are dropped; `RX Number` / `Filled Date` → the hidden de-dup key), and
  `BACKFILL_HASH_FIELDS` (which columns form the fallback key when a row has no
  RX Number).
- **Database model** — `TABLE_NAME`, `CSV_FIELDS` (imported), `MANUAL_FIELDS`
  (hand-entered), `ALL_FIELDS` (display/schema order — **the source of truth for
  what the DB holds**), `MANUAL_FIELD_NAMES`.

> **Current state / TODO.** In this repo `INBOX_DIR` is temporarily set to
> `sample_data/` (marked `#TODO: switch back to inbox`) so the sample file is
> picked up for testing. On the real machine, revert it to
> `INBOX_DIR = BASE_DIR / "inbox"`.

### `scripts/pharmacy_common.py` — the shared engine

Not meant to be edited. Provides:

- `_normalize()` — lowercases and strips non-alphanumerics so `Ins.Code:` /
  `ins code` / `INSCODE` all match.
- `get_connection()` — creates `BASE_DIR` if missing, opens `pharmacy.db`.
- `ensure_schema()` — creates `nf_insurance_log` from `config.ALL_FIELDS` (in
  order; every column defaults to `''` so a field an import doesn't supply reads
  as blank, not NULL) plus the hidden bookkeeping columns and the
  `UNIQUE(rx_number, filled_date)` constraint. On an existing table it also
  `ALTER TABLE ... ADD COLUMN`s any `ALL_FIELDS` column that's missing, so
  growing the model doesn't need a manual rebuild. Then it (re)installs the two
  `payment_due` triggers (`_payment_due_ai` on insert, `_payment_due_au` on
  update of `insurance_paid` / `payment_received`) and back-fills `payment_due`
  for any pre-existing rows that were blank.
- `extract_date_key()` — normalizes a date string to `YYYY-MM-DD` for a stable
  de-dup key; falls back to raw text on an unknown format so nothing is dropped.
- `read_nf_ins_csv()` — parses the **daily** NF Insurance export: finds the
  `Ins.Code:` marker on each line, reads `CSV_FIELD_SEQUENCE`
  (name/drug/quantity/insurance_paid from cells AJ/AK/AM/AR), strips whitespace,
  normalizes the fill date. Returns one dict per prescription.
- `insert_from_csv()` — `INSERT OR IGNORE` of the daily import's columns plus the
  de-dup key. Manual fields are never written, so hand-typed values survive every
  re-import. Returns the count of genuinely new rows.
- `read_backfill_csv()` — the **one-time** backfill reader. Reads the single
  "Daily Log" sheet CSV as a flat table: finds the header row via
  `BACKFILL_COLUMN_MAP`, returns one dict per data row with the mapped model
  columns plus `rx_number` / `filled_date` for the de-dup key. Treats literal
  `NULL` / `N/A` cells as blank, cleans numbers (`$3,779.40` → `3779.4`),
  normalizes `filled_date` to `YYYY-MM-DD`, computes `payment_due` when blank,
  drops unmapped headers (`Claim Number`, `Balance Due`). `_synthetic_rx()`
  supplies a `BF-<hash>` `rx_number` (from `BACKFILL_HASH_FIELDS`) for any row
  with no real RX Number, so it isn't collapsed into another keyless row.
- `insert_backfill()` — inserts historical rows (all model columns); on a row
  that already exists (same `rx_number` + `filled_date`) it fills only the
  columns that are still blank, so daily-import data and hand edits are never
  overwritten. Returns `(new_rows, existing_rows_filled)`.

### `scripts/2_daily_import.py` — the import job

Standard library only. Ensures `inbox/` and `archive/` exist, processes every
`*.csv` in `inbox/` via `read_nf_ins_csv()` + `insert_from_csv()`, then moves
each processed file to `archive/` as `<name>_<YYYYMMDD_HHMMSS>.csv`. Files that
fail to parse are left in `inbox/` with a message. Prints per-file
`Rows found / new` counts.

### `scripts/3_export_for_powerbi.py` — flat CSV export

Optional. Dumps **only the ten model columns**, in `ALL_FIELDS` order, with
human-readable headers and a UTF-8 BOM (so Excel opens it cleanly), ordered by
fill date then Rx number, to `nf_insurance_export.csv`. Re-run any time; hit
**Refresh** in Power BI / Excel. Errors out if the database doesn't exist yet.

### `scripts/1_backfill_from_excel.py` — one-time history load

Run **once**, before daily imports start. Reads the single `BACKFILL_FILE` (a CSV
export of the old workbook's "Daily Log" sheet, which now also carries the
billing columns) via `read_backfill_csv()` + `insert_backfill()`. Maps
**Name → name, Office → office, Drug → drug, Qty → quantity, Date Billing →
billing_date, Amount Billed → insurance_paid, Payment Received $ →
payment_received, Notes → notes**, with **RX Number** and **Filled Date** as the
hidden de-dup key. **Claim Number** and **Balance Due** are not mapped —
`expense_case_number` stays blank for hand entry, and `payment_due` is derived
(`insurance_paid − payment_received`).

Prints `Rows found / new / blank fields filled on existing rows`. Rows with no
RX Number are keyed by a content hash (`BACKFILL_HASH_FIELDS`) so they still
land; the script reports how many, and only rows identical across every hashed
field are treated as one. Standard library only (the filename still says "excel";
the input is the sheet's CSV export).

### Folders

| Folder | Role |
|---|---|
| `inbox/` | Drop each NF Insurance CSV export here. Read by the import. |
| `archive/` | Where processed CSVs are moved automatically, timestamped. Nothing reads from here. |
| `sample_data/` | `NF Ins Test.csv` — a sample daily export (53 rows). `…Daily Log.csv` — a sample backfill file. |

### Generated files

| File | What it is |
|---|---|
| `pharmacy.db` | The SQLite database. The whole dataset is this one file — **this is what you back up.** |
| `nf_insurance_export.csv` | Rebuilt each time you run script 3. Safe to delete. |

---

## Requirements

- **Python 3.9+** (any recent 3.x). On Windows, tick *"Add python.exe to PATH"*
  in the installer.
- **No third-party packages.** The import and export use the standard library
  only.
- **DB Browser for SQLite** (free, <https://sqlitebrowser.org>) — for
  hand-editing the manual fields.
- **Power BI Desktop** or **Excel** — optional, for reporting.

---

## Running the project

`./run_all.sh` at the repo root runs the backfill then the daily import in one
go (works from any directory; a backfill failure is reported but doesn't stop
the import). The individual steps below are run from the `scripts/` folder.

### Practice on the sample first

The sample lives in `sample_data/`, and (per the TODO above) `INBOX_DIR` is
currently pointed there, so:

```
cd "PharmacyLogDB 2/scripts"          # on the pharmacy PC:  cd C:\PharmacyLogDB\scripts
python 2_daily_import.py
```

You should see `Rows found: 53  new: 53` and the file move to `archive/`. Run it
again — the re-imported copy reports `new: 0`.

### One-time: backfill history

Export the old workbook's **"Daily Log"** sheet (the one that now carries the
billing columns and an `RX Number` / `Filled Date` column) to a single CSV, point
`BACKFILL_FILE` in `config.py` at it, then:

```
python 1_backfill_from_excel.py
```

Run this **once, before** you start daily imports. Safe to re-run — existing rows
are only topped up in their blank columns. Rows without an `RX Number` are kept
(keyed by content); if the "keyed by content" count looks high and two real
prescriptions look merged, add `RX Number`s to those rows and re-run.

### Daily routine (~30 seconds)

1. Pull the **NF Insurance report** and **export to CSV**.
2. Save that CSV into `inbox/` (after reverting the `INBOX_DIR` TODO).
3. Run:
   ```
   python 2_daily_import.py
   ```
   It loads every CSV in `inbox/`, skips anything already imported, and moves
   files to `archive/`.

### Filling in the manual fields

1. Open **DB Browser for SQLite** → *Open Database* → `pharmacy.db`.
2. *Browse Data* tab → `nf_insurance_log` table.
3. Click a cell in `office` / `billing_date` / `payment_received` /
   `expense_case_number` / `notes` and type. (Leave `payment_due` alone — it
   recomputes itself from `insurance_paid − payment_received`.)
4. **Write Changes** to save. Future imports never overwrite these.

### Reporting

```
python 3_export_for_powerbi.py
```

Then in Power BI Desktop: **Get Data → Text/CSV** → pick `nf_insurance_export.csv`
→ **Load**. (Or Excel: **Data → From Text/CSV**.) Re-run the export and hit
**Refresh** for fresh numbers. Keep the file on the local drive — never in
OneDrive.

### Automating the import (optional, Windows)

Create `run_daily.bat` in `scripts/`:

```
cd C:\PharmacyLogDB\scripts
python 2_daily_import.py
```

Then **Task Scheduler → Create Basic Task → Daily**, *Start a program* →
`run_daily.bat`.

---

## Safety properties

- **Idempotent imports.** `UNIQUE(rx_number, filled_date)` + `INSERT OR IGNORE`
  means re-running the daily import is a no-op for rows that already exist. The
  backfill is idempotent too — rows without an RX Number get a content-hash key
  so a re-run merges instead of duplicating.
- **Manual edits are protected.** The daily import never writes the hand-entered
  columns; the backfill only fills ones that are still blank.
- **`payment_due` stays honest.** SQLite triggers recompute it from
  `insurance_paid − payment_received` on every relevant insert/update, so it
  can't drift out of sync with the numbers it's derived from.
- **Nothing is silently dropped.** Unparseable dates fall back to raw text; lines
  without the `Ins.Code:` marker or an Rx number are skipped; CSV files that fail
  to parse stay in `inbox/` with an error message.
- **Local only.** No network calls anywhere in the codebase.

## Backups & encryption

- Back up **`pharmacy.db`** weekly to an **encrypted USB drive**. That one file
  is the whole dataset.
- On the pharmacy PC, turn on **BitLocker** (or Device Encryption on Windows
  Home) for the drive holding the database. Store the recovery key off the
  machine.
- Never cloud-sync `pharmacy.db`, the export CSV, or any report built from them.

---

## Troubleshooting

| Message | Fix |
|---|---|
| `'python' is not recognized` | Re-run the Python installer and tick *Add python.exe to PATH*. |
| `No new CSV files found` | The folder `INBOX_DIR` points at is empty. Normal until you drop today's export in. |
| `No prescription rows detected` | The CSV isn't the NF Insurance report format (no `Ins.Code:` marker), or it's empty. Re-export the report. |
| `could not find the database at …` (export) | Run `2_daily_import.py` at least once first. |
| Import found fewer rows than expected | Check that the export wasn't filtered; lines with a blank Rx number are skipped by design. |

---

## Quick reference

- **Database (back this up):** `PharmacyLogDB 2/pharmacy.db`
- **Table:** `nf_insurance_log` — **10 columns**, unique key `rx_number` + `filled_date`
- **Load data:** `python 2_daily_import.py`
- **Export:** `python 3_export_for_powerbi.py`
- **Edit manual fields:** DB Browser for SQLite → `nf_insurance_log`
