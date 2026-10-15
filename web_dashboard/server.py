"""
CareFlow - Clinical Pathway Process Mining
Script: server.py
Domain: Healthcare Operations & Process Analytics

Purpose:
Lightweight HTTP web server to serve the interactive CareFlow Process Mining Dashboard
locally at http://localhost:8050.
"""

import http.server
import socketserver
import os
import webbrowser
import sys

PORT = 8050
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

class CustomHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def end_headers(self):
        # Enable CORS and disable aggressive caching for local dashboard testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def run_server():
    os.chdir(DASHBOARD_DIR)
    with socketserver.TCPServer(("", PORT), CustomHTTPHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 70)
        print("CareFlow Clinical Process Mining Interactive Dashboard")
        print("=" * 70)
        print(f"[+] Serving dashboard live at: {url}")
        print("[+] Press Ctrl+C to terminate the local server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[!] Dashboard server stopped.")
            sys.exit(0)

if __name__ == "__main__":
    run_server()
