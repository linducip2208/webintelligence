"""Round-3 features: semantic search, reviews, RUNNING, AI providers, paging."""
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.search import semantic as sem  # noqa: E402


class _AIStub(BaseHTTPRequestHandler):
    def _send(self, obj, status=200):
        import json as _j
        body = _j.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send({"data": [{"id": "m1"}]} if self.path == "/models" else {}, 200 if self.path == "/models" else 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        self._send({"choices": [{"message": {"content": "hi"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1}})

    def log_message(self, *a):
        pass


def test_semantic_real_ranking(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    sem._IDX["i"] = None
    idx = sem.Index(str(tmp_path / "v.json"))
    idx.add("d1", "apple banana cherry fruit")
    idx.add("d2", "quantum physics tensor calculus")
    top = idx.search("apple fruit")
    assert top[0]["id"] == "d1" and top[0]["score"] > 0
    # persistence across instances
    idx2 = sem.Index(str(tmp_path / "v.json"))
    assert idx2.search("quantum")[0]["id"] == "d2"


def test_semantic_endpoint_and_doc_index():
    c = TestClient(app)
    d = c.post("/api/v1/documents", json={"kind": "txt", "title": "t",
                                          "text": "solar panel efficiency report panel"}).json()
    assert d["chunks"]
    r = c.get("/api/v1/search/semantic?q=solar+panel").json()
    assert r["method"].startswith("hashed-token")
    assert any("doc:" in h["id"] for h in r["items"])


def test_reviews_import_summary():
    c = TestClient(app)
    p = c.post("/api/v1/projects", json={"name": "RP", "description": ""}).json()
    t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "example.com",
                                        "url": "https://example.com/rp"}).json()
    out = c.post("/api/v1/reviews/import", json={"reviews": [
        {"product_id": t["id"], "rating": 5, "text": "love it excellent"},
        {"product_id": t["id"], "rating": 1, "text": "terrible broken refund"}]}).json()
    assert out["imported"] == 2
    s = c.get(f"/api/v1/reviews/summary?product_id={t['id']}").json()
    assert s["count"] == 2 and s["avg_rating"] == 3.0
    assert s["sentiment"] == {"positive": 1, "negative": 1}


def test_running_state_guards():
    c = TestClient(app)
    p = c.post("/api/v1/projects", json={"name": "RS", "description": ""}).json()
    t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "example.com",
                                        "url": "https://example.com/r2"}).json()
    j = c.post("/api/v1/jobs", json={"project_id": p["id"], "target_id": t["id"],
                                     "url": "https://example.com/r2"}).json()
    assert c.post(f"/api/v1/jobs/{j['job_id']}/cancel", json={}).json()["status"] == "cancelled"
    assert c.post(f"/api/v1/jobs/{j['job_id']}/cancel", json={}).status_code == 409
    assert c.post(f"/api/v1/jobs/{j['job_id']}/retry", json={}).json()["status"] == "queued"


def test_ai_provider_crud_no_secret_leak():
    c = TestClient(app)
    srv = HTTPServer(("127.0.0.1", 0), _AIStub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    try:
        created = c.post("/api/v1/ai/providers/db", json={"name": "prov-x",
                         "preset": "ollama", "base_url": base, "api_key": "K" * 16,
                         "model": "m1"}).json()
        assert "api_key_enc" not in created
        assert "K" * 16 not in str(created)  # raw key never echoed
        assert created["masked_key"].endswith("KKKK")  # masked form only
        assert created["key_configured"] is True
        listed = c.get("/api/v1/ai/providers/db").json()["items"]
        assert all("api_key_enc" not in x for x in listed)
        assert c.post("/api/v1/ai/providers/db", json={"name": "prov-x",
                      "base_url": base}).status_code == 409
        # SSRF guard still rejects unresolvable/private hosts at create time
        assert c.post("/api/v1/ai/providers/db", json={"name": "prov-fake",
                      "base_url": "https://ai.local/v1"}).status_code == 400
        chat = c.post("/api/v1/ai/chat", json={"messages": [], "provider": "prov-x"}).json()
        assert chat.get("text") == "hi" and chat.get("provider") == "prov-x"
        missing = c.post("/api/v1/ai/chat", json={"messages": [], "provider": "prov-missing"})
        assert missing.status_code == 404  # honest error, not fake output
        assert c.post("/api/v1/ai/providers/db/9999/disable", json={}).status_code == 404
    finally:
        srv.shutdown()


def test_keyset_pagination_totals():
    c = TestClient(app)
    p1 = c.get("/api/v1/prices?page=1&size=1").json()
    p2 = c.get("/api/v1/prices?page=2&size=1").json()
    assert p1["total"] == p2["total"] and p1["page"] == 1 and p2["page"] == 2
    if p1["total"] > 1:
        assert p1["items"] != p2["items"]
    e = c.get("/api/v1/events?page=1&size=5").json()
    assert set(e) >= {"items", "total", "page", "size"}


def test_browser_health_shape():
    c = TestClient(app)
    h = c.get("/api/v1/browser/health").json()
    assert set(h) >= {"installed", "pool", "browser_alive", "reused"}
