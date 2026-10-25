
# CareFlow: Clinical Pathway Process Mining

## Project Overview

CareFlow is a beginner-friendly data analytics prototype
that explores clinical event logs and patient journeys.

## Objectives

- Load and clean event-log data.
- Analyze patient journeys through clinical activities.
- Calculate overall journey duration.
- Visualize activity frequency.
- Examine elapsed time between consecutive activities.
- Display findings through an interactive dashboard.

## Technologies Used

- Python
- Pandas
- Plotly
- Streamlit
- CSV

## Dataset

The initial dataset contains synthetic patient activity
records created for development and demonstration.

It does not contain real patient information.

## Features

1. Patient case statistics.
2. Activity frequency chart.
3. Individual patient journey visualization.
4. Elapsed time analysis.
5. Event-log data preview.

## How to Run

Install the dependencies:

python -m pip install pandas plotly streamlit

Run the dashboard:

python -m streamlit run app.py

Keep app.py and clinical_events.csv in the same folder.

## Limitations

This is an initial prototype using a small synthetic
dataset. Its results are not validated clinical findings.
Elapsed time between activities does not necessarily
represent actual waiting time.
