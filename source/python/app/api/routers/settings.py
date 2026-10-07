"""Workspace settings: real persisted defaults + live system facts.

Only settings with genuine storage or genuine effect live here:
- defaults: search mode/limit and investigation scope, consumed by the
  search console and the New Investigation wizard (verified by tests).
- system: live facts (version, env, backends, counts) for the System section.
Appearance/language/theme stay client-side (localStorage) by design.
"""
from fastapi import APIRouter, Header

from ..shared import (
    HTTPException,
    Header,
    STORE,
    _need,
    repo,
)

router = APIRouter()

DEFAULTS_KEY = "ui:defaults"
DEFAULTS = {"search_mode": "hybrid", "search_limit": 20,
            "ni_scope": ["dns", "subdomains", "tls", "tech"],
            "timezone": "Asia/Jakarta"}
SCOPES = {"dns", "subdomains", "tls", "tech", "content", "infra",
          "entities", "documents", "threat", "risk"}
MODES = {"hybrid", "keyword", "semantic", "exact"}


def _valid_tz(name: str) -> bool:
    try:
        import zoneinfo
        zoneinfo.ZoneInfo(name or "")
        return True
    except Exception:
        return False


def _read():
    try:
        saved = repo.kv_get(DEFAULTS_KEY, {}) or {}
    except Exception:
        saved = {}
    out = dict(DEFAULTS)
    out.update({k: v for k, v in saved.items() if k in DEFAULTS})
    return out


@router.get("/api/v1/settings/defaults")
def settings_defaults_get():
    return _read()


@router.patch("/api/v1/settings/defaults")
def settings_defaults_patch(spec: dict, authorization: str = Header(""),
                            x_api_key: str = Header("")):
    email, _, _ = _need(authorization, "configure", x_api_key)
    cur = _read()
    if "search_mode" in spec:
        if spec["search_mode"] not in MODES:
            raise HTTPException(400, "search_mode must be hybrid|keyword|semantic|exact")
        cur["search_mode"] = spec["search_mode"]
    if "search_limit" in spec:
        try:
            n = int(spec["search_limit"])
        except (TypeError, ValueError):
            raise HTTPException(400, "search_limit must be a number")
        if not 5 <= n <= 100:
            raise HTTPException(400, "search_limit must be 5..100")
        cur["search_limit"] = n
    if "ni_scope" in spec:
        scope = spec["ni_scope"] or []
        if not isinstance(scope, list) or not scope or any(s not in SCOPES for s in scope):
            raise HTTPException(400, "ni_scope must be a non-empty list of known scopes")
        cur["ni_scope"] = scope
    if "timezone" in spec:
        if not _valid_tz(spec["timezone"]):
            raise HTTPException(400, "unknown timezone")
        cur["timezone"] = spec["timezone"]
    try:
        repo.kv_set(DEFAULTS_KEY, cur)
    except Exception as e:
        raise HTTPException(500, f"could not save defaults: {e}"[:200])
    from ..shared import _audit
    _audit(email, "settings.defaults.update", str(sorted(cur)))
    return cur


@router.post("/api/v1/settings/reset")
def settings_reset(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Reset workspace UI defaults to factory values (confirmation happens
    in the UI). Only the ui:defaults key is touched."""
    email, _, _ = _need(authorization, "configure", x_api_key)
    try:
        repo.kv_set(DEFAULTS_KEY, dict(DEFAULTS))
    except Exception as e:
        raise HTTPException(500, f"could not reset defaults: {e}"[:200])
    from ..shared import _audit
    _audit(email, "settings.defaults.reset", "ui:defaults")
    return dict(DEFAULTS)


@router.get("/api/v1/settings/system")
def settings_system():
    import platform as _pf
    from ...core.deps import get_redis, redis_status
    r = get_redis()
    try:
        from ...search.semantic import get_index
        index_docs = len(get_index().docs)
    except Exception:
        index_docs = -1
    from ...main import app as _app
    import os as _o
    return {
        "app_version": _app.version, "api": "v1",
        "env": _o.getenv("ENV", "dev"),
        "python": _pf.python_version(),
        "database": {"backend": getattr(repo, "backend", "?")},
        "redis": {"connected": r is not None, **redis_status()},
        "search_index_documents": index_docs,
        "ai_providers_configured": len(STORE.get("ai_providers", [])),
        "counts": {k: len(STORE.get(k, [])) for k in
                   ("projects", "targets", "jobs", "investigations", "cases",
                    "entities", "findings", "evidence", "reports")},
    }
