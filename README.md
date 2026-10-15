# CareFlow - Clinical Pathway Process Mining & Patient Trajectory Optimization
**Backend Architecture & Data Analytics Engine**  
*Author:* Annagiri Goutham (Data Associate L1 Intern, Infotact Solutions)

---

## 🏥 Project Overview
**CareFlow** is an enterprise healthcare backend and data engineering pipeline designed to analyze electronic health record (EHR) event streams. By applying process mining algorithms (Directly-Follows Graphs and Bottleneck Discovery), CareFlow identifies operational latencies, redundant loop-backs, and dwell-times across hospital clinical pathways.

---

## 🛠️ Tech Stack & Architecture
- **Language**: Python 3.10+
- **REST API**: Flask (JSON endpoints with CORS enabled)
- **Analytical Storage**: DuckDB (in-process analytical SQL OLAP database)
- **Data Transformations**: dbt-core patterns & Pandas vectorized operations
- **Process Mining**: PM4Py (Process Mining for Python) & NetworkX
- **Testing**: Python `unittest` suite

---

## 📂 Project Structure
```text
careflow-clinical-process-mining/
├── api/
│   ├── __init__.py
│   └── app.py                      # Flask REST API endpoints
├── core/ & scripts/
│   ├── generate_ehr_logs.py        # EHR event simulator & synthetic dataset generator
│   ├── run_dbt_transformations.py  # DuckDB OLAP pipeline & staging transformations
│   ├── process_mining_engine.py    # PM4Py discovery, DFG graph & bottleneck detector
│   └── export_powerbi_dataset.py   # Star-schema dimensional data exporter
├── data/
│   ├── raw_ehr_events.csv          # Raw simulated event streams
│   ├── processed_event_log.csv     # Cleaned standard event logs
│   ├── patients_metadata.csv       # Patient demographics and cohort data
│   ├── careflow_warehouse.duckdb   # Analytical DuckDB warehouse
│   └── process_metrics.json        # Precomputed DFG nodes, edges & bottleneck KPIs
├── dbt_project/
│   ├── dbt_project.yml             # dbt configuration
│   └── models/
│       ├── staging/                # Cleaned staging views
│       └── marts/                  # Fact and dimension models
├── tests/
│   └── test_backend.py             # Backend unit test suite
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Execute Data Pipelines
```bash
# Step 1: Generate EHR dataset
python scripts/generate_ehr_logs.py

# Step 2: Build DuckDB warehouse and run transformations
python scripts/run_dbt_transformations.py

# Step 3: Run Process Mining discovery engine
python scripts/process_mining_engine.py
```

### 3. Launch Backend REST API
```bash
python api/app.py
```
The API starts on `http://127.0.0.1:5000`.

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and database connectivity |
| `GET` | `/api/metrics/summary` | Overall KPIs (total cases, events, variants, fitness %) |
| `GET` | `/api/metrics/bottlenecks` | Identified clinical bottlenecks with delays & cost impact |
| `GET` | `/api/graph/dfg` | Nodes and directed edges for process flow visualization |
| `GET` | `/api/patients?limit=50` | Paginated cohort metadata from DuckDB |
| `POST`| `/api/pipeline/run-discovery` | Triggers PM4Py discovery re-computation |

---

## 🧪 Running Unit Tests
```bash
python -m unittest tests/test_backend.py
```
