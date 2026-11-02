# Central MIS Automated Sync & Export Pipeline
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import init_db
from backend.automation import run_exception_scanner
from backend.export_powerbi import export_all_to_excel_and_csv
from backend.executive_brief import generate_director_brief

def main():
    print("=======================================================")
    print("CENTRAL MIS AUTOMATION: SCHEDULED SYNC & EXPORT RUNNER")
    print("=======================================================")
    
    init_db(force_reseed=False)
    
    print("\n[Step 1/3] Running Exception Scanner & Health Evaluation...")
    scan_res = run_exception_scanner()
    print(" ->", scan_res["message"])
    
    print("\n[Step 2/3] Generating Power BI Relational Model (.xlsx & .csv)...")
    exp_res = export_all_to_excel_and_csv()
    print(f" -> Excel Model: {exp_res['excel_path']}")
    print(f" -> Exported {exp_res['csv_count']} individual CSV tables to exports/csv/")
    print(f" -> Power Query M script updated: {exp_res['power_query_file']}")
    print(f" -> DAX Measures updated: {exp_res['dax_file']}")
    
    print("\n[Step 3/3] Compiling Director Daily Flash Briefing...")
    brief = generate_director_brief()
    print(f" -> Overall Company Health: {brief['company_status']}")
    print(f" -> Brief saved to: {brief['markdown_path']}")
    
    print("\n=======================================================")
    print("AUTOMATED SYNC & POWER BI EXPORT COMPLETED SUCCESSFULLY")
    print("=======================================================")

if __name__ == "__main__":
    main()
