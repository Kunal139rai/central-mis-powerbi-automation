"""
================================================================================
CENTRAL MANAGEMENT INFORMATION SYSTEM & DIRECTOR CONTROL ROOM
================================================================================
Comprehensive executive management application implementing the 8-page
Director Dashboard specification, 6 automated organizational workflows,
Management-by-Exception engine, and Power BI integration hub.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import altair as alt
import os
import sys

# Ensure backend package is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import init_db, load_all_tables, get_connection, insert_record, update_record
from backend.automation import (
    process_new_employee, process_new_lead, process_new_project,
    process_expense_entry, process_daily_operations, process_marketing_sync,
    run_exception_scanner, resolve_alert
)
from backend.export_powerbi import export_all_to_excel_and_csv
from backend.executive_brief import generate_director_brief
from backend import config

# Page Configuration
st.set_page_config(
    page_title="Central MIS | Director Control Room",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0F172A;
        margin: 4px 0;
    }
    .badge-red {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-amber {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-green {
        background-color: #D1FAE5;
        color: #047857;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
    }
    .exception-card-red {
        background: #FFF5F5;
        border-left: 6px solid #EF4444;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .exception-card-amber {
        background: #FFFBEB;
        border-left: 6px solid #F59E0B;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .exception-card-green {
        background: #F0FDF4;
        border-left: 6px solid #10B981;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Ensure database is initialized
init_db(force_reseed=False)

# Load current tables into memory
data = load_all_tables()


# ==========================================
# SIDEBAR NAVIGATION & EXECUTIVE CONTROLS
# ==========================================
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=400&auto=format&fit=crop&q=60", use_container_width=True)
    st.markdown("### 🏢 **Central MIS Control Room**")
    st.caption("One Central View of the Entire Company")

    nav_selection = st.radio(
        "Select Management Console:",
        [
            "1. Director Overview",
            "2. Finance",
            "3. Sales & CRM",
            "4. Projects",
            "5. HR & Workforce",
            "6. Operations & QA",
            "7. Marketing & SEO",
            "8. Alerts & Exception Center",
            "9. Automation Intake Center",
            "10. Power BI Integration Hub"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("#### ⚡ **Quick Automation Actions**")

    if st.button("🔄 Sync & Scan Exceptions", use_container_width=True):
        scan_res = run_exception_scanner()
        st.success(f"Scanned! {scan_res['red_exceptions']} Red, {scan_res['amber_exceptions']} Amber.")
        st.rerun()

    if st.button("📊 Export Power BI Model", use_container_width=True):
        res = export_all_to_excel_and_csv()
        st.success("Power BI Excel & CSV Data Model Generated!")

    st.markdown("---")
    st.caption("Logged in as: **Managing Director**")
    st.caption("Target System: **Power BI + Microsoft 365**")


# ==========================================
# PAGE 1: DIRECTOR / CEO OVERVIEW
# ==========================================
if nav_selection == "1. Director Overview":
    st.title("🎯 Managing Director Central Dashboard")
    st.markdown("#### *How is the company performing right now?*")

    # High-level Alert Ticker
    alerts_df = data["alerts_exceptions"]
    red_alerts = alerts_df[(alerts_df["severity"] == "Red") & (alerts_df["resolution_status"] != "Resolved")]
    amber_alerts = alerts_df[(alerts_df["severity"] == "Amber") & (alerts_df["resolution_status"] != "Resolved")]

    if not red_alerts.empty:
        st.error(f"🚨 **CRITICAL ATTENTION REQUIRED**: {len(red_alerts)} Red Exceptions Active! Review Section 8 (Alerts & Exceptions) below.")
    elif not amber_alerts.empty:
        st.warning(f"⚠️ **MONITORING NOTICE**: {len(amber_alerts)} Amber Exceptions Pending Action.")
    else:
        st.success("✅ **ALL SYSTEMS NOMINAL**: Company operating within standard target variance.")

    # Top KPI Metrics Cards Row
    invoices = data["invoices"]
    expenses = data["expenses"]
    projects = data["projects"]
    leads = data["leads"]
    employees = data["employees"]

    tot_rev = invoices["amount"].sum()
    tot_exp = expenses["amount"].sum()
    net_profit = tot_rev - tot_exp
    margin_pct = (net_profit / tot_rev * 100) if tot_rev > 0 else 0.0

    active_prjs = len(projects[projects["status"].isin(["On Track", "Delayed", "At Risk"])])
    delayed_prjs = len(projects[projects["status"] == "Delayed"])
    open_pipeline = leads[leads["status"] == "Open"]["estimated_value"].sum()
    active_emp = len(employees[employees["status"] == "Active"])

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Billed Revenue</div>
            <div class="metric-value">${tot_rev:,.0f}</div>
            <span class="badge-green">Target: $450k (+6.7%)</span>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Operating Profit</div>
            <div class="metric-value">${net_profit:,.0f}</div>
            <span class="badge-green">Margin: {margin_pct:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Active Projects</div>
            <div class="metric-value">{active_prjs}</div>
            <span class="{'badge-red' if delayed_prjs > 0 else 'badge-green'}">{delayed_prjs} Delayed</span>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CRM Pipeline</div>
            <div class="metric-value">${open_pipeline:,.0f}</div>
            <span class="badge-green">6 Active Deals</span>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Active Workforce</div>
            <div class="metric-value">{active_emp}</div>
            <span class="badge-green">93.8% Attendance</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Two column: Target vs Actual KPIs + Management By Exception Spotlight
    col_kpi, col_exc = st.columns([3, 2])

    with col_kpi:
        st.subheader("📈 Company KPI Master (Target vs. Actual)")
        kpi_df = data["kpi_master"].copy()

        # Format status badge
        def format_status(s):
            if s == "Green":
                return "🟢 Green (On Target)"
            elif s == "Amber":
                return "🟡 Amber (Monitor)"
            else:
                return "🔴 Red (Action Needed)"

        kpi_display = kpi_df[["metric_name", "category", "target_value", "actual_value", "unit", "status"]].copy()
        kpi_display["status_label"] = kpi_display["status"].apply(format_status)
        st.dataframe(
            kpi_display.rename(columns={
                "metric_name": "KPI Metric",
                "category": "Department",
                "target_value": "Target",
                "actual_value": "Actual",
                "unit": "Unit",
                "status_label": "Health Status"
            }),
            use_container_width=True,
            hide_index=True
        )

        # Altair Target vs Actual Bar Chart for Key Metrics
        chart_data = kpi_df[kpi_df["unit"].isin(["$", "%"])].copy()
        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X("metric_name:N", title="KPI Metric", axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("actual_value:Q", title="Actual Value"),
            color=alt.Color("status:N", scale=alt.Scale(domain=["Green", "Amber", "Red"], range=["#10B981", "#F59E0B", "#EF4444"]))
        ).properties(height=260)
        st.altair_chart(chart, use_container_width=True)

    with col_exc:
        st.subheader("🚨 Management By Exception (Slide 5)")
        st.caption("Click into Red/Amber items to review root cause and responsible owner:")

        for _, alert in alerts_df[alerts_df["resolution_status"] != "Resolved"].iterrows():
            css_class = "exception-card-red" if alert["severity"] == "Red" else ("exception-card-amber" if alert["severity"] == "Amber" else "exception-card-green")
            badge = f'<span class="badge-{alert["severity"].lower()}">{alert["severity"].upper()}</span>'

            st.markdown(f"""
            <div class="{css_class}">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <strong>{alert["entity_name"]}</strong>
                    {badge}
                </div>
                <div style="font-size:0.85rem; color:#475569; margin: 4px 0;">
                    <strong>Issue:</strong> {alert["issue"]}
                </div>
                <div style="font-size:0.8rem; color:#64748B;">
                    <strong>Owner:</strong> {alert["owner"]} ({alert["responsible_team"]}) | <strong>Delay:</strong> {alert["delay_days"]} days
                </div>
                <div style="font-size:0.8rem; color:#1E3A8A; margin-top:4px;">
                    👉 <em>Action:</em> {alert["action_required"]}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# PAGE 2: FINANCE DASHBOARD
