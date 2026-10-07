"""AI end-to-end against a local stub (mocked HTTP is allowed in tests).

Proves the whole chain with zero vendor credentials: inventory -> masked
credential -> test -> model discovery -> sync -> default -> inference ->
usage record -> privacy enforcement -> delete. Storm-free: one stub server.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


class _Stub(BaseHTTPRequestHandler):
    def _send(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def do_GET(self):
        if self.path == "/models":
            self._send({"data": [{"id": "stub-m1", "protocol": "chat",
                                  "capabilities": ["chat"]}]})
        else:
            self._send({}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            payload = {}
        if self.path == "/responses":
            self._send({"output_text": "hi stub",
                        "usage": {"input_tokens": 2, "output_tokens": 2}})
        else:
            _ = payload
            self._send({"choices": [{"message": {"content": "hi stub"}}],
                        "usage": {"prompt_tokens": 2, "completion_tokens": 2}})

    def log_message(self, *a):
        pass


def test_ai_full_chain_stub(monkeypatch):
    monkeypatch.setenv("TRUSTED_EGRESS_CIDRS", "127.0.0.0/8")
    srv = HTTPServer(("127.0.0.1", 0), _Stub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    try:
        p = c.post("/api/v1/ai/providers/db",
                   json={"name": "E2EProv", "preset": "ollama",
                         "protocol": "chat", "base_url": base,
                         "api_key": "K" * 16, "model": "stub-m1"}).json()
        pid = p["id"]

        inv = c.get("/api/v1/ai/credentials/inventory").json()
        row = next(r for r in inv["inventory"] if r["provider"] == "E2EProv")
        assert row["configured"] is True and row["masked_key"].endswith("KKKK")
        assert "K" * 16 not in str(inv)

        t = c.post(f"/api/v1/ai/providers/db/{pid}/test", json={}).json()
        assert t["success"] is True and t["model"]["available"] is True
        assert [m["id"] for m in t["models"]] == ["stub-m1"]

        s = c.post("/api/v1/ai/providers/E2EProv/models/sync", json={}).json()
        assert s["count"] == 1 and s["models"][0]["id"] == "stub-m1"

        d = c.post("/api/v1/ai/default",
                   json={"scope": "system", "provider": "db:E2EProv",
                         "model": "stub-m1",
                         "use_cases": {"research": {"provider": "db:E2EProv",
                                                    "model": "stub-m1",
                                                    "enabled": True}}}).json()
        assert d["ok"] is True

        r = c.post("/api/v1/ai/chat",
                   json={"messages": [{"role": "user", "content": "summarize"}],
                         "evidence": [{"text": "stub evidence"}],
                         "use_case": "research"}).json()
        assert r.get("answer") == "hi stub" or "hi stub" in str(r)
        assert r.get("provider") == "E2EProv"
        assert r.get("provider") == "E2EProv"
        assert "fallbacks_tried" in r

        u = c.get("/api/v1/ai/usage").json()
        assert u["calls"] >= 1

        c.post("/api/v1/ai/privacy", json={"mode": "local_only"})
        try:
            cloud = c.post("/api/v1/ai/providers/db",
                           json={"name": "E2ECloud", "preset": "openai-compatible",
                                 "protocol": "chat", "base_url": base,
                                 "api_key": "k", "model": "stub-m1"}).json()
            try:
                denied = c.post("/api/v1/ai/chat",
                                json={"messages": [{"role": "user", "content": "hi"}],
                                      "provider": "db:E2ECloud"})
                assert denied.status_code == 403
            finally:
                c.delete(f"/api/v1/ai/providers/db/{cloud['id']}")
        finally:
            c.post("/api/v1/ai/privacy", json={"mode": "any"})
    finally:
        c.delete(f"/api/v1/ai/providers/db/{p['id']}")
        c.post("/api/v1/ai/default", json={"scope": "system", "provider": "", "model": ""})
        srv.shutdown()
