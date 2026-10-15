"""
CareFlow - Clinical Pathway Process Mining
Script: export_powerbi_dataset.py
Author: Annagiri Goutham (Data Associate L1 Intern, Infotact Solutions)
Domain: Healthcare Operations & Process Analytics

Purpose:
Prepares flat, denormalized dimensional datasets optimized for Microsoft PowerBI, 
Google Looker Studio, and Tableau process mining visuals.
"""

import os
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
POWERBI_DIR = os.path.join(DATA_DIR, "powerbi_export")

def export_powerbi_tables():
    print("=" * 70)
    print("CareFlow PowerBI & Looker Dataset Exporter")
    print("=" * 70)

    os.makedirs(POWERBI_DIR, exist_ok=True)

    events_path = os.path.join(DATA_DIR, "processed_event_log.csv")
    meta_path = os.path.join(DATA_DIR, "patients_metadata.csv")
    transitions_path = os.path.join(DATA_DIR, "dbt_transitions.csv")
    bottleneck_path = os.path.join(DATA_DIR, "bottleneck_analysis.csv")

    if not all(os.path.exists(p) for p in [events_path, meta_path, transitions_path, bottleneck_path]):
        raise FileNotFoundError("Missing prerequisite processed files in data/. Run pipeline first.")

    df_events = pd.read_csv(events_path)
    df_meta = pd.read_csv(meta_path)
    df_transitions = pd.read_csv(transitions_path)
    df_bottleneck = pd.read_csv(bottleneck_path)

    # 1. Dimension Table: Dim_Patient
    dim_patient = df_meta[[
        "case_id", "age", "gender", "esi_score", "triage_acuity", 
        "arrival_mode", "archetype", "had_radiology", "had_loopback",
        "num_events", "total_duration_minutes", "total_cost_usd", "disposition"
    ]].copy()
    dim_patient.to_csv(os.path.join(POWERBI_DIR, "Dim_Patient.csv"), index=False)

    # 2. Fact Table: Fact_Event_Stream (linked to Dim_Patient via case_id)
    fact_events = df_events[[
        "case_id", "event_sequence_num", "activity_name", "event_timestamp",
        "next_activity_name", "transition_duration_minutes", "staff_resource",
        "department_name", "activity_cost_usd", "execution_status"
    ]].copy()
    fact_events.to_csv(os.path.join(POWERBI_DIR, "Fact_Event_Stream.csv"), index=False)

    # 3. Process Flow Graph Table: Dim_Process_Edges (for Custom Process Visuals)
    df_transitions.to_csv(os.path.join(POWERBI_DIR, "Dim_Process_Graph_Edges.csv"), index=False)

    # 4. Bottleneck KPI Table
    df_bottleneck.to_csv(os.path.join(POWERBI_DIR, "Fact_Bottleneck_KPIs.csv"), index=False)

    print(f"\n[+] Exported 4 PowerBI / Looker Studio Star-Schema Tables to:")
    print(f"    {POWERBI_DIR}")
    print("    1. Dim_Patient.csv (1,200 rows)")
    print("    2. Fact_Event_Stream.csv (9,448 rows)")
    print("    3. Dim_Process_Graph_Edges.csv (19 edges)")
    print("    4. Fact_Bottleneck_KPIs.csv (19 rows)")
    print("=" * 70)

if __name__ == "__main__":
    export_powerbi_tables()
