"""MEGA E2E (Phase 44/58): full pipeline with persisted-state verification.

ORG/AUTH -> SOURCE -> TARGET -> JOB -> RUN(inline, real local HTTP) ->
PRICES(persisted) -> CHANGE scenario -> ENTITY -> EVIDENCE -> CLAIM verify ->
CONTRADICTION -> FINDING -> FEED -> WATCHLIST -> ALERT -> RESEARCH -> REPORT ->
WEBHOOK(HMAC verified) -> AUDIT. Plus IDOR isolation checks.
"""
import hashlib
import hmac
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app, repo  # noqa: E402


class Pages:
    html = "<html><body>Acme Widget Only $100.00 in stock</body></html>"


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = Pages.html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class Hook:
    got = None


class WH(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        Hook.got = {"sig": self.headers.get("X-WebIntel-Signature"),
                    "event": self.headers.get("X-WebIntel-Event"), "body": body}
        self.send_response(200)
        self.end_headers()

    def log_message(self, *a):
        pass


def _srv(handler):
    s = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def test_mega_pipeline(monkeypatch):
    monkeypatch.setenv("TRUSTED_EGRESS_CIDRS", "127.0.0.1/32")
    c = TestClient(app)
    # AUTH + ORG
    t = c.post("/api/v1/auth/login", json={"email": "admin@local",
                                           "password": "admin123"}).json()
    assert t["email"] == "admin@local"
    org2 = c.post("/api/v1/orgs", json={"name": "Other"}).json()
    assert org2["id"] != 1
    # SOURCE -> TARGET -> JOB
    p = c.post("/api/v1/projects", json={"name": "Mega", "description": ""}).json()
    srv = _srv(H)
    url = f"http://127.0.0.1:{srv.server_port}/p"
    tgt = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "127.0.0.1",
                                          "url": url}).json()
    job = c.post("/api/v1/jobs", json={"project_id": p["id"], "target_id": tgt["id"],
                                       "url": url}).json()
    assert job["plan"]["plan"][0] == "DIRECT_HTTP"
    # RUN 1: price 100 -> persisted prices + NEW
    r1 = c.post(f"/api/v1/jobs/{job['job_id']}/run", json={}).json()
    assert r1["status"] == "success" and r1["prices"][0]["price"] == 100.0
    assert r1["change"] == "NEW"
    assert len(c.get("/api/v1/prices").json()["items"]) >= 1
    assert repo.load_all()["prices"], "prices must persist in repository"
    # CHANGE SCENARIO: 100 -> 120
    Pages.html = "<html><body>Acme Widget Only $120.00 in stock</body></html>"
    job2 = c.post("/api/v1/jobs", json={"project_id": p["id"], "target_id": tgt["id"],
                                        "url": url}).json()
    r2 = c.post(f"/api/v1/jobs/{job2['job_id']}/run", json={}).json()
    assert r2["change"] == "CHANGED"
    assert any(a["rule"] == "price_changed" for a in c.get("/api/v1/alerts").json()["items"])
    n_alerts = len(c.get("/api/v1/alerts").json()["items"])
    # NO-CHANGE run: no new price_changed alert
    job3 = c.post("/api/v1/jobs", json={"project_id": p["id"], "target_id": tgt["id"],
                                        "url": url}).json()
    r3 = c.post(f"/api/v1/jobs/{job3['job_id']}/run", json={}).json()
    assert r3["change"] == "UNCHANGED"
    assert len(c.get("/api/v1/alerts").json()["items"]) == n_alerts
    # ENTITY -> EVIDENCE -> CLAIM -> CONTRADICTION (both preserved)
    ent = c.post("/api/v1/entities/resolve",
                 json={"candidate": {"name": "Acme", "domain": "acme.com"}}).json()
    assert ent["verdict"] == "NEW"
    ev1 = c.post("/api/v1/evidence", json={"source": "A", "url": url,
                                           "content_hash": "h1"}).json()
    ev2 = c.post("/api/v1/evidence", json={"source": "B", "url": url,
                                           "content_hash": "h2"}).json()
    v = c.post("/api/v1/claims/verify", json={"value": "2012", "evidence": [
        {"value": "2012", "reliability": 0.9}, {"value": "2014", "reliability": 0.8}]}).json()
    assert v["status"] == "CONFLICTED"
    cc = c.post("/api/v1/contradictions/check", json={"evidence": [
        {"value": "2012", "reliability": 0.9}, {"value": "2014", "reliability": 0.8}]}).json()
    assert cc["conflict"] and cc["preferred"] == "2012"
    # FINDING -> FEED -> WATCHLIST -> ALERT
    f = c.post("/api/v1/findings", json={"kind": "PRICE", "title": "Mega finding",
                                         "evidence_ids": [ev1["id"], ev2["id"]]}).json()
    assert any(i["kind"] == "RESEARCH_FINDING" for i in c.get("/api/v1/feed").json()["items"])
    c.post("/api/v1/watchlists", json={"kind": "keyword", "value": "mega-watch"}).json()
    c.post("/api/v1/events", json={"type": "NOTE", "entity_key": "mega-watch spike"}).json()
    assert any(a["rule"] == "watchlist_hit" for a in c.get("/api/v1/alerts").json()["items"])
    # RESEARCH -> REPORT (methodology + evidence, real data)
    plan = c.post("/api/v1/research/plan", json={"question": "Why did price move?"}).json()
    run = c.post("/api/v1/research/runs", json={"question": "Why did price move?",
                                                "plan": plan}).json()
    fin = c.post(f"/api/v1/research/runs/{run['id']}/finish",
                 json={"analysis": "price 100->120 per evidence",
                       "evidence_ids": [ev1["id"]]}).json()
    assert fin["reproducibility"]["evidence_ids"] == [ev1["id"]]
    rep = c.post("/api/v1/reports", json={"kind": "price", "project": "Mega"}).json()
    assert rep["source_coverage"] >= 2 and "methodology" in rep
    # WEBHOOK with real HMAC verification at receiver
    whs = _srv(WH)
    wh = c.post("/api/v1/webhooks", json={"event_types": ["ping"],
                                          "url": f"http://127.0.0.1:{whs.server_port}/h",
                                          "secret": "topsecret"}).json()
    assert c.post(f"/api/v1/webhooks/{wh['id']}/test", json={}).json()["ok"] is True
    assert Hook.got and Hook.got["event"] == "ping"
    expect = hmac.new(b"topsecret", Hook.got["body"], hashlib.sha256).hexdigest()
    assert hmac.compare_digest(expect, Hook.got["sig"])
    # AUDIT persisted
    assert any(a["action"] == "job.create" for a in c.get("/api/v1/audit").json()["items"])
    assert repo.load_all()["audit"], "audit must persist"
    # IDOR: org-2 key sees nothing of org-1
    key2 = c.post("/api/v1/apikeys", json={"name": "o2", "scopes": ["read", "collect"],
                                           "org_id": org2["id"]}).json()
    h2 = {"X-API-Key": key2["key"]}
    assert c.get("/api/v1/projects", headers=h2).json()["items"] == []
    assert c.get(f"/api/v1/findings/{f['id']}", headers=h2).status_code == 404
    assert c.post("/api/v1/jobs", json={"project_id": p["id"], "target_id": tgt["id"],
                                        "url": url}, headers=h2).status_code == 404
    srv.shutdown()
    whs.shutdown()
