# Pharmacy Daily Log Database — Setup Guide

This replaces the slow, giant Excel tracker with a fast **local SQLite database**
on one Windows PC. It keeps the pharmacy's exact workflow — pull the PrimeRx
"Daily Log Report" CSV, load it, then fill in the extra tracking fields — but the
data now lives in a real database instead of a spreadsheet that keeps growing.

Everything stays **100% on this computer**. Nothing syncs to the cloud, which is the
right call since there is **no Business Associate Agreement (BAA)** in place for the PHI.

Built and tested against your real `8.25.26.csv` export and your `PrimeRx_Patient_Tracker`
workbook, so the column mapping already matches your files.

---

## What this does (the big picture)

**Old way:** PrimeRx CSV → paste into *RawImport* → run Office Script → rows land in the *Daily Log* sheet → keep typing in DOA / Insurance / Office / Demo / Notes.

**New way:**
```
PrimeRx CSV  ->  drop in "inbox"  ->  run 2_daily_import.py  ->  SQLite database
                                                                  |
   fill in DOA / Insurance / Office / Demo / Notes  <-- DB Browser for SQLite
                                                                  |
                             reports/dashboards  <-- Power BI or Excel
```

The database has **one table, `daily_log`**, with two kinds of columns:
- **Auto fields** — filled straight from the PrimeRx CSV (Rx #, Date/Time Filled, Patient, Address, Prescriber, Drug, Qty, Days, Status, CoPay, Ins, PH/Tech). These use the *same column positions your old Office Script used*.
- **Manual fields** — start blank, your team fills them in later: **DOA (Date of Accident), Insurance Carrier, Office Location, Demo, Notes.**

Re-importing the same file is always safe: existing prescriptions are skipped and your manual edits are never overwritten.

---

## What's in this folder

| File | What it's for |
|---|---|
| `config.py` | The **only** file you normally edit (paths). |
| `1_backfill_from_excel.py` | Run **once** to load all history from the current Excel tracker. |
| `2_daily_import.py` | Run **daily** to load the new PrimeRx CSV(s). |
| `3_export_for_powerbi.py` | Optional — dumps everything to a CSV for Power BI/Excel. |
| `pharmacy_common.py` | Shared engine (do **not** edit). |
| `sample_data/` | A sanitized sample CSV so you can practice safely first. |

---

## Part A — One-time setup

### Step 1 — Create the folders
In **File Explorer**, make this exact layout on the C: drive:

```
C:\PharmacyLogDB\
C:\PharmacyLogDB\history      (put the current Excel tracker here)
C:\PharmacyLogDB\inbox        (daily PrimeRx CSV exports go here)
C:\PharmacyLogDB\archive      (processed files land here automatically)
C:\PharmacyLogDB\scripts      (put the 5 script files here)
```

Copy the five files (`config.py`, `pharmacy_common.py`, `1_backfill_from_excel.py`,
`2_daily_import.py`, `3_export_for_powerbi.py`) into `C:\PharmacyLogDB\scripts`.

Copy their current workbook into `C:\PharmacyLogDB\history\` and rename it to
`PrimeRx_Patient_Tracker.xlsx` (or update the name in `config.py`).

### Step 2 — Install Python
1. Go to **https://www.python.org/downloads/** → click **Download Python**.
2. Run the installer. **CHECK THE BOX "Add python.exe to PATH"** on the first screen, then **Install Now**.
3. Click **Close** when done.

### Step 3 — Install the one add-on the backfill needs
1. Press **Windows key**, type **cmd**, open **Command Prompt**.
2. Run:
   ```
   pip install openpyxl
   ```
   (The daily import uses only built-in Python, so this is the only install. Needs internet once.)

### Step 4 — Check config.py
Open `C:\PharmacyLogDB\scripts\config.py` (right-click → **Edit with Notepad**). The defaults
already match the folders above. Just confirm:
- `EXCEL_FILE` points at your workbook in the `history` folder.
- `EXCEL_DAILY_LOG_SHEET` matches the tab name exactly (it's preset to the "📋 Daily Log" tab).

Save and close.

### Step 5 — Practice on the sample first (recommended)
Before touching real data, prove it works:
1. Copy `sample_data\SAMPLE_primerx_daily_log.csv` into `C:\PharmacyLogDB\inbox`.
2. In Command Prompt:
   ```
   cd C:\PharmacyLogDB\scripts
   python 2_daily_import.py
   ```
   You should see **"Rows found: 19  new: 19"**. 🎉 The pipeline works.

### Step 6 — Load the real history (run the backfill ONCE)
```
cd C:\PharmacyLogDB\scripts
python 1_backfill_from_excel.py
```
It reads the *Daily Log* tab, skips the banner/date separator rows, and imports every
historical prescription **with the manual fields your team already filled in**.

### Step 7 — Turn on disk encryption (BitLocker)
Because the database holds PHI, encrypt the drive:
1. **Start** → type **Manage BitLocker** → open it.
2. Next to **C:**, click **Turn on BitLocker** and follow the prompts.
3. Store the recovery key somewhere safe **off** this machine.
   *(BitLocker needs Windows Pro. On Home, use Settings → Privacy & security → Device encryption, or upgrade to Pro.)*

Setup done.

---

## Part B — The daily routine (about 30 seconds)

1. In PrimeRx, pull the **Daily Log Report** and **export to CSV** (same report you use today).
2. Save that CSV into `C:\PharmacyLogDB\inbox`.
3. Run:
   ```
   cd C:\PharmacyLogDB\scripts
   python 2_daily_import.py
   ```
   It loads every CSV in the inbox, skips anything already imported, and moves files to `archive`.

> Want it hands-off? See Part E to schedule it.

---

## Part C — Filling in the manual fields (DOA, Insurance, Office, Demo, Notes)

The daily import fills the PrimeRx columns automatically and leaves the five manual
fields blank — just like the blank cells your team fills in today. To fill them in
with a friendly, spreadsheet-like editor:

1. Install **DB Browser for SQLite** (free) from **https://sqlitebrowser.org**.
2. Open it → **Open Database** → pick `C:\PharmacyLogDB\pharmacy.db`.
3. Go to the **Browse Data** tab → choose the **daily_log** table.
4. Click a cell in **doa / insurance_carrier / office_location / demo / notes** and type.
5. Click **Write Changes** to save.

Because imports never overwrite existing rows, you can enrich a prescription today and
re-run imports tomorrow without losing your edits.

---

## Part D — Seeing the data in Power BI (or Excel)

**Easiest (no database driver needed):**
1. Run:
   ```
   cd C:\PharmacyLogDB\scripts
   python 3_export_for_powerbi.py
   ```
   This creates `C:\PharmacyLogDB\daily_log_export.csv`.
2. In **Power BI Desktop** (free from Microsoft Store): **Get Data → Text/CSV** → pick that file → **Load**.
   (Or in **Excel**: **Data → From Text/CSV**.) Re-run the export + **Refresh** whenever you want fresh numbers.

**Live connection (optional, more advanced):** install the free **SQLite ODBC driver**, add a
System DSN pointing at `pharmacy.db`, then in Power BI use **Get Data → ODBC**.

> Keep any report file on the local C: drive — do not save PHI into OneDrive.

---

## Part E (optional) — Run the daily import automatically

1. Create `run_daily.bat` in `C:\PharmacyLogDB\scripts` containing:
   ```
   cd C:\PharmacyLogDB\scripts
   python 2_daily_import.py
   ```
2. Open **Task Scheduler** → **Create Basic Task** → name it "Pharmacy Daily Import" →
   **Daily** at a time after the export is saved → **Start a program** → browse to `run_daily.bat` → **Finish**.

---

## Backups (do this weekly)

The entire database is one file: `C:\PharmacyLogDB\pharmacy.db`.
Copy it to an **encrypted USB drive** once a week. Keep backups local and encrypted —
never cloud-sync PHI.

---

## Troubleshooting

| Message | Fix |
|---|---|
| `'python' is not recognized` | Re-run the Python installer and check **Add python.exe to PATH**. |
| `Missing 'openpyxl'` | Run `pip install openpyxl` in Command Prompt. |
| `could not find the Excel file` | Fix the `EXCEL_FILE` path in `config.py`. |
| `could not find a tab named ...` | The `EXCEL_DAILY_LOG_SHEET` name must match the tab exactly (it prints the tabs it found). |
| Daily import says "No prescription rows detected" | The CSV isn't the PrimeRx Daily Log Report format, or it's empty. Re-export from PrimeRx. |
| "No new CSV files found" | The inbox is empty — normal until you drop today's export in. |

---

## Quick reference

- **Database (back this up):** `C:\PharmacyLogDB\pharmacy.db`
- **Table:** `daily_log`
- **Unique key:** Rx # + Date Filled (prevents duplicates)
- **Scripts:** `C:\PharmacyLogDB\scripts`
- **Daily command:** `python 2_daily_import.py`
