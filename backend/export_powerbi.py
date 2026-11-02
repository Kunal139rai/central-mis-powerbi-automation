"""
Central MIS Power BI Export & Automation Engine
Generates:
1. Multi-sheet relational Excel model: Company_Central_MIS_DataModel.xlsx
2. Individual CSV datasets in exports/csv/
3. Power Query M scripts: exports/PowerQuery_Transforms.m
4. DAX Measures repository: exports/DAX_Measures.dax
"""

import os
import sqlite3
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from backend.database import load_all_tables

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
CSV_DIR = os.path.join(EXPORTS_DIR, "csv")
EXCEL_PATH_ROOT = os.path.join(BASE_DIR, "Company_Central_MIS_DataModel.xlsx")
EXCEL_PATH_EXPORTS = os.path.join(EXPORTS_DIR, "Company_Central_MIS_DataModel.xlsx")


def export_all_to_excel_and_csv() -> dict:
    """Exports all 13 tables into formatted Excel workbook and individual CSV files."""
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    os.makedirs(CSV_DIR, exist_ok=True)

    tables = load_all_tables()

    # 1. Export CSVs
    csv_files = []
    for tbl_name, df in tables.items():
        csv_path = os.path.join(CSV_DIR, f"{tbl_name}.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        csv_files.append(csv_path)

    # 2. Export multi-sheet Excel
    sheet_mapping = {
        "departments": "Departments",
        "employees": "Employees",
        "clients": "Clients",
        "leads": "Leads",
        "projects": "Projects",
        "tasks": "Tasks",
        "invoices": "Invoices",
        "expenses": "Expenses",
        "attendance": "Attendance",
        "daily_operations": "Daily_Operations",
        "marketing_metrics": "Marketing_Metrics",
        "kpi_master": "KPI_Master",
        "alerts_exceptions": "Alerts_Exceptions"
    }

    # Write to both root and exports folder
    for target_excel in [EXCEL_PATH_ROOT, EXCEL_PATH_EXPORTS]:
        with pd.ExcelWriter(target_excel, engine="openpyxl") as writer:
            for tbl_key, sheet_name in sheet_mapping.items():
                df = tables.get(tbl_key, pd.DataFrame())
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Apply executive formatting with openpyxl
        wb = openpyxl.load_workbook(target_excel)
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Dark Navy
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")

        for ws in wb.worksheets:
            ws.views.sheetView[0].showGridLines = True
            ws.freeze_panes = "A2"

            for col_num in range(1, ws.max_column + 1):
                cell = ws.cell(row=1, column=col_num)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        wb.save(target_excel)

    # 3. Generate Power Query M File
    m_script_path = os.path.join(EXPORTS_DIR, "PowerQuery_Transforms.m")
    generate_power_query_script(m_script_path, EXCEL_PATH_ROOT)

    # 4. Generate DAX Measures File
    dax_path = os.path.join(EXPORTS_DIR, "DAX_Measures.dax")
    generate_dax_measures(dax_path)

    return {
        "success": True,
        "excel_path": EXCEL_PATH_ROOT,
        "csv_count": len(csv_files),
        "power_query_file": m_script_path,
        "dax_file": dax_path
    }


# Column type specs for every sheet, used to generate a complete, typed Power
# Query for each of the 13 tables (not just a sample 3). Kept in one place so
# adding/renaming a column in models.py + database.py only needs a matching
# one-line update here to stay in sync.
# NOTE: *_pct columns are stored as plain 0-100 numbers (e.g. 78.0 = 78%), so
# they are typed as `type number` rather than `Percentage.Type` — Power
# Query's Percentage.Type treats the stored value itself as the fraction
# (0.78), which would otherwise render 78.0 as "7800%".
TABLE_COLUMN_TYPES = {
    "Departments": [
        ("dept_id", "type text"), ("name", "type text"), ("head", "type text"),
        ("monthly_budget", "Currency.Type"), ("headcount_target", "Int64.Type"),
    ],
    "Employees": [
        ("employee_id", "type text"), ("name", "type text"), ("dept_id", "type text"),
        ("role", "type text"), ("email", "type text"), ("phone", "type text"),
        ("joining_date", "type date"), ("salary_monthly", "Currency.Type"), ("status", "type text"),
    ],
    "Clients": [
        ("client_id", "type text"), ("name", "type text"), ("industry", "type text"),
        ("contact_person", "type text"), ("email", "type text"), ("phone", "type text"),
        ("status", "type text"), ("tier", "type text"),
    ],
    "Leads": [
        ("lead_id", "type text"), ("client_name", "type text"), ("contact_person", "type text"),
        ("email", "type text"), ("source", "type text"), ("stage", "type text"),
        ("estimated_value", "Currency.Type"), ("assigned_sales_rep", "type text"),
        ("created_date", "type date"), ("next_follow_up", "type date"), ("status", "type text"),
    ],
    "Projects": [
        ("project_id", "type text"), ("client_id", "type text"), ("name", "type text"),
        ("responsible_team", "type text"), ("project_manager", "type text"),
        ("start_date", "type date"), ("deadline", "type date"), ("status", "type text"),
        ("budget", "Currency.Type"), ("actual_cost", "Currency.Type"), ("billed_revenue", "Currency.Type"),
        ("completion_pct", "type number"), ("delay_reason", "type text"),
    ],
    "Tasks": [
        ("task_id", "type text"), ("project_id", "type text"), ("title", "type text"),
        ("assigned_to", "type text"), ("due_date", "type date"), ("status", "type text"),
        ("qa_status", "type text"), ("estimated_hours", "type number"), ("actual_hours", "type number"),
    ],
    "Invoices": [
        ("invoice_id", "type text"), ("client_id", "type text"), ("project_id", "type text"),
        ("invoice_date", "type date"), ("due_date", "type date"), ("amount", "Currency.Type"),
        ("paid_amount", "Currency.Type"), ("status", "type text"), ("payment_date", "type date"),
    ],
    "Expenses": [
        ("expense_id", "type text"), ("dept_id", "type text"), ("category", "type text"),
        ("vendor", "type text"), ("amount", "Currency.Type"), ("date", "type date"),
        ("description", "type text"), ("approved_by", "type text"), ("status", "type text"),
    ],
    "Attendance": [
        ("record_id", "type text"), ("employee_id", "type text"), ("date", "type date"),
        ("status", "type text"), ("leave_type", "type text"),
    ],
    "Daily_Operations": [
        ("operation_id", "type text"), ("date", "type date"), ("dept_id", "type text"),
        ("tasks_completed", "Int64.Type"), ("tasks_pending", "Int64.Type"),
        ("productivity_pct", "type number"), ("qa_pass_pct", "type number"),
        ("avg_turnaround_hours", "type number"), ("notes", "type text"),
    ],
    "Marketing_Metrics": [
        ("metric_id", "type text"), ("date", "type date"), ("channel", "type text"),
        ("sessions_or_impressions", "Int64.Type"), ("clicks_or_visitors", "Int64.Type"),
        ("spend", "Currency.Type"), ("leads_generated", "Int64.Type"), ("conversions", "Int64.Type"),
    ],
    "KPI_Master": [
        ("kpi_id", "type text"), ("metric_name", "type text"), ("category", "type text"),
        ("target_value", "type number"), ("actual_value", "type number"), ("unit", "type text"),
        ("status", "type text"), ("calculation_method", "type text"), ("frequency", "type text"),
    ],
    "Alerts_Exceptions": [
        ("alert_id", "type text"), ("category", "type text"), ("severity", "type text"),
        ("entity_id", "type text"), ("entity_name", "type text"), ("issue", "type text"),
        ("delay_days", "Int64.Type"), ("responsible_team", "type text"), ("owner", "type text"),
        ("action_required", "type text"), ("resolution_status", "type text"), ("logged_date", "type date"),
    ],
}


def generate_power_query_script(out_path: str, excel_path: str) -> None:
    """
    Generates a Power Query (M) script containing:
    1. A `CentralMISFolderPath` Parameter — the ONE place to point Power BI at
       wherever this application is actually installed. Because it is a real
       Power BI Parameter (not a value buried inside every query), refreshing
       on a different machine/path only requires editing this one parameter
       in Power BI Desktop, instead of hand-editing 13 queries.
    2. One fully-typed query per relational table (all 13, not a sample).
    """
    win_path = excel_path.replace("/", "\\")

    lines = [
        "/*",
        "================================================================================",
        "POWER QUERY (M) AUTOMATION TEMPLATES FOR CENTRAL MIS POWER BI DATA MODEL",
        "================================================================================",
        "Setup in Power BI Desktop:",
        '  1. Home -> Transform Data -> Manage Parameters -> New Parameter named',
        '     "CentralMISFolderPath" (Type: Text). Paste in the block below as its',
        "     Current Value, then update it any time the file moves.",
        "  2. For each table below: Home -> Advanced Editor -> New Blank Query,",
        "     paste the corresponding block, and rename the query to match",
        "     (e.g. \"Departments\", \"Projects\", ...).",
        "  3. Load all 13 queries; Power BI will auto-detect relationships via the",
        "     shared ID columns (dept_id, employee_id, client_id, project_id).",
        "*/",
        "",
        "// --- PARAMETER: CentralMISFolderPath ---",
        "// Set this Parameter's Current Value to the full path of",
        "// Company_Central_MIS_DataModel.xlsx on whichever machine refreshes this report.",
        "let",
        f'    CentralMISFolderPath = "{win_path}"',
        "in",
        "    CentralMISFolderPath",
        "",
    ]

    for sheet_name, columns in TABLE_COLUMN_TYPES.items():
        type_entries = ",\n".join(f'        {{"{col}", {mtype}}}' for col, mtype in columns)
        lines.extend([
            f"// --- QUERY: {sheet_name} ---",
            "let",
            '    Source = Excel.Workbook(File.Contents(CentralMISFolderPath), null, true),',
            f'    {sheet_name}_Sheet = Source{{[Item="{sheet_name}",Kind="Sheet"]}}[Data],',
            f'    #"Promoted Headers" = Table.PromoteHeaders({sheet_name}_Sheet, [PromoteAllScalars=true]),',
            '    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{',
            type_entries,
            "    })",
            "in",
            '    #"Changed Type"',
            "",
        ])

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def generate_dax_measures(out_path: str) -> None:
    lines = [
        "/*",
        "================================================================================",
        "POWER BI DAX MEASURES REPOSITORY FOR DIRECTOR'S CENTRAL MIS",
        "================================================================================",
        "Organized by the 8 Dashboard Pages defined in Section 15 of the Plan.",
        "*/",
        "",
        "// ==========================================",
        "// 1. DIRECTOR OVERVIEW & COMPANY HEALTH",
        "// ==========================================",
        "Total Revenue = SUM(Invoices[amount])",
        "",
        "Total Expenses = SUM(Expenses[amount])",
        "",
        "Net Operating Profit = [Total Revenue] - [Total Expenses]",
        "",
        "Operating Margin % = DIVIDE([Net Operating Profit], [Total Revenue], 0)",
        "",
        'Active Headcount = CALCULATE(COUNTROWS(Employees), Employees[status] = "Active")',
        "",
        'Total Pipeline Value = CALCULATE(SUM(Leads[estimated_value]), Leads[status] = "Open")',
        "",
        'Critical Red Exceptions = CALCULATE(COUNTROWS(Alerts_Exceptions), Alerts_Exceptions[severity] = "Red", Alerts_Exceptions[resolution_status] <> "Resolved")',
        "",
        'Amber Monitoring Exceptions = CALCULATE(COUNTROWS(Alerts_Exceptions), Alerts_Exceptions[severity] = "Amber", Alerts_Exceptions[resolution_status] <> "Resolved")',
        "",
        "Company Health Status = ",
        'IF([Critical Red Exceptions] > 0, "RED - Immediate Management Attention",',
        '   IF([Amber Monitoring Exceptions] > 0, "AMBER - Monitoring Required", "GREEN - Normal Operations"))',
        "",
        "// ==========================================",
        "// 2. FINANCE MEASURES",
        "// ==========================================",
        "Total Paid Billings = SUM(Invoices[paid_amount])",
        "",
        "Total Outstanding Receivables = SUMX(Invoices, Invoices[amount] - Invoices[paid_amount])",
        "",
        "Overdue Receivables Amount = ",
        "CALCULATE(",
        "    SUMX(Invoices, Invoices[amount] - Invoices[paid_amount]),",
        '    Invoices[status] = "Overdue"',
        ")",
        "",
        "// ==========================================",
        "// 3. SALES & CRM MEASURES",
        "// ==========================================",
        "Total Leads Count = COUNTROWS(Leads)",
        "",
        'Won Deals Count = CALCULATE(COUNTROWS(Leads), Leads[stage] = "Won")',
        "",
        "Lead Conversion Rate % = DIVIDE([Won Deals Count], [Total Leads Count], 0)",
        "",
        "// ==========================================",
        "// 4. PROJECT DELIVERY & MARGIN MEASURES",
        "// ==========================================",
        "Total Projects = COUNTROWS(Projects)",
        "",
        'Active Projects = CALCULATE(COUNTROWS(Projects), Projects[status] IN {"On Track", "Delayed", "At Risk"})',
        "",
        'Delayed Projects Count = CALCULATE(COUNTROWS(Projects), Projects[status] = "Delayed")',
        "",
        "On-Time Project Delivery % = ",
        "DIVIDE(",
        '    CALCULATE(COUNTROWS(Projects), Projects[status] IN {"Completed", "On Track"}),',
        "    [Total Projects],",
        "    1",
        ")",
        "",
        "Total Contract Value = SUM(Projects[budget])",
        "",
        "Total Incurred Project Cost = SUM(Projects[actual_cost])",
        "",
        "Project Gross Margin % = DIVIDE(SUM(Projects[billed_revenue]) - SUM(Projects[actual_cost]), SUM(Projects[billed_revenue]), 0)",
        "",
        "// ==========================================",
        "// 5. HR & WORKFORCE MEASURES",
        "// ==========================================",
        "Daily Attendance Rate % = ",
        'VAR PresentDays = CALCULATE(COUNTROWS(Attendance), Attendance[status] IN {"Present", "Half Day"})',
        "VAR TotalDays = COUNTROWS(Attendance)",
        "RETURN DIVIDE(PresentDays, TotalDays, 1)",
        "",
        "Average Monthly Salary = AVERAGE(Employees[salary_monthly])",
        "",
        "// ==========================================",
        "// 6. OPERATIONS & QA MEASURES",
        "// ==========================================",
        "Average Productivity % = AVERAGE(Daily_Operations[productivity_pct])",
        "",
        "Average QA Pass Rate % = AVERAGE(Daily_Operations[qa_pass_pct])",
        "",
        "Average Turnaround Hours = AVERAGE(Daily_Operations[avg_turnaround_hours])",
        "",
        "// ==========================================",
        "// 7. MARKETING & SEO MEASURES",
        "// ==========================================",
        "Total Web Visitors = SUM(Marketing_Metrics[clicks_or_visitors])",
        "",
        "Total Marketing Spend = SUM(Marketing_Metrics[spend])",
        "",
        "Total Inbound Leads = SUM(Marketing_Metrics[leads_generated])",
        "",
        "Cost Per Lead (CPL) = DIVIDE([Total Marketing Spend], [Total Inbound Leads], 0)"
    ]
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    print("Running Central MIS Power BI Export...")
    res = export_all_to_excel_and_csv()
    print("Export Result:", res)
    print("Company_Central_MIS_DataModel.xlsx generated successfully!")
