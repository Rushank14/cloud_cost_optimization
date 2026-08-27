# Project Postmortem & Design Decisions

*This document is a placeholder for you to fill in during and after development. It demonstrates an engineering mindset by reflecting on trade-offs, debugging processes, and limitations.*

## 1. Design Decisions & Trade-offs
*   **Orchestration**: Chose Airflow for industry familiarity (or Dagster for modern data practices).
*   **Warehouse Mocking**: Used DuckDB locally to emulate BigQuery. This allows the pipeline to run in CI and on local machines without incurring cloud costs or requiring GCP service accounts, while keeping the SQL dialect similar.
*   **Heuristics Engine**: Built in Python rather than pure SQL/dbt to allow for more complex regex parsing (e.g., extracting table names from CTAS) and easier integration with notification/reporting systems.

## 2. Debugging Log
*What broke while building this, how did I diagnose it, and how was it fixed?*

*   **[Date] Issue 1**: (Example: Regular expression for CTAS failed to capture table names without backticks).
    *   *Diagnosis*: Noticed `test_find_unused_materializations` failing in pytest. 
    *   *Fix*: Relaxed the regex `TABLE\s+`?([a-zA-Z0-9_\-\.]+)`?\s+AS` to make backticks optional.

## 3. Known Limitations (Production Gaps)
*   The `referenced_tables` field in our mock data is a string/JSON. In real BigQuery, this is a complex `ARRAY<STRUCT>`. The ingestion layer would need to `UNNEST()` this properly in `stg_jobs.sql`.
*   The unused materialization check uses simple string matching (`table_name not in all_selects`). In production, this can lead to false positives if table names are substrings of other words. A true production system would parse the SQL AST (e.g., using `sqlglot`) or rely on BigQuery's audit logs / metadata API.
