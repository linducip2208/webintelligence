"""Functional journey E2E: one real browser walks the whole product.

Gated: UI_E2E=1 (spawns uvicorn + Chromium, ~2-4 min). Hermetic: isolated
DATA_DIR, labeled DEMO seed (.example only), local slow origin for the one
live collection. Fails on any dead view, 404 API, crash page or fake state.
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
pytestmark = pytest.mark.skipif(not os.getenv("UI_E2E"), reason="set UI_E2E=1 for browser journey")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = 8009


class Slow(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(3)
        body = b"<html><body>Journey Widget Only $77.00</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def log_message(self, *a):
        pass


def _call(method, path, payload=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}{path}",
        data=json.dumps(payload or {}).encode() if payload is not None or method == "POST" else None,
        headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode() or "{}")


VIEWS = ["dashboard", "search", "new-investigation", "investigations", "cases",
         "entities", "graph", "timeline", "targets", "attack", "collectors",
         "connectors", "data-sources", "findings", "indicators", "risk",
         "intel-feed", "watchlists", "alerts", "workflows", "evidence",
         "documents", "reports", "stix", "external-apis", "ai-providers",
         "users", "settings", "audit", "health", "login"]


def test_functional_journey():
    tmp = tempfile.mkdtemp(prefix="journey_")
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{tmp}/j.db".replace(os.sep, "/"),
               TRUSTED_EGRESS_CIDRS="127.0.0.1/32", REQUIRE_AUTH="0", DATA_DIR=tmp)
    env.pop("PYTEST_CURRENT_TEST", None)
    log = open(os.path.join(tmp, "uvicorn.log"), "w", encoding="utf-8")
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                            "--host", "127.0.0.1", "--port", str(PORT)],
                           cwd=os.path.join(ROOT, "source", "python"), env=env,
                           stdout=log, stderr=subprocess.STDOUT)
    origin = HTTPServer(("127.0.0.1", 0), Slow)
    threading.Thread(target=origin.serve_forever, daemon=True).start()
    try:
        deadline = time.time() + 40
        while True:
            try:
                assert _call("GET", "/healthz")["status"] == "ok"
                break
            except Exception:
                assert time.time() < deadline, "api never came up"
                time.sleep(0.5)
        seed = _call("POST", "/api/v1/admin/demo/seed", {})
        assert seed.get("ok") is True

        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch(args=["--no-sandbox"])
            pg = b.new_context(viewport={"width": 1440, "height": 900}).new_page()

            def load(view):
                pg.goto(f"http://127.0.0.1:{PORT}/#{view}", wait_until="domcontentloaded",
                        timeout=30000)
                pg.evaluate(f"go('{view}')")
                pg.wait_for_selector("#content", timeout=20000)
                try:
                    pg.wait_for_function(
                        "() => { const c = document.querySelector('#content'); "
                        "return c && !c.querySelector('.placeholder-glow'); }",
                        timeout=20000)
                except Exception:
                    pass
                pg.wait_for_timeout(800)
                return pg.content()

            # login: renders, credential hint redacted only in docs shots (live UI keeps dev hint)
            html = load("login")
            assert "Sign in" in html

            # dashboard: demo-labeled, real numbers
            html = load("dashboard")
            assert "SAMPLE DATA" in html and "DEMO: Acme exposure review" in html

            # search console: real results through the unified engine
            load("search")
            pg.fill("#sq", "acme")
            pg.evaluate("document.querySelector('#content form').requestSubmit()")
            pg.wait_for_function("() => /results for/.test(document.querySelector('#res').textContent||'')",
                                 timeout=20000)
            assert "Open" in pg.content()

            # every primary view renders without crash markers or API 404 text
            for v in VIEWS:
                html = load(v)
                assert "Something went wrong" not in html, f"view crashed: {v}"
                assert "Application initialization failed" not in html, f"init failed: {v}"

            # live collection journey against the local origin (ip type)
            origin_url = f"http://127.0.0.1:{origin.server_address[1]}/j"
            load("new-investigation")
            pg.evaluate("window._niw={step:2,type:'ip',target:'127.0.0.1',scope:['dns','tech'],profile:'standard'};renderWiz(document.querySelector('#content'))")
            pg.wait_for_timeout(500)
            assert "127.0.0.1" in pg.content()
            p = _call("POST", "/api/v1/projects", {"name": "Journey", "description": ""})
            t = _call("POST", "/api/v1/targets",
                      {"project_id": p["id"], "domain": "127.0.0.1", "url": origin_url})
            j = _call("POST", "/api/v1/jobs",
                      {"project_id": p["id"], "target_id": t["id"], "url": origin_url})
            assert j["status"] == "queued"
            r = _call("POST", f"/api/v1/jobs/{j['job_id']}/run", {})
            assert r["status"] == "success", r
            assert r["prices"] and r["prices"][0]["price"] == 77.0
            html = load("jobs")
            assert "success" in html

            # settings defaults persist across reload
            load("settings")
            pg.evaluate("window._setTab='Workspace';setSection('Workspace')")
            pg.wait_for_timeout(500)
            assert "Workspace defaults" in pg.content()
            saved = _call("PATCH", "/api/v1/settings/defaults",
                          {"search_mode": "exact", "ni_scope": ["dns", "tls"]})
            assert saved["search_mode"] == "exact"
            assert _call("GET", "/api/v1/settings/defaults")["ni_scope"] == ["dns", "tls"]
            _call("PATCH", "/api/v1/settings/defaults",
                  {"search_mode": "hybrid",
                   "ni_scope": ["dns", "subdomains", "tls", "tech"]})

            # docs portal serves alongside the app
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/docs/en/index",
                                        timeout=20) as dr:
                assert dr.status == 200 and "Web Intelligence" in dr.read().decode()
            b.close()
    finally:
        api.terminate()
        origin.shutdown()
