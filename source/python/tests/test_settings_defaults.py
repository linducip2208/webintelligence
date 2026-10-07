"""Settings defaults: real persistence, validation, and consumption."""
from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_defaults_roundtrip_and_validation():
    d = c.get("/api/v1/settings/defaults").json()
    assert d["search_mode"] == "hybrid" and d["search_limit"] == 20
    assert isinstance(d["ni_scope"], list) and d["ni_scope"]

    r = c.patch("/api/v1/settings/defaults",
                json={"search_mode": "exact", "search_limit": 5,
                      "ni_scope": ["dns", "tls"]}).json()
    assert r["search_mode"] == "exact" and r["search_limit"] == 5
    assert r["ni_scope"] == ["dns", "tls"]
    assert c.get("/api/v1/settings/defaults").json()["ni_scope"] == ["dns", "tls"]

    assert c.patch("/api/v1/settings/defaults",
                   json={"search_mode": "nope"}).status_code == 400
    assert c.patch("/api/v1/settings/defaults",
                   json={"search_limit": 500}).status_code == 400
    assert c.patch("/api/v1/settings/defaults",
                   json={"ni_scope": []}).status_code == 400
    assert c.patch("/api/v1/settings/defaults",
                   json={"ni_scope": ["dns", "bogus"]}).status_code == 400

    c.patch("/api/v1/settings/defaults",
            json={"search_mode": "hybrid", "search_limit": 20,
                  "ni_scope": ["dns", "subdomains", "tls", "tech"]})


def test_system_facts_shape():
    s = c.get("/api/v1/settings/system").json()
    assert s["app_version"] and s["python"] and s["env"]
    assert "backend" in s["database"] and "connected" in s["redis"]
    assert isinstance(s["counts"], dict) and "projects" in s["counts"]
    assert "search_index_documents" in s and "ai_providers_configured" in s
