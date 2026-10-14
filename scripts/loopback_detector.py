"""
CareFlow - Circular Loopback Detector
Detects and isolates circular routing: Diagnostic Radiology -> Return to Triage.
"""
import pandas as pd

def detect_rework_cycles(df):
    cases_with_loopback = set()
    grouped = df.groupby("case_id")["activity_name"].apply(list)
    for case_id, trace in grouped.items():
        for i in range(len(trace) - 1):
            if "Radiology" in trace[i] and ("Triage" in trace[i+1] or "Paperwork" in trace[i+1]):
                cases_with_loopback.add(case_id)
                break
    return {
        "loopback_cases_count": len(cases_with_loopback),
        "total_cases": len(grouped),
        "loopback_rate_pct": round(len(cases_with_loopback) / len(grouped) * 100, 2)
    }
