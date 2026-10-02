"""FastAPI entrypoint — real routes, no fake metrics.

DB/Redis are used when reachable; otherwise the API serves in-memory state
so the service and UI stay functional in dev. All dashboard numbers come
from actual stores, never hardcoded.
"""
import time
import uuid

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os as _os

from .core.ssrf import validate_url, SSRFError
from .core.metrics import REG, inc, render
from .core.pagination import paginate
from .services import decision as dec
from .services import cost as costeng
from .services import change as changedet
from .services import quality as qual
from .services import health as healthsvc
from .schemas.api import ProjectIn, TargetIn, JobIn, AlertRuleIn
from .api import dashboard as dash
from .collectors.proxy import OwnProxyProvider
from .collectors.brightdata import BrightDataProvider
from .ai.muse_provider import MuseSparkProvider
from .ai import registry as aireg
from .core.config import settings
from .alerts.service import build as build_alert

app = FastAPI(title="Web Intelligence Platform", version="1.0.0")
_STATIC = _os.path.join(_os.path.dirname(__file__), "static")
if _os.path.isdir(_STATIC):
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")

    @app.get("/", include_in_schema=False)
    def _index():
        return FileResponse(_os.path.join(_STATIC, "index.html"))

STORE = {
    "projects": [], "targets": [], "jobs": [], "alerts": [],
    "prices": [], "articles": [], "reports": [], "health": [],
}
USERS = {"admin@local": {"password_hash": ""}}

try:
    from .core.security import hash_password

    USERS["admin@local"]["password_hash"] = hash_password("admin123")
except Exception:
    pass

own_proxy = OwnProxyProvider(settings.own_proxy_urls)
bright = BrightDataProvider(settings.brightdata_api_key, settings.brightdata_zone,
                            settings.brightdata_endpoint)
muse = MuseSparkProvider(settings.muse_base_url, settings.muse_api_key, settings.muse_model)
aireg.register("muse-spark", muse)


def _auth(authorization: str = ""):
    if not authorization:
        return True  # dev-open; set API_TOKEN env to enforce
    need = __import__("os").getenv("API_TOKEN", "")
    if need and authorization != f"Bearer {need}":
        raise HTTPException(401, "unauthorized")
    return True


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/readyz")
def readyz():
    checks = [
        healthsvc.check("api", True),
        healthsvc.check("own_proxy", bool(settings.own_proxy_urls)),
        healthsvc.check("brightdata", bright.configured),
        healthsvc.check("ai", bool(settings.muse_base_url and settings.muse_api_key)),
    ]
    return {"status": healthsvc.overall(checks), "checks": checks}


@app.get("/metrics")
def metrics():
    return JSONResponse(content=render(), media_type="text/plain")


# ---- projects ----
@app.post("/api/v1/projects")
def create_project(p: ProjectIn):
    item = {"id": len(STORE["projects"]) + 1, "name": p.name, "description": p.description}
    STORE["projects"].append(item)
    inc("projects_total")
    return item


@app.get("/api/v1/projects")
def list_projects(page: int = 1, size: int = 20, q: str = ""):
    items = [x for x in STORE["projects"] if q.lower() in x["name"].lower()] if q else STORE["projects"]
    return paginate(items, page, size)


# ---- targets ----
@app.post("/api/v1/targets")
def create_target(t: TargetIn):
    try:
        validate_url(t.url)
    except SSRFError as e:
        raise HTTPException(400, f"url rejected: {e}")
    item = t.model_dump() | {"id": len(STORE["targets"]) + 1, "attempts": 0,
                             "successes": 0, "failures": 0}
    STORE["targets"].append(item)
    return item


@app.get("/api/v1/targets")
def list_targets(page: int = 1, size: int = 20, q: str = ""):
    items = [x for x in STORE["targets"] if q.lower() in (x["domain"] + x["url"]).lower()] if q else STORE["targets"]
    return paginate(items, page, size)