# ==========================================
elif nav_selection == "2. Finance":
    st.title("💰 Finance & Accounts Control Room")
    st.caption("Revenue, Expenses, Receivables, Operating Profitability, and Cashflow")

    invoices = data["invoices"]
    expenses = data["expenses"]
    depts = data["departments"]

    tot_rev = invoices["amount"].sum()
    tot_paid = invoices["paid_amount"].sum()
    tot_exp = expenses["amount"].sum()
    unpaid_ar = (invoices["amount"] - invoices["paid_amount"]).sum()
    overdue_ar = invoices[invoices["status"] == "Overdue"]
    overdue_amt = (overdue_ar["amount"] - overdue_ar["paid_amount"]).sum()

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.metric("Total Invoiced Revenue", f"${tot_rev:,.2f}", "+14.2% MoM")
    with f2:
        st.metric("Total Operating Expenses", f"${tot_exp:,.2f}", "Within Budget")
    with f3:
        st.metric("Net Operating Margin", f"{(tot_rev - tot_exp) / tot_rev * 100:.1f}%", f"${tot_rev - tot_exp:,.2f}")
    with f4:
        st.metric("Overdue Receivables", f"${overdue_amt:,.2f}", f"{len(overdue_ar)} Invoices", delta_color="inverse")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("📊 Departmental Budget vs. Actual Spend")
        exp_by_dept = expenses.groupby("dept_id")["amount"].sum().reset_index()
        dept_merged = pd.merge(depts, exp_by_dept, on="dept_id", how="left").fillna(0)
        dept_merged.rename(columns={"amount": "actual_spend"}, inplace=True)

        chart_df = dept_merged.melt(id_vars=["name"], value_vars=["monthly_budget", "actual_spend"], var_name="Type", value_name="Amount")
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X("name:N", title="Department", axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("Amount:Q", title="USD ($)"),
            color=alt.Color("Type:N", scale=alt.Scale(domain=["monthly_budget", "actual_spend"], range=["#94A3B8", "#1E3A8A"])),
            xOffset="Type:N"
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)

    with col_chart2:
        st.subheader("⏳ Accounts Receivable Aging Breakdown")
        today = date.today()
        aging_bins = {"Current (0-30 days)": 0.0, "Overdue (31-60 days)": 0.0, "Critical (60+ days)": 0.0}

        for _, inv in invoices[invoices["status"].isin(["Overdue", "Outstanding"])].iterrows():
            due_d = datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
            diff = (today - due_d).days
            unpaid = inv["amount"] - inv["paid_amount"]
            if diff <= 0 or diff <= 30:
                aging_bins["Current (0-30 days)"] += unpaid
            elif diff <= 60:
                aging_bins["Overdue (31-60 days)"] += unpaid
            else:
                aging_bins["Critical (60+ days)"] += unpaid

        aging_df = pd.DataFrame(list(aging_bins.items()), columns=["Aging Category", "Unpaid Amount"])
        chart_aging = alt.Chart(aging_df).mark_bar().encode(
            x=alt.X("Aging Category:N", sort=None),
            y=alt.Y("Unpaid Amount:Q", title="Receivable Balance ($)"),
            color=alt.Color("Aging Category:N", scale=alt.Scale(domain=list(aging_bins.keys()), range=["#10B981", "#F59E0B", "#EF4444"]))
        ).properties(height=320)
        st.altair_chart(chart_aging, use_container_width=True)

    st.subheader("📋 Invoices Register & Payment Status")
    st.dataframe(invoices, use_container_width=True, hide_index=True)


