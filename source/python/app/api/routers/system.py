"""system routes (split from main.py; behavior unchanged)."""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from ..shared import (
    HTTPException,
    Header,
    STORE,
    USERS,
    _audit,
    _ctx,
    _need,
    _require_auth,
    _secret,
    aireg,
    bright,
    dash,
    healthsvc,
    inc,
    muse,
    own_proxy,
    redis_status,
    render,
    repo,
    settings,
    time,
    tok,
    verify_password,
)

router = APIRouter()

# ---- auth ----
@router.post("/api/v1/auth/login")
def login(creds: dict):
    hit = repo.verify_user(creds.get("email", ""), creds.get("password", ""))
    if hit:
        _audit(hit["email"], "auth.login", "ok")
        return {"token": tok.issue(hit["email"], _secret()), "email": hit["email"]}
    u = USERS.get(creds.get("email", ""))
    if not u or not verify_password(creds.get("password", ""), u["password_hash"]):
        raise HTTPException(401, "bad credentials")
    _audit(creds.get("email", ""), "auth.login", "ok")
    return {"token": tok.issue(creds["email"], _secret()), "email": creds["email"]}


@router.get("/healthz")
def healthz():
    return {"status": "ok", "version": "1.0.0"}


@router.get("/readyz")
def readyz():
    checks = [
        healthsvc.check("api", True),
        healthsvc.check("redis", redis_status()["ok"], "connected" if redis_status()["ok"] else "memory fallback"),
        healthsvc.check("database", True, f"backend={repo.backend}"),
        healthsvc.check("own_proxy", bool(settings.own_proxy_urls)),
        healthsvc.check("brightdata", bright.configured),
        healthsvc.check("ai", bool(settings.muse_base_url and settings.muse_api_key)),
    ]
    live = [c for c in checks if c["name"] in ("api", "redis", "database")]
    status = "healthy" if all(c["status"] == "up" for c in live) else "degraded"
    STORE["health"].append({"at": time.time(), "status": status,
                            "checks": {c["name"]: c["status"] for c in checks}})
    return {"status": status, "checks": checks}


@router.get("/metrics")
def metrics():
    return JSONResponse(content=render(), media_type="text/plain")


# ---- proxies / brightdata ----
@router.get("/api/v1/proxies/health")
def proxy_health():
    return {"own": own_proxy.health_check(), "brightdata": bright.health_check()}


@router.post("/api/v1/brightdata/test")
def bright_test():
    return bright.test_connection()



# ---- AI ----
@router.get("/api/v1/ai/providers")
def ai_providers():
    return {"providers": aireg.names(), "models": [settings.muse_model]}


