"""FastAPI entrypoint — real routes, no fake metrics.

MySQL/Redis are used when reachable; otherwise in-memory state keeps the
service and UI functional. All dashboard numbers come from actual stores.
"""
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os as _os

from .core.ssrf import validate_url, SSRFError
from .core.metrics import inc, render
from .core.pagination import paginate
from .core.deps import get_redis, redis_status, init_db, data_dir
from .services import decision as dec
from .services import cost as costeng
from .services import change as changedet
from .services import quality as qual
from .services import health as healthsvc
from .services import pipeline as pipe
from .services import scheduler as sched
from .schemas.api import ProjectIn, TargetIn, JobIn, AlertRuleIn
from .api import dashboard as dash
from .collectors.proxy import OwnProxyProvider
from .collectors.brightdata import BrightDataProvider
from .ai.muse_provider import MuseSparkProvider
from .ai import registry as aireg
from .core.config import settings
from .alerts.service import build as build_alert
from .auth import tokens as tok
from .core.security import hash_password, verify_password

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
    "schedules": [], "raw": [], "changes": [],
}
USERS = {"admin@local": {"password_hash": hash_password("admin123")}}

DB_OK, DB_DETAIL = init_db()

own_proxy = OwnProxyProvider(settings.own_proxy_urls)
bright = BrightDataProvider(settings.brightdata_api_key, settings.brightdata_zone,
                            settings.brightdata_endpoint)
muse = MuseSparkProvider(settings.muse_base_url, settings.muse_api_key, settings.muse_model)
aireg.register("muse-spark", muse)


def _secret():
    return settings.secret_key or "dev-secret"


def _require_auth(authorization: str = ""):
    if os.getenv("REQUIRE_AUTH", "") != "1":
        return "dev-open"
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    email = tok.verify(authorization[7:], _secret())
    if not email:
        raise HTTPException(401, "invalid/expired token")
    return email


def _providers():
    return {"own_proxy": {"healthy": True, "cost": 0.002},
            "brightdata": {"healthy": True, "cost": 0.05,
                           "configured": bright.configured}}


def _apply_result(res: dict, job_url: str, project_id: int, target_id: int):
    """Persist a pipeline/collector result bundle into STORE. Shared by
    inline runs, /results ingestion, and worker ticks."""
    job = next((j for j in STORE["jobs"] if j.get("job_id") == res.get("job_id")), None)
    if job:
        job["status"] = res.get("status", job["status"])
        job["finished_at"] = time.time()
        job["actual_cost"] = res.get("cost", 0)
    if res.get("content_hash"):
        STORE["raw"].append({"job_id": res.get("job_id"), "url": job_url,
                             "hash": res["content_hash"], "size": res.get("content_size", 0),
                             "strategy": res.get("strategy"), "at": time.time()})
    for p in res.get("prices", []):
        STORE["prices"].append({"product_id": target_id, "price": p["price"],
                                "currency": p.get("currency", "USD"), "seller": "",
                                "observed_at": time.time(), "job_id": res.get("job_id")})
    if res.get("change") in ("CHANGED", "NEW"):
        STORE["changes"].append({"target_id": target_id, "kind": res["change"],
                                 "diff": res.get("diagnostics", {}), "at": time.time()})
    for a in res.get("alerts", []):
        STORE["alerts"].append({"id": len(STORE["alerts"]) + 1, **a,
                                "project_id": project_id, "is_read": False})
    if res.get("status") == "success":
        inc("jobs_success")
    elif res.get("status") in ("failed",):
        inc("jobs_failed")
    return res


def _execute_job(job: dict):
    target = next((t for t in STORE["targets"] if t["id"] == job["target_id"]), {"url": job["url"]})
    last = [p for p in STORE["prices"] if p.get("product_id") == job["target_id"]][-3:]
    res = pipe.run_job(job, target, last,
                       dec.Policy(allow_brightdata=bright.configured),
                       _providers())
    if res.get("content_hash") and res.get("status") == "success":
        try:
            body = b""  # body already hashed; raw bytes live with collector/browser
            path = os.path.join(data_dir(), "raw", res["content_hash"])
            if not os.path.exists(path):
                open(path, "wb").write(body)
        except Exception:
            pass
    return _apply_result(res, job["url"], job["project_id"], job["target_id"])


