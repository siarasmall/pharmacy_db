# NF Insurance Prescription Log — Setup Guide

This replaces the manual spreadsheet tracking of **NF (non-formulary) insurance**
prescriptions with a fast **local SQLite database** on one Windows PC. You export
the **NF Insurance report** from the pharmacy system as a CSV, load it with one
command, then fill in a few billing fields by hand.

Everything stays **100% on this computer**. Nothing syncs to the cloud, which is
the right call since there is **no Business Associate Agreement (BAA)** in place
for the PHI.

Built and tested against the real `NF Ins Test.csv` export, so the column mapping
already matches your file.

---

## What this does (the big picture)

```
NF Insurance CSV  ->  drop in "inbox"  ->  run 2_daily_import.py  ->  SQLite database
                                                                        |
   fill in Office / Billing Date / Payment Received / Expense Case #     |
                  / Discrepancy   <--  DB Browser for SQLite             |
                                                                        |
                             reports/dashboards  <--  Power BI or Excel
```

The database has **one table, `nf_insurance_log`**, with exactly **nine columns**:

| Column | Where it comes from |
|---|---|
| **Name** | the CSV — cell AJ (patient name) |
| **Office** | you type it in |
| **Drug** | the CSV — cell AK |
| **Quantity** | the CSV — cell AM |
| **Billing Date** | you type it in |
| **Insurance Paid** | the CSV — cell AR (amount) |
| **Payment Received** | you fill in later |
| **Expense Case Number** | you fill in later |
| **Discrepancy** | you fill in later |

Re-importing the same file is always safe: prescriptions already loaded are
skipped, and anything you typed in by hand is never overwritten.

---

## What's in this folder

| File | What it's for |
|---|---|
| `scripts/config.py` | The **only** file you normally edit (paths). |
| `scripts/2_daily_import.py` | Run to load an NF Insurance CSV export. |
| `scripts/3_export_for_powerbi.py` | Optional — dumps the 9 columns to a CSV for Power BI/Excel. |
| `scripts/pharmacy_common.py` | Shared engine — do **not** edit. |
| `scripts/1_backfill_from_excel.py` | Not used in this workflow (leftover from the old pipeline). |
| `sample_data/NF Ins Test.csv` | A sample export so you can practice safely first. |

---

## Part A — One-time setup

### Step 1 — Put the folder on the PC

