"""Management layer: CRUD/lifecycle per resource (list/create/validation/
view/edit/delete/auth/404/pagination/filter)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as M  # noqa: E402


def _c():
    return TestClient(M.app)


def test_projects_crud_guards():
    c = _c()
    p = c.post("/api/v1/projects", json={"name": "MGMT-P", "description": "d"}).json()
    pid = p["id"]
    assert c.get(f"/api/v1/projects/{pid}").json()["target_count"] == 0
    assert c.get("/api/v1/projects/999999").status_code == 404
    assert c.get("/api/v1/projects?q=MGMT-P").json()["total"] >= 1
    r = c.put(f"/api/v1/projects/{pid}", json={"name": "MGMT-P2"})
    assert r.json()["name"] == "MGMT-P2"
    assert c.put("/api/v1/projects/999999", json={"name": "x"}).status_code == 404
    t = c.post("/api/v1/targets", json={"project_id": pid, "domain": "e.com",
                                        "url": "https://example.com/mgmt"}).json()
    r = c.delete(f"/api/v1/projects/{pid}")
    assert r.status_code == 409  # blocked: has targets
    assert c.delete("/api/v1/projects/999999").status_code == 404
    assert c.delete(f"/api/v1/targets/{t['id']}").json() == {"ok": True}
    assert c.delete(f"/api/v1/projects/{pid}").json() == {"ok": True}


def test_targets_crud_detail_bulk():
    c = _c()
    p = c.post("/api/v1/projects", json={"name": "MGMT-T"}).json()
    t1 = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "a.com",
                                         "url": "https://example.com/a"}).json()
    t2 = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "b.com",
                                         "url": "https://example.com/b"}).json()
    d = c.get(f"/api/v1/targets/{t1['id']}").json()
    assert d["job_count"] == 0 and d["recent_jobs"] == []
    assert c.get("/api/v1/targets/999999").status_code == 404
    r = c.put(f"/api/v1/targets/{t1['id']}",
              json={"tags": ["shop"], "notes": "note-1", "country": "ID"})
    assert r.json()["tags"] == ["shop"] and r.json()["notes"] == "note-1"
    assert c.get(f"/api/v1/targets/{t1['id']}").json()["tags"] == ["shop"]  # persisted via data
    out = c.post("/api/v1/targets/bulk-delete", json={"ids": [t1["id"], t2["id"], 999999]}).json()
    assert out["deleted"] == [t1["id"], t2["id"]] and out["skipped"].get("999999") == "not found"
    assert c.delete(f"/api/v1/projects/{p['id']}").json() == {"ok": True}


def test_target_delete_blocked_by_jobs():
    c = _c()
    p = c.post("/api/v1/projects", json={"name": "MGMT-TJ"}).json()
    t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "j.com",
                                        "url": "https://example.com/j"}).json()
    j = c.post("/api/v1/jobs", json={"project_id": p["id"], "target_id": t["id"],
                                     "url": "https://example.com/j"}).json()
    assert c.delete(f"/api/v1/targets/{t['id']}").status_code == 409
    d = c.get(f"/api/v1/jobs/{j['job_id']}").json()
    assert d["job_id"] == j["job_id"] and "attempts" in d and "prices" in d
    assert c.get("/api/v1/jobs/nope").status_code == 404
    assert c.delete(f"/api/v1/jobs/{j['job_id']}").json() == {"ok": True}
    assert c.delete(f"/api/v1/targets/{t['id']}").json() == {"ok": True}
    assert c.delete(f"/api/v1/projects/{p['id']}").json() == {"ok": True}


def test_schedules_lifecycle():
    c = _c()
    s = c.post("/api/v1/schedules", json={"kind": "interval", "every_min": 60,
                                          "url": "https://example.com/s",
                                          "project_id": 1, "target_id": 1}).json()
    sid = s["id"]
    assert c.get(f"/api/v1/schedules/{sid}").json()["id"] == sid
    assert c.get("/api/v1/schedules/999999").status_code == 404
    r = c.put(f"/api/v1/schedules/{sid}", json={"every_min": 30, "status": "paused"})
    assert r.json()["every_min"] == 30 and r.json()["status"] == "paused"
    assert c.put(f"/api/v1/schedules/{sid}", json={"status": "bogus"}).status_code == 400
    assert c.post(f"/api/v1/schedules/{sid}/enable").json() == {"ok": True}
    run = c.post(f"/api/v1/schedules/{sid}/run").json()
    assert run["status"] == "queued" and run["url"] == "https://example.com/s"
    assert c.post(f"/api/v1/schedules/{sid}/disable").json() == {"ok": True}
    assert c.delete(f"/api/v1/schedules/{sid}").json() == {"ok": True}
    assert c.delete(f"/api/v1/jobs/{run['job_id']}").json() == {"ok": True}


def test_alerts_detail_and_filters():
    c = _c()
    a = c.post("/api/v1/alerts", json={"rule": "price_changed", "message": "m",
                                       "project_id": 0}).json()
    aid = a["id"]
    assert c.get(f"/api/v1/alerts/{aid}").json()["rule"] == "price_changed"
    assert c.get("/api/v1/alerts/999999").status_code == 404
    assert c.post(f"/api/v1/alerts/{aid}/ack").json() == {"ok": True}
    out = c.post("/api/v1/alerts/bulk", json={"action": "resolve", "ids": [aid, 999999]}).json()
    assert out == {"ok": True, "updated": 1}
    assert c.post("/api/v1/alerts/bulk", json={"action": "nope"}).status_code == 400


def test_reports_lifecycle():
    c = _c()
    r = c.post("/api/v1/reports", json={"kind": "price", "project": "MGMT-R"}).json()
    rid = r["id"]
    assert c.get(f"/api/v1/reports/{rid}").json()["id"] == rid
    assert c.get("/api/v1/reports/999999").status_code == 404
    r2 = c.post(f"/api/v1/reports/{rid}/regenerate").json()
    assert r2["id"] != rid and r2["kind"] == r["kind"]
    assert c.delete(f"/api/v1/reports/{rid}").json() == {"ok": True}
    assert c.delete(f"/api/v1/reports/{rid}").status_code == 404
    assert c.delete(f"/api/v1/reports/{r2['id']}").json() == {"ok": True}


def test_watchlists_update():
    c = _c()
    w = c.post("/api/v1/watchlists", json={"kind": "keyword", "value": "mgmt-w"}).json()
    r = c.put(f"/api/v1/watchlists/{w['id']}", json={"value": "mgmt-w2"})
    assert r.json()["value"] == "mgmt-w2"
    assert c.put("/api/v1/watchlists/999999", json={"value": "x"}).status_code == 404
    assert c.delete(f"/api/v1/watchlists/{w['id']}").json() == {"ok": True}


def test_workflows_lifecycle_and_runs():
    c = _c()
    w = c.post("/api/v1/workflows", json={"name": "mgmt-wf", "definition": {"steps": []}}).json()
    wid = w["id"]
    d = c.get(f"/api/v1/workflows/{wid}").json()
    assert d["run_count"] == 0 and d["recent_runs"] == []
    assert c.get("/api/v1/workflows/999999").status_code == 404
    assert c.post(f"/api/v1/workflows/{wid}/disable").json() == {"ok": True}
    assert c.post(f"/api/v1/workflows/{wid}/run", json={"event": {}}).status_code == 404  # disabled
    assert c.post(f"/api/v1/workflows/{wid}/enable").json() == {"ok": True}
    run = c.post(f"/api/v1/workflows/{wid}/run", json={"event": {"type": "x"}}).json()
    assert run["run"]["status"] == "done"
    runs = c.get(f"/api/v1/workflows/{wid}/runs").json()
    assert runs["total"] >= 1
    assert c.delete(f"/api/v1/workflows/{wid}").json() == {"ok": True}
    assert c.delete(f"/api/v1/workflows/{wid}").status_code == 404


def test_webhooks_lifecycle_masked():
    c = _c()
    w = c.post("/api/v1/webhooks", json={"url": "https://example.com/wh",
                                         "secret": "shh-secret",
                                         "event_types": ["alert"]}).json()
    wid = w["id"]
    assert "secret" not in w
    d = c.get(f"/api/v1/webhooks/{wid}").json()
    assert d["has_secret"] is True and "secret" not in d
    assert "shh-secret" not in str(d)
    r = c.put(f"/api/v1/webhooks/{wid}", json={"secret": "***", "enabled": False})
    assert r.json()["enabled"] is False
    d2 = c.get(f"/api/v1/webhooks/{wid}").json()
    assert d2["has_secret"] is True  # *** kept existing secret
    r = c.put(f"/api/v1/webhooks/{wid}", json={"secret": "new-secret"})
    assert c.get(f"/api/v1/webhooks/{wid}").json()["has_secret"] is True
    assert c.post(f"/api/v1/webhooks/{wid}/enable").json() == {"ok": True}
    deliveries = c.get("/api/v1/webhooks/deliveries").json()
    assert "items" in deliveries
    assert c.delete(f"/api/v1/webhooks/{wid}").json() == {"ok": True}
    assert c.get(f"/api/v1/webhooks/{wid}").status_code == 404


def test_connectors_lifecycle_masked():
    c = _c()
    w = c.post("/api/v1/connectors", json={"name": "mgmt-conn", "category": "WEB",
               "manifest": {"name": "mgmt-conn", "category": "WEB", "version": "1",
                            "capabilities": ["collect"]},
               "config": {"api_token": "tok-secret", "user": "u"}}).json()
    cid = w["id"]
    got = c.get(f"/api/v1/connectors/{cid}").json()
    assert got["config"]["api_token"] == "***" and got["config"]["user"] == "u"
    assert "tok-secret" not in str(got)
    r = c.put(f"/api/v1/connectors/{cid}", json={"config": {"api_token": "***"}}).json()
    assert r["config"]["api_token"] == "***"  # kept, still masked
    assert c.put(f"/api/v1/connectors/{cid}", json={"manifest": {}}).status_code == 400
    assert c.post(f"/api/v1/connectors/{cid}/disable").json() == {"ok": True}
    assert c.post(f"/api/v1/connectors/{cid}/enable").json() == {"ok": True}
    assert c.delete(f"/api/v1/connectors/{cid}").json() == {"ok": True}
    assert c.delete(f"/api/v1/connectors/{cid}").status_code == 404


def test_datasets_documents_articles_reviews_lists():
    c = _c()
    ds = c.post("/api/v1/datasets", json={"name": "mgmt-ds", "kind": "generic"}).json()
    assert c.get(f"/api/v1/datasets/{ds['id']}").json()["version_count"] == 0
    assert c.put(f"/api/v1/datasets/{ds['id']}", json={"status": "published"}).json()["status"] == "published"
    doc = c.post("/api/v1/documents", json={"kind": "txt", "title": "mgmt-doc",
                                            "text": "hello world"}).json()
    assert c.delete(f"/api/v1/documents/{doc['id']}").json() == {"ok": True}
    art = c.post("/api/v1/articles", json={"publisher": "p", "title": "t",
                                           "url": "https://example.com/a"}).json()
    assert c.delete(f"/api/v1/articles/{art['id']}").json() == {"ok": True}
    assert "items" in c.get("/api/v1/reviews").json()
    assert c.delete(f"/api/v1/datasets/{ds['id']}").json() == {"ok": True}


def test_memberships_and_user_disable_guards():
    c = _c()
    members = c.get("/api/v1/memberships").json()["items"]
    assert any(m["email"] == "admin@local" for m in members)
    assert all("id" in m for m in members)
    m = c.post("/api/v1/memberships", json={"email": "mgmt@example.com",
                                            "role": "viewer"}).json()
    assert m["role"] == "viewer"
    assert c.post("/api/v1/memberships", json={"email": "mgmt@example.com"}).status_code == 409
    assert c.post("/api/v1/memberships", json={"email": "x@y.z", "role": "bogus"}).status_code == 400
    r = c.put(f"/api/v1/memberships/{m['id']}", json={"role": "analyst"})
    assert r.json()["role"] == "analyst"
    assert c.put(f"/api/v1/memberships/{m['id']}", json={"role": "bogus"}).status_code == 400
    # last-owner + self guards (admin@local is the only owner here)
    admin = next(x for x in members if x["email"] == "admin@local")
    assert c.put(f"/api/v1/memberships/{admin['id']}", json={"role": "viewer"}).status_code == 409
    assert c.delete(f"/api/v1/memberships/{admin['id']}").status_code in (404, 409)
    assert c.delete(f"/api/v1/memberships/{m['id']}").json() == {"ok": True}
    assert c.post("/api/v1/users/admin@local/disable").status_code == 409
    assert c.post("/api/v1/users/nobody@x/disable").status_code == 404


def test_custom_roles_crud_and_enforcement():
    c = _c()
    base = c.get("/api/v1/roles").json()
    assert set(base["builtin"]) >= {"owner", "admin", "analyst", "viewer"}
    assert base["roles"]["viewer"] == ["read"]
    # validation
    assert c.post("/api/v1/roles", json={"name": "admin", "permissions": ["read"]}).status_code == 409
    assert c.post("/api/v1/roles", json={"name": "bad name!", "permissions": ["read"]}).status_code == 400
    assert c.post("/api/v1/roles", json={"name": "ops", "permissions": ["fly"]}).status_code == 400
    assert c.post("/api/v1/roles", json={"name": "ops", "permissions": []}).status_code == 400
    r = c.post("/api/v1/roles", json={"name": "ops", "permissions": ["read", "collect"]}).json()
    assert r["permissions"] == ["collect", "read"]
    assert c.post("/api/v1/roles", json={"name": "ops", "permissions": ["read"]}).status_code == 409
    # builtin immutable
    assert c.put("/api/v1/roles/admin", json={"permissions": ["read"]}).status_code == 403
    assert c.delete("/api/v1/roles/admin").status_code == 403
    assert c.put("/api/v1/roles/nope", json={"permissions": ["read"]}).status_code == 404
    # assign + enforce
    m = c.post("/api/v1/memberships", json={"email": "ops@example.com", "role": "ops"}).json()
    assert c.put(f"/api/v1/memberships/{m['id']}", json={"role": "ghost"}).status_code == 400
    # delete blocked while assigned
    assert c.delete("/api/v1/roles/ops").status_code == 409
    assert c.delete(f"/api/v1/memberships/{m['id']}").json() == {"ok": True}
    assert c.put("/api/v1/roles/ops", json={"permissions": ["read"]}).json()["permissions"] == ["read"]
    assert c.delete("/api/v1/roles/ops").json() == {"ok": True}
    assert c.delete("/api/v1/roles/ops").status_code == 404


def test_rbac_custom_resolution():
    from app.services import rbac as R
    assert R.can("owner", "configure") and not R.can("viewer", "configure")
    assert R.can("anything", "read", {"read", "collect"})
    assert not R.can("anything", "configure", {"read", "collect"})
    assert not R.can("ghost", "read")
    assert set(R.ACTIONS) >= {"read", "collect", "research", "alert", "ai", "configure", "users"}
