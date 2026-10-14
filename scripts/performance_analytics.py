"""
CareFlow - Performance & Queue Transition Analytics
Measures dwell times and inter-activity lags across clinical stages.
"""
import pandas as pd
import numpy as np

def calculate_step_latencies(event_df):
    event_df = event_df.sort_values(by=["case_id", "event_timestamp"])
    event_df["prev_activity"] = event_df.groupby("case_id")["activity_name"].shift(1)
    event_df["prev_timestamp"] = event_df.groupby("case_id")["event_timestamp"].shift(1)
    
    event_df["transition_minutes"] = (
        pd.to_datetime(event_df["event_timestamp"]) - pd.to_datetime(event_df["prev_timestamp"])
    ).dt.total_seconds() / 60.0
    
    summary = event_df.groupby(["prev_activity", "activity_name"])["transition_minutes"].agg(
        ["count", "mean", "median", "max"]
    ).reset_index()
    return summary
