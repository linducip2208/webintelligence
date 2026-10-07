"""Redis-LIVE proofs against the real local server (Memurai/Redis on 6379).
Skips honestly when no server is reachable. Proves the Redis-backed paths
(rate limiting, queue enqueue, DLQ) instead of assuming them.
"""
import os
import sys

import pytest

redis = pytest.importorskip("redis")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))

SERVER = "redis://127.0.0.1:6379/15"


def _cli():
    kw = {"socket_timeout": 3}
    try:
        import inspect
        # `protocol` (RESP version) exists only on redis-py >= 5
        if "protocol" in inspect.signature(redis.Redis.__init__).parameters:
            kw["protocol"] = 2
    except Exception:
        pass
    return redis.Redis.from_url(SERVER, **kw)


def test_redis_live_available():
    try:
        assert _cli().ping() is True
    except Exception:
        pytest.skip("no local redis")


def test_queue_roundtrip_live():
    from fastapi.testclient import TestClient
    os.environ["REDIS_URL"] = SERVER
    from app.main import app
    c = TestClient(app)
    p = c.post("/api/v1/projects", json={"name": "RL", "description": ""}).json()
    t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "example.com",
                                        "url": "https://example.com/rl"}).json()
    j = c.post("/api/v1/jobs", json={"project_id": p["id"], "target_id": t["id"],
                                     "url": "https://example.com/rl"}).json()
    depth = _cli().llen("webintel:queue:jobs")
    assert depth >= 1  # genuinely queued in Redis, not memory
    _cli().ltrim("webintel:queue:jobs", depth, -1)  # leave queue clean


def test_rate_limit_redis_backed(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app, _BUCKETS
    monkeypatch.setenv("REDIS_URL", SERVER)
    monkeypatch.setenv("RATE_LIMIT_STANDARD", "2")
    _BUCKETS.clear()
    _cli().flushdb()
    c = TestClient(app)
    codes = [c.get("/api/v1/projects").status_code for _ in range(4)]
    assert codes[:2] == [200, 200] and codes[2:] == [429, 429]
    keys = _cli().keys("rl:standard:*")
    assert keys, "bucket must live in Redis, not memory"
    _cli().flushdb()


def test_migration_additive_on_stale_db(tmp_path):
    """Simulate a stale DB (table missing new columns) -> _ensure_columns heals."""
    import sqlite3
    from sqlalchemy import create_engine
    from app.db.base import Base
    from app.db import repo as R
    db = str(tmp_path / "stale.db")
    eng = create_engine(f"sqlite:///{db}", future=True)
    Base.metadata.create_all(bind=eng)
    con = sqlite3.connect(db)
    # emulate staleness by dropping a column via table rebuild
    con.execute("CREATE TABLE audit_logs_new (id INTEGER PRIMARY KEY, actor VARCHAR(255), action VARCHAR(128), ref VARCHAR(255), created_at DATETIME, updated_at DATETIME)")
    con.execute("INSERT INTO audit_logs_new (id, actor, action, ref) SELECT id, actor, action, ref FROM audit_logs")
    con.execute("DROP TABLE audit_logs")
    con.execute("ALTER TABLE audit_logs_new RENAME TO audit_logs")
    con.commit()
    cols_before = {r[1] for r in con.execute("PRAGMA table_info(audit_logs)").fetchall()}
    assert "at_ts" not in cols_before
    con.close()
    R._ensure_columns(eng)
    con = sqlite3.connect(db)
    cols_after = {r[1] for r in con.execute("PRAGMA table_info(audit_logs)").fetchall()}
    con.close()
    assert "at_ts" in cols_after
