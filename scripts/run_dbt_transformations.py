"""
CareFlow - Clinical Pathway Process Mining
Script: run_dbt_transformations.py
Author: Annagiri Goutham (Data Associate L1 Intern, Infotact Solutions)
Domain: Healthcare Operations & Process Analytics

Purpose:
Executes the data transformation pipeline locally via DuckDB (serving as an in-memory
representation of the BigQuery / Snowflake data warehouse). Runs staging models, computes
windowed lead transitions, and materializes process mining marts.
"""

import os
import duckdb
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_LOG_PATH = os.path.join(DATA_DIR, "raw_ehr_events.csv")
DB_PATH = os.path.join(DATA_DIR, "careflow_warehouse.duckdb")

def run_transformations():
    print("=" * 70)
    print("CareFlow Data Transformation Engine (dbt / SQL Warehouse)")
    print("=" * 70)

    if not os.path.exists(RAW_LOG_PATH):
        raise FileNotFoundError(f"Source file not found: {RAW_LOG_PATH}. Run generate_ehr_logs.py first.")

    con = duckdb.connect(database=DB_PATH)

    # 1. Load Raw Source Table
    print("\n[Step 1/5] Ingesting raw EHR event logs into warehouse...")
    con.execute(f"CREATE OR REPLACE TABLE raw_ehr_events AS SELECT * FROM read_csv_auto('{RAW_LOG_PATH.replace(chr(92), '/')}')")
    raw_count = con.execute("SELECT COUNT(*) FROM raw_ehr_events").fetchone()[0]
    print(f"    -> Successfully loaded {raw_count:,} raw events into 'raw_ehr_events'.")

    # 2. Materialize Staging: stg_raw_ehr_logs
    print("\n[Step 2/5] Compiling and executing stg_raw_ehr_logs view...")
    con.execute("""
    CREATE OR REPLACE VIEW stg_raw_ehr_logs AS
    SELECT
        TRIM(case_id) AS case_id,
        TRIM(activity) AS activity_name,
        CAST(timestamp AS TIMESTAMP) AS event_timestamp,
        TRIM(resource) AS staff_resource,
        TRIM(department) AS department_name,
        CAST(cost_usd AS DECIMAL(10, 2)) AS activity_cost_usd,
        TRIM(status) AS execution_status,
        ROW_NUMBER() OVER (
            PARTITION BY case_id 
            ORDER BY CAST(timestamp AS TIMESTAMP) ASC
        ) AS event_sequence_num
    FROM raw_ehr_events;
    """)
    print("    -> Staging view 'stg_raw_ehr_logs' compiled successfully.")

    # 3. Materialize Mart: fct_patient_event_log
    print("\n[Step 3/5] Materializing fct_patient_event_log with transition windows...")
    con.execute("""
    CREATE OR REPLACE TABLE fct_patient_event_log AS
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
        FROM stg_raw_ehr_logs
    )
    SELECT
        case_id,
        event_sequence_num,
        activity_name,
        event_timestamp,
        next_activity_name,
        next_event_timestamp,
        ROUND(
            date_diff('second', event_timestamp, next_event_timestamp) / 60.0, 
            2
        ) AS transition_duration_minutes,
        staff_resource,
        department_name,
        activity_cost_usd,
        execution_status,
        CASE WHEN event_sequence_num = 1 THEN TRUE ELSE FALSE END AS is_case_start,
        CASE WHEN next_activity_name IS NULL THEN TRUE ELSE FALSE END AS is_case_end,
        CASE
            WHEN activity_name = 'Diagnostic Radiology (X-Ray)' 
                 AND next_activity_name IN ('Missing Paperwork Flagged', 'Return to Triage (Paperwork Resolution)')
            THEN TRUE
            ELSE FALSE
        END AS is_radiology_loopback_trigger
    FROM ranked_events;
    """)
    mart_count = con.execute("SELECT COUNT(*) FROM fct_patient_event_log").fetchone()[0]
    print(f"    -> Table 'fct_patient_event_log' materialized with {mart_count:,} records.")

    # 4. Materialize Mart: fct_process_transitions
    print("\n[Step 4/5] Computing Directly-Follows Graph edges & transition latency...")
    con.execute("""
    CREATE OR REPLACE TABLE fct_process_transitions AS
    WITH transitions AS (
        SELECT
            activity_name AS source_activity,
            next_activity_name AS target_activity,
            transition_duration_minutes
        FROM fct_patient_event_log
        WHERE next_activity_name IS NOT NULL
    )
    SELECT
        source_activity,
        target_activity,
        COUNT(*) AS transition_frequency,
        ROUND(AVG(transition_duration_minutes), 2) AS avg_duration_minutes,
        ROUND(MEDIAN(transition_duration_minutes), 2) AS median_duration_minutes,
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
    ORDER BY transition_frequency DESC;
    """)
    edge_count = con.execute("SELECT COUNT(*) FROM fct_process_transitions").fetchone()[0]
    print(f"    -> Table 'fct_process_transitions' materialized with {edge_count} distinct process edges.")

    # 5. Materialize Mart: fct_bottleneck_analysis
    print("\n[Step 5/5] Extracting operational bottleneck rankings...")
    con.execute("""
    CREATE OR REPLACE TABLE fct_bottleneck_analysis AS
    WITH transition_stats AS (
        SELECT * FROM fct_process_transitions
    ),
    totals AS (
        SELECT SUM(transition_frequency) AS total_all_transitions FROM transition_stats
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
    ORDER BY ts.avg_duration_minutes DESC;
    """)

    # Export clean datasets to CSV for PM4Py & BI Dashboards
    print("\n[Exporting Curated Data Files]")
    fct_event_df = con.execute("SELECT * FROM fct_patient_event_log").df()
    fct_transitions_df = con.execute("SELECT * FROM fct_process_transitions").df()
    fct_bottleneck_df = con.execute("SELECT * FROM fct_bottleneck_analysis").df()

    fct_event_df.to_csv(os.path.join(DATA_DIR, "processed_event_log.csv"), index=False)
    fct_transitions_df.to_csv(os.path.join(DATA_DIR, "dbt_transitions.csv"), index=False)
    fct_bottleneck_df.to_csv(os.path.join(DATA_DIR, "bottleneck_analysis.csv"), index=False)

    print(f"    - Saved 'processed_event_log.csv' ({len(fct_event_df):,} rows)")
    print(f"    - Saved 'dbt_transitions.csv' ({len(fct_transitions_df)} edges)")
    print(f"    - Saved 'bottleneck_analysis.csv' ({len(fct_bottleneck_df)} bottleneck rows)")

    # Display Top Bottlenecks
    print("\n" + "=" * 70)
    print("TOP 5 OPERATIONAL BOTTLENECKS BY DURATION (MINUTES)")
    print("=" * 70)
    top_5 = fct_bottleneck_df.head(5)[["source_activity", "target_activity", "transition_frequency", "avg_duration_minutes", "flow_classification"]]
    print(top_5.to_string(index=False))

    con.close()
    print("\n[+] Transformation Pipeline Completed Successfully!")

if __name__ == "__main__":
    run_transformations()
