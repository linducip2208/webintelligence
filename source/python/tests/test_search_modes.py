"""Unified search tests: modes, ranking, filters, pagination, org isolation.

No AI required for any mode (semantic = hashed lexical vectors).
"""
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


class _H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><body>SearchSuite demo page</body></html>"
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


@pytest.fixture(scope="module")
def local_url():
    srv = HTTPServer(("127.0.0.1", 0), _H)
    import threading
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}/s"
    srv.shutdown()


@pytest.fixture(autouse=True)
def _trust_local(monkeypatch, local_url):
    monkeypatch.setenv("TRUSTED_EGRESS_CIDRS", "127.0.0.1/32")


def _seed(local_url):
    p = c.post("/api/v1/projects", json={"name": "SearchSuite", "description": ""}).json()
    t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "searchsuite.example",
                                        "url": local_url}).json()
    e = c.post("/api/v1/entities/resolve",
               json={"candidate": {"name": "SearchSuite Corp",
                                   "domain": "searchsuite.example",
                                   "confidence": 85}}).json()
    f = c.post("/api/v1/findings", json={"kind": "OBS", "title": "SearchSuite exposed panel",
                                         "severity": "high"}).json()
    inv = c.post("/api/v1/investigations", json={"title": "SearchSuite review"}).json()
    c.post(f"/api/v1/investigations/{inv['id']}/links",
           json={"kind": "target_ids", "ids": [t["id"]]})
    d = c.post("/api/v1/documents", json={"kind": "txt", "title": "SearchSuite notes",
                                          "text": "SearchSuite Corp runs searchsuite.example on nginx"}).json()
    return {"project": p, "target": t, "entity": e, "finding": f, "inv": inv, "doc": d}


def test_keyword_finds_across_kinds(local_url):
    _seed(local_url)
    r = c.get("/api/v1/search", params={"q": "searchsuite", "mode": "keyword"}).json()
    kinds = {i["kind"] for i in r["items"]}
    assert {"target", "finding", "investigation", "document"} <= kinds
    assert r["total"] >= len(r["items"]) > 0
    for it in r["items"]:
        assert set(it) >= {"id", "kind", "title", "score", "status", "open", "route"}


def test_exact_mode(local_url):
    _seed(local_url)
    r = c.get("/api/v1/search", params={"q": "searchsuite.example", "mode": "exact"}).json()
    assert r["items"], "exact domain must match"
    assert all(i["score"] == 100.0 for i in r["items"])
    r = c.get("/api/v1/search", params={"q": "searchsuite.exampl", "mode": "exact"}).json()
    assert r["items"] == []


def test_semantic_without_ai(local_url):
    _seed(local_url)
    r = c.get("/api/v1/search", params={"q": "nginx corporation", "mode": "semantic"}).json()
    assert isinstance(r["items"], list)


def test_hybrid_is_default_and_merges(local_url):
    _seed(local_url)
    a = c.get("/api/v1/search", params={"q": "searchsuite"}).json()
    assert a["mode"] == "hybrid"
    assert a["items"], "hybrid must return keyword results at minimum"


def test_ranking_exact_first(local_url):
    _seed(local_url)
    r = c.get("/api/v1/search", params={"q": "searchsuite.example", "mode": "keyword"}).json()
    assert r["items"][0]["score"] >= r["items"][-1]["score"]
    assert r["items"][0]["title"] == "searchsuite.example"


def test_filters_and_pagination(local_url):
    _seed(local_url)
    r = c.get("/api/v1/search", params={"q": "searchsuite", "kind": "finding"}).json()
    assert r["items"] and all(i["kind"] == "finding" for i in r["items"])
    r = c.get("/api/v1/search", params={"q": "searchsuite", "risk_min": 70}).json()
    assert all((i["risk"] or 0) >= 70 for i in r["items"])
    a = c.get("/api/v1/search", params={"q": "searchsuite", "limit": 1, "offset": 0}).json()
    b = c.get("/api/v1/search", params={"q": "searchsuite", "limit": 1, "offset": 1}).json()
    assert a["items"] and b["items"]
    assert (a["items"][0]["kind"], a["items"][0]["id"]) != (b["items"][0]["kind"], b["items"][0]["id"])


def test_investigation_filter(local_url):
    s = _seed(local_url)
    r = c.get("/api/v1/search", params={"q": "searchsuite",
                                        "investigation_id": s["inv"]["id"]}).json()
    kinds = {i["kind"] for i in r["items"]}
    assert "target" in kinds  # linked target of the investigation
    assert "finding" not in kinds  # unlinked finding excluded


def test_empty_query_returns_empty():
    assert c.get("/api/v1/search", params={"q": ""}).json()["items"] == []


def test_org_isolation(local_url):
    _seed(local_url)
    org2 = c.post("/api/v1/orgs", json={"name": "SearchOther"}).json()
    key = c.post("/api/v1/apikeys", json={"name": "s2", "scopes": ["read"],
                                          "org_id": org2["id"]}).json()
    r = c.get("/api/v1/search", params={"q": "searchsuite"},
              headers={"X-API-Key": key["key"]}).json()
    assert r["items"] == [] and r["total"] == 0


def test_legacy_scope_param_still_works(local_url):
    _seed(local_url)
    r = c.get("/api/v1/search", params={"q": "searchsuite", "scope": "targets"}).json()
    assert "items" in r and "facets" in r


def test_confidence_and_status_filters(local_url):
    _seed(local_url)
    r = c.get("/api/v1/search", params={"q": "searchsuite", "confidence_min": 50}).json()
    assert r["items"] and all((i.get("confidence") or 0) >= 50 for i in r["items"])
    r = c.get("/api/v1/search", params={"q": "searchsuite", "status": "open"}).json()
    assert all("open" in str(i.get("status") or "").lower() for i in r["items"])


def test_entity_isolation(local_url):
    s = _seed(local_url)
    ent_id = s["entity"]["entity"]["id"]
    org2 = c.post("/api/v1/orgs", json={"name": "EntOther"}).json()
    key = c.post("/api/v1/apikeys", json={"name": "e2", "scopes": ["read", "collect"],
                                          "org_id": org2["id"]}).json()
    h = {"X-API-Key": key["key"]}
    assert c.get("/api/v1/entities", headers=h).json()["items"] == []
    assert c.get(f"/api/v1/entities/{ent_id}", headers=h).status_code == 404
    r = c.post("/api/v1/entities/resolve", headers=h,
               json={"candidate": {"name": "SearchSuite Corp",
                                   "domain": "searchsuite.example"}}).json()
    assert r["verdict"] == "NEW"  # other org's entity invisible here
