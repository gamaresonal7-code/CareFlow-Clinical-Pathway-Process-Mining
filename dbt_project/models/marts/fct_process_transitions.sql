-- Mart Model: fct_process_transitions.sql
-- Description: Generates Directed Process Graph edges with transition volumes and latency metrics.

WITH transitions AS (
    SELECT
        activity_name AS source_activity,
        next_activity_name AS target_activity,
        transition_duration_minutes
    FROM {{ ref('fct_patient_event_log') }}
    WHERE next_activity_name IS NOT NULL
)

SELECT
    source_activity,
    target_activity,
    COUNT(*) AS transition_frequency,
    ROUND(AVG(transition_duration_minutes), 2) AS avg_duration_minutes,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY transition_duration_minutes), 2) AS median_duration_minutes,
    ROUND(MIN(transition_duration_minutes), 2) AS min_duration_minutes,
    ROUND(MAX(transition_duration_minutes), 2) AS max_duration_minutes,
    ROUND(SUM(transition_duration_minutes), 2) AS total_wait_duration_minutes,
    CASE 
        WHEN source_activity = 'Diagnostic Radiology (X-Ray)' 
             AND target_activity = 'Missing Paperwork Flagged' 
        THEN 'CRITICAL_BOTTLENECK_LOOP'
        WHEN source_activity = 'Return to Triage (Paperwork Resolution)'
        THEN 'REWORK_PENALTY'
        ELSE 'STANDARD_FLOW'
    END AS flow_classification
FROM transitions
GROUP BY source_activity, target_activity
ORDER BY transition_frequency DESC
