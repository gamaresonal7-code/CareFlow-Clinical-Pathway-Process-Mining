"""
CareFlow - Clinical Process Mining & Trajectory Optimization
Backend REST API Server (Flask)
Author: Annagiri Goutham (Data Associate L1 Intern, Infotact Solutions)
"""

import os
import json
import duckdb
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
METRICS_PATH = os.path.join(DATA_DIR, "process_metrics.json")
DB_PATH = os.path.join(DATA_DIR, "careflow_warehouse.duckdb")
PROCESSED_LOG_PATH = os.path.join(DATA_DIR, "processed_event_log.csv")


def get_db_connection():
    if os.path.exists(DB_PATH):
        return duckdb.connect(DB_PATH, read_only=True)
    return None


@app.route("/", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify backend status."""
    return jsonify({
        "status": "healthy",
        "service": "CareFlow Backend Analytics API",
        "version": "1.0.0",
        "author": "Annagiri Goutham",
        "database_connected": os.path.exists(DB_PATH),
        "data_ready": os.path.exists(METRICS_PATH)
    }), 200


@app.route("/api/metrics/summary", methods=["GET"])
def get_metrics_summary():
    """Returns high-level process mining KPIs and summary."""
    if not os.path.exists(METRICS_PATH):
        return jsonify({"error": "Process metrics not found. Run discovery engine first."}), 404

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify(data.get("summary", {})), 200


@app.route("/api/metrics/bottlenecks", methods=["GET"])
def get_bottlenecks():
    """Returns identified clinical bottlenecks with latency and cost impacts."""
    conn = get_db_connection()
    if conn:
        try:
            df = conn.execute("SELECT * FROM fct_bottleneck_analysis").df()
            conn.close()
            return jsonify({
                "count": len(df),
                "data": df.to_dict(orient="records")
            }), 200
        except Exception:
            conn.close()

    bottlenecks_csv = os.path.join(DATA_DIR, "bottleneck_analysis.csv")
    if os.path.exists(bottlenecks_csv):
        df = pd.read_csv(bottlenecks_csv)
        return jsonify({
            "count": len(df),
            "data": df.to_dict(orient="records")
        }), 200

    return jsonify({"error": "Bottleneck analysis not found."}), 404


@app.route("/api/graph/dfg", methods=["GET"])
def get_dfg_graph():
    """Returns Directed Follows Graph (nodes and edges) for process visualization."""
    if not os.path.exists(METRICS_PATH):
        return jsonify({"error": "Graph data not found."}), 404

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify({
        "nodes": data.get("nodes", []),
        "edges": data.get("edges", []),
        "variants": data.get("variants", []),
        "roi_metrics": data.get("roi_metrics", {})
    }), 200


@app.route("/api/patients", methods=["GET"])
def get_patients():
    """Returns paginated patient cohort metadata."""
    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)

    patients_csv = os.path.join(DATA_DIR, "patients_metadata.csv")
    if os.path.exists(patients_csv):
        df = pd.read_csv(patients_csv)
        subset = df.iloc[offset:offset+limit]
        return jsonify({
            "total_count": len(df),
            "limit": limit,
            "offset": offset,
            "data": subset.to_dict(orient="records")
        }), 200
    return jsonify({"error": "Patient metadata not found."}), 404


@app.route("/api/pipeline/run-discovery", methods=["POST"])
def trigger_process_discovery():
    """Triggers the backend PM4Py discovery and bottleneck analysis pipeline."""
    try:
        from scripts.process_mining_engine import run_process_mining
        run_process_mining()
        return jsonify({
            "status": "success",
            "message": "Process mining discovery pipeline executed successfully."
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[*] Starting CareFlow Backend REST API on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
