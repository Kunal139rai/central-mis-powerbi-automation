"""
Central MIS Database Layer
Manages SQLite database storage, schema definitions, initial seed data generation,
and CRUD / query interfaces for all 13 organizational modules.
"""

import sqlite3
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "central_mis.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(force_reseed: bool = False) -> None:
    """Initializes tables and seeds initial data if database is new or force_reseed=True."""
    conn = get_connection()
    cur = conn.cursor()

    # Create Tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        head TEXT NOT NULL,
        monthly_budget REAL NOT NULL,
        headcount_target INTEGER NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dept_id TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        joining_date TEXT NOT NULL,
        salary_monthly REAL NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        client_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        industry TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        status TEXT NOT NULL,
        tier TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        lead_id TEXT PRIMARY KEY,
        client_name TEXT NOT NULL,
        contact_person TEXT NOT NULL,
        email TEXT NOT NULL,
        source TEXT NOT NULL,
        stage TEXT NOT NULL,
        estimated_value REAL NOT NULL,
        assigned_sales_rep TEXT NOT NULL,
        created_date TEXT NOT NULL,
        next_follow_up TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        name TEXT NOT NULL,
        responsible_team TEXT NOT NULL,
        project_manager TEXT NOT NULL,
        start_date TEXT NOT NULL,
        deadline TEXT NOT NULL,
        status TEXT NOT NULL,
        budget REAL NOT NULL,
        actual_cost REAL NOT NULL,
        billed_revenue REAL NOT NULL,
        completion_pct REAL NOT NULL,
        delay_reason TEXT,
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        title TEXT NOT NULL,
        assigned_to TEXT NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT NOT NULL,
        qa_status TEXT NOT NULL,
        estimated_hours REAL NOT NULL,
        actual_hours REAL NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        project_id TEXT NOT NULL,
        invoice_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        amount REAL NOT NULL,
        paid_amount REAL NOT NULL,
        status TEXT NOT NULL,
        payment_date TEXT,
        FOREIGN KEY (client_id) REFERENCES clients(client_id),
        FOREIGN KEY (project_id) REFERENCES projects(project_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        expense_id TEXT PRIMARY KEY,
        dept_id TEXT NOT NULL,
        category TEXT NOT NULL,
        vendor TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        approved_by TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        record_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        leave_type TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS daily_operations (
        operation_id TEXT PRIMARY KEY,
        date TEXT NOT NULL,
        dept_id TEXT NOT NULL,
        tasks_completed INTEGER NOT NULL,
        tasks_pending INTEGER NOT NULL,
        productivity_pct REAL NOT NULL,
        qa_pass_pct REAL NOT NULL,
        avg_turnaround_hours REAL NOT NULL,
        notes TEXT,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS marketing_metrics (
        metric_id TEXT PRIMARY KEY,
        date TEXT NOT NULL,
        channel TEXT NOT NULL,
        sessions_or_impressions INTEGER NOT NULL,
        clicks_or_visitors INTEGER NOT NULL,
        spend REAL NOT NULL,
        leads_generated INTEGER NOT NULL,
        conversions INTEGER NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS kpi_master (
        kpi_id TEXT PRIMARY KEY,
        metric_name TEXT NOT NULL,
        category TEXT NOT NULL,
        target_value REAL NOT NULL,
        actual_value REAL NOT NULL,
        unit TEXT NOT NULL,
        status TEXT NOT NULL,
        calculation_method TEXT NOT NULL,
        frequency TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts_exceptions (
        alert_id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        severity TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        entity_name TEXT NOT NULL,
        issue TEXT NOT NULL,
        delay_days INTEGER NOT NULL,
        responsible_team TEXT NOT NULL,
        owner TEXT NOT NULL,
        action_required TEXT NOT NULL,
        resolution_status TEXT NOT NULL,
        logged_date TEXT NOT NULL
    );
    """)

    conn.commit()

    # Check if seeding is needed
    cur.execute("SELECT COUNT(*) FROM departments")
    dept_count = cur.fetchone()[0]
    if dept_count == 0 or force_reseed:
        _seed_data(conn)

    conn.close()


def _seed_data(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # Clear existing tables if re-seeding
    for table in [
        "alerts_exceptions", "kpi_master", "marketing_metrics",
        "daily_operations", "attendance", "expenses", "invoices",
        "tasks", "projects", "leads", "clients", "employees", "departments"
    ]:
        cur.execute(f"DELETE FROM {table}")

    # 1. Departments
    departments = [
        ("DEPT-001", "Executive Management", "Vikram Malhotra (MD)", 25000.0, 3),
        ("DEPT-002", "Finance & Accounts", "Sunita Sharma (CFO)", 18000.0, 5),
        ("DEPT-003", "IT & Engineering", "Rajesh Varma (VP Tech)", 65000.0, 18),
        ("DEPT-004", "Sales & CRM", "Ananya Deshmukh (Head Sales)", 35000.0, 8),
        ("DEPT-005", "Operations & Delivery", "Manoj Tiwari (Head Ops)", 40000.0, 12),
        ("DEPT-006", "Human Resources", "Pooja Hegde (Head HR)", 15000.0, 4),
        ("DEPT-007", "Marketing & Growth", "Arjun Nair (Head Marketing)", 28000.0, 5),
    ]
    cur.executemany("INSERT INTO departments VALUES (?, ?, ?, ?, ?)", departments)

    # 2. Employees
    employees = [
        ("EMP-101", "Vikram Malhotra", "DEPT-001", "Managing Director", "v.malhotra@company.com", "+91-9820011221", "2021-01-15", 22000.0, "Active"),
        ("EMP-102", "Sunita Sharma", "DEPT-002", "Chief Financial Officer", "s.sharma@company.com", "+91-9820011222", "2021-03-01", 16000.0, "Active"),
        ("EMP-103", "Rajesh Varma", "DEPT-003", "VP Technology & Delivery", "r.varma@company.com", "+91-9820011223", "2021-06-10", 17500.0, "Active"),
        ("EMP-104", "Ananya Deshmukh", "DEPT-004", "VP Sales & Partnerships", "a.deshmukh@company.com", "+91-9820011224", "2021-08-15", 15000.0, "Active"),
        ("EMP-105", "Manoj Tiwari", "DEPT-005", "Head of Operations", "m.tiwari@company.com", "+91-9820011225", "2022-01-10", 14000.0, "Active"),
        ("EMP-106", "Pooja Hegde", "DEPT-006", "Head of People & HR", "p.hegde@company.com", "+91-9820011226", "2022-02-01", 12000.0, "Active"),
        ("EMP-107", "Arjun Nair", "DEPT-007", "Marketing Director", "a.nair@company.com", "+91-9820011227", "2022-04-15", 13000.0, "Active"),
        ("EMP-108", "Rohan Mehta", "DEPT-003", "Lead Solutions Architect", "r.mehta@company.com", "+91-9820011228", "2022-07-01", 11500.0, "Active"),
        ("EMP-109", "Priya Sen", "DEPT-003", "Senior Cloud Engineer", "p.sen@company.com", "+91-9820011229", "2022-09-15", 9500.0, "Active"),
        ("EMP-110", "Amit Bansal", "DEPT-004", "Enterprise Sales Lead", "a.bansal@company.com", "+91-9820011230", "2023-01-10", 8500.0, "Active"),
        ("EMP-111", "Sneha Iyer", "DEPT-005", "Senior QA Lead", "s.iyer@company.com", "+91-9820011231", "2023-03-20", 8000.0, "Active"),
        ("EMP-112", "Karan Patel", "DEPT-002", "Senior Financial Analyst", "k.patel@company.com", "+91-9820011232", "2023-05-15", 7500.0, "Active"),
        ("EMP-113", "Neha Kapoor", "DEPT-007", "Growth & SEO Specialist", "n.kapoor@company.com", "+91-9820011233", "2023-08-01", 6500.0, "Active"),
        ("EMP-114", "Deepak Rao", "DEPT-003", "Full Stack Developer", "d.rao@company.com", "+91-9820011234", "2024-01-15", 6000.0, "Active"),
        ("EMP-115", "Divya Joshi", "DEPT-005", "Operations Coordinator", "d.joshi@company.com", "+91-9820011235", "2024-03-01", 5000.0, "Active"),
    ]
    cur.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", employees)

    # 3. Clients
    clients = [
        ("CLT-501", "Zenith Retail Group", "Retail & E-commerce", "Kabir Bedi", "k.bedi@zenithretail.com", "+91-9988771101", "Active", "Enterprise"),
        ("CLT-502", "CloudScale FinTech", "Financial Services", "Shalini Roy", "s.roy@cloudscalefintech.io", "+91-9988771102", "Active", "Enterprise"),
        ("CLT-503", "OmniHealth Systems", "Healthcare & Pharma", "Dr. A. Kulkarni", "kulkarni@omnihealth.org", "+91-9988771103", "Active", "Enterprise"),
        ("CLT-504", "Apex Logistics Ltd", "Supply Chain & Transport", "Gaurav Singhal", "g.singhal@apexlogistics.in", "+91-9988771104", "Active", "Mid-Market"),
        ("CLT-505", "Horizon Media Works", "Digital Media & AdTech", "Tarun Khanna", "tarun@horizonmedia.co", "+91-9988771105", "Active", "Mid-Market"),
        ("CLT-506", "Nova Precision Mfg", "Industrial Manufacturing", "Sunil Chawla", "s.chawla@novamfg.com", "+91-9988771106", "Active", "SMB"),
        ("CLT-507", "Sterling Hospitality", "Hotels & Resorts", "Ritu Sethi", "r.sethi@sterlinghotels.com", "+91-9988771107", "Lead", "Mid-Market"),
    ]
    cur.executemany("INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?, ?)", clients)

    # 4. Leads
    leads = [
        ("LED-301", "Sterling Hospitality", "Ritu Sethi", "r.sethi@sterlinghotels.com", "Website Form", "Proposal Sent", 65000.0, "Amit Bansal", "2026-08-10", "2026-09-08", "Open"),
        ("LED-302", "BioGen Diagnostics", "Dr. H. Saxena", "hsaxena@biogen.in", "LinkedIn Ads", "Negotiation", 85000.0, "Ananya Deshmukh", "2026-08-05", "2026-09-07", "Open"),
        ("LED-303", "Metro Infra Rail", "K. N. Murthy", "kn.murthy@metroinfra.gov", "Referral", "Won", 120000.0, "Amit Bansal", "2026-07-15", "2026-08-20", "Won"),
        ("LED-304", "Pulse Fitness Tech", "Kareena Luthra", "kareena@pulsefit.co", "Google Search", "Contacted", 35000.0, "Amit Bansal", "2026-08-22", "2026-09-10", "Open"),
        ("LED-305", "Vanguard Cyber Systems", "Col. R. S. Negi", "negi@vanguardcyber.net", "Cold Outreach", "Proposal Sent", 95000.0, "Ananya Deshmukh", "2026-08-14", "2026-09-09", "Open"),
        ("LED-306", "GreenLeaf Agrotech", "Rameshwar Patel", "ramesh@greenleafagro.com", "Website Form", "New", 28000.0, "Amit Bansal", "2026-09-02", "2026-09-07", "Open"),
        ("LED-307", "QuickShip Global", "Tanvi Merchant", "tanvi@quickship.com", "Google Ads", "Stalled", 55000.0, "Amit Bansal", "2026-07-28", "2026-08-15", "Stalled"),
        ("LED-308", "EduSpark Academy", "Prof. V. Raman", "raman@eduspark.org", "Referral", "Disqualified", 18000.0, "Amit Bansal", "2026-08-01", "2026-08-10", "Disqualified"),
    ]
    cur.executemany("INSERT INTO leads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", leads)

    # 5. Projects (Includes the 2 RED Delayed projects matching Slide 5 & Section 14)
    projects = [
        ("PRJ-201", "CLT-501", "Global Retail Portal ERP Integration", "IT & Delivery Team Alpha", "Rohan Mehta", "2026-05-01", "2026-08-25", "Delayed", 145000.0, 118000.0, 95000.0, 78.0, "Third-party ERP connector spec change by client; waiting for revised API token"),
        ("PRJ-202", "CLT-502", "FinTech Payment Gateway Revamp", "IT & Delivery Team Beta", "Rajesh Varma", "2026-06-01", "2026-08-30", "Delayed", 160000.0, 135000.0, 110000.0, 82.0, "Statutory security compliance audit pendency with external auditing agency"),
        ("PRJ-203", "CLT-503", "OmniHealth Patient Record System", "IT & Delivery Team Alpha", "Rohan Mehta", "2026-06-15", "2026-10-31", "On Track", 185000.0, 72000.0, 90000.0, 48.0, None),
        ("PRJ-204", "CLT-504", "Apex Smart Fleet Telematics Hub", "Operations & Tech", "Deepak Rao", "2026-04-10", "2026-08-15", "Completed", 95000.0, 68000.0, 95000.0, 100.0, None),
        ("PRJ-205", "CLT-505", "Horizon Media Ad Bidding Pipeline", "Engineering Core", "Priya Sen", "2026-07-01", "2026-11-15", "On Track", 110000.0, 41000.0, 55000.0, 42.0, None),
        ("PRJ-206", "CLT-506", "Nova Shopfloor IoT & QA Telemetry", "Engineering Core", "Deepak Rao", "2026-07-20", "2026-09-30", "At Risk", 75000.0, 48000.0, 35000.0, 52.0, "Hardware sensor delivery delayed from vendor by 7 business days"),
    ]
    cur.executemany("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", projects)

    # 6. Tasks
    tasks = [
        ("TSK-1001", "PRJ-201", "Client ERP API Connector Refactor", "Rohan Mehta", "2026-08-20", "Overdue", "Pending QA", 40.0, 52.0),
        ("TSK-1002", "PRJ-201", "Catalog Sync Module Unit Tests", "Deepak Rao", "2026-08-24", "In Progress", "Pending QA", 32.0, 28.0),
        ("TSK-1003", "PRJ-201", "End-to-end Inventory Load Testing", "Sneha Iyer", "2026-08-28", "Not Started", "Pending QA", 24.0, 0.0),
        ("TSK-1004", "PRJ-202", "PCI-DSS v4.0 Audit Remediation", "Rajesh Varma", "2026-08-25", "Overdue", "Pending QA", 36.0, 45.0),
        ("TSK-1005", "PRJ-202", "AES-256 Token Vault Re-encryption", "Priya Sen", "2026-08-29", "In Progress", "Passed", 28.0, 30.0),
        ("TSK-1006", "PRJ-203", "FHIR / HL7 Data Pipeline Ingestion", "Rohan Mehta", "2026-09-15", "In Progress", "Pending QA", 50.0, 35.0),
        ("TSK-1007", "PRJ-203", "Role-Based Doctor Portal Auth", "Deepak Rao", "2026-09-20", "Completed", "Passed", 25.0, 24.0),
        ("TSK-1008", "PRJ-204", "GPS Live Stream Kafka Consumer", "Deepak Rao", "2026-08-10", "Completed", "Passed", 45.0, 42.0),
        ("TSK-1009", "PRJ-205", "Real-Time Bidding Bidder Engine", "Priya Sen", "2026-09-30", "In Progress", "Pending QA", 60.0, 38.0),
        ("TSK-1010", "PRJ-206", "Modbus Gateway Sensor Firmware", "Deepak Rao", "2026-09-05", "In Progress", "Failed", 35.0, 39.0),
    ]
    cur.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", tasks)

    # 7. Invoices (Includes Overdue Receivables > 30 Days)
    invoices = [
        ("INV-4001", "CLT-501", "PRJ-201", "2026-06-01", "2026-07-01", 50000.0, 50000.0, "Paid", "2026-06-28"),
        ("INV-4002", "CLT-501", "PRJ-201", "2026-07-05", "2026-08-05", 45000.0, 0.0, "Overdue", None), # 32 days overdue
        ("INV-4003", "CLT-502", "PRJ-202", "2026-06-15", "2026-07-15", 60000.0, 60000.0, "Paid", "2026-07-12"),
        ("INV-4004", "CLT-502", "PRJ-202", "2026-07-20", "2026-08-20", 50000.0, 20000.0, "Overdue", "2026-08-18"), # 17 days overdue on remaining 30k
        ("INV-4005", "CLT-503", "PRJ-203", "2026-07-01", "2026-08-01", 45000.0, 45000.0, "Paid", "2026-07-29"),
        ("INV-4006", "CLT-503", "PRJ-203", "2026-08-15", "2026-09-15", 45000.0, 0.0, "Outstanding", None),
        ("INV-4007", "CLT-504", "PRJ-204", "2026-06-01", "2026-07-01", 50000.0, 50000.0, "Paid", "2026-06-25"),
        ("INV-4008", "CLT-504", "PRJ-204", "2026-08-15", "2026-09-15", 45000.0, 45000.0, "Paid", "2026-08-25"),
        ("INV-4009", "CLT-505", "PRJ-205", "2026-07-10", "2026-08-10", 35000.0, 35000.0, "Paid", "2026-08-08"),
        ("INV-4010", "CLT-505", "PRJ-205", "2026-08-20", "2026-09-20", 20000.0, 0.0, "Outstanding", None),
        ("INV-4011", "CLT-506", "PRJ-206", "2026-08-01", "2026-08-31", 35000.0, 0.0, "Overdue", None), # 6 days overdue
    ]
    cur.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", invoices)

    # 8. Expenses
    expenses = [
        ("EXP-7001", "DEPT-003", "Cloud Infrastructure", "Amazon Web Services", 6850.0, "2026-08-05", "Monthly AWS production cloud hosting", "Rajesh Varma", "Approved"),
        ("EXP-7002", "DEPT-003", "Software Licences", "Atlassian Jira & GitHub", 1950.0, "2026-08-08", "Dev tools enterprise subscriptions", "Rajesh Varma", "Approved"),
        ("EXP-7003", "DEPT-007", "Digital Marketing", "Google Ads & Meta", 8500.0, "2026-08-10", "B2B Lead Generation campaign spend", "Arjun Nair", "Approved"),
        ("EXP-7004", "DEPT-007", "Content & SEO Tools", "Semrush & Ahrefs", 1200.0, "2026-08-12", "SEO keyword tracking software", "Arjun Nair", "Approved"),
        ("EXP-7005", "DEPT-005", "Office & Facilities", "Regus Business Center", 5500.0, "2026-08-01", "HQ office lease and utilities", "Manoj Tiwari", "Approved"),
        ("EXP-7006", "DEPT-004", "Travel & Client Meetings", "MakeMyTrip Corporate", 3400.0, "2026-08-18", "Client pitch flights for Ananya and Amit", "Ananya Deshmukh", "Approved"),
        ("EXP-7007", "DEPT-002", "Audit & Compliance", "KPMG Advisory", 6500.0, "2026-08-22", "Quarterly statutory tax and audit filing", "Sunita Sharma", "Approved"),
        ("EXP-7008", "DEPT-006", "Recruitment & HR Tech", "LinkedIn Recruiter", 2200.0, "2026-08-15", "Talent sourcing for Cloud and Ops roles", "Pooja Hegde", "Approved"),
        ("EXP-7009", "DEPT-003", "Hardware Equipment", "Dell Technologies", 7800.0, "2026-08-28", "High-performance developer laptops", "Rajesh Varma", "Approved"),
        ("EXP-7010", "DEPT-005", "QA Lab & Test Devices", "Electronics Hub", 2600.0, "2026-08-29", "IoT testing boards and sensors", "Manoj Tiwari", "Approved"),
    ]
    cur.executemany("INSERT INTO expenses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", expenses)

    # 9. Attendance (Recent 7 days sample for 15 employees)
    attendance_records = []
    att_idx = 9001
    base_date = date(2026, 8, 31)
    for day_offset in range(7):
        curr_d = base_date + timedelta(days=day_offset)
        curr_d_str = curr_d.strftime("%Y-%m-%d")
        if curr_d.weekday() >= 5: # Skip weekends
            continue
        for emp in employees:
            emp_id = emp[0]
            # Introduce a couple realistic leaves/absences
            if emp_id == "EMP-109" and day_offset in [1, 2]:
                att_status = "Approved Leave"
                leave_type = "Sick"
            elif emp_id == "EMP-114" and day_offset == 3:
                att_status = "Absent"
                leave_type = None
            elif emp_id == "EMP-110" and day_offset == 4:
                att_status = "Half Day"
                leave_type = "Casual"
            else:
                att_status = "Present"
                leave_type = None

            attendance_records.append((
                f"ATT-{att_idx}", emp_id, curr_d_str, att_status, leave_type
            ))
            att_idx += 1
    cur.executemany("INSERT INTO attendance VALUES (?, ?, ?, ?, ?)", attendance_records)

    # 10. Daily Operations (Past 14 Days)
    ops_records = []
    ops_idx = 8001
    ops_start = date(2026, 8, 20)
    for d in range(15):
        curr_d = ops_start + timedelta(days=d)
        curr_d_str = curr_d.strftime("%Y-%m-%d")
        # Department 003 IT
        ops_records.append((
            f"OPS-{ops_idx}", curr_d_str, "DEPT-003", 18 + (d % 5), 4 + (d % 3),
            round(88.0 + (d % 7) * 1.5, 1), round(94.0 + (d % 4) * 1.2, 1),
            round(4.2 - (d % 3) * 0.2, 1), "Core engineering sprints on track"
        ))
        ops_idx += 1
        # Department 005 Ops / QA
        ops_records.append((
            f"OPS-{ops_idx}", curr_d_str, "DEPT-005", 26 + (d % 6), 5 + (d % 4),
            round(85.0 + (d % 6) * 1.8, 1), round(91.5 + (d % 5) * 1.1, 1),
            round(3.8 - (d % 4) * 0.15, 1), "Daily QA tickets and release audits"
        ))
        ops_idx += 1
    cur.executemany("INSERT INTO daily_operations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", ops_records)

    # 11. Marketing Metrics (Past 14 Days)
    mkt_records = []
    mkt_idx = 6001
    mkt_start = date(2026, 8, 20)
    for d in range(15):
        curr_d = mkt_start + timedelta(days=d)
        curr_d_str = curr_d.strftime("%Y-%m-%d")
        # GA4 Organic
        mkt_records.append((
            f"MKT-{mkt_idx}", curr_d_str, "GA4 Organic Search",
            1240 + d * 35, 840 + d * 25, 0.0, 3 + (d % 3), 1 + (d % 2)
        ))
        mkt_idx += 1
        # Google Search Console
        mkt_records.append((
            f"MKT-{mkt_idx}", curr_d_str, "Google Search Console",
            4850 + d * 110, 610 + d * 20, 0.0, 2 + (d % 2), 1
        ))
        mkt_idx += 1
        # LinkedIn Ads
        mkt_records.append((
            f"MKT-{mkt_idx}", curr_d_str, "LinkedIn B2B Ads",
            3200 + d * 80, 195 + d * 15, 280.0 + (d % 4) * 35.0, 4 + (d % 3), 1 + (d % 3)
        ))
        mkt_idx += 1
    cur.executemany("INSERT INTO marketing_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?)", mkt_records)

    # 12. KPI Master (Company-wide Target vs Actuals across all 6 departments)
    kpis = [
        ("KPI-001", "Monthly Revenue Run Rate", "Finance", 125000.0, 135000.0, "$", "Green", "Sum of current month recognized billings", "Monthly"),
        ("KPI-002", "Operating Profit Margin", "Finance", 22.0, 24.5, "%", "Green", "(Revenue - Operating Cost) / Revenue", "Monthly"),
        ("KPI-003", "Overdue Accounts Receivable", "Finance", 20000.0, 81000.0, "$", "Red", "Total outstanding invoices past due date", "Weekly"),
        ("KPI-004", "New Qualified Pipeline Value", "Sales", 350000.0, 413000.0, "$", "Green", "Total weighted pipeline value in CRM", "Monthly"),
        ("KPI-005", "Lead to Deal Conversion Rate", "Sales", 18.0, 15.2, "%", "Amber", "Won deals / Total closed opportunities", "Monthly"),
        ("KPI-006", "On-Time Project Delivery Rate", "Projects", 90.0, 66.7, "%", "Red", "Projects delivering on schedule without milestone breach", "Monthly"),
        ("KPI-007", "Active Delayed Projects Count", "Projects", 0.0, 2.0, "Count", "Red", "Active projects with status Delayed or past SLA", "Daily"),
        ("KPI-008", "Daily Workforce Attendance", "HR", 95.0, 93.8, "%", "Green", "Present employees / Total active headcount", "Daily"),
        ("KPI-009", "Operations QA First-Pass Rate", "Operations", 95.0, 92.4, "%", "Amber", "Tasks passed QA on first submission / Total QA tasks", "Weekly"),
        ("KPI-010", "Digital Inbound Lead Volume", "Marketing", 100.0, 118.0, "Count", "Green", "Unique leads captured via website & organic channels", "Monthly"),
    ]
    cur.executemany("INSERT INTO kpi_master VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", kpis)

    # 13. Alerts & Exceptions (Management by Exception - Slide 5 & Section 14)
    alerts = [
        ("ALT-101", "Projects", "Red", "PRJ-201", "Global Retail Portal ERP Integration", "Project delayed by 14 days due to client ERP API specification change", 14, "IT & Delivery Team Alpha", "Rohan Mehta", "Convene technical alignment with client CTO Kabir Bedi to lock API spec", "Open", "2026-08-25"),
        ("ALT-102", "Projects", "Red", "PRJ-202", "FinTech Payment Gateway Revamp", "Project delayed by 9 days due to external PCI-DSS compliance audit backlog", 9, "IT & Delivery Team Beta", "Rajesh Varma", "Escalate to lead auditor for expedited certification clearance", "Open", "2026-08-30"),
        ("ALT-103", "Finance", "Red", "INV-4002", "Zenith Retail Group - Invoice #4002", "Payment of $45,000 is 32 days overdue past agreed credit terms", 32, "Finance & Accounts", "Sunita Sharma", "Issue formal CFO escalation letter; pause delivery milestone #4 pending payment", "Open", "2026-08-05"),
        ("ALT-104", "Finance", "Amber", "INV-4004", "CloudScale FinTech - Invoice #4004", "Balance $30,000 overdue by 17 days past due date", 17, "Finance & Accounts", "Sunita Sharma", "Finance follow-up with Shalini Roy; scheduled for release next payment run", "In Progress", "2026-08-20"),
        ("ALT-105", "Projects", "Amber", "PRJ-206", "Nova Shopfloor IoT & QA Telemetry", "Sensor delivery from hardware vendor delayed by 7 days; risk of missing deadline", 7, "Engineering Core", "Deepak Rao", "Authorize express courier from alternate local supplier in Pune", "Open", "2026-08-28"),
        ("ALT-106", "Sales", "Amber", "LED-307", "QuickShip Global CRM Lead", "High-value lead ($55,000) stalled for 22 days without client response", 22, "Sales & CRM", "Amit Bansal", "VP Sales Ananya Deshmukh to schedule executive breakfast meeting with client VP", "In Progress", "2026-08-15"),
        ("ALT-107", "Operations", "Amber", "OPS-8018", "Modbus Firmware QA Failure Rate", "QA first-pass yield slipped to 89.2% for shopfloor telemetry modules", 4, "Operations & Delivery", "Sneha Iyer", "Implement automated linting checks and pre-release regression battery", "Open", "2026-09-01"),
    ]
    cur.executemany("INSERT INTO alerts_exceptions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", alerts)

    conn.commit()


def load_all_tables() -> Dict[str, pd.DataFrame]:
    """Loads all 13 relational tables as pandas DataFrames."""
    conn = get_connection()
    tables = [
        "departments", "employees", "clients", "leads", "projects",
        "tasks", "invoices", "expenses", "attendance", "daily_operations",
        "marketing_metrics", "kpi_master", "alerts_exceptions"
    ]
    dfs = {}
    for tbl in tables:
        dfs[tbl] = pd.read_sql_query(f"SELECT * FROM {tbl}", conn)
    conn.close()
    return dfs


def insert_record(table_name: str, record: Dict[str, Any]) -> bool:
    """Inserts a new record into any table."""
    conn = get_connection()
    cur = conn.cursor()
    columns = list(record.keys())
    placeholders = ", ".join(["?"] * len(columns))
    col_str = ", ".join(columns)
    vals = list(record.values())

    query = f"INSERT INTO {table_name} ({col_str}) VALUES ({placeholders})"
    try:
        cur.execute(query, vals)
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error inserting into {table_name}: {e}")
        success = False
    finally:
        conn.close()
    return success


def update_record(table_name: str, id_col: str, id_val: Any, updates: Dict[str, Any]) -> bool:
    """Updates fields in a record by ID."""
    conn = get_connection()
    cur = conn.cursor()
    set_clauses = [f"{k} = ?" for k in updates.keys()]
    set_str = ", ".join(set_clauses)
    vals = list(updates.values()) + [id_val]

    query = f"UPDATE {table_name} SET {set_str} WHERE {id_col} = ?"
    try:
        cur.execute(query, vals)
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error updating {table_name}: {e}")
        success = False
    finally:
        conn.close()
    return success


if __name__ == "__main__":
    print("Initializing Central MIS Database...")
    init_db(force_reseed=True)
    dfs = load_all_tables()
    for name, df in dfs.items():
        print(f"Table '{name}': {len(df)} rows")
    print("Central MIS Database initialized successfully!")
