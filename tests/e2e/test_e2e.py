"""Full E2E flow: project → target → job → run → prices → report → alert."""
import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
import sys as _sys  # noqa: E402
import os as _os  # noqa: E402

_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), "..", "..", "source", "python"))
from app.main import app  # noqa: E402


def test_e2e_flow():
    c = TestClient(app)
    assert c.get("/healthz").status_code == 200
    p = c.post("/api/v1/projects", json={"name": "E2E", "description": ""}).json()
    t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "example.com",
                                        "url": "https://example.com/p"}).json()
    j = c.post("/api/v1/jobs", json={"project_id": p["id"], "target_id": t["id"],
                                     "url": "https://example.com/p"}).json()
    assert j["status"] == "queued"
    # simulate collector result
    r = c.post("/api/v1/results", json={
        "schema_version": "1.0", "job_id": j["job_id"], "status": "success",
        "strategy": "DIRECT_HTTP", "http_status": 200, "content_hash": "e2e1",
        "content_size": 500, "retrieved_at": "2026-10-02T00:00:00Z",
        "parse_status": "ok"}).json()
    assert r["status"] == "success"
    # schedule + tick (not due yet -> empty, must not error)
    c.post("/api/v1/schedules", json={"kind": "interval", "every_min": 60,
                                      "url": "https://example.com/p"})
    assert "fired" in c.post("/api/v1/worker/tick", json={}).json()
    # analytics + costs + report + search + audit all live
    assert "count" in c.get("/api/v1/analytics/prices").json()
    assert "estimated" in c.get("/api/v1/costs/summary").json()
    rep = c.post("/api/v1/reports", json={"kind": "price", "project": "E2E"}).json()
    assert rep["methodology"].startswith("direct-first")
    assert c.get(f"/api/v1/reports/{rep['id']}/export?format=csv").status_code == 200
    assert c.get("/api/v1/search?q=e2e").status_code == 200
    assert c.get("/api/v1/audit").status_code == 200
    d = c.get("/api/v1/dashboard").json()
    assert d["jobs_total"] >= 1 and d["jobs_success"] >= 1
