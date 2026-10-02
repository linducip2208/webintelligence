"""FastAPI entrypoint: app wiring only (Phase 52 refactor).

Business logic lives in api/shared.py (store, auth, execution) and
api/routers/*.py. Behavior and contracts are unchanged from the monolith.
"""
import os as _os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .api.shared import _rate_ok, _key_lookup, _secret, tok, STORE, get_redis
from .api.routers import system, catalog, collection, intel, knowledge, ops

app = FastAPI(title="Web Intelligence Platform", version="2.0.0",
              description="Universal Intelligence Platform. Auth: Bearer login token "
                          "(POST /api/v1/auth/login) or X-API-Key header with scopes. "
                          "Mutating routes return 401 without credentials when REQUIRE_AUTH=1, "
                          "403 when role/scopes lack the action. All errors are JSON.")

_STATIC = _os.path.join(_os.path.dirname(__file__), "static")
if _os.path.isdir(_STATIC):
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def _index():
        return FileResponse(_os.path.join(_STATIC, "index.html"))


@app.middleware("http")
async def _guard(request, call_next):
    import os as _o
    import time as _t
    rid = request.headers.get("x-request-id", "") or __import__("uuid").uuid4().hex[:12]
    request.state.request_id = rid
    if request.url.path.startswith("/api/v1"):
        import app.api.shared as _sh
        if _sh.repo.env == "production" and not _sh.repo.available and request.url.path not in (
                "/api/v1/auth/login",):
            return JSONResponse({"error": {"code": "db_unavailable",
                                           "message": f"database unavailable: {_sh.repo.boot_error}",
                                           "request_id": rid}}, status_code=503)
        try:
            maxb = int(_o.getenv("MAX_BODY_BYTES", "10485760") or 10485760)
        except ValueError:
            maxb = 10485760
        if request.headers.get("content-length") and int(request.headers["content-length"]) > maxb:
            return JSONResponse({"error": {"code": "too_large", "message": "payload too large",
                                           "request_id": rid}}, status_code=413)
        if _o.getenv("REQUIRE_AUTH", "") == "1" and request.url.path not in (
                "/api/v1/auth/login", "/api/v1/ingest/webhook"):
            auth = request.headers.get("authorization", "")
            key = request.headers.get("x-api-key", "")
            ok = False
            if auth.startswith("Bearer ") and tok.verify(auth[7:], _secret()):
                ok = True
            if key and _key_lookup(key):
                ok = True
            if not ok:
                return JSONResponse({"error": {"code": "unauthorized", "message": "unauthorized",
                                               "request_id": rid}}, status_code=401)
        allowed, retry_after = _quota(request)
        if not allowed:
            return JSONResponse({"error": {"code": "rate_limited", "message": "rate limit exceeded",
                                           "request_id": rid}},
                                status_code=429, headers={"Retry-After": str(retry_after)})
    resp = await call_next(request)
    resp.headers["X-Request-ID"] = rid
    return resp


COST_CLASSES = [
    ("/api/v1/ai", "ai", 30),
    ("/api/v1/research", "research", 30),
    ("/api/v1/graph/render", "browser", 30),
    ("/api/v1/documents", "browser", 30),
    ("/api/v1/analytics", "analytics", 100),
    ("/api/v1/intel", "analytics", 100),
    ("/api/v1/search", "search", 200),
    ("/api/v1/reports", "export", 20),
    ("/api/v1/datasets", "export", 20),
    ("/api/v1/webhooks", "webhook", 100),
    ("/api/v1/ingest", "webhook", 100),
]
_DEFAULT_LIMIT = 300


def _cost_class(path: str):
    for prefix, cls, limit in COST_CLASSES:
        if path.startswith(prefix):
            return cls, _env_limit(cls, limit)
    return "standard", _env_limit("standard", _DEFAULT_LIMIT)


def _env_limit(cls: str, default: int) -> int:
    import os as _o
    try:
        return int(_o.getenv(f"RATE_LIMIT_{cls.upper()}", str(default)) or default)
    except ValueError:
        return default


def _identity(request) -> str:
    """org > api-key > user > ip. Separate buckets per identity, no bypass by rotation within one identity."""
    key = request.headers.get("x-api-key", "")
    if key:
        k = _key_lookup(key)
        if k:
            return f"key:{k['org_id']}:{k['name']}"
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        email = tok.verify(auth[7:], _secret())
        if email:
            try:
                ms = [m for m in STORE["memberships"] if m["email"] == email]
                org = ms[0]["org_id"] if ms else 0
            except Exception:
                org = 0
            return f"user:{org}:{email}"
    ip = request.client.host if request.client else "?"
    return f"ip:{ip}"


def _quota(request):
    """(allowed, retry_after_s). Redis-backed when available, else memory."""
    import time as _t
    cls, limit = _cost_class(request.url.path)
    ident = _identity(request)
    bucket = f"rl:{cls}:{ident}"
    r = get_redis()
    if r is not None:
        try:
            n = int(r.incr(bucket))
            if n == 1:
                r.expire(bucket, 60)
            ttl = int(r.ttl(bucket) or 60)
            return n <= limit, max(ttl, 0)
        except Exception:
            pass
    now = _t.time()
    b = _BUCKETS.get(bucket)
    if not b or now - b["ts"] > 60:
        b = {"n": 0, "ts": now}
        _BUCKETS[bucket] = b
    if len(_BUCKETS) > 20000:
        _BUCKETS.clear()
    b["n"] += 1
    return b["n"] <= limit, max(0, int(60 - (now - b["ts"])))


def _rate_ok(ip: str) -> bool:
    import time as _t
    now = _t.time()
    b = _BUCKETS.get("legacy:" + ip)
    if not b or now - b["ts"] > 60:
        b = {"n": 0, "ts": now}
        _BUCKETS["legacy:" + ip] = b
    b["n"] += 1
    return True


for _r in (system, catalog, collection, intel, knowledge, ops):
    app.include_router(_r.router)


@app.exception_handler(RuntimeError)
async def _runtime_handler(request, exc):
    import uuid as _u
    rid = getattr(request.state, "request_id", "") or _u.uuid4().hex[:12]
    msg = str(exc)
    if msg.startswith("db-unavailable"):
        return JSONResponse({"error": {"code": "db_unavailable", "message": msg,
                                       "request_id": rid}}, status_code=503)
    return JSONResponse({"error": {"code": "internal", "message": "internal error",
                                   "request_id": rid}}, status_code=500)


@app.exception_handler(HTTPException)
async def _http_handler(request, exc):
    import uuid as _u
    from fastapi import HTTPException as _H
    rid = getattr(request.state, "request_id", "") or _u.uuid4().hex[:12]
    codes = {400: "bad_request", 401: "unauthorized", 403: "forbidden",
             404: "not_found", 409: "conflict", 413: "too_large",
             422: "validation", 429: "rate_limited", 501: "unavailable",
             502: "bad_gateway", 503: "unavailable"}
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)[:500]
    return JSONResponse({"error": {"code": codes.get(exc.status_code, "error"),
                                   "message": detail, "request_id": rid}},
                        status_code=exc.status_code,
                        headers={"X-Request-ID": rid})

# compat re-exports (tests, workers, scripts import from app.main)
from .api.shared import STORE, repo, USERS, _BUCKETS  # noqa: E402,F401
