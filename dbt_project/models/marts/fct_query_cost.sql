{{ config(materialized='table') }}

with jobs as (
    select * from {{ ref('stg_jobs') }}
),

calculated_costs as (
    select
        job_id,
        creation_time,
        date_trunc('day', creation_time) as execution_date,
        user_email,
        job_type,
        statement_type,
        query,
        total_bytes_processed,
        total_slot_ms,
        cache_hit,
        referenced_tables,
        -- BigQuery pricing: ~$6.25 per TiB (1024^4 bytes)
        -- Formula: (bytes / 1024^4) * 6.25
        case 
            when cache_hit then 0
            else coalesce((total_bytes_processed * 1.0 / power(1024, 4)) * 6.25, 0) 
        end as estimated_cost_usd
    from jobs
    where job_type = 'QUERY'
)

select * from calculated_costs
