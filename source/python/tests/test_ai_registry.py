"""AI provider registry tests: catalog, CRUD shape, masking, live-test honesty,
defaults cascade. No real vendor credentials: failure paths use an
unreachable local endpoint and assert STRUCTURED honest errors."""
import time

from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)
KEY = "sk-test-ONLY-FAKE-1234abcd"


def test_presets_cover_vendors_and_adapters():
    r = c.get("/api/v1/ai/provider-presets").json()
    ids = {p["id"] for p in r["presets"]}
    for want in ("openai", "claude", "google", "ollama", "opencode-go",
                 "openrouter", "groq", "deepseek", "mistral", "xai", "cohere",
                 "together", "fireworks", "perplexity",
                 "openai-compatible", "responses-compatible",
                 "anthropic-compatible", "google-compatible"):
        assert want in ids, f"preset missing: {want}"
    for p in r["presets"]:
        assert p["protocol"] in ("chat", "responses", "anthropic", "google")
        assert isinstance(p["capabilities"], list) and p["capabilities"]
        assert "endpoint_mode" in p and "local" in p
    # every preset maps to a real adapter (no giant if/else, protocol is data)
    from app.ai.factory import build_provider
    for p in r["presets"]:
        prov = build_provider(p["protocol"], p["default_endpoint"] or "https://example.com/v1",
                              "k", p["default_model"] or "m")
        assert prov is not None


def test_provider_crud_masks_and_shapes():
    r = c.post("/api/v1/ai/providers/db",
               json={"name": "AuditProv", "preset": "openai-compatible",
                     "protocol": "chat", "base_url": "https://example.com/v1",
                     "api_key": KEY, "model": "audit-model"}).json()
    pid = r["id"]
    assert r["key_configured"] is True
    assert r["masked_key"].endswith("abcd") and KEY not in r["masked_key"]
    assert r["configured"] is True
    assert r["created_at"] > 0
    assert "chat" in r["capabilities"]
    assert r["default_model"] == "audit-model"
    assert "api_key_enc" not in r and KEY not in str(r)

    lst = c.get("/api/v1/ai/providers/db").json()["items"]
    row = next(x for x in lst if x["id"] == pid)
    assert "api_key_enc" not in row and KEY not in str(row)
    assert row["masked_key"].endswith("abcd")

    det = c.get(f"/api/v1/ai/providers/db/{pid}").json()
    assert "api_key_enc" not in det and KEY not in str(det)

    assert c.post(f"/api/v1/ai/providers/db/{pid}/disable", json={}).json() == {"ok": True}
    assert c.post(f"/api/v1/ai/providers/db/{pid}/enable", json={}).json() == {"ok": True}
    assert c.delete(f"/api/v1/ai/providers/db/{pid}").json() == {"ok": True}


def test_live_test_honest_failure_without_creds(monkeypatch):
    # loopback unreachable endpoint; trusted SSRF-wise so the test exercises
    # the CONNECTION failure path, not the guard.
    monkeypatch.setenv("TRUSTED_EGRESS_CIDRS", "127.0.0.0/8")
    r = c.post("/api/v1/ai/providers/db",
               json={"name": "AuditUnreachable", "preset": "openai-compatible",
                     "protocol": "chat", "base_url": "http://127.0.0.1:9/v1",
                     "api_key": "bogus", "model": "nope"}).json()
    pid = r["id"]
    try:
        t = c.post(f"/api/v1/ai/providers/db/{pid}/test", json={}).json()
        assert t["success"] is False
        assert t["error"]["code"] in ("PROVIDER_UNAVAILABLE", "CONNECTION_TIMEOUT",
                                      "AUTHENTICATION_FAILED", "ENDPOINT_OR_MODEL_NOT_FOUND")
        assert "bogus" not in str(t)
        row = c.get(f"/api/v1/ai/providers/db/{pid}").json()
        assert row["last_test_status"] == "failed"
        assert row["last_tested_at"] > 0
        assert "bogus" not in str(row)
        h = c.get("/api/v1/ai/health").json()
        names = [p["name"] for p in h.get("providers", [])]
        assert "AuditUnreachable" in names
    finally:
        c.delete(f"/api/v1/ai/providers/db/{pid}")


def test_test_all_is_sequential_and_audited():
    r = c.post("/api/v1/ai/providers/db",
               json={"name": "AuditAll", "preset": "ollama",
                     "protocol": "chat", "base_url": "http://127.0.0.1:9/v1",
                     "api_key": "", "model": ""}).json()
    pid = r["id"]
    try:
        t0 = time.time()
        out = c.post("/api/v1/ai/providers/db/test-all", json={}).json()
        assert out["tested"] >= 1
        assert time.time() - t0 < 120
        names = [x["name"] for x in out["results"]]
        assert "AuditAll" in names
    finally:
        c.delete(f"/api/v1/ai/providers/db/{pid}")


def test_defaults_cascade_and_validation():
    assert c.post("/api/v1/ai/default",
                  json={"scope": "system", "provider": "no-such", "model": ""}).status_code == 404
    assert c.post("/api/v1/ai/default",
                  json={"scope": "bogus", "provider": "", "model": ""}).status_code == 400
    # defaults must point at something usable: create, then default to it
    p = c.post("/api/v1/ai/providers/db",
               json={"name": "AuditDefault", "preset": "openai-compatible",
                     "protocol": "chat", "base_url": "https://example.com/v1",
                     "api_key": "k", "model": "m"}).json()
    try:
        r = c.post("/api/v1/ai/default",
                   json={"scope": "system", "provider": "db:AuditDefault",
                          "model": "m"}).json()
        assert r["ok"] is True
        v = c.get("/api/v1/ai/default").json()
        assert v["system"]["provider"] == "db:AuditDefault"
        assert v["effective"]["provider"] == "db:AuditDefault"
    finally:
        c.delete(f"/api/v1/ai/providers/db/{p['id']}")
        c.post("/api/v1/ai/default", json={"scope": "system", "provider": "", "model": ""})


def test_ollama_unreachable_is_honest():
    r = c.post("/api/v1/ai/providers/db/test",
               json={"name": "probe", "preset": "ollama", "protocol": "chat",
                     "base_url": "http://127.0.0.1:9/v1", "api_key": "",
                     "model": ""}).json()
    assert r["success"] is False
    assert r["error"]["code"] in ("PROVIDER_UNAVAILABLE", "CONNECTION_TIMEOUT",
                                 "INVALID_CONFIGURATION")
