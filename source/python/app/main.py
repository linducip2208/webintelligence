"""FastAPI entrypoint: app wiring only (Phase 52 refactor).

Business logic lives in api/shared.py (store, auth, execution) and
api/routers/*.py. Behavior and contracts are unchanged from the monolith.
"""
import os as _os

from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .api.shared import _rate_ok, _key_lookup, _secret, tok
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
    if request.url.path.startswith("/api/v1"):
        try:
            maxb = int(_o.getenv("MAX_BODY_BYTES", "10485760") or 10485760)
        except ValueError:
            maxb = 10485760
        if request.headers.get("content-length") and int(request.headers["content-length"]) > maxb:
            return JSONResponse({"detail": "payload too large"}, status_code=413)
        ip = (request.client.host if request.client else "?")
        if not _rate_ok(ip):
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
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
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
    return await call_next(request)


for _r in (system, catalog, collection, intel, knowledge, ops):
    app.include_router(_r.router)

# compat re-exports (tests, workers, scripts import from app.main)
from .api.shared import STORE, repo, USERS, _BUCKETS  # noqa: E402,F401
