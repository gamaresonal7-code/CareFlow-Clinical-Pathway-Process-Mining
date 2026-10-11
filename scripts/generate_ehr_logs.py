"""
CareFlow - Clinical Pathway Process Mining
Script: generate_ehr_logs.py
Author: Annagiri Goutham (Data Associate L1 Intern, Infotact Solutions)
Domain: Healthcare Operations & Process Analytics

Purpose:
Simulates raw, timestamped Electronic Health Record (EHR) event logs for 1,200 emergency
department patients over 30 days. Deliberately models operational inefficiencies, 
including the documented 40% post-radiology paperwork loop-back to Triage.
"""

import os
import random
import datetime
import pandas as pd
import numpy as np

# Set seed for reproducible synthetic data generation
random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RAW_LOG_PATH = os.path.join(OUTPUT_DIR, "raw_ehr_events.csv")
PATIENTS_META_PATH = os.path.join(OUTPUT_DIR, "patients_metadata.csv")

# Clinical Staff Resources
DOCTORS = ["Dr. Meredith Grey", "Dr. Gregory House", "Dr. Shaun Murphy", "Dr. John Dorian", "Dr. Miranda Bailey"]
NURSES = ["Nurse Jackie Peyton", "Nurse Carol Hathaway", "Nurse Carla Espinosa", "Nurse Chuny Marquez"]
TECH_RADIOLOGY = ["Tech Mark Sloan", "Tech Lexie Grey", "Tech Peter Parker"]
LAB_TECHS = ["LabTech Bruce Banner", "LabTech Walter Bishop"]
ADMIN_STAFF = ["Clerk Pam Beesly", "Clerk Donna Noble", "Clerk Stanley Hudson"]

# Departments
DEPTS = {
    "Registration & Arrival": "Front Desk",
    "Triage Assessment": "Emergency Triage",
    "Physician Initial Consultation": "ED Acute Ward",
    "Diagnostic Imaging Order": "ED Acute Ward",
    "Diagnostic Radiology (X-Ray)": "Radiology Department",
    "Missing Paperwork Flagged": "Radiology Department",
    "Return to Triage (Paperwork Resolution)": "Emergency Triage",
    "Physician Re-consultation": "ED Acute Ward",
    "Laboratory Blood Test Order": "ED Acute Ward",
    "Laboratory Specimen Analysis": "Central Pathology",
    "Clinical Treatment & Medication Admin": "ED Treatment Bays",
    "Observation & Vital Re-check": "ED Short Stay Unit",
    "Discharge Planning & Summary": "Discharge Lounge",
    "Hospital Inpatient Admission": "Inpatient Ward"
}

ACTIVITY_COSTS = {
    "Registration & Arrival": 25.0,
    "Triage Assessment": 45.0,
    "Physician Initial Consultation": 180.0,
    "Diagnostic Imaging Order": 35.0,
    "Diagnostic Radiology (X-Ray)": 240.0,
    "Missing Paperwork Flagged": 50.0,  # Administrative waste cost
    "Return to Triage (Paperwork Resolution)": 65.0,  # Re-triage penalty cost
    "Physician Re-consultation": 120.0,
    "Laboratory Blood Test Order": 40.0,
    "Laboratory Specimen Analysis": 110.0,
    "Clinical Treatment & Medication Admin": 150.0,
    "Observation & Vital Re-check": 80.0,
    "Discharge Planning & Summary": 50.0,
    "Hospital Inpatient Admission": 1200.0
}

