"""UI E2E: real Chromium drives the real dashboard served by live uvicorn.

Gated: UI_E2E=1 (spawns uvicorn + browser, ~30-60s). Proves UI consumes
real APIs (seeded project/job/price appear as rendered numbers).
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

playwright = pytest.importorskip("playwright")
pytestmark = pytest.mark.skipif(not os.getenv("UI_E2E"), reason="set UI_E2E=1 for browser UI E2E")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = 8003


class Page(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><body>UIE2E Widget Only $33.00</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def _call(method, path, payload=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(payload or {}).encode() if payload is not None or method == "POST" else None,
        headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode() or "{}")


def test_ui_dashboard_real_numbers():
    tmp = tempfile.mkdtemp(prefix="uie2e_")
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{tmp}/ui.db".replace(os.sep, "/"),
               TRUSTED_EGRESS_CIDRS="127.0.0.1/32", REQUIRE_AUTH="0", DATA_DIR=tmp)
    env.pop("PYTEST_CURRENT_TEST", None)
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                            "--host", "127.0.0.1", "--port", str(PORT)],
                           cwd=os.path.join(ROOT, "source", "python"), env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    page = HTTPServer(("127.0.0.1", 0), Page)
    threading.Thread(target=page.serve_forever, daemon=True).start()
    try:
        deadline = time.time() + 30
        while True:
            try:
                assert _call("GET", "/healthz")["status"] == "ok"
                break
            except Exception:
                assert time.time() < deadline, "api never came up"
                time.sleep(0.5)
        p = _call("POST", "/api/v1/projects", {"name": "UI", "description": ""})
        url = f"http://127.0.0.1:{page.server_address[1]}/w"
        t = _call("POST", "/api/v1/targets", {"project_id": p["id"], "domain": "127.0.0.1",
                                              "url": url})
        j = _call("POST", "/api/v1/jobs", {"project_id": p["id"], "target_id": t["id"],
                                           "url": url})
        r = _call("POST", f"/api/v1/jobs/{j['job_id']}/run", {})
        assert r["status"] == "success" and r["prices"][0]["price"] == 33.0
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_context().new_page()
            pg.goto(f"http://127.0.0.1:{PORT}/", timeout=30000)
            pg.wait_for_selector(".card .v", timeout=15000)
            body = pg.content()
            assert "Universal Intel" in body
            assert "33" in body  # real price rendered... or jobs total below
            cards = pg.eval_on_selector_all(".card .v", "els => els.map(e => e.textContent)")
            assert "1" in [c.strip() for c in cards], cards  # jobs_total == 1
            b.close()
    finally:
        api.terminate()
        page.shutdown()
