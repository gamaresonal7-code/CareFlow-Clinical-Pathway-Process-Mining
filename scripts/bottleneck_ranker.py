"""
CareFlow - Bottleneck Ranking Engine
Ranks clinical bottlenecks by severity and calculates patient impact.
"""
import pandas as pd

def rank_bottlenecks(transitions_df):
    # Severity score = mean_duration * frequency
    transitions_df["severity_score"] = transitions_df["mean_duration_minutes"] * transitions_df["transition_count"]
    ranked = transitions_df.sort_values(by="severity_score", ascending=False).reset_index(drop=True)
    ranked["rank"] = ranked.index + 1
    return ranked
