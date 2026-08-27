import os
from datetime import datetime
from typing import Any, Dict, List

from src.heuristics.engine import HeuristicsEngine

def generate_markdown_report(results: Dict[str, List[Dict[str, Any]]], output_path: str = "report.md") -> None:
    """Generates a Markdown report ranking findings by potential savings."""
    
    with open(output_path, "w") as f:
        f.write(f"# Cloud Data Warehouse Cost Optimization Report\n")
        f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        # 1. Executive Summary
        f.write("## 1. Executive Summary\n")
        
        total_large_scans = len(results["large_scans"])
        total_large_cost = sum(r["estimated_cost_usd"] for r in results["large_scans"])
        
        total_repeated = len(results["repeated_queries"])
        total_repeated_savings = sum(r["potential_savings_usd"] for r in results["repeated_queries"])
        
        total_unused = len(results["unused_materializations"])
        total_unused_cost = sum(r["estimated_cost_usd"] for r in results["unused_materializations"])
        
        f.write(f"- **Large Unpartitioned Scans Flagged**: {total_large_scans} (Total wasted cost: ${total_large_cost:.2f})\n")
        f.write(f"- **Repeated Queries Flagged**: {total_repeated} (Potential daily savings: ${total_repeated_savings:.2f})\n")
        f.write(f"- **Unused Materializations Flagged**: {total_unused} (Total wasted cost: ${total_unused_cost:.2f})\n\n")

        # 2. Detailed Findings (Ranked by Cost/Savings)
        f.write("## 2. Top Inefficiencies (Action Required)\n\n")
        
        # 2a. Large Scans
        if results["large_scans"]:
            f.write("### A. Large Unpartitioned Scans\n")
            f.write("*These single queries scanned massive amounts of data without partition filters.*\n\n")
            
            # Sort by cost descending
            sorted_scans = sorted(results["large_scans"], key=lambda x: x["estimated_cost_usd"], reverse=True)
            for scan in sorted_scans[:5]: # Show top 5
                f.write(f"- **Job ID**: `{scan['job_id']}` (User: {scan['user_email']})\n")
                f.write(f"  - **Cost**: ${scan['estimated_cost_usd']:.2f}\n")
                f.write(f"  - **Details**: {scan['details']}\n")
                f.write(f"  - **Simulation**: *If this table were partitioned by date and the query filtered to a single day, the cost would drop to ~${(scan['estimated_cost_usd']/365):.2f}.*\n\n")

        # 2b. Repeated Queries
        if results["repeated_queries"]:
            f.write("### B. Repeated Dashboard/BI Queries\n")
            f.write("*These exact queries are run multiple times a day and should be cached or materialized.* \n\n")
            
            sorted_repeated = sorted(results["repeated_queries"], key=lambda x: x["potential_savings_usd"], reverse=True)
            for req in sorted_repeated[:5]:
                f.write(f"- **Query**: `{req['query_snippet']}`\n")
                f.write(f"  - **Executions**: {req['execution_count']} times\n")
                f.write(f"  - **Current Cost**: ${req['estimated_cost_usd']:.2f}\n")
                f.write(f"  - **Potential Savings**: **${req['potential_savings_usd']:.2f}**\n")
                f.write(f"  - **Simulation**: *Materializing this query via dbt into a daily incremental model would cost ${ (req['estimated_cost_usd'] / req['execution_count']):.2f} once per day, saving ${req['potential_savings_usd']:.2f}.*\n\n")

        # 2c. Unused Materializations
        if results["unused_materializations"]:
            f.write("### C. Unused Materialized Views / CTAS\n")
            f.write("*These tables are being built at a cost, but are never queried by downstream users.*\n\n")
            
            sorted_unused = sorted(results["unused_materializations"], key=lambda x: x["estimated_cost_usd"], reverse=True)
            for mat in sorted_unused[:5]:
                f.write(f"- **Table**: `{mat['table_name']}` (Created by Job: {mat['job_id']})\n")
                f.write(f"  - **Wasted Cost**: ${mat['estimated_cost_usd']:.2f}\n")
                f.write(f"  - **Recommendation**: Drop this model from the dbt DAG or convert it to a view.\n\n")

    print(f"Report generated successfully at: {output_path}")

def main():
    config_path = "config/heuristics_config.yaml"
    db_path = "data/local_warehouse.duckdb"
    
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} not found. Did you run the ingestion and dbt steps?")
        return
        
    engine = HeuristicsEngine(config_path, db_path)
    results = engine.run_all()
    generate_markdown_report(results, output_path="cost_report.md")

if __name__ == "__main__":
    main()
