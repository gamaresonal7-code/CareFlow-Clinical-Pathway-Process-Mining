-- Staging Model: stg_raw_ehr_logs.sql
-- Description: Standardizes and casts raw EHR audit logs from source tables.

WITH raw_events AS (
    SELECT
        TRIM(case_id) AS case_id,
        TRIM(activity) AS activity_name,
        CAST(timestamp AS TIMESTAMP) AS event_timestamp,
        TRIM(resource) AS staff_resource,
        TRIM(department) AS department_name,
        CAST(cost_usd AS DECIMAL(10, 2)) AS activity_cost_usd,
        TRIM(status) AS execution_status
    FROM {{ ref('raw_ehr_events') }}
)

SELECT
    case_id,
    activity_name,
    event_timestamp,
    staff_resource,
    department_name,
    activity_cost_usd,
    execution_status,
    ROW_NUMBER() OVER (
        PARTITION BY case_id 
        ORDER BY event_timestamp ASC
    ) AS event_sequence_num
FROM raw_events
