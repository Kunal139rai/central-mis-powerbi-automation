# Walkthrough: Central MIS & Power BI Automation Suite

We have built and verified the complete **Central MIS & Power BI Automation Suite** in `d:\Central MIS & Power BI Automation\`, directly fulfilling the specifications of:
- **`Managing_Director_Central_MIS_PowerBI_Proposal.pptx`**
- **`Organization_Automation_PowerBI_MIS_Plan_Updated_Director_Dashboard.docx`**

---

## 🏗️ What Was Built

### 1. Central Relational Data Store & Unique ID Schemas (`backend/`)
- [backend/models.py](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/backend/models.py): Defines standardized schemas with unique ID prefixes:
  - `EMP-` (Employees), `DEPT-` (Departments), `CLT-` (Clients), `LED-` (Leads), `PRJ-` (Projects), `TSK-` (Tasks), `INV-` (Invoices), `EXP-` (Expenses), `ATT-` (Attendance), `OPS-` (Daily Operations), `MKT-` (Marketing), `KPI-` (KPI Master), `ALT-` (Alerts & Exceptions).
- [backend/database.py](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/backend/database.py): Multi-tier data manager with SQLite database (`data/central_mis.db`), auto-schema initialization, and a seed dataset reflecting the proposal scenarios (including the 2 delayed projects from Slide 5, overdue receivables past 30 days, sales funnel deals, and attendance).

### 2. Workflow Automation Engine (`backend/automation.py`)
- Implements all **6 automated workflows** (Section 6 & Slide 6):
  1. `process_new_employee()`: ID allocation, headcount plan validation, onboarding notice.
  2. `process_new_lead()`: Intake, SLA follow-up date calculation, high-value deal alerts.
  3. `process_new_project()`: Project registration, automated Planner task breakdown (Requirements, Sprints, QA, UAT).
  4. `process_expense_entry()`: Budget compliance validation against department cap, over-budget alert generation.
  5. `process_daily_operations()`: Work update ingestion, productivity index calculation, QA yield anomaly detection.
  6. `process_marketing_sync()`: Ingestion of GA4 and Search Console metrics, CPL calculation.
- **Management-by-Exception Scanner (`run_exception_scanner()`)**: Continuously audits the company for Green, Amber, and Red conditions (overdue invoices, delayed projects, stalled leads, QA dips) and syncs the Alerts register.
- **Action Resolution Logger (`resolve_alert()`)**: Implements Slide 5's action flow: Click → Delay Reason → Responsible Team → Action Logged → Resolved.

### 3. Power BI Automated Export Pipeline (`backend/export_powerbi.py`)
- Generates [Company_Central_MIS_DataModel.xlsx](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/Company_Central_MIS_DataModel.xlsx) (formatted 13-sheet relational workbook with headers, styling, and freeze panes).
- Generates 13 standalone CSV tables in [exports/csv/](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/exports/csv/).
- Generates [PowerQuery_Transforms.m](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/exports/PowerQuery_Transforms.m) (pre-configured Power Query M transformations).
- Generates [DAX_Measures.dax](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/exports/DAX_Measures.dax) (enterprise DAX formulas across all 8 dashboard areas).

### 4. Director's Daily Flash Briefing (`backend/executive_brief.py`)
- Automatically generates [Director_Executive_Brief.md](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/exports/Director_Executive_Brief.md) answering the 10 core questions from Section 18.

### 5. Director's Central MIS Web Application ([app.py](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/app.py))
An interactive Streamlit application with **10 management consoles**:
1. **Director Overview**: Company health status, top KPI banners, Target vs Actual bar chart, and Slide 5 exception spotlight.
2. **Finance**: Revenue vs Expenses, Profit Margin, AR aging (0-30, 31-60, 60+ days), and Department budget vs actual spend.
3. **Sales & CRM**: Pipeline funnel by stage, sales rep leaderboard, and deal conversion rates.
4. **Projects**: Delivery tracker, contract gross margin, and delayed project focus (`PRJ-201`, `PRJ-202`).
5. **HR & Workforce**: Headcount distribution, attendance rates, payroll, and employee directory.
6. **Operations & QA**: Completed tasks, productivity index, first-pass QA yield over time.
7. **Marketing & SEO**: GA4 traffic, Google Search Console clicks, CAC, and lead volume.
8. **Alerts & Exception Center**: Management-by-Exception center with action assignment and one-click resolution.
9. **Automation Intake Center**: Interactive forms to run and test all 6 automated workflows live.
10. **Power BI Integration Hub**: One-click model export, file downloads, Power Query M code, and DAX measures.

### 6. Windows Launchers & Automation Scripts
- [run_app.bat](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/run_app.bat): 1-click launcher to start the Streamlit web dashboard.
- [sync_and_export.bat](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/sync_and_export.bat): 1-click launcher for headless automated sync and Power BI export.
- [sync_and_export.py](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/sync_and_export.py): Standalone CLI runner for Windows Task Scheduler or cron.
- [README.md](file:///d:/Central%20MIS%20&%20Power%20BI%20Automation/README.md): Comprehensive system documentation.

---

## 🧪 Verification & Test Results

| Test Category | Command Executed | Result |
|---|---|---|
| **Database Initialization** | `python -m backend.database` | **PASSED**: All 13 relational tables created and seeded. |
| **Workflow Automations** | `python -m backend.automation` | **PASSED**: All 6 workflows executed, capacity checked, and exceptions flagged. |
| **Power BI Export Engine** | `python -m backend.export_powerbi` | **PASSED**: `Company_Central_MIS_DataModel.xlsx`, 13 CSVs, `PowerQuery_Transforms.m`, and `DAX_Measures.dax` generated. |
| **Director Briefing Generator** | `python -m backend.executive_brief` | **PASSED**: Flash brief generated and saved to `exports/Director_Executive_Brief.md`. |
| **Headless Sync Pipeline** | `python sync_and_export.py` | **PASSED**: End-to-end sync, audit scan, and export completed with exit code 0. |
| **Streamlit App Validation** | `python -m py_compile app.py` & startup test | **PASSED**: Zero syntax errors; web server started cleanly. |

---

## 🚀 How to Use the System

### 1. Launch the Executive Web App
Double-click `run_app.bat` or run:
```bash
streamlit run app.py
```
This will open the Director Control Room in your browser at `http://localhost:8501`.

### 2. Run Scheduled Refresh & Export
Double-click `sync_and_export.bat` or run:
```bash
python sync_and_export.py
```

### 3. Load into Power BI Desktop
1. Open **Power BI Desktop**.
2. Click **Get Data** → **Excel Workbook**.
3. Select `d:\Central MIS & Power BI Automation\Company_Central_MIS_DataModel.xlsx`.
4. Select all 13 sheets to load the relational model.
