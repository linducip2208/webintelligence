"""system routes (split from main.py; behavior unchanged)."""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from ..shared import (
    HTTPException,
    Header,
    STORE,
    USERS,
    _audit,
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
    _require_auth(authorization, x_api_key)
    messages = spec.get("messages", [])
    model = spec.get("model", "")
    provider = spec.get("provider", "")
    p = aireg.get("muse-spark")
    use_model = model or settings.muse_model
    if provider:
        from ...core.crypto import decrypt
        dbp = next((x for x in STORE["ai_providers"]
                    if x.get("name") == provider and x.get("enabled")), None)
        if not dbp:
            raise HTTPException(404, "provider not found/disabled")
        from ...ai.muse_provider import MuseSparkProvider
        p = MuseSparkProvider(dbp.get("base_url", ""), decrypt(dbp.get("api_key_enc", "")),
                              dbp.get("model", "") or use_model)
        use_model = dbp.get("model", "") or use_model
    if not p:
        raise HTTPException(503, "no ai provider registered")
    inc("AI_requests")
    return p.chat(messages, use_model)


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

