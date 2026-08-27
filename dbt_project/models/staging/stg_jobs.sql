with source as (
    select * from {{ source('raw', 'raw_information_schema_jobs') }}
),

renamed as (
    select
        job_id,
        creation_time::timestamp as creation_time,
        project_id,
        user_email,
        job_type,
        statement_type,
        query,
        total_bytes_processed::bigint as total_bytes_processed,
        total_slot_ms::bigint as total_slot_ms,
        referenced_tables, -- this is a string representation in our mock
        cache_hit::boolean as cache_hit,
        error_result
    from source
)

select * from renamed
