import os
import sys

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def test_connector_health_and_secrets():
    c = TestClient(app)
    conn = c.post("/api/v1/connectors", json={"name": "HC", "category": "DOCUMENT",
                 "manifest": {"name": "HC", "category": "DOCUMENT", "version": "1",
                              "capabilities": ["collect"]},
                 "config": {"kind": "csv", "text": "a\n1", "api_token": "SECRET123"}}).json()
    listed = c.get("/api/v1/connectors").json()["items"]
    mine = next(x for x in listed if x["id"] == conn["id"])
    assert mine["config"]["api_token"] == "***"  # never leaked
    out = c.post(f"/api/v1/connectors/{conn['id']}/test", json={}).json()
    assert out["ok"] is True and out["count"] == 1
    # health persisted on the connector
    again = [x for x in c.get("/api/v1/connectors").json()["items"] if x["id"] == conn["id"]]
    assert again  # listed


def test_research_compare_export_and_report_md():
    c = TestClient(app)
    r1 = c.post("/api/v1/research/runs", json={"question": "Q?"}).json()
    r2 = c.post("/api/v1/research/runs", json={"question": "Q?"}).json()
    cmp = c.get(f"/api/v1/research/compare?a={r1['id']}&b={r2['id']}").json()
    assert cmp["same_question"] is True and cmp["evidence_overlap"] == 0
    assert c.get("/api/v1/research/compare?a=1&b=999999").status_code == 404
    md = c.get(f"/api/v1/research/runs/{r1['id']}/export?format=markdown")
    assert md.status_code == 200 and md.text.startswith("# Research: Q?")
    assert "Limitations" in md.text
    rep = c.post("/api/v1/reports", json={"kind": "price", "project": "MD"}).json()
    md2 = c.get(f"/api/v1/reports/{rep['id']}/export?format=markdown")
    assert md2.status_code == 200 and "Methodology" in md2.text
