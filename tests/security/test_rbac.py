import os
import sys

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.auth import tokens as tok  # noqa: E402
from app.core.config import settings  # noqa: E402


def _login(c, email="admin@local", pw="admin123"):
    return c.post("/api/v1/auth/login", json={"email": email, "password": pw}).json()["token"]


def test_rbac_negative(monkeypatch):
    monkeypatch.setenv("REQUIRE_AUTH", "1")
    c = TestClient(app)
    admin = _login(c)
    ah = {"Authorization": "Bearer " + admin}
    c.post("/api/v1/memberships", json={"email": "viewer@x.io", "role": "viewer"}, headers=ah)
    c.post("/api/v1/memberships", json={"email": "analyst@x.io", "role": "analyst"}, headers=ah)
    viewer = tok.issue("viewer@x.io", settings.secret_key or "dev-secret")
    analyst = tok.issue("analyst@x.io", settings.secret_key or "dev-secret")
    vh, nh = {"Authorization": "Bearer " + viewer}, {"Authorization": "Bearer " + analyst}
    # viewer: reads ok, writes forbidden
    assert c.get("/api/v1/projects", headers=vh).status_code == 200
    assert c.post("/api/v1/projects", json={"name": "VX"}, headers=vh).status_code == 403
    assert c.post("/api/v1/jobs", json={"project_id": 1, "target_id": 1,
                                        "url": "https://example.com"}, headers=vh).status_code == 403
    # analyst: collect ok, configure forbidden
    assert c.post("/api/v1/projects", json={"name": "AX"}, headers=nh).status_code in (200, 402)
    assert c.post("/api/v1/apikeys", json={"name": "x"}, headers=nh).status_code == 403
    assert c.post("/api/v1/entities/merge", json={"keep_id": 1, "drop_id": 2},
                  headers=nh).status_code == 403
    # read-only key cannot mutate; unknown key rejected
    rk = c.post("/api/v1/apikeys", json={"name": "ro", "scopes": ["read"]}, headers=ah).json()
    rh = {"X-API-Key": rk["key"]}
    assert c.get("/api/v1/projects", headers=rh).status_code == 200
    assert c.post("/api/v1/projects", json={"name": "RX"}, headers=rh).status_code == 403
    assert c.get("/api/v1/projects", headers={"X-API-Key": "wi_nope"}).status_code == 401
    # admin owner retains full power
    assert c.get("/api/v1/audit", headers=ah).status_code == 200
