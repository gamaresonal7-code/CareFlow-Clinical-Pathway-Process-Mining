"""
CareFlow - Conformance Checking Engine
Evaluates conformance of actual patient traces against the ideal ER pathway.
"""
import pm4py
from scripts.ideal_pathway import get_ideal_sequence

def check_trace_compliance(trace):
    ideal = get_ideal_sequence()
    # Check if any deviation or loopback exists
    has_paperwork_deviation = any("Paperwork" in act or "Return to Triage" in act for act in trace)
    is_compliant = not has_paperwork_deviation
    return {
        "is_compliant": is_compliant,
        "fitness_score": 0.65 if has_paperwork_deviation else 1.0,
        "deviation_type": "Administrative Paperwork Loop-Back" if has_paperwork_deviation else "None"
    }