# ---- auth ----
@app.post("/api/v1/auth/login")
def login(creds: dict):
    u = USERS.get(creds.get("email", ""))
    if not u or not verify_password(creds.get("password", ""), u["password_hash"]):
        raise HTTPException(401, "bad credentials")
    return {"token": tok.issue(creds["email"], _secret()), "email": creds["email"]}


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/readyz")
def readyz():
    checks = [
        healthsvc.check("api", True),
        healthsvc.check("redis", redis_status()["ok"], "connected" if redis_status()["ok"] else "in-memory fallback"),
        healthsvc.check("mysql", DB_OK, DB_DETAIL),
        healthsvc.check("own_proxy", bool(settings.own_proxy_urls)),
        healthsvc.check("brightdata", bright.configured),
        healthsvc.check("ai", bool(settings.muse_base_url and settings.muse_api_key)),
    ]
    live = [c for c in checks if c["name"] in ("api", "redis", "mysql")]
    status = "healthy" if all(c["status"] == "up" for c in live) else "degraded"
    return {"status": status, "checks": checks}


@app.get("/metrics")
def metrics():
    return JSONResponse(content=render(), media_type="text/plain")


# ---- projects ----
@app.post("/api/v1/projects")
def create_project(p: ProjectIn, authorization: str = Header("")):
    _require_auth(authorization)
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
def create_target(t: TargetIn, authorization: str = Header("")):
    _require_auth(authorization)
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
def create_job(j: JobIn, authorization: str = Header("")):
    _require_auth(authorization)
    try:
        validate_url(j.url)
    except SSRFError as e:
        raise HTTPException(400, f"url rejected: {e}")
    engine = dec.Engine()
    policy = dec.Policy(allow_brightdata=bright.configured)
    target = next((t for t in STORE["targets"] if t["id"] == j.target_id), {"url": j.url})
    plan = engine.decide(target, policy, _providers())
    job = {"job_id": uuid.uuid4().hex, "trace_id": uuid.uuid4().hex,
           "project_id": j.project_id, "target_id": j.target_id, "url": j.url,
           "strategy": j.strategy, "plan": plan, "status": "queued",
           "created_at": time.time(),
           "estimated_cost": costeng.estimate(plan["plan"][0] if plan["plan"] else "DIRECT_HTTP")}
    STORE["jobs"].append(job)
    r = get_redis()
    if r is not None:
        try:
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


@app.post("/api/v1/jobs/{job_id}/run")
def run_job_now(job_id: str, authorization: str = Header("")):
    """Execute the full pipeline inline: fetch → validate → normalize →
    change-detect → alerts. BROWSER/proxy legs stay deferred to workers."""
    _require_auth(authorization)
    job = next((j for j in STORE["jobs"] if j.get("job_id") == job_id), None)
    if not job:
        raise HTTPException(404, "job not found")
    return _execute_job(job)


@app.post("/api/v1/results")
def ingest_result(res: dict, authorization: str = Header("")):
    """Go collector / Python worker result ingestion (contracts/results/result.json)."""
    _require_auth(authorization)
    if res.get("schema_version") != "1.0" or not res.get("job_id"):
        raise HTTPException(400, "bad result contract")
    job = next((j for j in STORE["jobs"] if j.get("job_id") == res["job_id"]), None)
    if not job:
        raise HTTPException(404, "unknown job_id")
    bundle = {"job_id": res["job_id"], "status": res.get("status", "failed"),
              "strategy": res.get("strategy", ""), "content_hash": res.get("content_hash", ""),
              "content_size": res.get("content_size", 0),
              "diagnostics": res.get("diagnostics", {}),
              "prices": [], "alerts": [], "change": None, "cost": 0}
    return _apply_result(bundle, job["url"], job["project_id"], job["target_id"])


# ---- data listings ----
@app.get("/api/v1/prices")
def list_prices(page: int = 1, size: int = 20, product_id: int = 0):
    items = [p for p in STORE["prices"] if p.get("product_id") == product_id] if product_id else STORE["prices"]
    return paginate(items, page, size)


@app.get("/api/v1/articles")
def list_articles(page: int = 1, size: int = 20):
    return paginate(STORE["articles"], page, size)


@app.post("/api/v1/articles")
def create_article(a: dict, authorization: str = Header("")):
    _require_auth(authorization)
    item = {"id": len(STORE["articles"]) + 1, **a}
    STORE["articles"].append(item)
    return item


