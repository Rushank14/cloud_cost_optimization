# Cloud Data Warehouse Cost Optimization Report
*Generated on: 2026-08-28 01:00:32*

## 1. Executive Summary
- **Large Unpartitioned Scans Flagged**: 131 (Total wasted cost: $4093.75)
- **Repeated Queries Flagged**: 27 (Potential daily savings: $3590.15)
- **Unused Materializations Flagged**: 14 (Total wasted cost: $62.50)

## 2. Top Inefficiencies (Action Required)

### A. Large Unpartitioned Scans
*These single queries scanned massive amounts of data without partition filters.*

- **Job ID**: `bquxjob_9e1224ed_US` (User: analyst_junior@example.com)
  - **Cost**: $31.25
  - **Details**: Query scanned 5120.00 GB.
  - **Simulation**: *If this table were partitioned by date and the query filtered to a single day, the cost would drop to ~$0.09.*

- **Job ID**: `bquxjob_f9d63afb_US` (User: analyst_junior@example.com)
  - **Cost**: $31.25
  - **Details**: Query scanned 5120.00 GB.
  - **Simulation**: *If this table were partitioned by date and the query filtered to a single day, the cost would drop to ~$0.09.*

- **Job ID**: `bquxjob_edda93f8_US` (User: analyst_junior@example.com)
  - **Cost**: $31.25
  - **Details**: Query scanned 5120.00 GB.
  - **Simulation**: *If this table were partitioned by date and the query filtered to a single day, the cost would drop to ~$0.09.*

- **Job ID**: `bquxjob_796ae911_US` (User: analyst_junior@example.com)
  - **Cost**: $31.25
  - **Details**: Query scanned 5120.00 GB.
  - **Simulation**: *If this table were partitioned by date and the query filtered to a single day, the cost would drop to ~$0.09.*

- **Job ID**: `bquxjob_55c3d81b_US` (User: analyst_junior@example.com)
  - **Cost**: $31.25
  - **Details**: Query scanned 5120.00 GB.
  - **Simulation**: *If this table were partitioned by date and the query filtered to a single day, the cost would drop to ~$0.09.*

### B. Repeated Dashboard/BI Queries
*These exact queries are run multiple times a day and should be cached or materialized.* 

- **Query**: `SELECT * FROM `portfolio-cost-optimization.analytics_prod.events_raw` WHERE event_type = 'click'...`
  - **Executions**: 14 times
  - **Current Cost**: $437.50
  - **Potential Savings**: **$406.25**
  - **Simulation**: *Materializing this query via dbt into a daily incremental model would cost $31.25 once per day, saving $406.25.*

- **Query**: `SELECT * FROM `portfolio-cost-optimization.analytics_prod.events_raw` WHERE event_type = 'click'...`
  - **Executions**: 13 times
  - **Current Cost**: $406.25
  - **Potential Savings**: **$375.00**
  - **Simulation**: *Materializing this query via dbt into a daily incremental model would cost $31.25 once per day, saving $375.00.*

- **Query**: `SELECT * FROM `portfolio-cost-optimization.analytics_prod.events_raw` WHERE event_type = 'click'...`
  - **Executions**: 12 times
  - **Current Cost**: $375.00
  - **Potential Savings**: **$343.75**
  - **Simulation**: *Materializing this query via dbt into a daily incremental model would cost $31.25 once per day, saving $343.75.*

- **Query**: `SELECT * FROM `portfolio-cost-optimization.analytics_prod.events_raw` WHERE event_type = 'click'...`
  - **Executions**: 12 times
  - **Current Cost**: $375.00
  - **Potential Savings**: **$343.75**
  - **Simulation**: *Materializing this query via dbt into a daily incremental model would cost $31.25 once per day, saving $343.75.*

- **Query**: `SELECT * FROM `portfolio-cost-optimization.analytics_prod.events_raw` WHERE event_type = 'click'...`
  - **Executions**: 12 times
  - **Current Cost**: $375.00
  - **Potential Savings**: **$343.75**
  - **Simulation**: *Materializing this query via dbt into a daily incremental model would cost $31.25 once per day, saving $343.75.*

### C. Unused Materialized Views / CTAS
*These tables are being built at a cost, but are never queried by downstream users.*

- **Table**: `portfolio-cost-optimization.analytics_prod.mv_unused_summary` (Created by Job: bquxjob_53412277_US)
  - **Wasted Cost**: $4.46
  - **Recommendation**: Drop this model from the dbt DAG or convert it to a view.

- **Table**: `portfolio-cost-optimization.analytics_prod.mv_unused_summary` (Created by Job: bquxjob_30fc0afe_US)
  - **Wasted Cost**: $4.46
  - **Recommendation**: Drop this model from the dbt DAG or convert it to a view.

- **Table**: `portfolio-cost-optimization.analytics_prod.mv_unused_summary` (Created by Job: bquxjob_f6a99e00_US)
  - **Wasted Cost**: $4.46
  - **Recommendation**: Drop this model from the dbt DAG or convert it to a view.

- **Table**: `portfolio-cost-optimization.analytics_prod.mv_unused_summary` (Created by Job: bquxjob_34b3c112_US)
  - **Wasted Cost**: $4.46
  - **Recommendation**: Drop this model from the dbt DAG or convert it to a view.

- **Table**: `portfolio-cost-optimization.analytics_prod.mv_unused_summary` (Created by Job: bquxjob_3f985f02_US)
  - **Wasted Cost**: $4.46
  - **Recommendation**: Drop this model from the dbt DAG or convert it to a view.

