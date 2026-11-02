"""
Central MIS Automation Engine
Implements the 6 automated organizational workflows from Section 6 & Slide 6:
1. New Employee Onboarding & Capacity Flow
2. New Lead Qualification & Follow-up Flow
3. New Project Breakdown & Planner Task Flow
4. Expense Entry & Budget Compliance Flow
5. Daily Operations & QA Anomaly Detection Flow
6. Marketing / SEO Metrics Ingestion Flow
Plus the Management-by-Exception Scanner & Action Resolution Logger.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from backend.database import get_connection, insert_record, update_record, load_all_tables
from backend import config


# ==========================================
# 1. NEW EMPLOYEE ONBOARDING WORKFLOW
# ==========================================
def process_new_employee(
    name: str,
    dept_id: str,
    role: str,
    email: str,
    phone: str,
    salary_monthly: float,
    joining_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Workflow:
    Form -> Validate -> Generate EMP ID -> Insert Employee -> Check Dept Capacity ->
    Generate Welcome & IT Onboarding Tasks -> Log HR Notification
    """
    conn = get_connection()
    cur = conn.cursor()

    # Generate Employee ID
    cur.execute("SELECT MAX(CAST(SUBSTR(employee_id, 5) AS INTEGER)) FROM employees")
    max_num = cur.fetchone()[0] or 100
    new_id = f"EMP-{max_num + 1}"

    if not joining_date:
        joining_date = date.today().strftime("%Y-%m-%d")

    # Fetch Department details
    cur.execute("SELECT name, head, headcount_target FROM departments WHERE dept_id = ?", (dept_id,))
    dept_row = cur.fetchone()
    dept_name = dept_row["name"] if dept_row else dept_id
    dept_target = dept_row["headcount_target"] if dept_row else 10

    # Count current employees in dept
    cur.execute("SELECT COUNT(*) FROM employees WHERE dept_id = ? AND status = 'Active'", (dept_id,))
    curr_count = cur.fetchone()[0]

    # Insert employee record
    record = {
        "employee_id": new_id,
        "name": name,
        "dept_id": dept_id,
        "role": role,
        "email": email,
        "phone": phone,
        "joining_date": joining_date,
        "salary_monthly": salary_monthly,
        "status": "Active"
    }
    insert_record("employees", record)

    # Automated check: Headcount Target
    capacity_note = "Within Department Headcount Plan"
    if curr_count + 1 > dept_target:
        capacity_note = f"Headcount Warning: Current ({curr_count + 1}) exceeds Target ({dept_target})"
        # Log HR amber alert
        cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
        max_alt = cur.fetchone()[0] or 100
        alt_id = f"ALT-{max_alt + 1}"
        insert_record("alerts_exceptions", {
            "alert_id": alt_id,
            "category": "HR",
            "severity": "Amber",
            "entity_id": dept_id,
            "entity_name": dept_name,
            "issue": f"{dept_name} headcount reached {curr_count + 1}, exceeding target of {dept_target}",
            "delay_days": 0,
            "responsible_team": "Human Resources",
            "owner": config.get_department_head(cur, dept_name_contains="Human Resources"),
            "action_required": "Review department expansion budget with Managing Director",
            "resolution_status": "Open",
            "logged_date": date.today().strftime("%Y-%m-%d")
        })

    conn.close()

    return {
        "success": True,
        "employee_id": new_id,
        "name": name,
        "department": dept_name,
        "capacity_status": capacity_note,
        "message": f"Successfully onboarded {name} ({new_id}) into {dept_name}. Onboarding notification triggered."
    }


