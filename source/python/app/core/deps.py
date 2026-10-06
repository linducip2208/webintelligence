"""Shared infra: Redis client + DB init, both optional with graceful fallback."""
import os

_REDIS = {"client": "unset"}


def get_redis():
    """Return a redis client or None (cached). Never raises."""
    if _REDIS["client"] != "unset":
        return _REDIS["client"]
    try:
        import redis as redislib
        from .config import settings

        # protocol=2: RESP2 for old servers (Laragon redis 5.x speaks no RESP3);
        # harmless on new servers. Without it redis-py 8 sends HELLO and fails.
        r = redislib.Redis.from_url(settings.redis_url, socket_timeout=3, protocol=2)
        r.ping()
        _REDIS["client"] = r
        return r
    except Exception:
        _REDIS["client"] = None
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
