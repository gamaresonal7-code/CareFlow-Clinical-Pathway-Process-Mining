-- Mart Model: fct_bottleneck_analysis.sql
-- Description: Quantifies delay bottlenecks, loop-backs, and administrative rework costs.

WITH transition_stats AS (
    SELECT
        source_activity,
        target_activity,
        transition_frequency,
        avg_duration_minutes,
        median_duration_minutes,
        total_wait_duration_minutes,
        flow_classification
    FROM {{ ref('fct_process_transitions') }}
),
totals AS (
    SELECT SUM(transition_frequency) AS total_all_transitions
    FROM transition_stats
)

SELECT
    ts.source_activity,
    ts.target_activity,
    ts.transition_frequency,
    ROUND((ts.transition_frequency * 100.0) / t.total_all_transitions, 2) AS pct_of_all_transitions,
    ts.avg_duration_minutes,
    ts.median_duration_minutes,
    ts.total_wait_duration_minutes,
    ROUND(ts.total_wait_duration_minutes / 60.0, 1) AS total_wait_hours_lost,
    ts.flow_classification,
    CASE
        WHEN ts.flow_classification IN ('CRITICAL_BOTTLENECK_LOOP', 'REWORK_PENALTY') THEN 'HIGH_PRIORITY_ACTION_REQUIRED'
        WHEN ts.avg_duration_minutes > 40 THEN 'MODERATE_MONITORING'
        ELSE 'NORMAL_EFFICIENCY'
    END AS operational_recommendation
FROM transition_stats ts
CROSS JOIN totals t
ORDER BY ts.avg_duration_minutes DESC
