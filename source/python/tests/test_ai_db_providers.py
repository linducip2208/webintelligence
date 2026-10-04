"""DB-configured AI providers: CRUD, protocol validation, encryption at rest,
enable/disable, and default-chain inclusion. No hardcoded vendors."""
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as M  # noqa: E402


class Stub(BaseHTTPRequestHandler):
    def _send(self, obj, status=200):
        import json as _j
        body = _j.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        if self.path == "/chat/completions":
            self._send({"choices": [{"message": {"content": "stub-db-answer"}}],
                        "usage": {"prompt_tokens": 2, "completion_tokens": 1}})
        else:
            self._send({}, 404)

    def log_message(self, *a):
        pass


def _srv():
    s = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def _client():
    return TestClient(M.app)


def _clear(name):
    M.STORE["ai_providers"][:] = [x for x in M.STORE["ai_providers"] if x.get("name") != name]


def test_db_provider_crud_protocol_validation():
    c = _client()
    _clear("t-gw")
    r = c.post("/api/v1/ai/providers/db", json={"name": "t-gw"})
    assert r.status_code == 400  # base_url required
    r = c.post("/api/v1/ai/providers/db", json={"name": "t-gw", "base_url": "http://x",
                                                "protocol": "bogus"})
    assert r.status_code == 400
    r = c.post("/api/v1/ai/providers/db", json={"name": "t-gw", "base_url": "http://x",
                                                "protocol": "responses", "model": "m",
                                                "api_key": "k-secret"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["protocol"] == "responses"
    assert "api_key_enc" not in body  # never leaked
    r = c.post("/api/v1/ai/providers/db", json={"name": "t-gw", "base_url": "http://x"})
    assert r.status_code == 409
    items = c.get("/api/v1/ai/providers/db").json()["items"]
    row = next(x for x in items if x["name"] == "t-gw")
    assert "api_key_enc" not in row
    pid = row["id"]
    r = c.post(f"/api/v1/ai/providers/db/{pid}", json={"model": "m2"})
    assert r.json()["model"] == "m2"
    r = c.post(f"/api/v1/ai/providers/db/{pid}/disable")
    assert r.json() == {"ok": True}
    assert next(x for x in c.get("/api/v1/ai/providers/db").json()["items"]
                if x["name"] == "t-gw")["enabled"] is False
    r = c.post(f"/api/v1/ai/providers/db/{pid}/enable")
    assert r.json() == {"ok": True}
    _clear("t-gw")


def test_db_provider_test_button_paths():
    c = _client()
    r = c.post("/api/v1/ai/providers/db/999999/test")
    assert r.status_code == 404
    _clear("t-nokey")
    r = c.post("/api/v1/ai/providers/db", json={"name": "t-nokey", "base_url": "http://x",
                                                "protocol": "chat", "model": "m"})
    pid = r.json()["id"]
    out = c.post(f"/api/v1/ai/providers/db/{pid}/test").json()
    assert out == {"ok": False, "reason": "no-key-saved"}
    _clear("t-nokey")


def test_db_provider_encrypted_and_in_default_chain(monkeypatch):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("CREDENTIALS_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AI_EXTRA_MODELS", "stub-m")
    s = _srv()
    base = f"http://127.0.0.1:{s.server_port}"
    c = _client()
    _clear("t-stub")
    r = c.post("/api/v1/ai/providers/db", json={"name": "t-stub", "base_url": base,
                                                "protocol": "chat", "model": "stub-m",
                                                "api_key": "k-plain-test"})
    assert r.status_code == 200, r.text
    stored = next(x for x in M.STORE["ai_providers"] if x["name"] == "t-stub")
    assert stored["api_key_enc"].startswith("enc:") and "k-plain-test" not in stored["api_key_enc"]
    out = c.post("/api/v1/ai/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert out.status_code == 200, out.text
    body = out.json()
    assert body["provider"] == "t-stub" and body["text"] == "stub-db-answer"
    _clear("t-stub")
    s.shutdown()


def test_seed_staged_parents_before_children():
    """Regression: single-transaction seed died on MySQL FK 1452, leaving
    organizations missing — every FK-backed write then lived in memory
    only and vanished on restart. Staged commits must leave org+member."""
    orgs = [o for o in M.STORE["orgs"] if o.get("name") == "Default"]
    assert orgs, "default org hydrated"
    assert any(m.get("org_id") == orgs[0]["id"] for m in M.STORE["memberships"])