@router.post("/api/v1/ai/chat")
def ai_chat(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Evidence-first chat: optional spec.evidence is sanitized + wrapped as
    untrusted DATA; every call is usage/cost-tracked; fallback chain on error."""
    from ...ai import fallback as _fb
    from ...ai import safety as _safe
    from ...ai.factory import fallback_order
    from ...services import flags as _fl
    email0, org0, _ = _ctx(authorization, x_api_key)
    if not _fl.is_enabled(repo, "ai", org0, email0):
        raise HTTPException(403, "ai disabled by feature flag")
    _require_auth(authorization, x_api_key)
    messages = list(spec.get("messages", []))
    model = spec.get("model", "")
    provider = spec.get("provider", "")
    if spec.get("evidence"):
        messages = messages + [{"role": "user",
                                "content": _safe.wrap_evidence(spec["evidence"])}]
    use_model = model or settings.muse_model
    chain = []
    db_name = provider[3:] if provider.startswith("db:") else provider
    dbp = next((x for x in STORE["ai_providers"]
                if x.get("name") == db_name and x.get("enabled")), None) if provider else None
    if dbp:
        from ...core.crypto import decrypt
        from ...ai.muse_provider import MuseSparkProvider
        chain = [(dbp["name"], MuseSparkProvider(
            dbp.get("base_url", ""), decrypt(dbp.get("api_key_enc", "")),
            dbp.get("model", "") or use_model))]
        use_model = dbp.get("model", "") or use_model
    elif provider:
        p0 = aireg.get(provider)
        if not p0:
            raise HTTPException(404, f"unknown provider {provider}")
        chain = [(provider, p0)]
    else:
        names = fallback_order() or ["muse-spark", "openai", "anthropic", "google", "ollama"]
        chain = [(n, aireg.get(n)) for n in names]
    out = _fb.chat_fallback(chain, messages, use_model)
    _record_usage(out)
    inc("AI_requests")
    return out


def _record_usage(out: dict):
    try:
        name = out.get("provider", "muse-spark")
        p = aireg.get(name)
        cost = p.estimate_cost(out.get("input_tokens", 0), out.get("output_tokens", 0)) if p else 0.0
        STORE["ai_usage"].append({"provider": name, "model": out.get("model", ""),
                                  "input_tokens": out.get("input_tokens", 0),
                                  "output_tokens": out.get("output_tokens", 0),
                                  "cost": cost, "latency_ms": out.get("latency_ms", 0)})
        inc("AI_tokens", out.get("input_tokens", 0) + out.get("output_tokens", 0))
    except Exception:
        pass


@router.get("/api/v1/ai/usage", tags=["admin"])
def ai_usage():
    items = STORE["ai_usage"]
    return {"calls": len(items),
            "input_tokens": sum(i.get("input_tokens", 0) for i in items),
            "output_tokens": sum(i.get("output_tokens", 0) for i in items),
            "cost": round(sum(i.get("cost", 0) for i in items), 6),
            "by_provider": {n: sum(1 for i in items if i.get("provider") == n)
                            for n in {i.get("provider") for i in items}}}


@router.get("/api/v1/ai/models", tags=["admin"])
def ai_models(provider: str = ""):
    p = aireg.get(provider) if provider else None
    if provider and not p:
        raise HTTPException(404, f"unknown provider {provider}")
    if p:
        return {"provider": provider, **p.list_models()}
    return {n: aireg.get(n).list_models() for n in aireg.names()}


@router.get("/api/v1/ai/prompts", tags=["admin"])
def ai_prompts():
    from ...ai import prompts as _pr
    return {"prompts": _pr.catalog()}


@router.get("/api/v1/flags", tags=["admin"])
def flags_list():
    from ...services import flags as _fl
    return {"flags": _fl.DEFAULTS}


@router.post("/api/v1/flags", tags=["admin"])
def flags_set(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import flags as _fl
    email, _, _ = _need(authorization, "configure")
    out = _fl.set_flag(repo, spec.get("name", ""), spec.get("on", True),
                       spec.get("scope", "global"), str(spec.get("ref", "")))
    _audit(email, "flag.set", f"{out['name']}={out['on']}")
    return out


@router.post("/api/v1/admin/retention/run", tags=["admin"])
def retention_run(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Delete aged operational rows per policy. Audited. Canonical
    entities/evidence are never touched unless explicitly listed."""
    import time as _t
    email, _, _ = _need(authorization, "configure")
    days = float(spec.get("older_than_days", 90))
    cutoff = _t.time() - days * 86400
    policies = {"raw": ("at", "content_hash", "hash"),
                "history": ("at", "key", "key"),
                "events": ("observed_at", "id", "id")}
    removed = {}
    for coll in spec.get("collections", ["raw", "history"]):
        if coll not in policies:
            continue
        field, dbkey, itemkey = policies[coll]
        victims = [x for x in STORE[coll]
                   if isinstance(x.get(field), (int, float)) and x[field] < cutoff]
        for v in victims:
            STORE[coll].remove(v)
            try:
                repo.delete(coll, v.get(itemkey), dbkey)
            except Exception:
                pass
        removed[coll] = len(victims)
    _audit(email, "retention.run", f"{days}d:{removed}")
    return {"removed": removed, "cutoff_days": days}


@router.get("/api/v1/ai/health")
def ai_health():
    return muse.health_check()


@router.get("/api/v1/browser/health", tags=["sources"])
def browser_health():
    try:
        from ...browser.worker import pool_status
        return pool_status()
    except Exception as e:
        return {"installed": False, "error": str(e)[:200]}


@router.get("/api/version")
def api_version():
    return {"app": "universal-intelligence", "api": "v1", "version": "2.5.0",
            "contracts": {"jobs": "1.0", "results": "1.0", "events": "1.0"},
            "deprecation": "v1 stable; no deprecation scheduled"}


@router.get("/api/v1/system/doctor", tags=["admin"])
def system_doctor():
    import shutil as _sh
    checks = []
    try:
        import sqlalchemy  # noqa
        checks.append({"name": "database", "ok": True, "detail": f"backend={repo.backend}"})
    except ImportError:
        checks.append({"name": "database", "ok": False, "detail": "sqlalchemy missing",
                       "action": "pip install -r requirements.txt"})
    checks.append({"name": "redis", "ok": _redis_ok(),
                   "detail": "connected" if _redis_ok() else "fallback: memory queue"})
    try:
        from ...browser.worker import pool_status as _ps
        ps = _ps()
        checks.append({"name": "browser", "ok": ps["installed"],
                       "detail": "pool=%s alive=%s" % (ps["pool"], ps["browser_alive"]),
                       "action": None if ps["installed"] else "pip install playwright"})
    except Exception as e:
        checks.append({"name": "browser", "ok": False, "detail": str(e)[:160]})
    try:
        du = _sh.disk_usage(".")
        checks.append({"name": "disk", "ok": du.free > 100 * 1024 * 1024,
                       "detail": f"free={du.free // 1024 // 1024}MB"})
    except Exception as e:
        checks.append({"name": "disk", "ok": False, "detail": str(e)[:120]})
    checks.append({"name": "migrations", "ok": True,
                   "detail": f"{len(repo.engine.table_names()) if hasattr(repo.engine, 'table_names') else '?'} tables"})
    sec = {"require_auth": __import__("os").getenv("REQUIRE_AUTH", "0") == "1",
           "credentials_key": bool(__import__("os").getenv("CREDENTIALS_KEY", ""))}
    checks.append({"name": "security-config", "ok": sec["require_auth"],
                   "detail": str(sec),
                   "action": None if sec["require_auth"] else "set REQUIRE_AUTH=1 in production"})
    return {"healthy": all(c["ok"] for c in checks), "checks": checks}


def _redis_ok():
    try:
        from ...core.deps import redis_status
        return bool(redis_status()["ok"])
    except Exception:
        return False


@router.post("/api/v1/ai/providers/db", tags=["admin"])
def ai_provider_create(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...core.crypto import encrypt
    email, _, _ = _need(authorization, "configure")
    if not spec.get("name") or not spec.get("base_url"):
        raise HTTPException(400, "name and base_url required")
    if any(x.get("name") == spec["name"] for x in STORE["ai_providers"]):
        raise HTTPException(409, "provider exists")
    item = {"id": len(STORE["ai_providers"]) + 1, "name": spec["name"],
            "base_url": spec["base_url"],
            "api_key_enc": encrypt(spec.get("api_key", "")),
            "model": spec.get("model", ""), "enabled": True}
    STORE["ai_providers"].append(item)
    _audit(email, "ai.provider.create", item["name"])
    return {k: v for k, v in item.items() if k != "api_key_enc"}


@router.get("/api/v1/ai/providers/db", tags=["admin"])
def ai_provider_list():
    return {"items": [{k: v for k, v in x.items() if k != "api_key_enc"}
                      for x in STORE["ai_providers"]]}


@router.post("/api/v1/ai/providers/db/{pid}/disable", tags=["admin"])
def ai_provider_disable(pid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _need(authorization, "configure")
    p = next((x for x in STORE["ai_providers"] if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "not found")
    p["enabled"] = False
    repo.sync("ai_providers", p)
    _audit(email, "ai.provider.disable", p["name"])
    return {"ok": True}



# ---- i18n ----
@router.get("/api/v1/i18n", tags=["admin"])
def get_strings(lang: str = "en"):
    from ...i18n.lang import STRINGS, langs
    return {"lang": lang, "strings": STRINGS.get(lang, STRINGS["en"]), "langs": langs()}



# ---- dashboard ----
@router.get("/api/v1/dashboard")
def dashboard():
    return dash.build(STORE["jobs"], STORE["alerts"], STORE["prices"],
                      STORE["health"], {"estimated": sum(
                          j.get("estimated_cost", 0) for j in STORE["jobs"])})

