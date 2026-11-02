# Changelog

## Review & Fixes (this update)

A full read-through of the application (`app.py`, all of `backend/`, the Power BI
export pipeline, and the automation workflows) turned up the following gaps
between what the docs/README promised and what the code actually did, plus
some portability and maintainability issues. All were fixed and the full
pipeline was re-tested end to end (`backend.database` → `backend.automation`
→ `backend.export_powerbi` → `backend.executive_brief` → `sync_and_export.py`).

### Added
- **`backend/config.py`** — a single settings module for every organizational
  policy value (budget utilization bands, invoice overdue-day thresholds, QA
  and productivity minimums, the high-value-lead cutoff, currency symbol).
  Previously these were magic numbers scattered across `automation.py`.
- **Continuous stalled-lead auditing** in `run_exception_scanner()`. The
  docstring already claimed this ("Stalled Leads: Amber if > 21 days with no
  follow-up") but the scanner never actually checked it — leads only got
  flagged if they happened to already be stalled at seed time.
- **Continuous department budget-overrun auditing** in
  `run_exception_scanner()`. Previously budget overruns were only caught at
  the moment a new expense was logged through the intake form; a scheduled
  scan never re-checked existing spend against budget.
- **Productivity-drop exception** in `process_daily_operations()` — the
  docstring promised an exception "if QA < 90% or Productivity < 75%" but
  only the QA half was implemented.

### Fixed
- **Duplicate alert bug**: the "is this already tracked?" dedup check in the
  scanner only matched alerts with `resolution_status = 'Open'`, so any alert
  already marked `In Progress` was invisible to the check and got a duplicate
  alert created on the next scan. Now matches anything not `Resolved`.
- **Hardcoded alert owners**: alerts for HR headcount, Finance overdue
  invoices, and Operations QA dips always named the same fictional person
  regardless of who's actually configured as that department's head. Owners
  are now resolved live from `departments.head`.
- **Hardcoded department count** in the executive brief ("across 6
  departments" no matter how many departments actually exist) — now counts
  the live `departments` table.
- **Power Query portability**: `PowerQuery_Transforms.m` had a literal
  `D:\Central MIS & Power BI Automation\...` path baked into the M code. It
  now resolves the real install path automatically and exposes it as a
  proper Power BI **Parameter** (`CentralMISFolderPath`), so moving the
  folder or deploying on a different machine only means updating one
  parameter in Power BI Desktop, not editing every query.
- **Power Query coverage**: the M script only had queries for 3 of the 13
  tables (Departments, Projects, Invoices). It now generates a fully typed
  query for all 13, keyed off the same schema used by `models.py`.
- **Percentage-formatting bug**: `completion_pct` (and other `*_pct` columns)
  were typed as `Percentage.Type` in Power Query, which would render a
  stored `78.0` as `7800%` instead of `78%`. Changed to `type number` so
  formatting is applied correctly in report visuals/DAX instead.
- **Streamlit form dropdowns** (departments, sales reps, project managers,
  approvers, "authorized by") were hardcoded lists matching only the demo
  seed data. They now populate live from the database, so the forms keep
  working correctly as your real department/employee list changes.

### Not changed (needs your input)
- The seed data in `backend/database.py` (`_seed_data()`) is still the
  original demo company. Swap in your real departments, employees, clients,
  and budgets — or replace the seed step with a real data feed — when you're
  ready to go live. See the **Adapting This to Your Organization** section
  in `README.md`.
