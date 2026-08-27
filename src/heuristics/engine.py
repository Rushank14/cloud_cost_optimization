import logging
import re
from typing import Any, Dict, List

import duckdb
import pandas as pd
import yaml

logger = logging.getLogger(__name__)

class HeuristicsEngine:
    def __init__(self, config_path: str, db_path: str):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)["rules"]
        self.db_path = db_path
        
    def _execute_query(self, query: str) -> pd.DataFrame:
        """Executes a SQL query against the warehouse and returns a pandas DataFrame."""
        with duckdb.connect(self.db_path, read_only=True) as conn:
            return conn.execute(query).df()

    def find_expensive_scans(self) -> List[Dict[str, Any]]:
        """
        Rule 1: Flag full table scans or highly expensive scans 
        that exceed the threshold and should likely be clustered/partitioned.
        """
        min_bytes = self.config["large_unpartitioned_scan"]["min_bytes_scanned"]
        
        query = f"""
        SELECT 
            job_id,
            user_email,
            query as sql_text,
            total_bytes_processed,
            estimated_cost_usd,
            execution_date
        FROM main.fct_query_cost
        WHERE statement_type = 'SELECT'
          AND total_bytes_processed >= {min_bytes}
          AND cache_hit = false
        ORDER BY estimated_cost_usd DESC
        """
        df = self._execute_query(query)
        
        results = []
        for _, row in df.iterrows():
            results.append({
                "rule": "LARGE_SCAN",
                "job_id": row["job_id"],
                "user_email": row["user_email"],
                "estimated_cost_usd": row["estimated_cost_usd"],
                "details": f"Query scanned {row['total_bytes_processed'] / (1024**3):.2f} GB."
            })
        return results

    def find_repeated_queries(self) -> List[Dict[str, Any]]:
        """
        Rule 2: Flag identical queries that are run multiple times a day
        costing significant money, which should be cached or materialized.
        """
        min_execs = self.config["repeated_query"]["min_executions_per_day"]
        min_cost = self.config["repeated_query"]["min_total_cost_usd"]
        
        query = f"""
        SELECT 
            query as sql_text,
            execution_date,
            COUNT(*) as execution_count,
            SUM(estimated_cost_usd) as total_daily_cost
        FROM main.fct_query_cost
        WHERE statement_type = 'SELECT' 
          AND cache_hit = false
        GROUP BY 1, 2
        HAVING COUNT(*) >= {min_execs}
           AND SUM(estimated_cost_usd) >= {min_cost}
        ORDER BY total_daily_cost DESC
        """
        df = self._execute_query(query)
        
        results = []
        for _, row in df.iterrows():
            # Potential savings assumes 1 execution instead of N (materialize once)
            savings = row["total_daily_cost"] - (row["total_daily_cost"] / row["execution_count"])
            results.append({
                "rule": "REPEATED_QUERY",
                "query_snippet": row["sql_text"][:100] + "...",
                "execution_count": row["execution_count"],
                "estimated_cost_usd": row["total_daily_cost"],
                "potential_savings_usd": savings,
                "details": f"Query run {row['execution_count']} times on {row['execution_date'].date()} costing ${row['total_daily_cost']:.2f}."
            })
        return results

    def find_unused_materializations(self) -> List[Dict[str, Any]]:
        """
        Rule 3: Find tables created via CTAS that are never referenced 
        by subsequent SELECT queries.
        """
        min_cost = self.config["unused_materialization"]["min_creation_cost_usd"]
        
        # Get all materializations
        ctas_query = f"""
        SELECT 
            job_id,
            query as sql_text,
            estimated_cost_usd
        FROM main.fct_query_cost
        WHERE statement_type = 'CREATE_TABLE_AS_SELECT'
          AND estimated_cost_usd >= {min_cost}
        """
        ctas_df = self._execute_query(ctas_query)
        
        # Get all references (very simplistic regex for mock data)
        # In a real environment, we would use BigQuery's destination_table and referenced_tables metadata.
        selects_query = "SELECT query FROM main.fct_query_cost WHERE statement_type = 'SELECT'"
        selects_df = self._execute_query(selects_query)
        all_selects = " ".join(selects_df["query"].tolist()).lower()
        
        results = []
        for _, row in ctas_df.iterrows():
            # Extract table name from CREATE OR REPLACE TABLE `my.table` AS (backticks optional)
            match = re.search(r"TABLE\s+`?([a-zA-Z0-9_\-\.]+)`?\s+AS", row["sql_text"], re.IGNORECASE)
            if match:
                table_name = match.group(1).lower()
                if table_name not in all_selects:
                    results.append({
                        "rule": "UNUSED_MATERIALIZATION",
                        "job_id": row["job_id"],
                        "table_name": table_name,
                        "estimated_cost_usd": row["estimated_cost_usd"],
                        "details": f"Table {table_name} was created costing ${row['estimated_cost_usd']:.2f} but never queried."
                    })
        return results

    def run_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Runs all heuristics and returns a compiled report."""
        logger.info("Running heuristics engine...")
        return {
            "large_scans": self.find_expensive_scans(),
            "repeated_queries": self.find_repeated_queries(),
            "unused_materializations": self.find_unused_materializations()
        }
