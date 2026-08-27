{{ config(materialized='table') }}

with query_costs as (
    select * from {{ ref('fct_query_cost') }}
)

select
    execution_date,
    user_email,
    count(job_id) as total_queries,
    sum(estimated_cost_usd) as total_spend_usd,
    sum(total_bytes_processed) as total_bytes_scanned,
    sum(case when cache_hit then 1 else 0 end) as total_cache_hits
from query_costs
group by 1, 2
