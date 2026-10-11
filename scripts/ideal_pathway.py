"""
CareFlow - Normative Clinical Pathway Model
Defines the mandated hospital journey for patients requiring emergency radiology.
"""

IDEAL_PATHWAY_STEPS = [
    {"step": 1, "activity": "Registration & Arrival", "target_minutes": 10},
    {"step": 2, "activity": "Triage Assessment", "target_minutes": 15},
    {"step": 3, "activity": "Physician Initial Consultation", "target_minutes": 25},
    {"step": 4, "activity": "Diagnostic Imaging Order", "target_minutes": 5},
    {"step": 5, "activity": "Diagnostic Radiology (X-Ray)", "target_minutes": 30},
    {"step": 6, "activity": "Clinical Treatment & Medication Admin", "target_minutes": 45},
    {"step": 7, "activity": "Observation & Vital Re-check", "target_minutes": 60},
    {"step": 8, "activity": "Discharge Planning & Summary", "target_minutes": 20}
]

def get_ideal_sequence():
    return [s["activity"] for s in IDEAL_PATHWAY_STEPS]
