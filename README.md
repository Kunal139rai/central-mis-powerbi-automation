# Central MIS & Power BI Automation Suite

An enterprise-grade Central Management Information System (MIS) and Executive Control Room application developed specifically to satisfy the architecture, operational workflows, and dashboard requirements defined in:
1. `Managing_Director_Central_MIS_PowerBI_Proposal.pptx`
2. `Organization_Automation_PowerBI_MIS_Plan_Updated_Director_Dashboard.docx`

---

## 🎯 Key Capabilities

### 1. One Central View (Slide 1 & Section 18)
Answers the Managing Director's 10 core questions in real time:
- Overall company operational health (`Green`, `Amber`, `Red`).
- Current billed revenue, operating expenses, and net profit margins.
- Active, completed, delayed, and at-risk project delivery.
- CRM sales pipeline, lead conversion, and rep performance.
- Overdue accounts receivable aging (0-30, 31-60, 60+ days).
- Workforce attendance, headcount, and payroll.
- Daily operational productivity and first-pass QA yield.
- Digital inbound traffic (GA4), Search Console clicks, and Customer Acquisition Cost (CAC).

### 2. Management-by-Exception Model (Slide 5 & Section 14)
- Automated rule engine that continuously audits projects, invoices, leads, operations, and budgets.
- **Red Alert**: Immediate management attention required (e.g. `PRJ-201` 14 days delayed due to client ERP API change; `PRJ-202` 9 days delayed due to PCI-DSS audit; `INV-4002` 32 days overdue).
- **Amber Alert**: Performance requiring monitoring or corrective action (e.g. `PRJ-206` sensor shipment delay; `LED-307` stalled deal; budget utilization > 90%).
- **Interactive Action Logger**: Click into any exception, review the delay reason and responsible owner, log corrective management actions, and mark items resolved.

### 3. Automated Workflows (Section 6 & Slide 6)
- **New Employee**: Form -> HR record -> Headcount capacity check -> Welcome notification.
- **New Lead**: Intake form -> CRM record -> SLA follow-up date calculation -> High-value alert.
- **New Project**: Project intake -> Automatic Planner task breakdown (Milestones, QA, Sprints) -> Manager alert.
- **Expense Entry**: Expense form -> Budget compliance check -> Over-budget alert -> Finance update.
- **Daily Operations**: Standup update -> Productivity % & QA yield calculation -> Operations anomaly detection.
- **Marketing Sync**: Ingest GA4, Search Console, and Paid Ads data -> Auto-calculate Cost Per Lead.

### 4. Power BI Turnkey Integration (Section 2 & 16)
- Generates `Company_Central_MIS_DataModel.xlsx` (multi-sheet formatted workbook with 13 relational tables).
- Exports individual clean CSV tables in `exports/csv/`.
- Includes `PowerQuery_Transforms.m` (copy-paste M code for Power BI Desktop Advanced Editor).
- Includes `DAX_Measures.dax` (full suite of enterprise DAX measures for Revenue, Margin, Delivery %, Attendance, and Exceptions).

---

## 🚀 How to Run

### Step 0: Install dependencies (one-time)
```bash
pip install -r requirements.txt
```
`run_app.bat` and `sync_and_export.bat` (below) will also auto-install this for you the first time you run them if it's missing.

### Method A: 1-Click Launchers (Windows)
1. **Launch Executive Dashboard**: Double-click `run_app.bat` to launch the Director's Control Room in your browser at `http://localhost:8501`.
2. **Run Scheduled Sync & Export**: Double-click `sync_and_export.bat` to audit exceptions, update datasets, and export fresh Power BI files headlessly.

### Method B: Command Line (PowerShell / Terminal)
```bash
# 1. Start the Streamlit Executive Dashboard
streamlit run app.py

# 2. Run the Automated Sync & Power BI Exporter
python sync_and_export.py

# 3. Print the Director's Daily Flash Briefing
python -m backend.executive_brief
```

