"""
Central MIS Organization Configuration
========================================
Single source of truth for organization-specific policy values (thresholds,
currency, escalation rules). Every workflow in `automation.py`,
`executive_brief.py`, and `export_powerbi.py` reads from here instead of
hardcoding numbers or people's names, so the whole platform can be re-pointed
at a different organization, department structure, or policy by editing this
one file only.

HOW TO ADAPT THIS TO YOUR ORGANIZATION:
1. Update the threshold constants below to match your real finance/HR/ops
   policies (budget caps, SLA days, QA targets, etc.).
2. Update `CURRENCY_SYMBOL` / `CURRENCY_CODE` to your operating currency.
3. Department "owners" for alerts are no longer hardcoded people's names —
   they are looked up live from the `departments.head` column at run time
   via `get_department_head()`. Just keep that column accurate in
   `backend/database.py` (or, in production, in whatever HRMS table feeds
   the `departments` table) and every alert will route to the right person
   automatically, even if department heads change.
"""

from typing import Optional

# ---------------------------------------------------------------------------
# Currency / locale
# ---------------------------------------------------------------------------
CURRENCY_SYMBOL = "$"
CURRENCY_CODE = "USD"

# ---------------------------------------------------------------------------
# Management-by-Exception thresholds (Section 14 / Slide 5)
# ---------------------------------------------------------------------------
# Sales: leads at or above this estimated value trigger an executive-visibility alert
HIGH_VALUE_LEAD_THRESHOLD = 75000.0

# Sales: an Open lead with no follow-up activity for this many days is flagged Stalled
LEAD_STALL_DAYS = 21

# Finance: department monthly budget utilization bands
BUDGET_AMBER_UTILIZATION_PCT = 90.0
BUDGET_RED_UTILIZATION_PCT = 100.0

# Finance: invoice overdue severity band (days past due_date)
INVOICE_OVERDUE_RED_DAYS = 30

# Finance: company-wide overdue receivables KPI bands (absolute amount)
OVERDUE_RECEIVABLES_RED_AMOUNT = 40000.0
OVERDUE_RECEIVABLES_AMBER_AMOUNT = 15000.0

# Operations: QA first-pass yield below this triggers an exception
QA_PASS_MIN_PCT = 90.0

# Operations: productivity below this triggers an exception
PRODUCTIVITY_MIN_PCT = 75.0

# Projects: on-time delivery rate KPI bands
ONTIME_DELIVERY_GREEN_PCT = 85.0
ONTIME_DELIVERY_AMBER_PCT = 70.0

# Projects: count of concurrently delayed projects that flips the KPI to Red
DELAYED_PROJECTS_RED_COUNT = 2


# ---------------------------------------------------------------------------
# Dynamic ownership resolution
# ---------------------------------------------------------------------------
def clean_head_name(raw_head: Optional[str]) -> str:
    """`departments.head` is stored as 'Full Name (Title)'; return just the name."""
    if not raw_head:
        return "Department Head"
    return raw_head.split("(")[0].strip()


def get_department_head(cur, dept_id: str = None, dept_name_contains: str = None) -> str:
    """
    Resolves the responsible owner for an alert dynamically from the live
    `departments` table, instead of hardcoding a person's name inside the
    workflow logic. This means alert routing automatically stays correct
    even if department heads change, without touching any automation code.

    Pass either `dept_id` (preferred, exact match) or `dept_name_contains`
    (fuzzy match on department name, e.g. "Finance" or "Human Resources").
    """
    if dept_id:
        cur.execute("SELECT head FROM departments WHERE dept_id = ?", (dept_id,))
    elif dept_name_contains:
        cur.execute(
            "SELECT head FROM departments WHERE name LIKE ? LIMIT 1",
            (f"%{dept_name_contains}%",),
        )
    else:
        return "Department Head"
    row = cur.fetchone()
    return clean_head_name(row["head"]) if row else "Department Head"
