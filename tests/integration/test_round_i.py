import os
import sys

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.services import commercial as CM  # noqa: E402


def test_branding_verticals():
    c = TestClient(app)
    assert c.put("/api/v1/orgs/1/branding", json={"branding": {"primary_color": "red"}}).status_code == 400
    ok = c.put("/api/v1/orgs/1/branding", json={"branding": {"app_name": "Acme Intel",
                                                            "primary_color": "#112233"}}).json()
    assert ok["ok"] is True
    assert c.get("/api/v1/orgs/1/branding").json()["branding"]["app_name"] == "Acme Intel"
    assert c.get("/api/v1/orgs/2/branding").status_code == 404
    vs = c.get("/api/v1/verticals").json()["verticals"]
    assert len(vs) == 10 and "pricing" in vs
    assert c.get("/api/v1/verticals/nope").status_code == 404
    pv = c.get("/api/v1/verticals/pricing").json()
    assert "kpis" in pv and "questions" in pv
    ap = c.post("/api/v1/verticals/pricing/apply", json={}).json()
    assert ap["ok"] and ap["watchlists"]
    assert c.post("/api/v1/verticals/nope/apply", json={}).status_code == 404
    assert CM.validate_branding({"logo_url": "http://x/y.png"})
    assert CM.get_vertical("PRICING")["kpis"]


def test_oidc_honest():
    c = TestClient(app)
    provs = c.get("/api/v1/auth/providers").json()["providers"]
    local = next(p for p in provs if p["name"] == "local")
    oidc = next(p for p in provs if p["name"] == "oidc")
    assert local["configured"] is True and oidc["configured"] is False
    assert c.post("/api/v1/auth/oidc/login", json={}).status_code == 501
    assert c.post("/api/v1/auth/oidc/callback", json={}).status_code == 501


def test_flags_gate_and_retention():
    c = TestClient(app)
    c.post("/api/v1/flags", json={"name": "ai", "on": False})
    assert c.post("/api/v1/ai/chat", json={"messages": []}).status_code == 403
    c.post("/api/v1/flags", json={"name": "ai", "on": True})
    r = c.post("/api/v1/admin/retention/run", json={"collections": ["nope"],
                                                   "older_than_days": 1}).json()
    assert r["removed"] == {}
    r2 = c.post("/api/v1/admin/retention/run", json={"collections": ["raw"],
                                                    "older_than_days": 100000}).json()
    assert r2["removed"] == {"raw": 0}


def test_graph_path_endpoint():
    c = TestClient(app)
    a = c.post("/api/v1/graph/nodes", json={"kind": "company", "key": "gp-a", "name": "A"}).json()
    b = c.post("/api/v1/graph/nodes", json={"kind": "company", "key": "gp-b", "name": "B"}).json()
    g = c.post("/api/v1/graph/nodes", json={"kind": "company", "key": "gp-c", "name": "C"}).json()
    c.post("/api/v1/graph/edges", json={"src": a["id"], "dst": b["id"], "rel": "OWNS"})
    c.post("/api/v1/graph/edges", json={"src": b["id"], "dst": g["id"], "rel": "SELLS"})
    p = c.get(f"/api/v1/graph/path?src={a['id']}&dst={g['id']}").json()
    assert p["connected"] is True and [h["via"] for h in p["path"]] == [None, "OWNS", "SELLS"]
    assert c.get(f"/api/v1/graph/path?src={a['id']}&dst=999999").status_code == 404
    assert c.get(f"/api/v1/graph/path?src={a['id']}&dst={g['id']}&rel=OWNS").json()["connected"] is False
