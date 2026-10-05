"""UI E2E: AI Providers page — list, empty state, add-wizard flow (gated).

Gated: UI_E2E=1 (spawns uvicorn + Chromium, ~30-60s). Uses a local stub AI
endpoint so TEST CONNECTION performs a real backend test without internet.
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
PORT = 8004


class Stub(BaseHTTPRequestHandler):
    def _send(self, obj, status=200):
        import json as _j
        body = _j.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.endswith("/models"):
            self._send({"data": [{"id": "stub-e2e"}]})
        else:
            self._send({}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        if self.path.endswith("/chat/completions"):
            self._send({"choices": [{"message": {"content": "ok"}}],
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
            return
        self._send({"output": [{"type": "message", "content": [
            {"type": "output_text", "text": "ok"}]}],
            "usage": {"input_tokens": 1, "output_tokens": 1}})

    def log_message(self, *a):
        pass


def _call(method, path, payload=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(payload or {}).encode() if payload is not None or method == "POST" else None,
        headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode() or "{}")


def test_ui_ai_providers_flow():
    tmp = tempfile.mkdtemp(prefix="uiaie2e_")
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
        assert _call("GET", "/api/v1/ai/provider-presets")["presets"]
        assert _call("GET", "/api/v1/ai/providers/db") == {"items": []}
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_context().new_page()
            pg.goto(f"http://127.0.0.1:{PORT}/", timeout=30000)
            pg.wait_for_selector(".navbar-vertical", timeout=15000)
            pg.evaluate("view='ai'; load()")
            pg.wait_for_selector("text=AI Providers", timeout=15000)
            assert pg.locator("text=No AI providers configured").count() > 0
            assert pg.locator("text=+ Add AI provider").count() >= 1
            pg.locator("text=+ Add AI provider").first.click()
            pg.wait_for_selector("text=Select AI provider", timeout=10000)
            cards = pg.eval_on_selector_all(".card .card-body b",
                                            "els => els.map(e => e.textContent)")
            assert any("Ollama" in c for c in cards), cards
            pg.locator("#preset-ollama").click()
            pg.wait_for_selector("text=Test connection", timeout=10000)
            ep = f"http://127.0.0.1:{stub.server_address[1]}/v1"
            pg.fill("#wep", ep)
            pg.fill("#wmodel", "stub-e2e")
            pg.click("#wtest")
            pg.wait_for_selector("text=Connection successful", timeout=30000)
            opts = pg.eval_on_selector_all("#wmodel option",
                                           "els => els.map(e => e.textContent)")
            assert "stub-e2e" in opts, opts
            pg.fill("#wname", "e2e-ollama")
            pg.click("text=Save provider")
            pg.wait_for_selector("text=e2e-ollama", timeout=15000)
            rows = _call("GET", "/api/v1/ai/providers/db")["items"]
            assert any(r["name"] == "e2e-ollama" and r["last_test_status"] == "untested"
                       for r in rows)
            b.close()
    finally:
        api.terminate()
        stub.shutdown()
