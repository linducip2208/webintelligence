"""AI Provider configuration UX backend: presets, CRUD, test-before-save,
discovery, status metadata, encryption, SSRF, error normalization."""
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi.testclient import TestClient  # noqa: E402

import app.main as M  # noqa: E402
from ai import diagnose as DG  # noqa: E402
from ai.presets import list_presets, get_preset, valid_protocol  # noqa: E402


class Stub(BaseHTTPRequestHandler):
    """Local OpenAI-compatible stub. Asserts Bearer key; 401 otherwise."""

    def _send(self, obj, status=200):
        import json as _j
        body = _j.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        return self.headers.get("Authorization") == "Bearer k-good"

    def do_GET(self):
        if self.path == "/models":
            if not self._auth():
                self._send({"error": {"message": "invalid api key"}}, 401)
                return
            self._send({"data": [{"id": "stub-m"}, {"id": "stub-m2"}]})
        else:
            self._send({}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        import json as _j
        try:
            payload = _j.loads(body or b"{}")
        except Exception:
            payload = {}
        if self.path == "/responses":
            if not self._auth():
                self._send({"error": {"message": "invalid api key"}}, 401)
                return
            if payload.get("model") not in ("stub-m", "stub-m2"):
                self._send({"error": {"message": "unknown model"}}, 404)
                return
            self._send({"output": [{"type": "message", "content": [
                {"type": "output_text", "text": "stub-resp"}]}],
                "usage": {"input_tokens": 6, "output_tokens": 3}})
            return
        if self.path == "/chat/completions":
            if not self._auth():
                self._send({"error": {"message": "invalid api key"}}, 401)
                return
            if payload.get("model") not in ("stub-m", "stub-m2"):
                self._send({"error": {"message": "unknown model"}}, 404)
                return
            self._send({"choices": [{"message": {"content": "stub-answer"}}],
                        "usage": {"prompt_tokens": 2, "completion_tokens": 1}})
            return
        self._send({}, 404)

    def log_message(self, *a):
        pass


def _srv():
    s = HTTPServer(("127.0.0.1", 0), Stub)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def _client():
    return TestClient(M.app)


def _clear(*names):
    M.STORE["ai_providers"][:] = [x for x in M.STORE["ai_providers"]
                                  if x.get("name") not in names]


def test_presets_shape_and_protocols():
    ps = list_presets()
    assert len(ps) >= 8
    ids = [p["id"] for p in ps]
    for want in ("opencode-go", "opencode-zen", "claude", "openai", "google",
                 "ollama", "openai-compatible", "anthropic-compatible",
                 "google-compatible"):
        assert want in ids, want
    for p in ps:
        assert valid_protocol(p["protocol"]), p
        assert p["auth"] in ("api_key", "optional_key")
        assert p["endpoint_mode"] in ("fixed", "editable", "required")
        assert isinstance(p["discovery"], bool)
    assert get_preset("nope") is None
    assert get_preset("Ollama")["local"] is True


def test_list_empty_state_and_only_configured():
    c = _client()
    before = {x["name"] for x in M.STORE["ai_providers"]}
    assert c.get("/api/v1/ai/providers/db").json() == {"items": [
        {k: v for k, v in x.items() if k != "api_key_enc"}
        for x in M.STORE["ai_providers"]]}
    # no key material anywhere in the list payload
    import json as _j
    assert "api_key_enc" not in _j.dumps(c.get("/api/v1/ai/providers/db").json())
    assert before == before  # configured rows only; presets live at /provider-presets
    assert isinstance(c.get("/api/v1/ai/provider-presets").json()["presets"], list)


def test_crud_detail_update_delete():
    c = _client()
    _clear("ux-1")
    s = _srv()
    base = f"http://127.0.0.1:{s.server_port}"
    r = c.post("/api/v1/ai/providers/db",
               json={"name": "ux-1", "preset": "ollama", "base_url": base,
                     "protocol": "chat", "model": "stub-m", "api_key": "k-good"})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    assert r.json()["protocol"] == "chat"
    d = c.get(f"/api/v1/ai/providers/db/{pid}").json()
    assert d["name"] == "ux-1" and "api_key_enc" not in d
    assert c.get("/api/v1/ai/providers/db/999999").status_code == 404
    r = c.put(f"/api/v1/ai/providers/db/{pid}", json={"model": "stub-m2"})
    assert r.json()["model"] == "stub-m2"
    r = c.post(f"/api/v1/ai/providers/db/{pid}/disable")
    assert r.json() == {"ok": True}
    r = c.post(f"/api/v1/ai/providers/db/{pid}/enable")
    assert r.json() == {"ok": True}
    assert c.delete(f"/api/v1/ai/providers/db/{pid}").json() == {"ok": True}
    assert c.delete(f"/api/v1/ai/providers/db/{pid}").status_code == 404
    _clear("ux-1")
    s.shutdown()


def test_saved_test_success_structure_and_status():
    c = _client()
    _clear("ux-test")
    s = _srv()
    base = f"http://127.0.0.1:{s.server_port}"
    pid = c.post("/api/v1/ai/providers/db",
                 json={"name": "ux-test", "preset": "ollama", "base_url": base,
                       "protocol": "chat", "model": "stub-m", "api_key": "k-good"}).json()["id"]
    out = c.post(f"/api/v1/ai/providers/db/{pid}/test").json()
    assert out["success"] is True
    assert out["provider"]["protocol"] == "chat"
    assert out["connection"]["authenticated"] is True
    assert out["connection"]["latency_ms"] >= 0
    assert out["model"] == {"selected": "stub-m", "available": True}
    assert [m["id"] for m in out["models"]] == ["stub-m", "stub-m2"]
    assert out["message"] == "Connection successful"
    assert "api_key" not in str(out).lower().replace("api key", "")
    row = next(x for x in M.STORE["ai_providers"] if x["name"] == "ux-test")
    assert row["last_test_status"] == "passed" and row["last_tested_at"] > 0
    _clear("ux-test")
    s.shutdown()


def test_saved_test_bad_key_and_unknown_model():
    c = _client()
    _clear("ux-bad", "ux-model")
    s = _srv()
    base = f"http://127.0.0.1:{s.server_port}"
    bad = c.post("/api/v1/ai/providers/db",
                 json={"name": "ux-bad", "preset": "ollama", "base_url": base,
                       "protocol": "chat", "model": "stub-m", "api_key": "k-wrong"}).json()["id"]
    out = c.post(f"/api/v1/ai/providers/db/{bad}/test").json()
    assert out["success"] is False
    assert out["error"]["code"] == "AUTHENTICATION_FAILED"
    assert "k-wrong" not in str(out)
    row = next(x for x in M.STORE["ai_providers"] if x["name"] == "ux-bad")
    assert row["last_test_status"] == "failed"
    assert row["last_test_error"] == "AUTHENTICATION_FAILED"
    mid = c.post("/api/v1/ai/providers/db",
                 json={"name": "ux-model", "preset": "ollama", "base_url": base,
                       "protocol": "chat", "model": "nope-m", "api_key": "k-good"}).json()["id"]
    out2 = c.post(f"/api/v1/ai/providers/db/{mid}/test").json()
    assert out2["success"] is False
    assert out2["error"]["code"] == "ENDPOINT_OR_MODEL_NOT_FOUND"
    _clear("ux-bad", "ux-model")
    s.shutdown()


def test_unsaved_test_and_discovery():
    c = _client()
    s = _srv()
    base = f"http://127.0.0.1:{s.server_port}"
    spec = {"name": "draft", "preset": "ollama", "base_url": base,
            "protocol": "chat", "model": "stub-m2", "api_key": "k-good"}
    out = c.post("/api/v1/ai/providers/db/test", json=spec).json()
    assert out["success"] is True and out["model"]["available"] is True
    assert [m["id"] for m in out["models"]] == ["stub-m", "stub-m2"]
    # nothing persisted by unsaved test
    assert not any(x.get("name") == "draft" for x in M.STORE["ai_providers"])
    bad = dict(spec, api_key="k-wrong")
    out2 = c.post("/api/v1/ai/providers/db/test", json=bad).json()
    assert out2["success"] is False and out2["error"]["code"] == "AUTHENTICATION_FAILED"
    disc = c.post("/api/v1/ai/providers/db/models", json=spec).json()
    assert disc["discovery"] is True and len(disc["models"]) == 2
    s.shutdown()


def test_discovery_without_support_allows_manual():
    c = _client()
    out = c.post("/api/v1/ai/providers/db/models",
                 json={"name": "g", "preset": "google",
                       "base_url": "https://generativelanguage.googleapis.com",
                       "protocol": "google", "api_key": "k", "model": "gemini-2.0-flash"}).json()
    assert out["discovery"] is False and out["manual_entry"] is True


def test_ssrf_and_unreachable():
    c = _client()
    r = c.post("/api/v1/ai/providers/db/test",
               json={"name": "evil", "base_url": "http://169.254.169.254/",
                     "protocol": "chat", "api_key": "k"})
    assert r.status_code == 400
    r = c.post("/api/v1/ai/providers/db/test",
               json={"name": "evil2", "base_url": "http://localhost:9/",
                     "protocol": "chat", "api_key": "k"})
    assert r.status_code == 400
    out = c.post("/api/v1/ai/providers/db/test",
                 json={"name": "down", "preset": "ollama",
                       "base_url": "http://127.0.0.1:9/", "protocol": "chat",
                       "api_key": "", "model": ""}).json()
    assert out["success"] is False
    assert out["error"]["code"] in ("PROVIDER_UNAVAILABLE", "CONNECTION_TIMEOUT")


def test_normalize_and_scrub():
    assert DG.normalize_error("http 401: bad")[0] == "AUTHENTICATION_FAILED"
    assert DG.normalize_error("http 403 x")[0] == "ACCESS_DENIED"
    assert DG.normalize_error("http 404 nope")[0] == "ENDPOINT_OR_MODEL_NOT_FOUND"
    assert DG.normalize_error("http 429 slow")[0] == "RATE_LIMITED"
    assert DG.normalize_error("http 500 boom")[0] == "PROVIDER_UNAVAILABLE"
    assert DG.normalize_error("timed out after 5s")[0] == "CONNECTION_TIMEOUT"
    s = DG.scrub("key Bearer oc_sk_abc123 and sk-xyz and ?key=qqq done")
    assert "oc_sk_abc123" not in s and "sk-xyz" not in s and "key=qqq" not in s
    assert "[redacted]" in s


def test_rate_limit_on_test_endpoint():
    c = _client()
    seen_429 = False
    for _ in range(40):
        r = c.post("/api/v1/ai/providers/db/test",
                   json={"name": "rl", "base_url": "http://127.0.0.1:9/",
                         "protocol": "chat"})
        if r.status_code == 429:
            seen_429 = True
            assert r.headers.get("Retry-After") is not None
            break
    assert seen_429, "expected 429 within 40 rapid test calls"


def test_seed_staged_parents_before_children():
    """Regression: single-transaction seed died on MySQL FK 1452, leaving
    organizations missing — FK-backed writes then lived in memory only."""
    orgs = [o for o in M.STORE["orgs"] if o.get("name") == "Default"]
    assert orgs, "default org hydrated"
    assert any(m.get("org_id") == orgs[0]["id"] for m in M.STORE["memberships"])


def test_key_encrypted_and_chain_inclusion(monkeypatch):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("CREDENTIALS_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AI_EXTRA_MODELS", "stub-m")
    c = _client()
    _clear("ux-chain")
    s = _srv()
    base = f"http://127.0.0.1:{s.server_port}"
    r = c.post("/api/v1/ai/providers/db",
               json={"name": "ux-chain", "preset": "ollama", "base_url": base,
                     "protocol": "chat", "model": "stub-m", "api_key": "k-good"})
    assert r.status_code == 200, r.text
    stored = next(x for x in M.STORE["ai_providers"] if x["name"] == "ux-chain")
    assert stored["api_key_enc"].startswith("enc:")
    assert "k-good" not in stored["api_key_enc"]
    out = c.post("/api/v1/ai/chat",
                 json={"messages": [{"role": "user", "content": "hi"}],
                       "model": "stub-m"})
    assert out.status_code == 200, out.text
    body = out.json()
    assert body["provider"] == "ux-chain" and body["text"] == "stub-answer"
    _clear("ux-chain")
    s.shutdown()
