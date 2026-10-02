import os
import sys

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def test_billing_quotas_enforced():
    c = TestClient(app)
    assert "starter" in c.get("/api/v1/billing/plans").json()["plans"]
    org = c.post("/api/v1/orgs", json={"name": "QuotaCo"}).json()
    key = c.post("/api/v1/apikeys", json={"name": "q", "scopes": ["read", "collect"],
                                          "org_id": org["id"]}).json()
    h = {"X-API-Key": key["key"]}
    for i in range(3):
        assert c.post("/api/v1/projects", json={"name": f"Q{i}"}, headers=h).status_code == 200
    assert c.post("/api/v1/projects", json={"name": "Q3"}, headers=h).status_code == 402
    usage = c.get("/api/v1/billing/usage", headers=h).json()
    assert usage["plan"] == "starter" and usage["used"]["projects"] == 3
    assert c.post("/api/v1/billing/plan", json={"org_id": org["id"], "plan": "nope"},
                  headers=h).status_code in (400, 403)
