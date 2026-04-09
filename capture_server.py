#!/usr/bin/env python3
"""
Screenshot capture relay server — runs on your Mac.
Receives JPEG screenshots POSTed from Chrome and saves them
to the shots/ subfolder alongside this script.

Usage:
    python3 capture_server.py

Then keep it running while Claude captures the walkthrough.
"""
import http.server
import json
import os
import base64
from datetime import datetime

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
PORT = 8765
ORIGIN = "https://wanna.freeup.life"

os.makedirs(SAVE_DIR, exist_ok=True)


class Handler(http.server.BaseHTTPRequestHandler):

    def _cors(self, extra=None):
        self.send_header("Access-Control-Allow-Origin", ORIGIN)
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/save":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body)

        name = data.get("name", datetime.now().strftime("shot_%H%M%S_%f") + ".jpg")
        img_b64 = data.get("image", "")
        img_bytes = base64.b64decode(img_b64)

        path = os.path.join(SAVE_DIR, name)
        with open(path, "wb") as f:
            f.write(img_bytes)

        print(f"  ✓ Saved {name}  ({len(img_bytes):,} bytes)")

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "path": path}).encode())

    def log_message(self, fmt, *args):
        pass  # suppress default request logs


print(f"📸  Screenshot relay server ready at http://localhost:{PORT}")
print(f"    Saving to: {SAVE_DIR}")
print(f"    Press Ctrl-C to stop.\n")
with http.server.HTTPServer(("localhost", PORT), Handler) as srv:
    srv.serve_forever()
