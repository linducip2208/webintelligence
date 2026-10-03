"""Hermetic tests: force in-memory DB before app modules are imported."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("DEFAULT_PLAN", "enterprise")
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/15"
try:
    import redis as _r
    _r.Redis.from_url(os.environ["REDIS_URL"], socket_timeout=2).flushdb()
except Exception:
    pass


def _iso():
    try:
        import redis as _r2
        _r2.Redis.from_url("redis://127.0.0.1:6379/15", socket_timeout=2).flushdb()
    except Exception:
        pass
    try:
        from app.main import _BUCKETS
        _BUCKETS.clear()
    except Exception:
        pass


try:
    import pytest as _pt

    @_pt.fixture(autouse=True)
    def _isolate_backend():
        _iso()
        yield
        _iso()
except ImportError:
    pass