# ==========================================
# PAGE 3: SALES & CRM DASHBOARD
# ==========================================
elif nav_selection == "3. Sales & CRM":
    st.title("🤝 Sales & CRM Pipeline Control")
    st.caption("Lead Intake, Funnel Stages, Deal Conversion, and Sales Leaderboard")

    leads = data["leads"]
    clients = data["clients"]

    open_leads = leads[leads["status"] == "Open"]
    total_pipeline = open_leads["estimated_value"].sum()
    won_leads = leads[leads["stage"] == "Won"]
    won_revenue = won_leads["estimated_value"].sum()
    conversion_rate = (len(won_leads) / len(leads) * 100) if len(leads) > 0 else 0.0

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total Qualified Pipeline", f"${total_pipeline:,.2f}", f"{len(open_leads)} Open Deals")
    with s2:
        st.metric("Closed Won Revenue", f"${won_revenue:,.2f}", f"{len(won_leads)} Deals Closed")
    with s3:
        st.metric("Deal Conversion Rate", f"{conversion_rate:.1f}%", "Target: 18.0%")
    with s4:
        st.metric("Average Deal Value", f"${leads['estimated_value'].mean():,.2f}")

    st.markdown("---")

    col_funnel, col_rep = st.columns(2)

    with col_funnel:
        st.subheader("🌪️ Pipeline Value by Stage")
        stage_order = ["New", "Contacted", "Proposal Sent", "Negotiation", "Won", "Stalled", "Disqualified"]
        stage_df = leads.groupby("stage")["estimated_value"].sum().reindex(stage_order).fillna(0).reset_index()

        chart_stage = alt.Chart(stage_df).mark_bar().encode(
            x=alt.X("stage:N", title="Pipeline Stage", sort=stage_order),
            y=alt.Y("estimated_value:Q", title="Total Value ($)"),
            color=alt.Color("stage:N", legend=None)
        ).properties(height=300)
        st.altair_chart(chart_stage, use_container_width=True)

    with col_rep:
        st.subheader("🏆 Sales Representative Performance")
        rep_df = leads.groupby("assigned_sales_rep").agg(
            total_deals=("lead_id", "count"),
            pipeline_value=("estimated_value", "sum")
        ).reset_index()
        chart_rep = alt.Chart(rep_df).mark_bar().encode(
            x=alt.X("assigned_sales_rep:N", title="Sales Executive"),
            y=alt.Y("pipeline_value:Q", title="Managed Pipeline ($)"),
            color=alt.value("#3B82F6")
        ).properties(height=300)
        st.altair_chart(chart_rep, use_container_width=True)

    st.subheader("📋 Active Deals in Funnel")
    st.dataframe(open_leads, use_container_width=True, hide_index=True)


