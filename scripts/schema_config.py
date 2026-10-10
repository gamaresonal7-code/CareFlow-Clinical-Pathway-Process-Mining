"""
CareFlow - Clinical Pathway Schema Configuration
Defines ER activities, departments, and baseline clinical attributes.
"""

ER_ACTIVITIES = [
    "Registration & Arrival",
    "Triage Assessment",
    "Physician Initial Consultation",
    "Diagnostic Imaging Order",
    "Diagnostic Radiology (X-Ray)",
    "Missing Paperwork Flagged",
    "Return to Triage (Paperwork Resolution)",
    "Physician Re-consultation",
    "Laboratory Blood Test Order",
    "Laboratory Specimen Analysis",
    "Clinical Treatment & Medication Admin",
    "Observation & Vital Re-check",
    "Discharge Planning & Summary",
    "Hospital Inpatient Admission"
]

DEPARTMENTS = {
    "Registration & Arrival": "Front Desk",
    "Triage Assessment": "Emergency Triage",
    "Physician Initial Consultation": "ED Acute Ward",
    "Diagnostic Radiology (X-Ray)": "Radiology Department",
    "Missing Paperwork Flagged": "Radiology Department",
    "Return to Triage (Paperwork Resolution)": "Emergency Triage"
}