Copy the whole `PharmacyLogDB` folder onto the C: drive, e.g. `C:\PharmacyLogDB\`.
The layout is:

```
C:\PharmacyLogDB\scripts     (the script files)
C:\PharmacyLogDB\inbox       (NF Insurance CSV exports go here)
C:\PharmacyLogDB\archive     (processed files land here automatically)
C:\PharmacyLogDB\sample_data (the practice CSV)
```

`config.py` figures out the base folder automatically from where `scripts` sits,
so it works no matter what drive or folder name you use — nothing to edit for
paths.

### Step 2 — Install Python

1. Go to **https://www.python.org/downloads/** → click **Download Python**.
2. Run the installer. **CHECK THE BOX "Add python.exe to PATH"** on the first
   screen, then **Install Now** → **Close**.

That's the only install. The scripts use built-in Python only — nothing else to
add.

### Step 3 — Practice on the sample

Before touching real data, prove it works. Out of the box, `config.py` reads from
the `sample_data` folder, so:

```
cd C:\PharmacyLogDB\scripts
python 2_daily_import.py
```

You should see **"Rows found: 53  new: 53"**. Run it again and it says
**"new: 0"** (nothing is imported twice). 🎉 The pipeline works.

### Step 4 — Point it at the real inbox

Open `C:\PharmacyLogDB\scripts\config.py` (right-click → **Edit with Notepad**).
Find this line near the top:

```python
INBOX_DIR = BASE_DIR / "sample_data"      #TODO: switch back to inbox
```

Change it to:

```python
INBOX_DIR = BASE_DIR / "inbox"
```

Save and close.

### Step 5 — Turn on disk encryption (BitLocker)

Because the database holds PHI, encrypt the drive:

1. **Start** → type **Manage BitLocker** → open it.
2. Next to **C:**, click **Turn on BitLocker** and follow the prompts.
3. Store the recovery key somewhere safe **off** this machine.
   *(BitLocker needs Windows Pro. On Home, use Settings → Privacy & security →
   Device encryption, or upgrade to Pro.)*

Setup done.

---

## Part B — The daily routine (about 30 seconds)

1. In the pharmacy system, pull the **NF Insurance report** and **export to CSV**.
2. Save that CSV into `C:\PharmacyLogDB\inbox`.
3. Run:
   ```
   cd C:\PharmacyLogDB\scripts
   python 2_daily_import.py
   ```
   It loads every CSV in the inbox, skips anything already imported, and moves
   files to `archive`.

> Want it hands-off? See Part E to schedule it.

---

## Part C — Filling in the manual fields

The import fills **Name / Drug / Quantity / Insurance Paid** from the CSV
(cells AJ / AK / AM / AR). The other five columns start blank for your team to
fill in: **Office, Billing Date, Payment Received, Expense Case Number,
Discrepancy.**

1. Install **DB Browser for SQLite** (free) from **https://sqlitebrowser.org**.
2. Open it → **Open Database** → pick `C:\PharmacyLogDB\pharmacy.db`.
3. Go to the **Browse Data** tab → choose the **nf_insurance_log** table.
4. Click a cell in **office / billing_date / payment_received /
   expense_case_number / discrepancy** and type.
5. Click **Write Changes** to save.

Because imports never overwrite existing rows, you can enrich a prescription
today and re-run imports tomorrow without losing your edits.

---

## Part D — Seeing the data in Power BI (or Excel)

1. Run:
   ```
   cd C:\PharmacyLogDB\scripts
   python 3_export_for_powerbi.py
   ```
   This creates `C:\PharmacyLogDB\nf_insurance_export.csv` with just the nine
   columns.
2. In **Power BI Desktop** (free from Microsoft Store): **Get Data → Text/CSV** →
   pick that file → **Load**. (Or in **Excel**: **Data → From Text/CSV**.) Re-run
   the export + **Refresh** whenever you want fresh numbers.

> Keep any report file on the local C: drive — do not save PHI into OneDrive.

---

## Part E (optional) — Run the import automatically

1. Create `run_daily.bat` in `C:\PharmacyLogDB\scripts` containing:
   ```
   cd C:\PharmacyLogDB\scripts
   python 2_daily_import.py
   ```
2. Open **Task Scheduler** → **Create Basic Task** → name it "NF Insurance
   Import" → **Daily** at a time after the export is saved → **Start a program**
   → browse to `run_daily.bat` → **Finish**.

---

## Backups (do this weekly)

The entire database is one file: `C:\PharmacyLogDB\pharmacy.db`.
Copy it to an **encrypted USB drive** once a week. Keep backups local and
encrypted — never cloud-sync PHI.

---

## Troubleshooting

| Message | Fix |
|---|---|
| `'python' is not recognized` | Re-run the Python installer and check **Add python.exe to PATH**. |
| `No new CSV files found` | The inbox is empty — normal until you drop today's export in. It also prints which folder it checked. |
| `No prescription rows detected` | The CSV isn't the NF Insurance report format (no `Ins.Code:` marker), or it's empty. Re-export the report. |
| `could not find the database` (export step) | Run `2_daily_import.py` at least once first. |
| Fewer rows imported than expected | Lines with a blank Rx number (e.g. a totals row) are skipped on purpose. |

---

## Quick reference

- **Database (back this up):** `C:\PharmacyLogDB\pharmacy.db`
- **Table:** `nf_insurance_log` (9 columns)
- **Unique key:** Rx # + fill date (prevents duplicates; both are hidden helper columns)
- **Scripts:** `C:\PharmacyLogDB\scripts`
- **Daily command:** `python 2_daily_import.py`