def generate_patient_records(num_patients=1200):
    start_date = datetime.datetime(2026, 9, 1, 8, 0, 0)
    all_events = []
    patients_meta = []

    loopback_count = 0
    radiology_count = 0

    print(f"[*] Generating {num_patients} clinical patient pathways...")

    for i in range(1, num_patients + 1):
        case_id = f"PAT-{10000 + i}"
        
        # Patient demographics & triage presentation
        age = int(np.random.normal(48, 18))
        age = max(18, min(92, age))
        gender = random.choice(["Male", "Female", "Other"])
        arrival_mode = random.choices(["Walk-in", "Ambulance", "Private Transport"], weights=[0.60, 0.25, 0.15])[0]
        
        # Triage Acuity (Emergency Severity Index: ESI 1 to 5)
        # 1: Immediate/Resuscitation, 2: Emergent, 3: Urgent, 4: Less Urgent, 5: Non-Urgent
        esi_score = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.20, 0.45, 0.20, 0.10])[0]

        # Case arrival timestamp spread over 30 days
        arrival_delta_seconds = int(np.random.uniform(0, 30 * 24 * 3600))
        patient_time = start_date + datetime.timedelta(seconds=arrival_delta_seconds)

        # Primary Physician and Nurse assigned
        doctor = random.choice(DOCTORS)
        nurse = random.choice(NURSES)
        clerk = random.choice(ADMIN_STAFF)

        # Determine clinical pathway archetype
        # 0: Trauma/Orthopedic (Imaging needed)
        # 1: Acute Medical (Labs needed)
        # 2: Combined Diagnostic (Labs + Imaging)
        # 3: Low Acuity / Fast-Track (Consultation only)
        if esi_score == 1:
            archetype = "Critical"
        elif esi_score in [2, 3]:
            archetype = random.choices(["Trauma_Imaging", "Acute_Medical", "Combined_Diagnostic"], weights=[0.45, 0.35, 0.20])[0]
        else:
            archetype = "Low_Acuity"

        events_for_patient = []
        is_loopback_patient = False

        # Step 1: Registration
        events_for_patient.append({
            "case_id": case_id,
            "activity": "Registration & Arrival",
            "timestamp": patient_time,
            "resource": clerk,
            "department": DEPTS["Registration & Arrival"],
            "cost_usd": ACTIVITY_COSTS["Registration & Arrival"],
            "status": "Completed"
        })

        # Wait for Triage (5 - 20 mins depending on arrival mode)
        triage_wait = random.randint(3, 12) if arrival_mode == "Ambulance" else random.randint(8, 25)
        patient_time += datetime.timedelta(minutes=triage_wait)

        # Step 2: Triage Assessment
        events_for_patient.append({
            "case_id": case_id,
            "activity": "Triage Assessment",
            "timestamp": patient_time,
            "resource": nurse,
            "department": DEPTS["Triage Assessment"],
            "cost_usd": ACTIVITY_COSTS["Triage Assessment"],
            "status": "Completed"
        })

        # Wait for Physician Consultation (15 - 60 mins depending on ESI)
        wait_for_doc = {1: random.randint(2, 5), 2: random.randint(10, 20), 3: random.randint(25, 45), 4: random.randint(40, 75), 5: random.randint(50, 90)}[esi_score]
        patient_time += datetime.timedelta(minutes=wait_for_doc)

        # Step 3: Physician Consultation
        events_for_patient.append({
            "case_id": case_id,
            "activity": "Physician Initial Consultation",
            "timestamp": patient_time,
            "resource": doctor,
            "department": DEPTS["Physician Initial Consultation"],
            "cost_usd": ACTIVITY_COSTS["Physician Initial Consultation"],
            "status": "Completed"
        })

        # Diagnostics execution based on archetype
        needs_radiology = archetype in ["Trauma_Imaging", "Combined_Diagnostic"]
        needs_labs = archetype in ["Acute_Medical", "Combined_Diagnostic", "Critical"]

        if needs_radiology:
            radiology_count += 1
            # Order Imaging
            patient_time += datetime.timedelta(minutes=random.randint(5, 12))
            events_for_patient.append({
                "case_id": case_id,
                "activity": "Diagnostic Imaging Order",
                "timestamp": patient_time,
                "resource": doctor,
                "department": DEPTS["Diagnostic Imaging Order"],
                "cost_usd": ACTIVITY_COSTS["Diagnostic Imaging Order"],
                "status": "Completed"
            })

            # Transit to Radiology & X-Ray Execution
            rad_tech = random.choice(TECH_RADIOLOGY)
            patient_time += datetime.timedelta(minutes=random.randint(15, 30))
            events_for_patient.append({
                "case_id": case_id,
                "activity": "Diagnostic Radiology (X-Ray)",
                "timestamp": patient_time,
                "resource": rad_tech,
                "department": DEPTS["Diagnostic Radiology (X-Ray)"],
                "cost_usd": ACTIVITY_COSTS["Diagnostic Radiology (X-Ray)"],
                "status": "Completed"
            })

            # --- KEY BOTTLENECK & LOOP-BACK IMPLEMENTATION ---
            # Approximately 40% of patients who get an X-Ray face the "Missing Paperwork Form 4B" issue!
            if random.random() < 0.40:
                is_loopback_patient = True
                loopback_count += 1

                # Missing paperwork flagged at Radiology discharge
                patient_time += datetime.timedelta(minutes=random.randint(6, 12))
                events_for_patient.append({
                    "case_id": case_id,
                    "activity": "Missing Paperwork Flagged",
                    "timestamp": patient_time,
                    "resource": rad_tech,
                    "department": DEPTS["Missing Paperwork Flagged"],
                    "cost_usd": ACTIVITY_COSTS["Missing Paperwork Flagged"],
                    "status": "Exception_Flagged"
                })

                # Sent BACK to Triage to fill out missing clinical consent/intake form
                transit_delay = random.randint(12, 22)
                patient_time += datetime.timedelta(minutes=transit_delay)
                events_for_patient.append({
                    "case_id": case_id,
                    "activity": "Return to Triage (Paperwork Resolution)",
                    "timestamp": patient_time,
                    "resource": nurse,
                    "department": DEPTS["Return to Triage (Paperwork Resolution)"],
                    "cost_usd": ACTIVITY_COSTS["Return to Triage (Paperwork Resolution)"],
                    "status": "Loopback_Rework"
                })

                # Re-assessment by Doctor after paperwork rectified
                patient_time += datetime.timedelta(minutes=random.randint(15, 30))
                events_for_patient.append({
                    "case_id": case_id,
                    "activity": "Physician Re-consultation",
                    "timestamp": patient_time,
                    "resource": doctor,
                    "department": DEPTS["Physician Re-consultation"],
                    "cost_usd": ACTIVITY_COSTS["Physician Re-consultation"],
                    "status": "Completed"
                })

        if needs_labs:
            # Order Lab tests
            patient_time += datetime.timedelta(minutes=random.randint(5, 10))
            events_for_patient.append({
                "case_id": case_id,
                "activity": "Laboratory Blood Test Order",
                "timestamp": patient_time,
                "resource": doctor,
                "department": DEPTS["Laboratory Blood Test Order"],
                "cost_usd": ACTIVITY_COSTS["Laboratory Blood Test Order"],
                "status": "Completed"
            })

            # Lab analysis
            lab_tech = random.choice(LAB_TECHS)
            patient_time += datetime.timedelta(minutes=random.randint(30, 60))
            events_for_patient.append({
                "case_id": case_id,
                "activity": "Laboratory Specimen Analysis",
                "timestamp": patient_time,
                "resource": lab_tech,
                "department": DEPTS["Laboratory Specimen Analysis"],
                "cost_usd": ACTIVITY_COSTS["Laboratory Specimen Analysis"],
                "status": "Completed"
            })

        # Treatment & Medication Administration
        patient_time += datetime.timedelta(minutes=random.randint(10, 25))
        events_for_patient.append({
            "case_id": case_id,
            "activity": "Clinical Treatment & Medication Admin",
            "timestamp": patient_time,
            "resource": nurse,
            "department": DEPTS["Clinical Treatment & Medication Admin"],
            "cost_usd": ACTIVITY_COSTS["Clinical Treatment & Medication Admin"],
            "status": "Completed"
        })

        # Observation (optional for urgent/emergent, or standard monitoring)
        if esi_score in [1, 2, 3] or is_loopback_patient:
            patient_time += datetime.timedelta(minutes=random.randint(20, 50))
            events_for_patient.append({
                "case_id": case_id,
                "activity": "Observation & Vital Re-check",
                "timestamp": patient_time,
                "resource": nurse,
                "department": DEPTS["Observation & Vital Re-check"],
                "cost_usd": ACTIVITY_COSTS["Observation & Vital Re-check"],
                "status": "Completed"
            })

        # Final Disposition: Discharge vs Admission
        patient_time += datetime.timedelta(minutes=random.randint(10, 20))
        if esi_score in [1, 2] and random.random() < 0.65:
            final_activity = "Hospital Inpatient Admission"
        else:
            final_activity = "Discharge Planning & Summary"

        events_for_patient.append({
            "case_id": case_id,
            "activity": final_activity,
            "timestamp": patient_time,
            "resource": doctor if "Admission" in final_activity else clerk,
            "department": DEPTS[final_activity],
            "cost_usd": ACTIVITY_COSTS[final_activity],
            "status": "Completed"
        })

        # Calculate total journey duration for metadata
        total_duration_minutes = (events_for_patient[-1]["timestamp"] - events_for_patient[0]["timestamp"]).total_seconds() / 60.0
        total_case_cost = sum(e["cost_usd"] for e in events_for_patient)

        patients_meta.append({
            "case_id": case_id,
            "age": age,
            "gender": gender,
            "esi_score": esi_score,
            "triage_acuity": {1: "Resuscitation", 2: "Emergent", 3: "Urgent", 4: "Less Urgent", 5: "Non-Urgent"}[esi_score],
            "arrival_mode": arrival_mode,
            "archetype": archetype,
            "had_radiology": needs_radiology,
            "had_loopback": is_loopback_patient,
            "num_events": len(events_for_patient),
            "total_duration_minutes": round(total_duration_minutes, 1),
            "total_cost_usd": round(total_case_cost, 2),
            "arrival_timestamp": events_for_patient[0]["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "departure_timestamp": events_for_patient[-1]["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "disposition": "Admitted" if "Admission" in final_activity else "Discharged"
        })

        all_events.extend(events_for_patient)

    # Format event logs DataFrame
    df_events = pd.DataFrame(all_events)
    df_events["timestamp"] = df_events["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    df_meta = pd.DataFrame(patients_meta)

    # Export CSVs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_events.to_csv(RAW_LOG_PATH, index=False)
    df_meta.to_csv(PATIENTS_META_PATH, index=False)

    print("\n[+] Data Generation Complete!")
    print(f"    - Total Events Logged: {len(df_events):,}")
    print(f"    - Total Patient Cases: {len(df_meta):,}")
    print(f"    - Radiology Patients: {radiology_count:,}")
    loopback_pct = (loopback_count / radiology_count * 100) if radiology_count else 0
    print(f"    - Paperwork Loop-Back Cases: {loopback_count:,} ({loopback_pct:.1f}% of Radiology cases)")
    
    # Calculate duration discrepancy
    loop_duration = df_meta[df_meta["had_loopback"]]["total_duration_minutes"].mean()
    no_loop_duration = df_meta[~df_meta["had_loopback"]]["total_duration_minutes"].mean()
    print(f"    - Average Stay (Loop-Back Patients): {loop_duration:.1f} mins ({loop_duration/60:.2f} hrs)")
    print(f"    - Average Stay (Standard Patients):  {no_loop_duration:.1f} mins ({no_loop_duration/60:.2f} hrs)")
    print(f"    - Operational Penalty: +{loop_duration - no_loop_duration:.1f} mins per affected patient!\n")

    return df_events, df_meta

if __name__ == "__main__":
    generate_patient_records(1200)
