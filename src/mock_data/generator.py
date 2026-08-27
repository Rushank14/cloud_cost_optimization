import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from faker import Faker

fake = Faker()

PROJECT_ID = "portfolio-cost-optimization"
DATASET_ID = "analytics_prod"

# Define mock tables and their characteristics (size in bytes)
TABLES = {
    "events_raw": {"size": 5 * 1024**4, "partitioned": False},  # 5 TB, unpartitioned (BAD)
    "events_partitioned": {"size": 5 * 1024**4, "partitioned": True},  # 5 TB, partitioned (GOOD)
    "dim_users": {"size": 10 * 1024**3, "partitioned": False},  # 10 GB
    "fct_daily_sales": {"size": 50 * 1024**3, "partitioned": True},  # 50 GB
    "mv_unused_summary": {"size": 100 * 1024**3, "partitioned": False},  # 100 GB
}

USERS = [
    "bi_service_account@example.com",
    "data_scientist_1@example.com",
    "data_engineer_1@example.com",
    "analyst_junior@example.com",
]

def generate_job_id() -> str:
    return f"bquxjob_{uuid.uuid4().hex[:8]}_US"

def generate_bad_full_scan(timestamp: datetime) -> Dict[str, Any]:
    """Simulates a junior analyst doing SELECT * on a massive unpartitioned table."""
    table = "events_raw"
    bytes_scanned = TABLES[table]["size"]
    
    return {
        "creation_time": timestamp.isoformat(),
        "project_id": PROJECT_ID,
        "user_email": "analyst_junior@example.com",
        "job_id": generate_job_id(),
        "job_type": "QUERY",
        "statement_type": "SELECT",
        "query": f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{table}` WHERE event_type = 'click'",
        "total_bytes_processed": bytes_scanned,
        "total_slot_ms": random.randint(50000, 200000),
        "referenced_tables": [{"project_id": PROJECT_ID, "dataset_id": DATASET_ID, "table_id": table}],
        "cache_hit": False,
        "error_result": None
    }

def generate_good_partitioned_scan(timestamp: datetime) -> Dict[str, Any]:
    """Simulates an engineer querying a partitioned table correctly."""
    table = "events_partitioned"
    # Scans only 1/365th of the table (1 day of data)
    bytes_scanned = TABLES[table]["size"] // 365 
    
    return {
        "creation_time": timestamp.isoformat(),
        "project_id": PROJECT_ID,
        "user_email": "data_engineer_1@example.com",
        "job_id": generate_job_id(),
        "job_type": "QUERY",
        "statement_type": "SELECT",
        "query": f"SELECT user_id, count(*) FROM `{PROJECT_ID}.{DATASET_ID}.{table}` WHERE date = '2023-10-01' GROUP BY 1",
        "total_bytes_processed": bytes_scanned,
        "total_slot_ms": random.randint(1000, 5000),
        "referenced_tables": [{"project_id": PROJECT_ID, "dataset_id": DATASET_ID, "table_id": table}],
        "cache_hit": False,
        "error_result": None
    }

def generate_repeated_dashboard_query(timestamp: datetime) -> Dict[str, Any]:
    """Simulates a BI tool running the exact same heavy query without caching."""
    table = "fct_daily_sales"
    bytes_scanned = TABLES[table]["size"] // 30 # Scans a month
    
    return {
        "creation_time": timestamp.isoformat(),
        "project_id": PROJECT_ID,
        "user_email": "bi_service_account@example.com",
        "job_id": generate_job_id(),
        "job_type": "QUERY",
        "statement_type": "SELECT",
        "query": f"SELECT product_id, SUM(revenue) FROM `{PROJECT_ID}.{DATASET_ID}.{table}` WHERE date >= '2023-09-01' GROUP BY 1",
        "total_bytes_processed": bytes_scanned,
        "total_slot_ms": random.randint(10000, 30000),
        "referenced_tables": [{"project_id": PROJECT_ID, "dataset_id": DATASET_ID, "table_id": table}],
        "cache_hit": False, # BI tool adds a timestamp comment or similar, defeating cache
        "error_result": None
    }

def generate_unused_materialization(timestamp: datetime) -> Dict[str, Any]:
    """Simulates a dbt run creating a table that nobody queries."""
    table = "mv_unused_summary"
    source_table = "events_partitioned"
    bytes_scanned = TABLES[source_table]["size"] // 7 # scans a week to build
    
    return {
        "creation_time": timestamp.isoformat(),
        "project_id": PROJECT_ID,
        "user_email": "data_engineer_1@example.com",
        "job_id": generate_job_id(),
        "job_type": "QUERY",
        "statement_type": "CREATE_TABLE_AS_SELECT",
        "query": f"CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.{table}` AS SELECT date, count(*) FROM `{PROJECT_ID}.{DATASET_ID}.{source_table}` GROUP BY 1",
        "total_bytes_processed": bytes_scanned,
        "total_slot_ms": random.randint(20000, 80000),
        "referenced_tables": [{"project_id": PROJECT_ID, "dataset_id": DATASET_ID, "table_id": source_table}],
        "cache_hit": False,
        "error_result": None
    }

def generate_mock_logs(days: int = 7, logs_per_day: int = 100) -> List[Dict[str, Any]]:
    logs = []
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # Add 1 materialization per day
        logs.append(generate_unused_materialization(current_date.replace(hour=2, minute=0)))
        
        for _ in range(logs_per_day):
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            log_time = current_date.replace(hour=hour, minute=minute)
            
            choice = random.choices(
                [generate_bad_full_scan, generate_good_partitioned_scan, generate_repeated_dashboard_query],
                weights=[0.2, 0.5, 0.3],
                k=1
            )[0]
            
            logs.append(choice(log_time))
            
    # Sort by creation_time
    logs.sort(key=lambda x: x["creation_time"])
    return logs

def main() -> None:
    print("Generating mock BigQuery logs...")
    logs = generate_mock_logs(days=14, logs_per_day=50)
    
    output_path = "data/mock_information_schema_jobs.jsonl"
    with open(output_path, "w") as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")
            
    print(f"Generated {len(logs)} logs at {output_path}")

if __name__ == "__main__":
    main()
