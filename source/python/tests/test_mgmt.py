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


def test_recon_unit_shapes():
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from app.services import recon as RC

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            body = (b"<html><head><title>T1</title></head><body>"
                    b'<script src="/x/jquery.min.js"></script>'
                    b'<a href="/in">i</a><a href="https://other.example/o">o</a>'
                    b"</body></html>" if self.path == "/" else b"User-agent: *\n")
            self.send_response(200)
            self.send_header("Content-Type", "text/html" if self.path == "/" else "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    s = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{s.server_port}/"
        body = (b"<html><head><title>T1</title></head><body>"
                b'<script src="/x/jquery.min.js"></script>'
                b'<a href="/in">i</a><a href="https://other.example/o">o</a>'
                b"</body></html>")
        out = RC.recon_target(url, body, trusted_cidrs=["127.0.0.0/8"])
        assert out["ok"] and out["host"] == "127.0.0.1"
        assert out["dns"]["ok"] and "127.0.0.1" in out["dns"]["ips"]
        assert out["tls"]["ok"] is False  # plain http
        assert out["http"]["ok"] and "jQuery" in out["http"]["tech"]
        assert out["http"]["robots_txt"] is True
        assert out["http"]["links_external"] == 1
        bad = RC.recon_target("http://169.254.169.254/", trusted_cidrs=[])
        assert bad["ok"] is False  # SSRF-guarded
        assert RC.recon_target("not a url", trusted_cidrs=[])["ok"] is False
    finally:
        s.shutdown()


def test_infra_correlation_candidates():
    from app.services import infracorr as IC
    store = {"targets": [{"id": 1, "org": 1, "domain": "a.com",
                          "recon": {"ok": True, "dns": {"ok": True, "ips": ["9.9.9.9"]},
                                    "tls": {"ok": True, "cert_key": "C1"},
                                    "http": {"ok": True, "tech": ["WordPress", "jQuery"]}}},
                         {"id": 2, "org": 1, "domain": "b.com",
                          "recon": {"ok": True, "dns": {"ok": True, "ips": ["9.9.9.9"]},
                                    "tls": {"ok": True, "cert_key": "C1"},
                                    "http": {"ok": True, "tech": ["WordPress", "jQuery"]}}},
                         {"id": 3, "org": 1, "domain": "c.com",
                          "recon": {"ok": True, "dns": {"ok": True, "ips": ["8.8.8.8"]},
                                    "tls": {"ok": False},
                                    "http": {"ok": True, "tech": ["React"]}}}],
             "findings": []}
    cands = IC.correlate(store, 1)
    signals = {c["signal"] for c in cands}
    assert {"SHARES_IP", "SHARES_CERTIFICATE", "SHARES_TECHNOLOGY"} <= signals
    assert all(c["members"] == [1, 2] for c in cands)
    made = IC.materialize(store, 1)
    assert len(made) == len(cands) and all(f["status"] == "OPEN" for f in made)
    assert IC.materialize(store, 1) == []  # idempotent, no duplicates
    assert IC.correlate({"targets": []}, 1) == []


def test_findings_lifecycle_and_risk():
    from app.services import risk as R
    c = _c()
    f = c.post("/api/v1/findings", json={"kind": "obs", "title": "F-RISK",
                                         "confidence": 0.9}).json()
    fid = f["id"]
    assert f["severity"] == "info" and f["status"] == "OPEN"
    assert c.put(f"/api/v1/findings/{fid}", json={"severity": "bogus"}).status_code == 400
    assert c.put(f"/api/v1/findings/{fid}", json={"status": "bogus"}).status_code == 400
    r = c.put(f"/api/v1/findings/{fid}", json={"severity": "critical"}).json()
    assert r["severity"] == "critical"
    out = c.post("/api/v1/findings/bulk", json={"action": "status", "status": "CONFIRMED",
                                                "ids": [fid, 999999]}).json()
    assert out == {"ok": True, "updated": 1}
    assert c.post("/api/v1/findings/bulk", json={"action": "nope", "ids": []}).status_code == 400
    store = {"targets": [{"id": 7, "org": 1, "project_id": 1}],
             "findings": [{"id": fid, "org": 1, "severity": "critical",
                           "status": "OPEN", "title": "F-RISK", "entities": [7]}],
             "alerts": [{"id": 1, "org": 1, "project_id": 1, "rule": "x",
                         "severity": "critical"}],
             "projects": [{"id": 1, "org": 1}], "changes": [], "jobs": [],
             "entities": [{"id": 7, "name": "e", "domain": "e.com"}],
             "nodes": [], "edges": [], "evidence": []}
    scored = R.score_target(store, 7, 1)
    assert scored["score"] == 40 and scored["level"] == "medium"  # 25 finding + 15 alert
    assert all({"name", "points", "why", "evidence"} <= set(fc) for fc in scored["factors"])
    assert R.score_target(store, 999, 1) == {"error": "target not found"}
    assert R.score_target(store, 7, 2) == {"error": "target not found"}
    ent = R.score_entity(store, 7, 1)
    assert ent["score"] >= 25 and "relationships" in ent
    assert R.score_entity(store, 999, 1) == {"error": "entity not found"}
    assert R._level(0) == "none" and R._level(100) == "critical"
    assert c.delete(f"/api/v1/findings/{fid}").json() == {"ok": True}
    assert c.delete(f"/api/v1/findings/{fid}").status_code == 404


def test_investigations_crud_links():
    c = _c()
    assert c.post("/api/v1/investigations", json={"title": ""}).status_code == 400
    assert c.post("/api/v1/investigations", json={"title": "x", "status": "bogus"}).status_code == 400
    inv = c.post("/api/v1/investigations", json={"title": "INV-1", "priority": "high",
                                                 "tags": ["t"]}).json()
    iid = inv["id"]
    assert c.get("/api/v1/investigations/999999").status_code == 404
    d = c.get(f"/api/v1/investigations/{iid}").json()
    assert d["linked"]["targets"] == [] and d["status"] == "open"
    assert c.put(f"/api/v1/investigations/{iid}", json={"status": "bogus"}).status_code == 400
    assert c.put(f"/api/v1/investigations/{iid}", json={"status": "investigating"}).json()["status"] == "investigating"
    t = c.post("/api/v1/targets", json={"project_id": 1, "domain": "inv.com",
                                        "url": "https://example.com/inv"}).json()
    r = c.post(f"/api/v1/investigations/{iid}/links", json={"kind": "target_ids", "ids": [t["id"], t["id"]]}).json()
    assert r["added"] == [t["id"]]
    assert c.post(f"/api/v1/investigations/{iid}/links", json={"kind": "nope", "ids": []}).status_code == 400
    n = c.post(f"/api/v1/investigations/{iid}/notes", json={"text": "note-1"}).json()
    assert len(n["notes"]) == 1 and n["notes"][0]["text"] == "note-1"
    assert c.post(f"/api/v1/investigations/{iid}/notes", json={"text": ""}).status_code == 400
    task = c.post(f"/api/v1/investigations/{iid}/tasks", json={"title": "task-1"}).json()
    assert task["done"] is False
    assert c.post(f"/api/v1/investigations/{iid}/tasks/{task['id']}/toggle").json() == {"ok": True, "done": True}
    assert c.post(f"/api/v1/investigations/{iid}/tasks/999999/toggle").status_code == 404
    m = c.post(f"/api/v1/investigations/{iid}/members", json={"email": "an@example.com"}).json()
    assert "an@example.com" in m["member_emails"]
    assert c.post(f"/api/v1/investigations/{iid}/members", json={"email": "bad"}).status_code == 400
    assert c.get("/api/v1/investigations?q=inv-1").json()["total"] >= 1
    assert c.get("/api/v1/investigations?status=investigating").json()["total"] >= 1
    assert c.delete(f"/api/v1/investigations/{iid}").json() == {"ok": True}
    assert c.delete(f"/api/v1/targets/{t['id']}").json() == {"ok": True}


def test_cases_lifecycle():
    c = _c()
    assert c.post("/api/v1/cases", json={"title": ""}).status_code == 400
    case = c.post("/api/v1/cases", json={"title": "CASE-1", "priority": "critical",
                                         "assignee": "lead@example.com"}).json()
    cid = case["id"]
    assert case["status"] == "OPEN"
    assert c.put(f"/api/v1/cases/{cid}", json={"status": "bogus"}).status_code == 400
    assert c.put(f"/api/v1/cases/{cid}", json={"status": "investigating"}).json()["status"] == "INVESTIGATING"
    inv = c.post("/api/v1/investigations", json={"title": "INV-C"}).json()
    r = c.post(f"/api/v1/cases/{cid}/links", json={"kind": "investigation_ids", "ids": [inv["id"]]}).json()
    assert r["added"] == [inv["id"]]
    assert c.post(f"/api/v1/cases/{cid}/links", json={"kind": "nope", "ids": []}).status_code == 400
    n = c.post(f"/api/v1/cases/{cid}/notes", json={"text": "case-note"}).json()
    assert n["notes"][0]["text"] == "case-note"
    task = c.post(f"/api/v1/cases/{cid}/tasks", json={"title": "ct"}).json()
    assert c.post(f"/api/v1/cases/{cid}/tasks/{task['id']}/toggle").json()["done"] is True
    d = c.get(f"/api/v1/cases/{cid}").json()
    assert len(d["linked"]["investigations"]) == 1 and "audit_trail" in d
    assert c.get("/api/v1/cases?q=case-1").json()["total"] >= 1
    assert c.delete(f"/api/v1/cases/{cid}").json() == {"ok": True}
    assert c.delete(f"/api/v1/investigations/{inv['id']}").json() == {"ok": True}
    assert c.get(f"/api/v1/cases/{cid}").status_code == 404
