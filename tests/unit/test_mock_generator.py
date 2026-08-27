import json
import os
from datetime import datetime

import pytest

from src.mock_data.generator import (
    generate_bad_full_scan,
    generate_good_partitioned_scan,
    generate_mock_logs,
)

def test_generate_bad_full_scan():
    timestamp = datetime(2023, 10, 1, 12, 0, 0)
    log = generate_bad_full_scan(timestamp)
    
    assert log["job_type"] == "QUERY"
    assert "SELECT *" in log["query"]
    assert log["total_bytes_processed"] > 1024**3  # Should be large (TB scale)
    assert log["user_email"] == "analyst_junior@example.com"
    assert not log["cache_hit"]

def test_generate_good_partitioned_scan():
    timestamp = datetime(2023, 10, 1, 12, 0, 0)
    log = generate_good_partitioned_scan(timestamp)
    
    assert "WHERE date =" in log["query"]
    # Should be significantly smaller than a full scan
    assert log["total_bytes_processed"] > 0

def test_generate_mock_logs():
    logs = generate_mock_logs(days=2, logs_per_day=5)
    
    # 2 days * 5 logs/day + 2 materializations = 12 logs
    assert len(logs) == 12
    
    # Check sorting
    for i in range(1, len(logs)):
        assert logs[i]["creation_time"] >= logs[i-1]["creation_time"]

def test_mock_data_structure():
    logs = generate_mock_logs(days=1, logs_per_day=1)
    log = logs[0]
    
    expected_keys = {
        "creation_time", "project_id", "user_email", "job_id", 
        "job_type", "statement_type", "query", "total_bytes_processed", 
        "total_slot_ms", "referenced_tables", "cache_hit", "error_result"
    }
    assert set(log.keys()) == expected_keys
