"""Shared infra: Redis client + DB init, both optional with graceful fallback."""
import os

_REDIS = {"client": "unset", "url": None, "retry_at": 0.0}


def _redis_kwargs():
    kw = {"socket_timeout": 3}
    try:
        import inspect as _ins
        import redis as _rl
        # `protocol` (RESP version) exists only on redis-py >= 5.
        if "protocol" in _ins.signature(_rl.Redis.__init__).parameters:
            kw["protocol"] = 2
    except Exception:
        pass
    return kw


def get_redis():
    """Return a redis client or None. Never raises.

    Version-tolerant (works with redis-py 4 and 5+), reconnects when
    REDIS_URL changes, and retries a failed server instead of caching
    the failure forever.
    """
    import time as _t
    from .config import settings
    url = os.getenv("REDIS_URL", settings.redis_url)
    cached = _REDIS["client"]
    if cached is not None and cached != "unset" and _REDIS.get("url") == url:
        return cached
    if cached is None and _REDIS.get("url") == url and _t.time() < _REDIS.get("retry_at", 0.0):
        return None
    try:
        import redis as redislib
        r = redislib.Redis.from_url(url, **_redis_kwargs())
        r.ping()
        _REDIS.update(client=r, url=url)
        return r
    except Exception:
        _REDIS.update(client=None, url=url, retry_at=_t.time() + 5.0)
        return None


def redis_status():
    r = get_redis()
    return {"ok": r is not None}


def init_db():
    """Create tables if SQLAlchemy + DB reachable. Returns (ok, detail)."""
    try:
        from ..db.session import engine
        from ..db.base import Base
        from ..models import entities  # noqa: F401  (register tables)

        Base.metadata.create_all(bind=engine)
        return True, "tables ensured"
    except Exception as e:
        return False, str(e)[:300]


def data_dir():
    d = os.getenv("DATA_DIR", "data")
    os.makedirs(os.path.join(d, "raw"), exist_ok=True)
    return d
