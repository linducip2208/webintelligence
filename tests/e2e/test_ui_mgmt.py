"""UI E2E: management flow — project/target/scan/alert/report/webhook/user.

Gated: UI_E2E=1 (spawns uvicorn + Chromium). All actions through the real
dashboard UI against a local stub HTTP server (no internet).
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
PORT = 8007


class Stub(BaseHTTPRequestHandler):
    def _send(self, obj, status=200, ctype="application/json"):
        import json as _j
        body = obj if isinstance(obj, bytes) else _j.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(b"<html><body>UIE2E Widget Only $42.00</body></html>", 200, "text/html")

    def log_message(self, *a):
        pass


def _call(method, path, payload=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(payload or {}).encode() if payload is not None or method == "POST" else None,
        headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode() or "{}")


def test_ui_management_flow():
    tmp = tempfile.mkdtemp(prefix="uimgmt_")
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{tmp}/ui.db".replace(os.sep, "/"),
               TRUSTED_EGRESS_CIDRS="127.0.0.1/32", REQUIRE_AUTH="0", DATA_DIR=tmp,
               OLLAMA_BASE_URL="disabled")
    env.pop("PYTEST_CURRENT_TEST", None)
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                            "--host", "127.0.0.1", "--port", str(PORT)],
                           cwd=os.path.join(ROOT, "source", "python"), env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    stub = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=stub.serve_forever, daemon=True).start()
    try:
        deadline = time.time() + 30
        while True:
            try:
                assert _call("GET", "/healthz")["status"] == "ok"
                break
            except Exception:
                assert time.time() < deadline, "api never came up"
                time.sleep(0.5)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_context().new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("dialog", lambda d: d.accept())
            pg.goto(f"http://127.0.0.1:{PORT}/", timeout=30000)
            pg.wait_for_selector(".navbar-vertical", timeout=15000)
            url = f"http://127.0.0.1:{stub.server_address[1]}/w"
            # project via modal
            pg.evaluate("view='projects'; load()")
            pg.wait_for_selector("text=+ Add project", timeout=10000)
            pg.click("text=+ Add project")
            pg.fill("input[name=name]", "E2E Project")
            pg.get_by_role("button", name="Create", exact=True).click()
            pg.wait_for_selector("text=E2E Project", timeout=10000)
            # target via modal
            pg.evaluate("view='targets'; load()")
            pg.wait_for_selector("text=+ Add target", timeout=10000)
            pg.click("text=+ Add target")
            pg.fill("input[name=domain]", "127.0.0.1")
            pg.fill("input[name=url]", url)
            pg.get_by_role("button", name="Create", exact=True).click()
            pg.wait_for_selector("text=127.0.0.1", timeout=10000)
            tids = [t["id"] for t in _call("GET", "/api/v1/targets?size=100")["items"]]
            assert tids
            # open target detail, scan now
            pg.evaluate(f"go('target',{tids[0]})")
            pg.wait_for_selector("text=Scan now", timeout=10000)
            pg.click("text=Scan now")
            pg.wait_for_selector("text=Scans", timeout=15000)
            jobs = []
            deadline = time.time() + 60
            while time.time() < deadline:
                jobs = _call("GET", "/api/v1/jobs?size=100")["items"]
                if any(j["status"] == "success" for j in jobs):
                    break
                time.sleep(1)
            assert any(j["status"] == "success" for j in jobs), jobs
            # alerts: create + ack via UI
            pg.evaluate("view='alerts'; load()")
            pg.wait_for_selector("text=+ New alert", timeout=10000)
            pg.click("text=+ New alert")
            pg.fill("input[name=message]", "e2e alert")
            pg.get_by_role("button", name="Create", exact=True).click()
            pg.wait_for_selector("text=e2e alert", timeout=10000)
            aids = [a["id"] for a in _call("GET", "/api/v1/alerts?size=100")["items"]]
            pg.evaluate(f"alertAck({aids[0]})")
            assert _call("GET", f"/api/v1/alerts/{aids[0]}")["acked"] is True
            # report generate + delete via UI
            pg.evaluate("view='reports'; load()")
            pg.wait_for_selector("text=Generate", timeout=10000)
            pg.fill("input[name=project]", "E2E Project")
            pg.get_by_role("button", name="Generate", exact=True).click()
            pg.wait_for_selector("text=E2E Project", timeout=15000)
            rids = [r["id"] for r in _call("GET", "/api/v1/reports?size=100")["items"]]
            assert rids
            # investigation + case via UI
            pg.evaluate("view='investigations'; load()")
            pg.wait_for_selector("text=+ New investigation", timeout=10000)
            pg.click("text=+ New investigation")
            pg.fill("#modal-root input[name=title]", "E2E Investigation")
            pg.get_by_role("button", name="Create", exact=True).click()
            pg.wait_for_selector("text=E2E Investigation", timeout=15000)
            iids = [i["id"] for i in _call("GET", "/api/v1/investigations?size=100")["items"]]
            assert iids
            pg.evaluate("view='cases'; load()")
            pg.wait_for_selector("text=+ New case", timeout=10000)
            pg.click("text=+ New case")
            pg.fill("#modal-root input[name=title]", "E2E Case")
            pg.get_by_role("button", name="Create", exact=True).click()
            pg.wait_for_selector("text=E2E Case", timeout=15000)
            cids = [c["id"] for c in _call("GET", "/api/v1/cases?size=100")["items"]]
            assert cids
            # webhook add via UI
            pg.evaluate("view='webhooks'; load()")
            pg.wait_for_selector("text=+ Add webhook", timeout=10000)
            pg.click("text=+ Add webhook")
            pg.fill("input[name=url]", "https://example.com/wh")
            pg.get_by_role("button", name="Add", exact=True).click()
            pg.wait_for_selector("text=example.com/wh", timeout=10000)
            # users: add member via UI
            pg.evaluate("view='users'; load()")
            pg.wait_for_selector("text=Add member", timeout=10000)
            pg.fill("input[name=email]", "e2e@example.com")
            pg.get_by_role("button", name="Add", exact=True).click()
            pg.wait_for_selector("text=e2e@example.com", timeout=10000)
            # settings page renders
            pg.evaluate("view='settings'; load()")
            pg.wait_for_selector("text=Feature flags", timeout=10000)
            assert errs == [], errs
            b.close()
    finally:
        api.terminate()
        stub.shutdown()