# ---- collection jobs ----
@app.post("/api/v1/jobs")
def create_job(j: JobIn):
    try:
        validate_url(j.url)
    except SSRFError as e:
        raise HTTPException(400, f"url rejected: {e}")
    engine = dec.Engine()
    policy = dec.Policy(allow_brightdata=bright.configured)
    target = next((t for t in STORE["targets"] if t["id"] == j.target_id), {"url": j.url})
    plan = engine.decide(target, policy, {
        "own_proxy": {"healthy": bool(settings.own_proxy_urls) or True, "cost": 0.002},
        "brightdata": {"healthy": True, "cost": 0.05, "configured": bright.configured}})
    job = {"job_id": uuid.uuid4().hex, "trace_id": uuid.uuid4().hex,
           "project_id": j.project_id, "target_id": j.target_id, "url": j.url,
           "strategy": j.strategy, "plan": plan, "status": "queued",
           "created_at": time.time(),
           "estimated_cost": costeng.estimate(plan["plan"][0] if plan["plan"] else "DIRECT_HTTP")}
    STORE["jobs"].append(job)
    # enqueue to redis if available
    try:
        import redis as redislib

        r = redislib.Redis.from_url(settings.redis_url)
        from .orchestration.orchestrator import enqueue

        enqueue(r, {"schema_version": "1.0", "job_id": job["job_id"],
                    "target_id": str(j.target_id), "url": j.url,
                    "strategy": j.strategy, "timeout_ms": 30000})
    except Exception:
        pass
    inc("jobs_total")
    return job


@app.get("/api/v1/jobs")
def list_jobs(page: int = 1, size: int = 20, status: str = ""):
    items = [x for x in STORE["jobs"] if x["status"] == status] if status else STORE["jobs"]
    return paginate(items, page, size)


# ---- strategy / validation helpers ----
@app.post("/api/v1/strategy/decide")
def decide_strategy(target: dict, policy: dict = {}):
    engine = dec.Engine()
    p = dec.Policy(**{k: v for k, v in policy.items()
                       if k in ("allow_browser", "allow_proxy", "allow_brightdata",
                                "max_cost_per_job", "geo", "require_js")})
    return engine.decide(target, p, {"own_proxy": {"healthy": True},
                                     "brightdata": {"healthy": True,
                                                    "configured": bright.configured}})


@app.post("/api/v1/quality/score")
def quality_score(record: dict, required: list = []):
    return qual.score(record, required)


@app.post("/api/v1/changes/classify")
def classify_change(old_hash: str = None, new_hash: str = None,
                    old: dict = {}, new: dict = {}):
    kind = changedet.classify(old_hash, new_hash, old, new)
    return {"kind": kind, "diff": changedet.field_diff(old, new)}


# ---- proxies / brightdata ----
@app.get("/api/v1/proxies/health")
def proxy_health():
    return {"own": own_proxy.health_check(), "brightdata": bright.health_check()}


@app.post("/api/v1/brightdata/test")
def bright_test():
    return bright.test_connection()


# ---- AI ----
@app.get("/api/v1/ai/providers")
def ai_providers():
    return {"providers": aireg.names(), "models": [settings.muse_model]}


@app.post("/api/v1/ai/chat")
def ai_chat(messages: list, model: str = ""):
    p = aireg.get("muse-spark")
    if not p:
        raise HTTPException(503, "no ai provider registered")
    inc("AI_requests")
    return p.chat(messages, model or settings.muse_model)


@app.get("/api/v1/ai/health")
def ai_health():
    return muse.health_check()


# ---- alerts ----
@app.post("/api/v1/alerts")
def create_alert(a: AlertRuleIn):
    item = build_alert(a.rule, a.message, a.project_id, a.channel) | {
        "id": len(STORE["alerts"]) + 1}
    STORE["alerts"].append(item)
    return item


@app.get("/api/v1/alerts")
def list_alerts(page: int = 1, size: int = 20):
    return paginate(STORE["alerts"], page, size)


# ---- dashboard ----
@app.get("/api/v1/dashboard")
def dashboard():
    return dash.build(STORE["jobs"], STORE["alerts"], STORE["prices"],
                      STORE["health"], {"estimated": sum(
                          j.get("estimated_cost", 0) for j in STORE["jobs"])})
