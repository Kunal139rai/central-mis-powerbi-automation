"""
Central MIS Data Models & Schemas
Defines structured schemas and validation rules for all 13 organizational entities
according to Section 7 of the Central MIS Architecture Specification.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any


@dataclass
class Department:
    dept_id: str          # e.g., DEPT-001
    name: str             # e.g., Finance, HR, Sales, IT / Projects, Operations, Marketing
    head: str             # Department head name
    monthly_budget: float # Allocated monthly operating budget
    headcount_target: int # Planned headcount


@dataclass
class Employee:
    employee_id: str      # e.g., EMP-101
    name: str
    dept_id: str          # FK -> Department
    role: str
    email: str
    phone: str
    joining_date: str     # YYYY-MM-DD
    salary_monthly: float
    status: str           # Active, On Leave, Resigned


@dataclass
class Client:
    client_id: str        # e.g., CLT-501
    name: str
    industry: str
    contact_person: str
    email: str
    phone: str
    status: str           # Active, Lead, Inactive
    tier: str             # Enterprise, Mid-Market, SMB


@dataclass
class Lead:
    lead_id: str          # e.g., LED-301
    client_name: str
    contact_person: str
    email: str
    source: str           # Website, Referral, Cold Outreach, LinkedIn, Google Ads
    stage: str            # New, Contacted, Proposal Sent, Negotiation, Won, Lost
    estimated_value: float
    assigned_sales_rep: str # Employee Name
    created_date: str     # YYYY-MM-DD
    next_follow_up: str   # YYYY-MM-DD
    status: str           # Open, Won, Stalled, Disqualified


@dataclass
class Project:
    project_id: str       # e.g., PRJ-201
    client_id: str        # FK -> Client
    name: str
    responsible_team: str # e.g., IT / Projects Team A
    project_manager: str  # Employee Name
    start_date: str       # YYYY-MM-DD
    deadline: str         # YYYY-MM-DD
    status: str           # On Track, Delayed, At Risk, Completed
    budget: float         # Contract / target revenue
    actual_cost: float    # Internal cost incurred
    billed_revenue: float # Invoiced so far
    completion_pct: float # 0 to 100
    delay_reason: Optional[str] = None # Reason if Delayed/At Risk


@dataclass
class Task:
    task_id: str          # e.g., TSK-1001
    project_id: str       # FK -> Project
    title: str
    assigned_to: str      # Employee Name
    due_date: str         # YYYY-MM-DD
    status: str           # Completed, In Progress, Overdue, Not Started
    qa_status: str        # Passed, Pending QA, Failed
    estimated_hours: float
    actual_hours: float


@dataclass
class Invoice:
    invoice_id: str       # e.g., INV-4001
    client_id: str        # FK -> Client
    project_id: str       # FK -> Project
    invoice_date: str     # YYYY-MM-DD
    due_date: str         # YYYY-MM-DD
    amount: float
    paid_amount: float
    status: str           # Paid, Partially Paid, Outstanding, Overdue
    payment_date: Optional[str] = None


@dataclass
class Expense:
    expense_id: str       # e.g., EXP-7001
    dept_id: str          # FK -> Department
    category: str         # Software, Cloud Infrastructure, Payroll, Office, Travel, Marketing
    vendor: str
    amount: float
    date: str             # YYYY-MM-DD
    description: str
    approved_by: str
    status: str           # Approved, Pending Review, Rejected


@dataclass
class AttendanceRecord:
    record_id: str        # e.g., ATT-9001
    employee_id: str      # FK -> Employee
    date: str             # YYYY-MM-DD
    status: str           # Present, Absent, Half Day, Approved Leave
    leave_type: Optional[str] = None # Casual, Sick, Annual, None


@dataclass
class DailyOperation:
    operation_id: str     # e.g., OPS-8001
    date: str             # YYYY-MM-DD
    dept_id: str          # FK -> Department
    tasks_completed: int
    tasks_pending: int
    productivity_pct: float # 0 to 100
    qa_pass_pct: float      # 0 to 100
    avg_turnaround_hours: float
    notes: Optional[str] = None


@dataclass
class MarketingMetric:
    metric_id: str        # e.g., MKT-6001
    date: str             # YYYY-MM-DD
    channel: str          # GA4 Organic, Google Search Console, LinkedIn Ads, Meta Ads, Email
    sessions_or_impressions: int
    clicks_or_visitors: int
    spend: float
    leads_generated: int
    conversions: int


@dataclass
class KPIMaster:
    kpi_id: str           # e.g., KPI-001
    metric_name: str
    category: str         # Finance, Sales, Projects, HR, Operations, Marketing
    target_value: float
    actual_value: float
    unit: str             # $, %, Count, Days
    status: str           # Green, Amber, Red
    calculation_method: str
    frequency: str        # Daily, Weekly, Monthly


@dataclass
class AlertException:
    alert_id: str         # e.g., ALT-101
    category: str         # Finance, Projects, Sales, HR, Operations
    severity: str         # Red, Amber, Green
    entity_id: str        # e.g., PRJ-202, INV-4003
    entity_name: str
    issue: str
    delay_days: int
    responsible_team: str
    owner: str
    action_required: str
    resolution_status: str # Open, In Progress, Resolved
    logged_date: str      # YYYY-MM-DD
