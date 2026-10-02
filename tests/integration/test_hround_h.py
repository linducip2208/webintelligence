import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><body>H Product Only $55.00</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def _srv():
    s = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def test_target_test_live(monkeypatch):
    monkeypatch.setenv("TRUSTED_EGRESS_CIDRS", "127.0.0.1/32")
    c = TestClient(app)
    p = c.post("/api/v1/projects", json={"name": "HT", "description": ""}).json()
    s = _srv()
    t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "127.0.0.1",
                                        "url": f"http://127.0.0.1:{s.server_port}/p"}).json()
    out = c.post(f"/api/v1/targets/{t['id']}/test", json={}).json()
    assert out["ok"] is True and out["http_status"] == 200
    assert out["profile"]["attempts"] >= 1
    s.shutdown()


def test_watchlist_evaluate_cooldown():
    c = TestClient(app)
    w = c.post("/api/v1/watchlists", json={"kind": "keyword", "value": "gadget"}).json()
    c.post("/api/v1/articles", json={"title": "new gadget launch", "publisher": "t"})
    r1 = c.post(f"/api/v1/watchlists/{w['id']}/evaluate", json={}).json()
    assert r1["matches"] >= 1 and r1["alerts"] >= 1
    r2 = c.post(f"/api/v1/watchlists/{w['id']}/evaluate", json={}).json()
    assert r2["alerts"] == 0  # cooldown suppresses duplicates


def test_aliases_versions_facets():
    c = TestClient(app)
    e = c.post("/api/v1/entities/resolve", json={"candidate": {"name": "HCo"}}).json()
    eid = e["entity"]["id"]
    assert c.post(f"/api/v1/entities/{eid}/aliases", json={"alias": "H Co"}).json()["aliases"] == ["H Co"]
    d = c.post("/api/v1/datasets", json={"name": "HV"}).json()
    c.post(f"/api/v1/datasets/{d['id']}/publish", json={"rows": [{"a": 1}], "lineage": {}}).json()
    vs = c.get(f"/api/v1/datasets/{d['id']}/versions").json()["items"]
    assert len(vs) == 1 and vs[0]["version"] == 1 and "rows" not in vs[0]
    f = c.get("/api/v1/search?q=hco").json()
    assert "facets" in f and isinstance(f["items"], list)


def test_research_analyze_no_creds():
    c = TestClient(app)
    r = c.post("/api/v1/research/runs", json={"question": "Why?"}).json()
    ev = c.post("/api/v1/evidence", json={"source": "s", "url": "https://e.io",
                                          "content_hash": "h"}).json()
    c.post(f"/api/v1/research/runs/{r['id']}/finish",
           json={"analysis": "", "evidence_ids": [ev["id"]]}).json()
    out = c.post(f"/api/v1/research/runs/{r['id']}/analyze", json={})
    assert out.status_code == 502  # honest: no AI backend configured
    assert "ai unavailable" in out.text


def test_pit_and_bulk_and_pdf():
    c = TestClient(app)
    n1 = c.post("/api/v1/graph/nodes", json={"kind": "company", "key": "pit-a", "name": "A"}).json()
    n2 = c.post("/api/v1/graph/nodes", json={"kind": "company", "key": "pit-b", "name": "B"}).json()
    c.post("/api/v1/graph/edges", json={"src": n1["id"], "dst": n2["id"],
                                        "rel": "OWNS", "at": "2026-01-01"}).json()
    assert c.get(f"/api/v1/graph/traverse?node={n1['id']}&at=2025-01-01").json()["items"] == []
    assert len(c.get(f"/api/v1/graph/traverse?node={n1['id']}&at=2027-01-01").json()["items"]) == 1
    assert c.get(f"/api/v1/graph/path?src={n1['id']}&dst={n2['id']}").json()["connected"] is True
    a1 = c.post("/api/v1/alerts", json={"rule": "anomaly", "message": "m1"}).json()
    a2 = c.post("/api/v1/alerts", json={"rule": "anomaly", "message": "m2"}).json()
    assert c.post("/api/v1/alerts/bulk", json={"ids": [a1["id"], a2["id"]],
                                               "action": "ack"}).json()["updated"] == 2
    assert c.post("/api/v1/alerts/bulk", json={"ids": [1], "action": "bogus"}).status_code == 400
    rep = c.post("/api/v1/reports", json={"kind": "price", "project": "H"}).json()
    pdf = c.get(f"/api/v1/reports/{rep['id']}/export?format=pdf")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    assert pdf.headers["content-type"] == "application/pdf"
    r = c.get("/api/v1/dashboard")
    assert "x-request-id" in r.headers and len(r.headers["x-request-id"]) == 12