@app.get("/api/v1/changes")
def list_changes(page: int = 1, size: int = 20):
    return paginate(STORE["changes"], page, size)


@app.get("/api/v1/search")
def search(q: str = "", scope: str = "all"):
    from .search.service import search as svc

    if not q:
        return {"items": []}
    return {"items": svc({"projects": STORE["projects"], "targets": STORE["targets"],
                          "articles": STORE["articles"]}, q, scope)}


# ---- reports ----
@app.post("/api/v1/reports")
def build_report(spec: dict, authorization: str = Header("")):
    _require_auth(authorization)
    from .reports.builder import build
    from .intelligence.market import summarize

    kind = spec.get("kind", "price")
    pid = spec.get("product_id", 0)
    prices = [p["price"] for p in STORE["prices"] if not pid or p.get("product_id") == pid]
    analysis = summarize(prices)
    if kind == "price" and settings.muse_api_key:
        try:
            ev = [p for p in STORE["prices"] if not pid or p.get("product_id") == pid][:10]
            r = muse.chat([{"role": "user", "content":
                             f"Summarize this price evidence in 3 bullets: {ev}"}])
            analysis["ai"] = str(r)[:2000]
        except Exception as e:
            analysis["ai_error"] = str(e)[:200]
    rep = build(kind, spec.get("project", ""), prices,
                [p.get("job_id") for p in STORE["prices"]][:50], str(analysis)[:4000])
    item = {"id": len(STORE["reports"]) + 1, **rep}
    STORE["reports"].append(item)
    return item


@app.get("/api/v1/reports")
def list_reports(page: int = 1, size: int = 20):
    return paginate(STORE["reports"], page, size)


# ---- schedules + worker ----
@app.post("/api/v1/schedules")
def create_schedule(s: dict, authorization: str = Header("")):
    _require_auth(authorization)
    item = {"id": len(STORE["schedules"]) + 1, "status": "active",
            "next_run": sched.next_run(s.get("kind", "interval"),
                                       s.get("every_min", 60)).isoformat(), **s}
    STORE["schedules"].append(item)
    return item


@app.get("/api/v1/schedules")
def list_schedules(page: int = 1, size: int = 20):
    return paginate(STORE["schedules"], page, size)


@app.post("/api/v1/worker/tick")
def worker_tick(authorization: str = Header("")):
    """Execute due schedules: creates collection jobs. Called by systemd
    worker or cron; also powers the UI 'Run scheduler' button."""
    _require_auth(authorization)
    import datetime

    now = datetime.datetime.utcnow()
    fired = []
    for s in STORE["schedules"]:
        if s.get("status") != "active":
            continue
        try:
            due = datetime.datetime.fromisoformat(s.get("next_run", ""))
        except Exception:
            due = now
        if due <= now:
            job = {"job_id": uuid.uuid4().hex, "trace_id": uuid.uuid4().hex,
                   "project_id": s.get("project_id", 1), "target_id": s.get("target_id", 1),
                   "url": s.get("url", ""), "strategy": "AUTO",
                   "plan": {"plan": ["DIRECT_HTTP"], "reasons": ["scheduled"]},
                   "status": "queued", "created_at": time.time(), "estimated_cost": 0.0001}
            if job["url"]:
                STORE["jobs"].append(job)
                fired.append(job["job_id"])
            s["last_run"] = now.isoformat()
            s["next_run"] = sched.next_run(s.get("kind", "interval"),
                                           s.get("every_min", 60)).isoformat()
    inc("jobs_total", len(fired))
    return {"fired": fired}


# ---- strategy / validation helpers ----
@app.post("/api/v1/strategy/decide")
def decide_strategy(target: dict, policy: dict = {}):
    engine = dec.Engine()
    p = dec.Policy(**{k: v for k, v in policy.items()
                       if k in ("allow_browser", "allow_proxy", "allow_brightdata",
                                "max_cost_per_job", "geo", "require_js")})
    return engine.decide(target, p, _providers())


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
def ai_chat(messages: list, model: str = "", authorization: str = Header("")):
    _require_auth(authorization)
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
def create_alert(a: AlertRuleIn, authorization: str = Header("")):
    _require_auth(authorization)
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
