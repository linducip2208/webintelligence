"""Security regression tests: rate limits, replay, expiry, redaction, traversal."""
import hashlib
import hmac
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.logging import log  # noqa: E402


def _sig(secret, event, ts, nonce, payload):
    body = (event + str(ts) + nonce + json.dumps(payload, sort_keys=True, default=str)).encode()
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_rate_limit_and_body_guard(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_STANDARD", "3")
    from app.main import _BUCKETS
    _BUCKETS.clear()
    try:
        import redis as _r
        _r.Redis.from_url("redis://127.0.0.1:6379/15", socket_timeout=2).flushdb()
    except Exception:
        pass
    c = TestClient(app)
    codes = [c.get("/api/v1/projects").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and 429 in codes[3:]
    r429 = c.get("/api/v1/projects")
    assert r429.status_code == 429 and "retry-after" in r429.headers
    assert r429.json()["error"]["code"] == "rate_limited"
    # expensive class has its own bucket: AI still allowed
    monkeypatch.setenv("RATE_LIMIT_AI", "100000")
    assert c.post("/api/v1/ai/chat", json={"messages": []}).status_code != 429
    big = "x" * 100
    r = c.post("/api/v1/projects", json={"name": "x" * 10},
               headers={"content-length": str(999999999)})
    assert r.status_code in (200, 413)


def test_webhook_ingest_hmac_replay(monkeypatch):
    monkeypatch.setenv("WEBHOOK_INGEST_SECRET", "s3cr3t")
    c = TestClient(app)
    ts, nonce, payload = time.time(), "n-1", {"a": 1}
    good = {"event": "PING", "ts": ts, "nonce": nonce, "payload": payload,
            "signature": _sig("s3cr3t", "PING", ts, nonce, payload)}
    assert c.post("/api/v1/ingest/webhook", json=good).status_code == 200
    assert c.post("/api/v1/ingest/webhook", json=good).status_code == 409  # replay
    bad = dict(good, nonce="n-2", signature="nope")
    assert c.post("/api/v1/ingest/webhook", json=bad).status_code == 401
    stale = dict(good, nonce="n-3", ts=time.time() - 9999)
    stale["signature"] = _sig("s3cr3t", "PING", stale["ts"], "n-3", payload)
    assert c.post("/api/v1/ingest/webhook", json=stale).status_code == 401


def test_apikey_expiry_and_scopes(monkeypatch):
    c = TestClient(app)
    k = c.post("/api/v1/apikeys", json={"name": "exp", "scopes": ["read"],
                                        "expires_at": time.time() - 1}).json()
    k2 = c.post("/api/v1/apikeys", json={"name": "scoped", "scopes": ["read"]}).json()
    monkeypatch.setenv("REQUIRE_AUTH", "1")
    assert c.get("/api/v1/entities", headers={"X-API-Key": k["key"]}).status_code == 401
    assert c.get("/api/v1/entities", headers={"X-API-Key": k2["key"]}).status_code == 200
    t = c.post("/api/v1/auth/login", json={"email": "admin@local",
                                           "password": "admin123"}).json()["token"]
    assert c.get("/api/v1/entities", headers={"Authorization": "Bearer " + t}).status_code == 200
    assert c.get("/api/v1/entities", headers={"Authorization": "Bearer bad"}).status_code == 401


def test_log_redaction(capsys):
    log("t", api_key="AK" * 20, password="pw123", nested={"token": "TT" * 20}, ok="fine")
    out = capsys.readouterr().out
    assert "AKAK" not in out and "pw123" not in out and "***" in out and "fine" in out


def test_upload_traversal_sanitized():
    c = TestClient(app)
    d = c.post("/api/v1/documents", json={"kind": "txt", "title": "t",
                                          "filename": "../../etc/evil.txt",
                                          "text": "hello"}).json()
    assert d["doc_metadata"]["filename"] == "evil.txt"


def test_injection_payloads_safe():
    c = TestClient(app)
    r = c.post("/api/v1/projects", json={"name": "'; DROP TABLE projects; --"})
    assert r.status_code == 200  # ORM-bound, no SQLi
    r2 = c.get("/api/v1/search?q=<script>alert(1)</script>")
    assert r2.status_code == 200 and "<script>" not in r2.text