---

## 📂 Project Architecture

```
d:\Central MIS & Power BI Automation\
├── app.py                             # 10-Console Director MIS Streamlit Application
├── run_app.bat                        # 1-Click launcher for Web Dashboard
├── sync_and_export.py                 # Automated headless sync & export runner
├── sync_and_export.bat                # 1-Click launcher for scheduled sync
├── Company_Central_MIS_DataModel.xlsx # Consolidated multi-sheet Power BI Data Model
│
├── backend/
│   ├── config.py                       # Organization policy settings (thresholds, currency) — edit this to retune the system
│   ├── models.py                      # Schemas & IDs for all 13 organizational entities
│   ├── database.py                    # SQLite data store & rich seed generator
│   ├── automation.py                  # 6 automated workflows & exception scanner
│   ├── export_powerbi.py              # Power BI Excel, CSV, M, & DAX generator
│   └── executive_brief.py             # Director Daily Flash Briefing generator
│
├── data/
│   └── central_mis.db                 # Central relational SQLite database
│
└── exports/
    ├── Company_Central_MIS_DataModel.xlsx # Power BI Relational Model
    ├── Director_Executive_Brief.md       # Latest Director flash report
    ├── PowerQuery_Transforms.m           # Power Query M transformations
    ├── DAX_Measures.dax                  # Enterprise DAX measures
    └── csv/                              # 13 individual CSV tables
```

---

## 📊 Connecting to Power BI Desktop

1. Open **Power BI Desktop**.
2. Click **Get Data** -> **Excel Workbook**.
3. Select `d:\Central MIS & Power BI Automation\Company_Central_MIS_DataModel.xlsx`.
4. Select all 13 sheets (`Departments`, `Employees`, `Clients`, `Projects`, `Leads`, `Tasks`, `Invoices`, `Expenses`, `Attendance`, `Daily_Operations`, `Marketing_Metrics`, `KPI_Master`, `Alerts_Exceptions`).
5. Relationships will automatically link via unique IDs (`dept_id`, `employee_id`, `client_id`, `project_id`).
6. Copy measures from `exports/DAX_Measures.dax` to create executive visuals!

---

## ⚙️ Adapting This to Your Organization

Before rolling this out for real use, edit these two things:

1. **`backend/config.py`** — all policy thresholds live here (budget utilization bands, invoice overdue days, QA/productivity minimums, high-value lead cutoff, currency symbol). Nothing else in the codebase needs to change to retune these.
2. **`backend/database.py` → `_seed_data()`** — replace the sample departments, employees, clients, projects, etc. with your real organizational data (or point `insert_record`/`update_record` at a real HRMS/CRM/ERP feed instead of static seed rows).

Alert "owners" are no longer hardcoded names — they're resolved live from each department's `head` field in the `departments` table, so alert routing stays correct automatically as staff change. See `CHANGELOG.md` for the full list of fixes made in this update.

---

## 🛠️ Troubleshooting

**`'streamlit' is not recognized as an internal or external command`**
This means Windows can't find `streamlit.exe` on your PATH — usually because
it was installed under a different Python than the one on PATH, or Python's
`Scripts` folder was never added to PATH. Fixes, easiest first:
1. Just re-run `run_app.bat` — it now installs missing packages automatically
   and launches via `python -m streamlit run app.py`, which works even when
   `streamlit.exe` itself isn't on PATH.
2. If it still fails, confirm Python is on PATH at all: open Command Prompt
   and run `python --version`. If that also fails, reinstall Python from
   python.org and check **"Add python.exe to PATH"** during setup.
3. As a manual fallback: `python -m pip install -r requirements.txt` then
   `python -m streamlit run app.py`.

**`No module named 'pandas'` / `'openpyxl'` / etc.**
Run `pip install -r requirements.txt` (or just re-run `run_app.bat` /
`sync_and_export.bat`, which do this automatically now).
