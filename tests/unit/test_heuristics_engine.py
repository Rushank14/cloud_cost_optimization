import json
import os
import tempfile

import duckdb
import pandas as pd
import pytest
import yaml

from src.heuristics.engine import HeuristicsEngine

@pytest.fixture
def mock_db_and_config():
    # Create temp directory for config and db
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.duckdb")
        config_path = os.path.join(tmpdir, "config.yaml")
        
        # Write config
        config_data = {
            "rules": {
                "large_unpartitioned_scan": {"min_bytes_scanned": 1000},
                "repeated_query": {"min_executions_per_day": 2, "min_total_cost_usd": 1.0},
                "unused_materialization": {"min_creation_cost_usd": 0.5}
            }
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        # Create DuckDB database and mock fct_query_cost table
        conn = duckdb.connect(db_path)
        conn.execute("CREATE SCHEMA IF NOT EXISTS main")
        conn.execute("""
            CREATE TABLE main.fct_query_cost (
                job_id VARCHAR,
                user_email VARCHAR,
                query VARCHAR,
                total_bytes_processed BIGINT,
                estimated_cost_usd DOUBLE,
                execution_date DATE,
                statement_type VARCHAR,
                cache_hit BOOLEAN
            )
        """)
        
        # Insert mock data
        conn.execute("""
            INSERT INTO main.fct_query_cost VALUES
            ('job1', 'u1', 'SELECT * FROM big_table', 5000, 5.0, '2023-10-01', 'SELECT', false),
            ('job2', 'u1', 'SELECT 1', 10, 0.01, '2023-10-01', 'SELECT', false),
            ('job3', 'u2', 'SELECT count(*) FROM x', 500, 2.0, '2023-10-02', 'SELECT', false),
            ('job4', 'u2', 'SELECT count(*) FROM x', 500, 2.0, '2023-10-02', 'SELECT', false),
            ('job5', 'u3', 'CREATE OR REPLACE TABLE my_table AS SELECT 1', 1000, 1.0, '2023-10-03', 'CREATE_TABLE_AS_SELECT', false)
        """)
        conn.close()
        
        yield config_path, db_path

def test_find_expensive_scans(mock_db_and_config):
    config_path, db_path = mock_db_and_config
    engine = HeuristicsEngine(config_path, db_path)
    
    results = engine.find_expensive_scans()
    
    assert len(results) == 1
    assert results[0]["job_id"] == "job1"
    assert results[0]["rule"] == "LARGE_SCAN"
    assert results[0]["estimated_cost_usd"] == 5.0

def test_find_repeated_queries(mock_db_and_config):
    config_path, db_path = mock_db_and_config
    engine = HeuristicsEngine(config_path, db_path)
    
    results = engine.find_repeated_queries()
    
    assert len(results) == 1
    assert results[0]["execution_count"] == 2
    assert results[0]["estimated_cost_usd"] == 4.0 # 2.0 + 2.0
    assert results[0]["potential_savings_usd"] == 2.0
    assert "SELECT count(*) FROM x" in results[0]["query_snippet"]

def test_find_unused_materializations(mock_db_and_config):
    config_path, db_path = mock_db_and_config
    engine = HeuristicsEngine(config_path, db_path)
    
    results = engine.find_unused_materializations()
    
    assert len(results) == 1
    assert results[0]["table_name"] == "my_table"
    assert results[0]["estimated_cost_usd"] == 1.0
