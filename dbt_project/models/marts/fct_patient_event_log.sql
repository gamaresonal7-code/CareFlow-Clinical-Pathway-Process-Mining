-- Mart Model: fct_patient_event_log.sql
-- Description: Enriches event log with next-activity lead transitions, durations, and loop flags.

WITH ranked_events AS (
    SELECT
        case_id,
        activity_name,
        event_timestamp,
        staff_resource,
        department_name,
        activity_cost_usd,
        execution_status,
        event_sequence_num,
        LEAD(activity_name) OVER (
            PARTITION BY case_id 
            ORDER BY event_sequence_num
        ) AS next_activity_name,
        LEAD(event_timestamp) OVER (
            PARTITION BY case_id 
            ORDER BY event_sequence_num
        ) AS next_event_timestamp
    FROM {{ ref('stg_raw_ehr_logs') }}
)

SELECT
    case_id,
    event_sequence_num,
    activity_name,
    event_timestamp,
    next_activity_name,
    next_event_timestamp,
    ROUND(
        EXTRACT(EPOCH FROM (next_event_timestamp - event_timestamp)) / 60.0, 
        2
    ) AS transition_duration_minutes,
    staff_resource,
    department_name,
    activity_cost_usd,
    execution_status,
    CASE 
        WHEN event_sequence_num = 1 THEN TRUE 
        ELSE FALSE 
    END AS is_case_start,
    CASE 
        WHEN next_activity_name IS NULL THEN TRUE 
        ELSE FALSE 
    END AS is_case_end,
    CASE
        WHEN activity_name = 'Diagnostic Radiology (X-Ray)' 
             AND next_activity_name IN ('Missing Paperwork Flagged', 'Return to Triage (Paperwork Resolution)')
        THEN TRUE
        ELSE FALSE
    END AS is_radiology_loopback_trigger
FROM ranked_events
