import os
import sys
import time

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.services import alertlife as AL  # noqa: E402


def test_maintenance_suppression_and_sla():
    c = TestClient(app)
    now = time.time()
    w = c.post("/api/v1/maintenance", json={"name": "deploy", "starts_at": now - 10,
                                            "ends_at": now + 3600, "suppress_rules": []}).json()
    assert w["enabled"] is True
    assert c.post("/api/v1/maintenance", json={"name": "bad", "starts_at": now + 5,
                                              "ends_at": now}).status_code == 400
    r = c.post("/api/v1/alerts/check", json={"value": 5, "op": "gt", "threshold": 1,
                                             "rule": "suppressed-rule"}).json()
    assert r.get("suppressed_by") == "deploy" and "alert_id" not in r
    c.post(f"/api/v1/maintenance/{w['id']}/disable", json={})
    r2 = c.post("/api/v1/alerts/check", json={"value": 5, "op": "gt", "threshold": 1,
                                              "rule": "suppressed-rule"}).json()
    assert r2.get("alert_id")
    assert AL.sla_due("critical") < AL.sla_due("info")
    inc = c.get("/api/v1/alerts/incidents").json()["incidents"]
    assert any(i["rule"] == "suppressed-rule" for i in inc)
    assert c.get("/api/v1/maintenance").status_code == 200


def test_workflow_pause_version_retry():
    c = TestClient(app)
    wf = c.post("/api/v1/workflows", json={"name": "PV", "definition": {"steps": [
        {"action": "create_alert", "params": {"rule": "pv", "message": "m"}}]}}).json()
    assert wf.get("version", 1) == 1
    c.put(f"/api/v1/workflows/{wf['id']}", json={"paused": True})
    assert c.post(f"/api/v1/workflows/{wf['id']}/run", json={"event": {}}).status_code == 409
    c.put(f"/api/v1/workflows/{wf['id']}", json={"paused": False, "definition": {"steps": []}})
    ev = {"k": 1}
    assert c.post(f"/api/v1/workflows/{wf['id']}/run", json={"event": ev}).status_code == 200
    ev2 = {"k": 2}
    r1 = c.post(f"/api/v1/workflows/{wf['id']}/retry", json={"event": ev2}).json()
    r2 = c.post(f"/api/v1/workflows/{wf['id']}/retry", json={"event": ev2}).json()
    assert r1["replayed"] is False and r2["replayed"] is True
    assert r1["run"]["id"] == r2["run"]["id"]
    assert c.post(f"/api/v1/workflows/{wf['id']}/cancel", json={"run_id": 99999}).status_code == 404


def test_dataset_diff_rollback():
    c = TestClient(app)
    d = c.post("/api/v1/datasets", json={"name": "DR"}).json()
    c.post(f"/api/v1/datasets/{d['id']}/publish", json={"rows": [{"a": 1}], "lineage": {}})
    c.post(f"/api/v1/datasets/{d['id']}/publish", json={"rows": [{"a": 1}, {"a": 2}], "lineage": {}})
    diff = c.get(f"/api/v1/datasets/{d['id']}/diff?v1=1&v2=2").json()
    assert diff == {"from": 1, "to": 2, "added": 1, "removed": 0, "unchanged": 1}
    rb = c.post(f"/api/v1/datasets/{d['id']}/rollback", json={"version": 1}).json()
    assert rb["version"] == 3 and rb["row_count"] == 1
    assert c.post(f"/api/v1/datasets/{d['id']}/rollback", json={"version": 99}).status_code == 404