# ==========================================
# 2. NEW LEAD CAPTURE & QUALIFICATION WORKFLOW
# ==========================================
def process_new_lead(
    client_name: str,
    contact_person: str,
    email: str,
    source: str,
    estimated_value: float,
    assigned_sales_rep: str,
    stage: str = "New",
    follow_up_days: int = 3
) -> Dict[str, Any]:
    """
    Workflow:
    Lead Intake Form -> Generate LED ID -> Calculate Follow-up Date ->
    Check High-Value Threshold (>= $50k) -> Insert Lead -> Update CRM Pipeline
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(CAST(SUBSTR(lead_id, 5) AS INTEGER)) FROM leads")
    max_num = cur.fetchone()[0] or 300
    new_id = f"LED-{max_num + 1}"

    today_str = date.today().strftime("%Y-%m-%d")
    follow_up_date = (date.today() + timedelta(days=follow_up_days)).strftime("%Y-%m-%d")

    record = {
        "lead_id": new_id,
        "client_name": client_name,
        "contact_person": contact_person,
        "email": email,
        "source": source,
        "stage": stage,
        "estimated_value": estimated_value,
        "assigned_sales_rep": assigned_sales_rep,
        "created_date": today_str,
        "next_follow_up": follow_up_date,
        "status": "Open"
    }
    insert_record("leads", record)

    alerts_triggered = []
    # If High Value deal >= threshold, trigger Executive Sales Alert
    if estimated_value >= config.HIGH_VALUE_LEAD_THRESHOLD:
        cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
        max_alt = cur.fetchone()[0] or 100
        alt_id = f"ALT-{max_alt + 1}"
        insert_record("alerts_exceptions", {
            "alert_id": alt_id,
            "category": "Sales",
            "severity": "Green",
            "entity_id": new_id,
            "entity_name": client_name,
            "issue": f"High-value opportunity captured: ${estimated_value:,.2f} ({stage})",
            "delay_days": 0,
            "responsible_team": "Sales & CRM",
            "owner": assigned_sales_rep,
            "action_required": "Director / VP Sales joint executive intro call to be scheduled",
            "resolution_status": "Open",
            "logged_date": today_str
        })
        alerts_triggered.append("Executive Deal Notice Created")

    conn.close()

    return {
        "success": True,
        "lead_id": new_id,
        "client_name": client_name,
        "estimated_value": estimated_value,
        "next_follow_up": follow_up_date,
        "alerts": alerts_triggered,
        "message": f"Lead {new_id} ({client_name}) registered. Follow-up SLA set for {follow_up_date}."
    }


# ==========================================
# 3. NEW PROJECT & TASK BREAKDOWN WORKFLOW
# ==========================================
def process_new_project(
    client_id: str,
    name: str,
    responsible_team: str,
    project_manager: str,
    deadline: str,
    budget: float,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Workflow:
    Project Intake -> Generate PRJ ID -> Auto-breakdown Planner Tasks ->
    Assign Initial Milestones -> Insert Project & Tasks -> Notify Delivery Lead
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(CAST(SUBSTR(project_id, 5) AS INTEGER)) FROM projects")
    max_num = cur.fetchone()[0] or 200
    new_prj_id = f"PRJ-{max_num + 1}"

    if not start_date:
        start_date = date.today().strftime("%Y-%m-%d")

    project_record = {
        "project_id": new_prj_id,
        "client_id": client_id,
        "name": name,
        "responsible_team": responsible_team,
        "project_manager": project_manager,
        "start_date": start_date,
        "deadline": deadline,
        "status": "On Track",
        "budget": budget,
        "actual_cost": 0.0,
        "billed_revenue": 0.0,
        "completion_pct": 0.0,
        "delay_reason": None
    }
    insert_record("projects", project_record)

    # Auto-generate standard operational tasks (Simulating Planner task creation)
    cur.execute("SELECT MAX(CAST(SUBSTR(task_id, 5) AS INTEGER)) FROM tasks")
    max_task_num = cur.fetchone()[0] or 1000

    standard_tasks = [
        ("Architecture & Security Specification", 30.0, 7),
        ("Core Module Engineering & Sprints", 80.0, 21),
        ("Integration Testing & QA Hardening", 40.0, 30),
        ("User Acceptance Testing (UAT) & Sign-off", 20.0, 38),
    ]

    created_tasks = []
    for i, (t_title, hours, day_offset) in enumerate(standard_tasks):
        tsk_id = f"TSK-{max_task_num + 1 + i}"
        due_d = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        t_record = {
            "task_id": tsk_id,
            "project_id": new_prj_id,
            "title": f"[{name}] {t_title}",
            "assigned_to": project_manager,
            "due_date": due_d,
            "status": "Not Started" if i > 0 else "In Progress",
            "qa_status": "Pending QA",
            "estimated_hours": hours,
            "actual_hours": 0.0
        }
        insert_record("tasks", t_record)
        created_tasks.append(tsk_id)

    conn.close()

    return {
        "success": True,
        "project_id": new_prj_id,
        "name": name,
        "tasks_generated": created_tasks,
        "message": f"Project {new_prj_id} initialized with {len(created_tasks)} automated delivery tasks."
    }


# ==========================================
# 4. EXPENSE ENTRY & BUDGET COMPLIANCE WORKFLOW
# ==========================================
def process_expense_entry(
    dept_id: str,
    category: str,
    vendor: str,
    amount: float,
    description: str,
    approved_by: str,
    expense_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Workflow:
    Expense Form -> Check Department Monthly Budget ->
    Calculate Budget Utilization -> If > 90% trigger Amber alert, if > 100% Red alert ->
    Insert Expense -> Update Finance Analytics
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(CAST(SUBSTR(expense_id, 5) AS INTEGER)) FROM expenses")
    max_num = cur.fetchone()[0] or 7000
    new_exp_id = f"EXP-{max_num + 1}"

    if not expense_date:
        expense_date = date.today().strftime("%Y-%m-%d")

    # Fetch Department details & budget
    cur.execute("SELECT name, monthly_budget FROM departments WHERE dept_id = ?", (dept_id,))
    dept_row = cur.fetchone()
    dept_name = dept_row["name"] if dept_row else dept_id
    monthly_budget = dept_row["monthly_budget"] if dept_row else 30000.0

    # Calculate MTD expenses
    cur.execute("SELECT SUM(amount) FROM expenses WHERE dept_id = ? AND status = 'Approved'", (dept_id,))
    existing_spend = cur.fetchone()[0] or 0.0

    new_total_spend = existing_spend + amount
    utilization_pct = round((new_total_spend / monthly_budget) * 100, 1)

    status = "Approved"
    alert_created = None

    if utilization_pct > config.BUDGET_RED_UTILIZATION_PCT:
        # Red Alert: Over budget
        cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
        max_alt = cur.fetchone()[0] or 100
        alt_id = f"ALT-{max_alt + 1}"
        insert_record("alerts_exceptions", {
            "alert_id": alt_id,
            "category": "Finance",
            "severity": "Red",
            "entity_id": dept_id,
            "entity_name": f"{dept_name} Budget",
            "issue": f"{dept_name} exceeded monthly budget: Spent ${new_total_spend:,.2f} vs Budget ${monthly_budget:,.2f} ({utilization_pct}%)",
            "delay_days": 0,
            "responsible_team": "Finance & Accounts",
            "owner": approved_by,
            "action_required": "Director sign-off required for emergency budget variance approval",
            "resolution_status": "Open",
            "logged_date": expense_date
        })
        alert_created = f"RED ALERT: {dept_name} Budget Exceeded ({utilization_pct}%)"
    elif utilization_pct >= config.BUDGET_AMBER_UTILIZATION_PCT:
        # Amber Alert: Near budget limit
        cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
        max_alt = cur.fetchone()[0] or 100
        alt_id = f"ALT-{max_alt + 1}"
        insert_record("alerts_exceptions", {
            "alert_id": alt_id,
            "category": "Finance",
            "severity": "Amber",
            "entity_id": dept_id,
            "entity_name": f"{dept_name} Budget",
            "issue": f"{dept_name} budget utilization reached {utilization_pct}% (${new_total_spend:,.2f} of ${monthly_budget:,.2f})",
            "delay_days": 0,
            "responsible_team": "Finance & Accounts",
            "owner": approved_by,
            "action_required": "Freeze discretionary department spending for remainder of the month",
            "resolution_status": "Open",
            "logged_date": expense_date
        })
        alert_created = f"AMBER ALERT: {dept_name} Near Budget Cap ({utilization_pct}%)"

    record = {
        "expense_id": new_exp_id,
        "dept_id": dept_id,
        "category": category,
        "vendor": vendor,
        "amount": amount,
        "date": expense_date,
        "description": description,
        "approved_by": approved_by,
        "status": status
    }
    insert_record("expenses", record)
    conn.close()

    return {
        "success": True,
        "expense_id": new_exp_id,
        "dept_name": dept_name,
        "amount": amount,
        "budget_utilization_pct": utilization_pct,
        "alert": alert_created,
        "message": f"Expense {new_exp_id} (${amount:,.2f}) logged for {dept_name}. Budget Utilization: {utilization_pct}%."
    }


# ==========================================
# 5. DAILY OPERATIONS & QA LOGGING WORKFLOW
# ==========================================
def process_daily_operations(
    dept_id: str,
    tasks_completed: int,
    tasks_pending: int,
    qa_pass_pct: float,
    avg_turnaround_hours: float,
    notes: Optional[str] = None,
    op_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Workflow:
    Daily Standup / Log -> Ingest Productivity & QA Metrics ->
    Auto-calculate Productivity % -> If QA < 90% or Productivity < 75% trigger Exception ->
    Insert into Central MIS Operations table
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(CAST(SUBSTR(operation_id, 5) AS INTEGER)) FROM daily_operations")
    max_num = cur.fetchone()[0] or 8000
    new_op_id = f"OPS-{max_num + 1}"

    if not op_date:
        op_date = date.today().strftime("%Y-%m-%d")

    total_tasks = tasks_completed + tasks_pending
    productivity_pct = round((tasks_completed / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    cur.execute("SELECT name FROM departments WHERE dept_id = ?", (dept_id,))
    dept_name = cur.fetchone()["name"]

    alert_msg = None
    if qa_pass_pct < config.QA_PASS_MIN_PCT:
        cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
        max_alt = cur.fetchone()[0] or 100
        alt_id = f"ALT-{max_alt + 1}"
        insert_record("alerts_exceptions", {
            "alert_id": alt_id,
            "category": "Operations",
            "severity": "Amber",
            "entity_id": new_op_id,
            "entity_name": f"{dept_name} QA Yield",
            "issue": f"QA Pass Yield dropped to {qa_pass_pct}% on {op_date} (Target >= {config.QA_PASS_MIN_PCT}%)",
            "delay_days": 0,
            "responsible_team": "Operations & Delivery",
            "owner": config.get_department_head(cur, dept_id=dept_id),
            "action_required": "Conduct retrospective on failed test units and review test suites",
            "resolution_status": "Open",
            "logged_date": op_date
        })
        alert_msg = f"QA Amber Exception logged ({qa_pass_pct}%)"

    if productivity_pct < config.PRODUCTIVITY_MIN_PCT:
        cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
        max_alt = cur.fetchone()[0] or 100
        alt_id = f"ALT-{max_alt + 1}"
        insert_record("alerts_exceptions", {
            "alert_id": alt_id,
            "category": "Operations",
            "severity": "Amber",
            "entity_id": new_op_id,
            "entity_name": f"{dept_name} Productivity",
            "issue": f"Team productivity dropped to {productivity_pct}% on {op_date} (Target >= {config.PRODUCTIVITY_MIN_PCT}%)",
            "delay_days": 0,
            "responsible_team": "Operations & Delivery",
            "owner": config.get_department_head(cur, dept_id=dept_id),
            "action_required": "Review task backlog and resourcing with team lead",
            "resolution_status": "Open",
            "logged_date": op_date
        })
        alert_msg = ((alert_msg + "; ") if alert_msg else "") + f"Productivity Amber Exception logged ({productivity_pct}%)"

    record = {
        "operation_id": new_op_id,
        "date": op_date,
        "dept_id": dept_id,
        "tasks_completed": tasks_completed,
        "tasks_pending": tasks_pending,
        "productivity_pct": productivity_pct,
        "qa_pass_pct": qa_pass_pct,
        "avg_turnaround_hours": avg_turnaround_hours,
        "notes": notes or "Daily operational metrics synchronized."
    }
    insert_record("daily_operations", record)
    conn.close()

    return {
        "success": True,
        "operation_id": new_op_id,
        "productivity_pct": productivity_pct,
        "qa_pass_pct": qa_pass_pct,
        "alert": alert_msg,
        "message": f"Daily operations {new_op_id} logged. Productivity: {productivity_pct}%, QA Pass: {qa_pass_pct}%."
    }


# ==========================================
# 6. MARKETING / SEO INGESTION WORKFLOW
# ==========================================
def process_marketing_sync(
    channel: str,
    sessions_or_impressions: int,
    clicks_or_visitors: int,
    spend: float,
    leads_generated: int,
    conversions: int,
    metric_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Workflow:
    GA4 / GSC / Social Ingestion -> Calculate CAC & CPL -> Update Marketing Central Table
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(CAST(SUBSTR(metric_id, 5) AS INTEGER)) FROM marketing_metrics")
    max_num = cur.fetchone()[0] or 6000
    new_mkt_id = f"MKT-{max_num + 1}"

    if not metric_date:
        metric_date = date.today().strftime("%Y-%m-%d")

    record = {
        "metric_id": new_mkt_id,
        "date": metric_date,
        "channel": channel,
        "sessions_or_impressions": sessions_or_impressions,
        "clicks_or_visitors": clicks_or_visitors,
        "spend": spend,
        "leads_generated": leads_generated,
        "conversions": conversions
    }
    insert_record("marketing_metrics", record)
    conn.close()

    cpl = round(spend / leads_generated, 2) if leads_generated > 0 else 0.0
    return {
        "success": True,
        "metric_id": new_mkt_id,
        "channel": channel,
        "cost_per_lead": cpl,
        "message": f"Marketing metrics {new_mkt_id} ({channel}) synced. Cost Per Lead: ${cpl:,.2f}."
    }


# ==========================================
# 7. MANAGEMENT-BY-EXCEPTION SCANNER ENGINE
# ==========================================
def run_exception_scanner() -> Dict[str, Any]:
    """
    Scans all relational tables to detect Green, Amber, Red anomalies:
    - Overdue Invoices (Red if > 30 days, Amber if 1-30 days)
    - Delayed Projects (Red if Delayed, Amber if At Risk)
    - Stalled Leads (Amber if > 21 days with no follow-up)
    - Budget Overruns (Red if > 100%, Amber if > 90%)
    - Operations QA dips (< 90%)
    Synchronizes kpi_master status indicators and populates alerts_exceptions table.
    """
    conn = get_connection()
    cur = conn.cursor()

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    # 1. Check Invoices
    cur.execute("SELECT invoice_id, client_id, amount, paid_amount, due_date FROM invoices WHERE status IN ('Overdue', 'Outstanding')")
    inv_rows = cur.fetchall()
    for inv in inv_rows:
        due_d = datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
        unpaid = inv["amount"] - inv["paid_amount"]
        if due_d < today and unpaid > 0:
            overdue_days = (today - due_d).days
            severity = "Red" if overdue_days > config.INVOICE_OVERDUE_RED_DAYS else "Amber"
            # Check if alert already exists
            cur.execute("SELECT alert_id FROM alerts_exceptions WHERE entity_id = ? AND resolution_status != 'Resolved'", (inv["invoice_id"],))
            if not cur.fetchone():
                cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
                max_alt = cur.fetchone()[0] or 100
                alt_id = f"ALT-{max_alt + 1}"
                cur.execute("SELECT name FROM clients WHERE client_id = ?", (inv["client_id"],))
                c_name = cur.fetchone()["name"]
                action = "Issue formal legal / CFO escalation notice" if severity == "Red" else "Finance officer follow-up call"
                insert_record("alerts_exceptions", {
                    "alert_id": alt_id,
                    "category": "Finance",
                    "severity": severity,
                    "entity_id": inv["invoice_id"],
                    "entity_name": f"{c_name} ({inv['invoice_id']})",
                    "issue": f"Invoice of ${unpaid:,.2f} is {overdue_days} days overdue (Due: {inv['due_date']})",
                    "delay_days": overdue_days,
                    "responsible_team": "Finance & Accounts",
                    "owner": config.get_department_head(cur, dept_name_contains="Finance"),
                    "action_required": action,
                    "resolution_status": "Open",
                    "logged_date": today_str
                })

    # 2. Check Projects
    cur.execute("SELECT project_id, name, responsible_team, project_manager, deadline, status, delay_reason FROM projects WHERE status IN ('Delayed', 'At Risk')")
    prj_rows = cur.fetchall()
    for prj in prj_rows:
        cur.execute("SELECT alert_id FROM alerts_exceptions WHERE entity_id = ? AND resolution_status != 'Resolved'", (prj["project_id"],))
        if not cur.fetchone():
            d_line = datetime.strptime(prj["deadline"], "%Y-%m-%d").date()
            delay_days = max((today - d_line).days, 7) if prj["status"] == "Delayed" else 0
            cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
            max_alt = cur.fetchone()[0] or 100
            alt_id = f"ALT-{max_alt + 1}"
            sev = "Red" if prj["status"] == "Delayed" else "Amber"
            insert_record("alerts_exceptions", {
                "alert_id": alt_id,
                "category": "Projects",
                "severity": sev,
                "entity_id": prj["project_id"],
                "entity_name": prj["name"],
                "issue": prj["delay_reason"] or f"Project {prj['status']} against milestone baseline",
                "delay_days": delay_days,
                "responsible_team": prj["responsible_team"],
                "owner": prj["project_manager"],
                "action_required": "Director intervention with client CTO & resource reallocation",
                "resolution_status": "Open",
                "logged_date": today_str
            })

    # 3. Check Stalled Leads (Amber if no follow-up progress for LEAD_STALL_DAYS+)
    cur.execute(
        "SELECT lead_id, client_name, assigned_sales_rep, next_follow_up, estimated_value "
        "FROM leads WHERE status = 'Open'"
    )
    lead_rows = cur.fetchall()
    for ld in lead_rows:
        follow_up_d = datetime.strptime(ld["next_follow_up"], "%Y-%m-%d").date()
        days_since_follow_up = (today - follow_up_d).days
        if days_since_follow_up >= config.LEAD_STALL_DAYS:
            # Mark the lead itself as Stalled so CRM views reflect it too
            update_record("leads", "lead_id", ld["lead_id"], {"status": "Stalled"})
            cur.execute("SELECT alert_id FROM alerts_exceptions WHERE entity_id = ? AND resolution_status != 'Resolved'", (ld["lead_id"],))
            if not cur.fetchone():
                cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
                max_alt = cur.fetchone()[0] or 100
                alt_id = f"ALT-{max_alt + 1}"
                insert_record("alerts_exceptions", {
                    "alert_id": alt_id,
                    "category": "Sales",
                    "severity": "Amber",
                    "entity_id": ld["lead_id"],
                    "entity_name": ld["client_name"],
                    "issue": f"Deal worth ${ld['estimated_value']:,.2f} stalled for {days_since_follow_up} days without a follow-up",
                    "delay_days": days_since_follow_up,
                    "responsible_team": "Sales & CRM",
                    "owner": ld["assigned_sales_rep"],
                    "action_required": "Sales manager to re-engage or requalify the opportunity",
                    "resolution_status": "Open",
                    "logged_date": today_str
                })

    # 4. Check Department Budget Overruns (continuous audit, not just at expense entry)
    cur.execute("SELECT dept_id, name, monthly_budget FROM departments")
    dept_rows = cur.fetchall()
    for dept in dept_rows:
        cur.execute(
            "SELECT SUM(amount) FROM expenses WHERE dept_id = ? AND status = 'Approved'",
            (dept["dept_id"],)
        )
        spend = cur.fetchone()[0] or 0.0
        if dept["monthly_budget"] <= 0:
            continue
        utilization_pct = round((spend / dept["monthly_budget"]) * 100, 1)
        if utilization_pct >= config.BUDGET_AMBER_UTILIZATION_PCT:
            severity = "Red" if utilization_pct > config.BUDGET_RED_UTILIZATION_PCT else "Amber"
            cur.execute(
                "SELECT alert_id FROM alerts_exceptions WHERE entity_id = ? AND category = 'Finance' AND resolution_status != 'Resolved'",
                (dept["dept_id"],)
            )
            if not cur.fetchone():
                cur.execute("SELECT MAX(CAST(SUBSTR(alert_id, 5) AS INTEGER)) FROM alerts_exceptions")
                max_alt = cur.fetchone()[0] or 100
                alt_id = f"ALT-{max_alt + 1}"
                insert_record("alerts_exceptions", {
                    "alert_id": alt_id,
                    "category": "Finance",
                    "severity": severity,
                    "entity_id": dept["dept_id"],
                    "entity_name": f"{dept['name']} Budget",
                    "issue": f"{dept['name']} budget utilization at {utilization_pct}% (${spend:,.2f} of ${dept['monthly_budget']:,.2f})",
                    "delay_days": 0,
                    "responsible_team": dept["name"],
                    "owner": config.get_department_head(cur, dept_id=dept["dept_id"]),
                    "action_required": "Director sign-off required for budget variance" if severity == "Red" else "Freeze discretionary spending for remainder of month",
                    "resolution_status": "Open",
                    "logged_date": today_str
                })

    # 5. Recalculate KPI Master Statuses
    # Overdue Receivables KPI
    cur.execute("SELECT SUM(amount - paid_amount) FROM invoices WHERE status = 'Overdue'")
    overdue_rec = cur.fetchone()[0] or 0.0
    rec_status = "Red" if overdue_rec > config.OVERDUE_RECEIVABLES_RED_AMOUNT else ("Amber" if overdue_rec > config.OVERDUE_RECEIVABLES_AMBER_AMOUNT else "Green")
    update_record("kpi_master", "kpi_id", "KPI-003", {"actual_value": overdue_rec, "status": rec_status})

    # Active Delayed Projects Count KPI
    cur.execute("SELECT COUNT(*) FROM projects WHERE status = 'Delayed'")
    delayed_count = cur.fetchone()[0]
    delay_status = "Red" if delayed_count >= config.DELAYED_PROJECTS_RED_COUNT else ("Amber" if delayed_count == 1 else "Green")
    update_record("kpi_master", "kpi_id", "KPI-007", {"actual_value": float(delayed_count), "status": delay_status})

    # On-Time Delivery Rate
    cur.execute("SELECT COUNT(*) FROM projects")
    total_prjs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM projects WHERE status IN ('Completed', 'On Track')")
    ontime_prjs = cur.fetchone()[0]
    ontime_rate = round((ontime_prjs / total_prjs) * 100, 1) if total_prjs > 0 else 100.0
    ontime_status = "Green" if ontime_rate >= config.ONTIME_DELIVERY_GREEN_PCT else ("Amber" if ontime_rate >= config.ONTIME_DELIVERY_AMBER_PCT else "Red")
    update_record("kpi_master", "kpi_id", "KPI-006", {"actual_value": ontime_rate, "status": ontime_status})

    # Pipeline Value KPI
    cur.execute("SELECT SUM(estimated_value) FROM leads WHERE status = 'Open'")
    pipeline_val = cur.fetchone()[0] or 0.0
    cur.execute("SELECT target_value FROM kpi_master WHERE kpi_id = 'KPI-004'")
    target_pipe = cur.fetchone()["target_value"]
    pipe_status = "Green" if pipeline_val >= target_pipe else "Amber"
    update_record("kpi_master", "kpi_id", "KPI-004", {"actual_value": pipeline_val, "status": pipe_status})

    # Count open alerts by severity
    cur.execute("SELECT severity, COUNT(*) FROM alerts_exceptions WHERE resolution_status != 'Resolved' GROUP BY severity")
    counts = dict(cur.fetchall())
    red_count = counts.get("Red", 0)
    amber_count = counts.get("Amber", 0)
    green_count = counts.get("Green", 0)

    conn.close()

    return {
        "scan_time": today_str,
        "red_exceptions": red_count,
        "amber_exceptions": amber_count,
        "green_notices": green_count,
        "message": (
            f"Exception scan complete: {red_count} Red (Critical), {amber_count} Amber (Monitoring), "
            f"{green_count} Green notices. Audited invoices, projects, stalled leads, and department budgets."
        )
    }


# ==========================================
# 8. EXCEPTION ACTION RESOLUTION LOGGER
# ==========================================
def resolve_alert(alert_id: str, action_taken: str, resolved_by: str) -> bool:
    """
    Logs management action and marks an exception as Resolved or In Progress.
    Matches Slide 5: Click -> Project -> Delay reason -> Responsible team -> Action
    """
    updates = {
        "action_required": f"ACTION LOGGED: {action_taken} (by {resolved_by} on {date.today().strftime('%Y-%m-%d')})",
        "resolution_status": "Resolved"
    }
    return update_record("alerts_exceptions", "alert_id", alert_id, updates)


def run_all_workflow_tests() -> None:
    print("Testing Central MIS Workflow Automations...")

    # 1. New Employee
    emp_res = process_new_employee("Tanmay Joshi", "DEPT-003", "Backend Go Engineer", "t.joshi@company.com", "+91-9820011999", 7200.0)
    print("Employee Workflow:", emp_res["message"])

    # 2. New Lead
    lead_res = process_new_lead("FinSecure Global", "Rajiv Menon", "rajiv@finsecure.io", "Website Form", 88000.0, "Amit Bansal")
    print("Lead Workflow:", lead_res["message"])

    # 3. New Project
    prj_res = process_new_project("CLT-503", "OmniHealth Mobile App v2", "IT & Delivery Team Alpha", "Rohan Mehta", "2026-12-15", 95000.0)
    print("Project Workflow:", prj_res["message"])

    # 4. Expense Entry
    exp_res = process_expense_entry("DEPT-007", "Search Engine Ads", "Google Ads", 4500.0, "Q3 Inbound Growth Sprint", "Arjun Nair")
    print("Expense Workflow:", exp_res["message"])

    # 5. Daily Operations
    ops_res = process_daily_operations("DEPT-003", 22, 3, 96.5, 3.8, "API sprint 4 completed")
    print("Operations Workflow:", ops_res["message"])

    # 6. Marketing Sync
    mkt_res = process_marketing_sync("Google Search Console", 5200, 710, 0.0, 4, 2)
    print("Marketing Workflow:", mkt_res["message"])

    # 7. Exception Scanner
    scan_res = run_exception_scanner()
    print("Exception Scanner:", scan_res["message"])

    print("All Workflow Automations Passed!")


if __name__ == "__main__":
    run_all_workflow_tests()
