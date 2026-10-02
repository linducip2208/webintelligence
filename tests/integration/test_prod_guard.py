import os
import sys

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
import app.api.shared as SH  # noqa: E402
from app.main import app  # noqa: E402


def test_prod_db_down_fails_closed(monkeypatch):
    monkeypatch.setattr(SH.repo, "env", "production", raising=False)
    monkeypatch.setattr(SH.repo, "available", False, raising=False)
    monkeypatch.setattr(SH.repo, "boot_error", "db-unavailable: test outage", raising=False)
    c = TestClient(app)
    r = c.get("/api/v1/projects")
    assert r.status_code == 503
    body = r.json()
    assert body["error"]["code"] == "db_unavailable" and body["error"]["request_id"]
    r2 = c.post("/api/v1/projects", json={"name": "x"})
    assert r2.status_code == 503  # writes fail explicitly, never silently lost
    assert c.get("/healthz").status_code == 200  # liveness stays
    rz = c.get("/readyz").json()
    assert rz["status"] == "degraded"
    assert any(ch["name"] == "database" and ch["status"] == "down" for ch in rz["checks"])
    monkeypatch.setattr(SH.repo, "env", "development", raising=False)
    monkeypatch.setattr(SH.repo, "available", True, raising=False)
