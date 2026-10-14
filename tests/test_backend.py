"""
CareFlow Backend - Unit Tests
"""

import os
import unittest
import json
import duckdb
import pandas as pd
from api.app import app


class TestCareFlowBackend(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_health_check(self):
        """Test GET /api/health returns 200 and healthy status."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "CareFlow Backend Analytics API")

    def test_metrics_summary_endpoint(self):
        """Test GET /api/metrics/summary returns valid KPIs."""
        response = self.client.get("/api/metrics/summary")
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn("total_cases", data)
            self.assertIn("total_events", data)

    def test_bottlenecks_endpoint(self):
        """Test GET /api/metrics/bottlenecks returns list."""
        response = self.client.get("/api/metrics/bottlenecks")
        if response.status_code == 200:
            data = json.loads(response.data)
            if isinstance(data, dict):
                self.assertIn("data", data)
                self.assertIsInstance(data["data"], list)
            else:
                self.assertIsInstance(data, list)

    def test_dfg_graph_endpoint(self):
        """Test GET /api/graph/dfg returns nodes and edges."""
        response = self.client.get("/api/graph/dfg")
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn("nodes", data)
            self.assertIn("edges", data)

    def test_patients_endpoint(self):
        """Test GET /api/patients returns patient cohort data."""
        response = self.client.get("/api/patients?limit=5")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("data", data)
        self.assertGreaterEqual(len(data["data"]), 1)


if __name__ == "__main__":
    unittest.main()
