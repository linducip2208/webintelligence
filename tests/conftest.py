"""Hermetic tests: force in-memory DB before app modules are imported."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("DEFAULT_PLAN", "enterprise")
# isolated Redis DB for tests (flush best-effort; falls back to memory anyway)
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/15"
try:
    import redis as _r

    def _flush():
        kw = {"socket_timeout": 2}
        try:
            import inspect
            if "protocol" in inspect.signature(_r.Redis.__init__).parameters:
                kw["protocol"] = 2
        except Exception:
            pass
        _r.Redis.from_url(os.environ["REDIS_URL"], **kw).flushdb()

    _flush()
except Exception:
    pass


def _iso():
    try:
        import redis as _r2

        _kw = {"socket_timeout": 2}
        try:
            import inspect as _ins
            if "protocol" in _ins.signature(_r2.Redis.__init__).parameters:
                _kw["protocol"] = 2
        except Exception:
            pass
        _r2.Redis.from_url("redis://127.0.0.1:6379/15", **_kw).flushdb()
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
