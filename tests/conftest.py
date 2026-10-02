"""Hermetic tests: force in-memory DB before app modules are imported."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("DEFAULT_PLAN", "enterprise")
# isolated Redis DB for tests (flush best-effort; falls back to memory anyway)
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/15"
try:
    import redis as _r
    _r.Redis.from_url(os.environ["REDIS_URL"], socket_timeout=2).flushdb()
except Exception:
    pass