# ==========================================
# PAGE 4: PROJECTS DASHBOARD
# ==========================================
elif nav_selection == "4. Projects":
    st.title("🚀 Project Delivery & Engineering Control")
    st.caption("Active Milestones, Delivery Deadlines, Profitability, and Tasks")

    projects = data["projects"]
    tasks = data["tasks"]
    clients = data["clients"]

    delayed_prjs = projects[projects["status"] == "Delayed"]
    at_risk_prjs = projects[projects["status"] == "At Risk"]
    ontime_prjs = projects[projects["status"].isin(["On Track", "Completed"])]

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric("Total Active Projects", len(projects), "Across 6 Clients")
    with p2:
        st.metric("Delayed Projects", len(delayed_prjs), "Slide 5 Exception", delta_color="inverse")
    with p3:
        st.metric("On-Time Delivery Rate", f"{len(ontime_prjs) / len(projects) * 100:.1f}%", "Target >= 90%")
    with p4:
        tot_budget = projects["budget"].sum()
        tot_cost = projects["actual_cost"].sum()
        st.metric("Contract Margin", f"{(tot_budget - tot_cost) / tot_budget * 100:.1f}%", f"${tot_budget - tot_cost:,.0f} Gross")

    st.markdown("---")

    st.subheader("⚠️ Management Focus: Delayed & At-Risk Projects (Slide 5)")
    for _, prj in pd.concat([delayed_prjs, at_risk_prjs]).iterrows():
        status_color = "red" if prj["status"] == "Delayed" else "amber"
        st.markdown(f"""
        <div class="exception-card-{status_color}">
            <div style="display:flex; justify-content:space-between;">
                <h4 style="margin:0; color:#0F172A;">{prj["name"]} ({prj["project_id"]})</h4>
                <span class="badge-{status_color}">{prj["status"].upper()}</span>
            </div>
            <p style="margin: 6px 0; color:#334155;"><strong>Reason:</strong> {prj["delay_reason"] or 'Awaiting client sign-off'}</p>
            <div style="font-size:0.85rem; color:#64748B;">
                <strong>Responsible Team:</strong> {prj["responsible_team"]} | <strong>Manager:</strong> {prj["project_manager"]} | 
                <strong>Deadline:</strong> {prj["deadline"]} | <strong>Progress:</strong> {prj["completion_pct"]}%
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("📋 Project Master Overview")
    st.dataframe(projects[["project_id", "name", "responsible_team", "project_manager", "deadline", "status", "budget", "actual_cost", "completion_pct"]], use_container_width=True, hide_index=True)

    st.subheader("📌 Project Tasks & QA Status")
    st.dataframe(tasks, use_container_width=True, hide_index=True)


# ==========================================
# PAGE 5: HR & WORKFORCE DASHBOARD
# ==========================================
elif nav_selection == "5. HR & Workforce":
    st.title("👥 Human Resources & Workforce Control")
    st.caption("Headcount, Department Allocations, Attendance Rates, and Staffing")

    employees = data["employees"]
    attendance = data["attendance"]
    depts = data["departments"]

    active_emp = employees[employees["status"] == "Active"]
    tot_payroll = active_emp["salary_monthly"].sum()
    avg_salary = active_emp["salary_monthly"].mean()

    # Attendance stats
    present_count = len(attendance[attendance["status"].isin(["Present", "Half Day"])])
    total_records = len(attendance)
    att_rate = (present_count / total_records * 100) if total_records > 0 else 100.0

    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.metric("Total Active Headcount", len(active_emp), "Across 6 Departments")
    with h2:
        st.metric("Workforce Attendance", f"{att_rate:.1f}%", "Target >= 95%")
    with h3:
        st.metric("Monthly Payroll Run", f"${tot_payroll:,.2f}")
    with h4:
        st.metric("Average Monthly Comp", f"${avg_salary:,.2f}")

    st.markdown("---")

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        st.subheader("📊 Headcount by Department")
        dept_counts = employees.groupby("dept_id")["employee_id"].count().reset_index()
        dept_counts = pd.merge(depts, dept_counts, on="dept_id", how="left").fillna(0)
        chart_dept = alt.Chart(dept_counts).mark_bar().encode(
            x=alt.X("name:N", title="Department", axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("employee_id:Q", title="Staff Count"),
            color=alt.value("#6366F1")
        ).properties(height=300)
        st.altair_chart(chart_dept, use_container_width=True)

    with col_h2:
        st.subheader("📅 Recent Attendance Status Distribution")
        att_dist = attendance.groupby("status")["record_id"].count().reset_index()
        chart_att = alt.Chart(att_dist).mark_arc(innerRadius=50).encode(
            theta=alt.Theta("record_id:Q"),
            color=alt.Color("status:N", scale=alt.Scale(domain=["Present", "Approved Leave", "Half Day", "Absent"], range=["#10B981", "#3B82F6", "#F59E0B", "#EF4444"]))
        ).properties(height=300)
        st.altair_chart(chart_att, use_container_width=True)

    st.subheader("📋 Employee Directory")
    st.dataframe(employees, use_container_width=True, hide_index=True)


# ==========================================
# PAGE 6: OPERATIONS & QA DASHBOARD
# ==========================================
elif nav_selection == "6. Operations & QA":
    st.title("⚙️ Operations, Productivity & QA Control")
    st.caption("Work Volumes, First-Pass QA Yield, Productivity %, and Turnaround Time")

    daily_ops = data["daily_operations"]
    recent_ops = daily_ops.tail(10)

    avg_prod = recent_ops["productivity_pct"].mean()
    avg_qa = recent_ops["qa_pass_pct"].mean()
    avg_turnaround = recent_ops["avg_turnaround_hours"].mean()
    completed_tasks = daily_ops["tasks_completed"].sum()

    o1, o2, o3, o4 = st.columns(4)
    with o1:
        st.metric("Total Completed Tasks", completed_tasks, "Operational Throughput")
    with o2:
        st.metric("Team Productivity Index", f"{avg_prod:.1f}%", "Target >= 85%")
    with o3:
        st.metric("QA First-Pass Yield", f"{avg_qa:.1f}%", "Target >= 95%")
    with o4:
        st.metric("Avg Turnaround Time", f"{avg_turnaround:.1f} hrs", "SLA <= 4.5 hrs")

    st.markdown("---")

    col_op1, col_op2 = st.columns(2)

    with col_op1:
        st.subheader("📈 Productivity Trend (%) Over Past Sprints")
        chart_prod = alt.Chart(daily_ops).mark_line(point=True).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("productivity_pct:Q", scale=alt.Scale(domain=[70, 100]), title="Productivity %"),
            color=alt.Color("dept_id:N")
        ).properties(height=300)
        st.altair_chart(chart_prod, use_container_width=True)

    with col_op2:
        st.subheader("🔬 QA Pass Rate vs SLA Threshold")
        chart_qa = alt.Chart(daily_ops).mark_line(point=True, color="#10B981").encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("qa_pass_pct:Q", scale=alt.Scale(domain=[80, 100]), title="QA Pass %")
        ).properties(height=300)
        st.altair_chart(chart_qa, use_container_width=True)

    st.subheader("📋 Daily Operations Log")
    st.dataframe(daily_ops, use_container_width=True, hide_index=True)


# ==========================================
# PAGE 7: MARKETING & SEO DASHBOARD
# ==========================================
elif nav_selection == "7. Marketing & SEO":
    st.title("🌐 Marketing, GA4 & Search Console Control")
    st.caption("Website Traffic, SEO Clicks/Impressions, Ad Spend, and Lead Generation")

    mkt = data["marketing_metrics"]
    tot_visitors = mkt["clicks_or_visitors"].sum()
    tot_spend = mkt["spend"].sum()
    tot_leads = mkt["leads_generated"].sum()
    cpl = (tot_spend / tot_leads) if tot_leads > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Web Visitors", f"{tot_visitors:,}", "GA4 + GSC Organic")
    with m2:
        st.metric("Total Ad Spend", f"${tot_spend:,.2f}", "LinkedIn & Search Ads")
    with m3:
        st.metric("Total Inbound Leads", tot_leads, "Form Submissions")
    with m4:
        st.metric("Blended Cost Per Lead", f"${cpl:,.2f}", "Target <= $75.00")

    st.markdown("---")

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.subheader("📊 Visitors & Clicks by Marketing Channel")
        channel_df = mkt.groupby("channel")["clicks_or_visitors"].sum().reset_index()
        chart_mkt = alt.Chart(channel_df).mark_bar().encode(
            x=alt.X("channel:N", title="Channel", axis=alt.Axis(labelAngle=-15)),
            y=alt.Y("clicks_or_visitors:Q", title="Visitors / Clicks"),
            color=alt.value("#EC4899")
        ).properties(height=300)
        st.altair_chart(chart_mkt, use_container_width=True)

    with col_m2:
        st.subheader("🎯 Leads Generated by Channel")
        lead_ch = mkt.groupby("channel")["leads_generated"].sum().reset_index()
        chart_leads = alt.Chart(lead_ch).mark_arc(innerRadius=45).encode(
            theta=alt.Theta("leads_generated:Q"),
            color=alt.Color("channel:N")
        ).properties(height=300)
        st.altair_chart(chart_leads, use_container_width=True)

    st.subheader("📋 Marketing & SEO Metrics Registry")
    st.dataframe(mkt, use_container_width=True, hide_index=True)


# ==========================================
# PAGE 8: ALERTS & EXCEPTION CENTER
# ==========================================
elif nav_selection == "8. Alerts & Exception Center":
    st.title("🚨 Alerts & Exception Management Center")
    st.markdown("#### *Management by Exception: Director Focuses on What Requires Attention (Slide 5)*")

    alerts_df = data["alerts_exceptions"]
    open_alerts = alerts_df[alerts_df["resolution_status"] != "Resolved"]
    resolved_alerts = alerts_df[alerts_df["resolution_status"] == "Resolved"]

    st.info("💡 **Director Action Flow (Slide 5)**: Click into an Exception → Review Issue & Delay → Assign or Log Action → Mark Resolved.")

    tabs = st.tabs(["🔥 Active Exceptions", "✅ Resolved Archive", "⚡ Scan & Trigger New Audit"])

    with tabs[0]:
        if open_alerts.empty:
            st.success("🎉 No active exceptions! All business operations are running within target parameters.")
        else:
            for _, alt_row in open_alerts.iterrows():
                sev = alt_row["severity"]
                box_color = "red" if sev == "Red" else ("amber" if sev == "Amber" else "green")

                with st.container():
                    st.markdown(f"""
                    <div class="exception-card-{box_color}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0;">[{alt_row["category"]}] {alt_row["entity_name"]}</h4>
                            <span class="badge-{box_color}">{sev.upper()} - {alt_row["delay_days"]} DAYS DELAYED</span>
                        </div>
                        <p style="margin:8px 0; color:#334155; font-size:0.95rem;"><strong>Issue Details:</strong> {alt_row["issue"]}</p>
                        <p style="margin:0; color:#64748B; font-size:0.85rem;">
                            <strong>Owner:</strong> {alt_row["owner"]} | <strong>Team:</strong> {alt_row["responsible_team"]} | <strong>Logged Date:</strong> {alt_row["logged_date"]}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander(f"Take Management Action on {alt_row['alert_id']}"):
                        action_input = st.text_input(
                            f"Action to assign or record for {alt_row['alert_id']}:",
                            value=alt_row["action_required"],
                            key=f"act_{alt_row['alert_id']}"
                        )
                        leadership_names = data["employees"][data["employees"]["status"] == "Active"]["name"].tolist()
                        resolved_by = st.selectbox(
                            "Authorized By:",
                            leadership_names,
                            key=f"by_{alt_row['alert_id']}"
                        )
                        if st.button("Mark Action Taken & Resolve Exception", key=f"btn_{alt_row['alert_id']}"):
                            resolve_alert(alt_row["alert_id"], action_input, resolved_by)
                            st.success(f"Exception {alt_row['alert_id']} marked as Resolved!")
                            st.rerun()

    with tabs[1]:
        if resolved_alerts.empty:
            st.caption("No resolved exceptions in archive.")
        else:
            st.dataframe(resolved_alerts, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Automated Exception Scanner Controls")
        st.write("Run the automated audit engine to recalculate overdue receivables, delayed project milestones, QA drops, and departmental budget variances.")
        if st.button("Run Full Exception Scan Now", type="primary"):
            res = run_exception_scanner()
            st.success(res["message"])
            st.rerun()


# ==========================================
# PAGE 9: WORKFLOW AUTOMATION INTAKE CENTER
# ==========================================
elif nav_selection == "9. Automation Intake Center":
    st.title("⚡ Operational Workflow Intake & Automation")
    st.markdown("#### *Automating Data Entry into Central Storage (Section 6 & Slide 6)*")

    wf_tabs = st.tabs([
        "1. New Employee",
        "2. New Lead",
        "3. New Project",
        "4. Log Expense",
        "5. Operations Update",
        "6. Marketing Sync"
    ])

    # 1. New Employee
    with wf_tabs[0]:
        st.subheader("👤 Onboard New Employee (Workflow 1)")
        with st.form("new_emp_form"):
            e_name = st.text_input("Full Name", "")
            e_dept = st.selectbox("Department", data["departments"]["dept_id"].tolist(), format_func=lambda x: f"{x} - {data['departments'].set_index('dept_id').loc[x, 'name']}")
            e_role = st.text_input("Designation / Role", "")
            e_email = st.text_input("Email Address", "")
            e_phone = st.text_input("Contact Phone", "")
            e_salary = st.number_input(f"Monthly Salary ({config.CURRENCY_SYMBOL})", min_value=1000.0, value=7500.0, step=500.0)
            submitted = st.form_submit_button("Automate Onboarding Flow")
            if submitted:
                res = process_new_employee(e_name, e_dept, e_role, e_email, e_phone, e_salary)
                st.success(res["message"])
                st.info(f"Department Status: {res['capacity_status']}")

    # 2. New Lead
    with wf_tabs[1]:
        st.subheader("🎯 Capture New Sales Lead (Workflow 2)")
        with st.form("new_lead_form"):
            l_client = st.text_input("Company / Client Name", "")
            l_contact = st.text_input("Contact Person", "")
            l_email = st.text_input("Email", "")
            l_source = st.selectbox("Lead Source", ["Website Form", "LinkedIn Ads", "Referral", "Google Search", "Cold Outreach"])
            l_val = st.number_input(f"Estimated Deal Value ({config.CURRENCY_SYMBOL})", min_value=1000.0, value=25000.0, step=5000.0)
            active_emp_names = data["employees"][data["employees"]["status"] == "Active"]["name"].tolist()
            l_rep = st.selectbox("Assigned Sales Executive", active_emp_names)
            l_stage = st.selectbox("Initial Stage", ["New", "Contacted", "Proposal Sent"])
            submitted = st.form_submit_button("Register Lead & Trigger SLA")
            if submitted:
                res = process_new_lead(l_client, l_contact, l_email, l_source, l_val, l_rep, l_stage)
                st.success(res["message"])

    # 3. New Project
    with wf_tabs[2]:
        st.subheader("🚀 Initialize New Project & Task Breakdown (Workflow 3)")
        with st.form("new_prj_form"):
            p_client = st.selectbox("Client", data["clients"]["client_id"].tolist(), format_func=lambda x: f"{x} - {data['clients'].set_index('client_id').loc[x, 'name']}")
            p_name = st.text_input("Project Name", "")
            existing_teams = sorted(data["projects"]["responsible_team"].dropna().unique().tolist())
            p_team = st.selectbox("Responsible Team", existing_teams if existing_teams else ["Delivery Team"])
            active_emp_names = data["employees"][data["employees"]["status"] == "Active"]["name"].tolist()
            p_pm = st.selectbox("Project Manager", active_emp_names)
            p_deadline = st.date_input("Contract Delivery Deadline", date.today() + timedelta(days=90))
            p_budget = st.number_input(f"Project Contract Value ({config.CURRENCY_SYMBOL})", min_value=5000.0, value=50000.0, step=5000.0)
            submitted = st.form_submit_button("Create Project & Auto-Generate Planner Tasks")
            if submitted:
                res = process_new_project(p_client, p_name, p_team, p_pm, p_deadline.strftime("%Y-%m-%d"), p_budget)
                st.success(res["message"])

    # 4. Expense Entry
    with wf_tabs[3]:
        st.subheader("💳 Log Departmental Expense & Budget Check (Workflow 4)")
        with st.form("new_exp_form"):
            x_dept = st.selectbox("Department", data["departments"]["dept_id"].tolist(), format_func=lambda x: f"{x} - {data['departments'].set_index('dept_id').loc[x, 'name']}")
            x_cat = st.selectbox("Category", sorted(data["expenses"]["category"].dropna().unique().tolist()) or ["General"])
            x_vendor = st.text_input("Vendor / Payee", "")
            x_amount = st.number_input(f"Amount ({config.CURRENCY_SYMBOL})", min_value=10.0, value=1000.0, step=100.0)
            x_desc = st.text_input("Description", "")
            active_emp_names = data["employees"][data["employees"]["status"] == "Active"]["name"].tolist()
            x_app = st.selectbox("Approved By", active_emp_names)
            submitted = st.form_submit_button("Validate Budget & Log Expense")
            if submitted:
                res = process_expense_entry(x_dept, x_cat, x_vendor, x_amount, x_desc, x_app)
                st.success(res["message"])
                if res.get("alert"):
                    st.warning(res["alert"])

    # 5. Operations Update
    with wf_tabs[4]:
        st.subheader("⚙️ Log Daily Team Operations & QA Yield (Workflow 5)")
        with st.form("ops_form"):
            o_dept = st.selectbox("Operational Team", data["departments"]["dept_id"].tolist(), format_func=lambda x: f"{x} - {data['departments'].set_index('dept_id').loc[x, 'name']}")
            o_comp = st.number_input("Tasks Completed Today", min_value=1, value=25)
            o_pend = st.number_input("Tasks Pending", min_value=0, value=3)
            o_qa = st.slider("QA First-Pass Yield (%)", min_value=50.0, max_value=100.0, value=96.0, step=0.5)
            o_turn = st.number_input("Average Turnaround Hours", min_value=0.5, value=3.5, step=0.5)
            o_notes = st.text_input("Daily Notes", "")
            submitted = st.form_submit_button("Record Daily Operations")
            if submitted:
                res = process_daily_operations(o_dept, o_comp, o_pend, o_qa, o_turn, o_notes)
                st.success(res["message"])

    # 6. Marketing Sync
    with wf_tabs[5]:
        st.subheader("📈 Marketing & SEO Metrics Sync (Workflow 6)")
        with st.form("mkt_form"):
            m_ch = st.selectbox("Channel", ["GA4 Organic Search", "Google Search Console", "LinkedIn B2B Ads", "Meta Ads"])
            m_imp = st.number_input("Impressions / Sessions", min_value=0, value=4500)
            m_clk = st.number_input("Clicks / Visitors", min_value=0, value=650)
            m_sp = st.number_input("Paid Spend ($)", min_value=0.0, value=350.0)
            m_ld = st.number_input("Leads Generated", min_value=0, value=5)
            m_cv = st.number_input("Conversions", min_value=0, value=2)
            submitted = st.form_submit_button("Ingest Marketing Data")
            if submitted:
                res = process_marketing_sync(m_ch, m_imp, m_clk, m_sp, m_ld, m_cv)
                st.success(res["message"])


# ==========================================
# PAGE 10: POWER BI INTEGRATION HUB
# ==========================================
elif nav_selection == "10. Power BI Integration Hub":
    st.title("🔌 Power BI Integration & Automation Hub")
    st.caption("Connecting Operational Sources to Power BI Desktop & Service (Architecture Section 2)")

    st.markdown("""
    ```mermaid
    graph LR
        Forms[Forms / Excel] --> Automate[Power Automate / Sync Script]
        Automate --> Model[(Company_Central_MIS_DataModel.xlsx)]
        Model --> PQ[Power Query Transforms]
        PQ --> PBI[Power BI Director Dashboard]
    ```
    """)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Trigger Full Power BI Model Export Now", type="primary", use_container_width=True):
            res = export_all_to_excel_and_csv()
            st.success(f"Power BI Dataset Exported! Excel file: `{res['excel_path']}`")

    with col_btn2:
        if st.button("📄 Generate Executive Briefing Report", use_container_width=True):
            brief = generate_director_brief()
            st.success(f"Director Daily Briefing generated at: `{brief['markdown_path']}`")

    st.markdown("---")

    pb_tabs = st.tabs(["📁 File Downloads & Locations", "💻 Power Query (M) Code", "📐 DAX Measures Library", "📋 Relational Schema"])

    with pb_tabs[0]:
        st.subheader("Data Files Ready for Power BI Desktop")
        excel_file = os.path.join(BASE_DIR, "Company_Central_MIS_DataModel.xlsx")
        if os.path.exists(excel_file):
            with open(excel_file, "rb") as f:
                st.download_button(
                    label="📥 Download Consolidated Power BI Data Model (.xlsx)",
                    data=f,
                    file_name="Company_Central_MIS_DataModel.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            st.info(f"**Local File Path**: `{excel_file}`")
        else:
            st.warning("Data model file not found. Click 'Trigger Full Power BI Model Export Now' above.")

    with pb_tabs[1]:
        st.subheader("Copy-Paste Power Query M Script")
        st.caption("Paste into Power BI Desktop -> Home -> Advanced Editor")
        pq_path = os.path.join(BASE_DIR, "exports", "PowerQuery_Transforms.m")
        if os.path.exists(pq_path):
            with open(pq_path, "r", encoding="utf-8") as f:
                pq_code = f.read()
            st.code(pq_code, language="powerquery")
        else:
            st.info("Click 'Export' to generate M script.")

    with pb_tabs[2]:
        st.subheader("Enterprise DAX Measures Library")
        st.caption("Pre-configured formulas for Revenue, Margin, Delayed Projects, Attendance, and Exceptions")
        dax_path = os.path.join(BASE_DIR, "exports", "DAX_Measures.dax")
        if os.path.exists(dax_path):
            with open(dax_path, "r", encoding="utf-8") as f:
                dax_code = f.read()
            st.code(dax_code, language="dax")
        else:
            st.info("Click 'Export' to generate DAX library.")

    with pb_tabs[3]:
        st.subheader("Central Relational Star Schema (Section 7)")
        st.markdown("""
        | Table Name | Primary Key | Foreign Keys | Role in Model |
        |---|---|---|---|
        | **Departments** | `dept_id` | - | Dimension |
        | **Employees** | `employee_id` | `dept_id` | Dimension |
        | **Clients** | `client_id` | - | Dimension |
        | **Projects** | `project_id` | `client_id` | Dimension / Fact |
        | **Leads** | `lead_id` | - | Fact |
        | **Tasks** | `task_id` | `project_id` | Fact |
        | **Invoices** | `invoice_id` | `client_id`, `project_id` | Fact |
        | **Expenses** | `expense_id` | `dept_id` | Fact |
        | **Attendance** | `record_id` | `employee_id` | Fact |
        | **Daily_Operations** | `operation_id` | `dept_id` | Fact |
        | **Marketing_Metrics** | `metric_id` | - | Fact |
        | **KPI_Master** | `kpi_id` | - | Governance Dimension |
        | **Alerts_Exceptions** | `alert_id` | `entity_id` | Management Fact |
        """)
