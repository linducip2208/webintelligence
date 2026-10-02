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
from .core import mirror as dbmirror
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
    "schedules": [], "raw": [], "changes": [], "entities": [],
    "audit": [], "budgets": {}, "orgs": [{"id": 1, "name": "Default", "slug": "default"}],
    "memberships": [{"org_id": 1, "email": "admin@local", "role": "owner"}],
    "apikeys": [], "nodes": [], "edges": [], "events": [], "evidence": [],
    "claims": [], "findings": [], "research": [], "watchlists": [],
    "workflows": [], "wfruns": [], "datasets": [], "dsversions": [],
    "connectors": [], "documents": [], "webhooks": [], "deliveries": [],
    "history": [], "tags": {},
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


def _ctx(authorization: str = "", x_api_key: str = ""):
    """(email, org_id, role). API keys scope to their org; login tokens use membership."""
    email = _require_auth(authorization)
    if x_api_key:
        import hashlib as _h
        h = _h.sha256(x_api_key.encode()).hexdigest()
        k = next((x for x in STORE["apikeys"] if x["key_hash"] == h and not x.get("revoked")), None)
        if not k:
            raise HTTPException(401, "bad api key")
        return ("apikey:" + k["name"], k["org_id"], "analyst")
    ms = [m for m in STORE["memberships"] if m["email"] == email]
    if ms:
        return (email, ms[0]["org_id"], ms[0]["role"])
    return (email, 1, "viewer")


def _need(authorization: str, action: str, x_api_key: str = ""):
    from .services import rbac as _rbac
    email, org, role = _ctx(authorization, x_api_key)
    if email.startswith("apikey:"):
        import hashlib as _h
        k = next((x for x in STORE["apikeys"]
                  if x["key_hash"] == _h.sha256(x_api_key.encode()).hexdigest()), None)
        if not k or (k.get("scopes") and action not in k["scopes"] and "*" not in k["scopes"]):
            raise HTTPException(403, f"api key lacks scope {action}")
        return (email, org, role)
    if not _rbac.can(role, action):
        raise HTTPException(403, f"role {role} cannot {action}")
    return (email, org, role)


def _providers():
    return {"own_proxy": {"healthy": True, "cost": 0.002},
            "brightdata": {"healthy": True, "cost": 0.05,
                           "configured": bright.configured}}


def _audit(actor, action, ref=""):
    STORE["audit"].append({"actor": actor, "action": action, "ref": ref,
                           "at": time.time()})
    if DB_OK:
        dbmirror.mirror_audit(actor, action, ref)


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
        if DB_OK:
            dbmirror.mirror_price(target_id, p["price"], p.get("currency", "USD"))
    if res.get("change") in ("CHANGED", "NEW"):
        STORE["changes"].append({"target_id": target_id, "kind": res["change"],
                                 "diff": res.get("diagnostics", {}), "at": time.time()})
    for a in res.get("alerts", []):
        STORE["alerts"].append({"id": len(STORE["alerts"]) + 1, **a,
                                "project_id": project_id, "is_read": False})
        if DB_OK:
            dbmirror.mirror_alert(a.get("rule", ""), a.get("message", "")[:500], project_id)
    if res.get("status") == "success":
        inc("jobs_success")
    elif res.get("status") in ("failed",):
        inc("jobs_failed")
        STORE["alerts"].append({"id": len(STORE["alerts"]) + 1,
                                "rule": "collection_failure", "channel": "inapp",
                                "message": f"Job {res.get('job_id')} failed "
                                           f"({res.get('strategy')}, http={res.get('http_status')})",
                                "project_id": project_id, "is_read": False})
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
    STORE["health"].append({"at": time.time(), "status": status,
                            "checks": {c["name"]: c["status"] for c in checks}})
    if DB_OK:
        for c in checks:
            dbmirror.mirror_health(c["name"], c["status"], c.get("detail", ""))
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
    _audit(authorization[:12] if authorization else "anon", "project.create", item["name"])
    if DB_OK:
        dbmirror.mirror_project(p.name, p.description)
    return item


def _sorted(items, sort="", order="asc"):
    if not sort:
        return items
    rev = order == "desc"
    try:
        return sorted(items, key=lambda x: (x.get(sort) is None, x.get(sort)), reverse=rev)
    except TypeError:
        return sorted(items, key=lambda x: str(x.get(sort)), reverse=rev)


@app.get("/api/v1/projects")
def list_projects(page: int = 1, size: int = 20, q: str = "", sort: str = "", order: str = "asc"):
    items = [x for x in STORE["projects"] if q.lower() in x["name"].lower()] if q else STORE["projects"]
    return paginate(_sorted(items, sort, order), page, size)


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
    _audit(authorization[:12] if authorization else "anon", "target.create", t.url[:120])
    if DB_OK:
        dbmirror.mirror_target(t.project_id, t.domain, t.url, t.source_type)
    return item


@app.get("/api/v1/targets")
def list_targets(page: int = 1, size: int = 20, q: str = "", sort: str = "", order: str = "asc"):
    items = [x for x in STORE["targets"] if q.lower() in (x["domain"] + x["url"]).lower()] if q else STORE["targets"]
    return paginate(_sorted(items, sort, order), page, size)


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
    _audit(authorization[:12] if authorization else "anon", "job.create", job["job_id"])
    if DB_OK:
        dbmirror.mirror_job(job["trace_id"], j.project_id, j.target_id,
                            j.url, j.strategy, "queued")
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
def list_jobs(page: int = 1, size: int = 20, status: str = "", sort: str = "", order: str = "asc"):
    items = [x for x in STORE["jobs"] if x["status"] == status] if status else STORE["jobs"]
    return paginate(_sorted(items, sort, order), page, size)


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
def list_prices(page: int = 1, size: int = 20, product_id: int = 0, sort: str = "", order: str = "asc"):
    items = [p for p in STORE["prices"] if p.get("product_id") == product_id] if product_id else STORE["prices"]
    return paginate(_sorted(items, sort, order), page, size)


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
                                       s.get("every_min", 60),
                                       cron=s.get("cron", "")).isoformat(), **s}
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
                _audit(authorization[:12] if authorization else "anon",
                       "job.scheduled", job["job_id"])
            s["last_run"] = now.isoformat()
            s["next_run"] = sched.next_run(s.get("kind", "interval"),
                                           s.get("every_min", 60),
                                           cron=s.get("cron", "")).isoformat()
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
def list_alerts(page: int = 1, size: int = 20, sort: str = "", order: str = "asc"):
    return paginate(_sorted(STORE["alerts"], sort, order), page, size)


# ---- analytics ----
@app.get("/api/v1/analytics/prices")
def analytics_prices(product_id: int = 0):
    from .analytics.stats import mean, volatility, anomaly_marks, pct_change
    pts = [p for p in STORE["prices"] if not product_id or p.get("product_id") == product_id]
    vals = [p["price"] for p in pts]
    marks = anomaly_marks(vals) if len(vals) > 3 else []
    return {"count": len(vals), "avg": mean(vals) if vals else None,
            "min": min(vals) if vals else None, "max": max(vals) if vals else None,
            "volatility": volatility(vals) if len(vals) > 1 else 0.0,
            "change_pct": pct_change(vals[0], vals[-1]) if len(vals) > 1 else None,
            "anomalies": [{"index": i, "price": vals[i]} for i in marks],
            "history": pts[-100:]}


@app.get("/api/v1/analytics/trends")
def analytics_trends():
    from .analytics.trends import emerging_topics
    titles = [a.get("title", "") for a in STORE["articles"]]
    return {"topics": emerging_topics(titles),
            "review_volume": len([1 for _ in STORE["prices"]]),
            "articles": len(STORE["articles"])}


@app.get("/api/v1/analytics/quality")
def analytics_quality():
    from .services.quality import score
    recs = [{"price": p.get("price"), "url": "job:" + str(p.get("job_id", ""))} for p in STORE["prices"]]
    req = ["price", "url"]
    scores = [score(r, req)["overall"] for r in recs] if recs else []
    return {"records": len(recs), "avg_overall": round(sum(scores) / len(scores), 3) if scores else None,
            "required": req}


# ---- intelligence ----
@app.post("/api/v1/intel/competitors/compare")
def intel_compare(spec: dict):
    from .intelligence.competitors import compare
    return compare(spec.get("a", []), spec.get("b", []))


@app.post("/api/v1/intel/reviews")
def intel_reviews(spec: dict):
    from .intelligence.reviews import analyze
    return analyze(spec.get("reviews", []))


@app.post("/api/v1/intel/news/summarize")
def intel_news(spec: dict):
    from .intelligence.news import summarize_article
    return summarize_article(spec.get("title", ""), spec.get("body", ""))


# ---- entities ----
@app.post("/api/v1/entities/resolve")
def entity_resolve(spec: dict, authorization: str = Header("")):
    _require_auth(authorization)
    from .services.entity_resolution import score, decide
    cand = spec.get("candidate", {})
    best, best_s = None, -1.0
    for e in STORE["entities"]:
        s = score(cand, e)
        if s > best_s:
            best, best_s = e, s
    verdict = decide(best_s) if best else "NEW"
    if verdict == "NEW":
        item = {"id": len(STORE["entities"]) + 1, **cand}
        STORE["entities"].append(item)
        return {"verdict": "NEW", "entity": item, "score": 0.0}
    if verdict == "LINK":
        return {"verdict": "LINK", "entity": best, "score": best_s}
    return {"verdict": "REVIEW", "entity": best, "score": best_s}


@app.get("/api/v1/entities")
def list_entities(page: int = 1, size: int = 20):
    return paginate(STORE["entities"], page, size)


# ---- costs & budgets ----
@app.get("/api/v1/costs/summary")
def costs_summary():
    return costeng.summary(STORE["jobs"])


@app.post("/api/v1/costs/budget")
def set_budget(spec: dict, authorization: str = Header("")):
    _require_auth(authorization)
    STORE["budgets"][str(spec.get("project_id", 1))] = float(spec.get("limit", 0))
    return {"ok": True, "budgets": STORE["budgets"]}


@app.get("/api/v1/costs/budget/check")
def budget_check(project_id: int = 1):
    spent = sum(j.get("actual_cost", 0) or j.get("estimated_cost", 0)
                for j in STORE["jobs"] if j.get("project_id") == project_id)
    limit = STORE["budgets"].get(str(project_id))
    return {"spent": round(spent, 6), "limit": limit,
            "over": limit is not None and spent > limit}


# ---- ML registry ----
@app.post("/api/v1/ml/register")
def ml_register(spec: dict, authorization: str = Header("")):
    _require_auth(authorization)
    from .analytics.ml import register
    register(spec.get("name", "model"), spec.get("version", "v1"),
             spec.get("metrics", {}))
    return {"ok": True}


@app.get("/api/v1/ml/models")
def ml_models():
    from .analytics.ml import REGISTRY
    return {"models": REGISTRY}


# ---- alert delivery ----
@app.post("/api/v1/alerts/{alert_id}/send")
def alert_send(alert_id: int, authorization: str = Header("")):
    _require_auth(authorization)
    a = next((x for x in STORE["alerts"] if x.get("id") == alert_id), None)
    if not a:
        raise HTTPException(404, "alert not found")
    channel = a.get("channel", "inapp")
    if channel == "webhook":
        url = os.getenv("ALERT_WEBHOOK_URL", "")
        if not url:
            return {"delivered": False, "reason": "ALERT_WEBHOOK_URL not set"}
        try:
            import json as _j
            import urllib.request as _u
            req = _u.Request(url, data=_j.dumps(a, default=str).encode(),
                             headers={"Content-Type": "application/json"})
            with _u.urlopen(req, timeout=10) as r:
                a["delivered"] = True
                return {"delivered": True, "status": r.status}
        except Exception as e:
            a["delivery_error"] = str(e)[:200]
            return {"delivered": False, "error": str(e)[:200]}
    if channel == "email":
        host = os.getenv("SMTP_HOST", "")
        if not host:
            return {"delivered": False, "reason": "SMTP not configured"}
        try:
            import smtplib
            from email.message import EmailMessage
            msg = EmailMessage()
            msg["Subject"] = f"[WebIntel] {a.get('rule')}"
            msg["From"] = os.getenv("SMTP_USER", "webintel@localhost")
            msg["To"] = os.getenv("ALERT_EMAIL_TO", msg["From"])
            msg.set_content(a.get("message", ""))
            with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as s:
                s.starttls()
                if os.getenv("SMTP_USER"):
                    s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS", ""))
                s.send_message(msg)
            a["delivered"] = True
            return {"delivered": True}
        except Exception as e:
            a["delivery_error"] = str(e)[:200]
            return {"delivered": False, "error": str(e)[:200]}
    a["is_read"] = False
    return {"delivered": True, "channel": "inapp"}


# ---- report export ----
@app.get("/api/v1/reports/{rep_id}/export")
def report_export(rep_id: int, format: str = "json"):
    r = next((x for x in STORE["reports"] if x.get("id") == rep_id), None)
    if not r:
        raise HTTPException(404, "report not found")
    if format == "csv":
        from .reports.builder import to_csv
        return JSONResponse(content={"csv": to_csv(r)})
    if format == "xlsx":
        try:
            import io as _io
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.append(["kind", "project", "generated_at"])
            ws.append([r.get("kind"), r.get("project"), r.get("generated_at")])
            buf = _io.BytesIO()
            wb.save(buf)
            return {"xlsx_bytes": len(buf.getvalue())}
        except ImportError:
            from .reports.builder import to_csv
            return {"fallback": "csv", "csv": to_csv(r)}
    return r


# ---- audit ----
@app.get("/api/v1/audit")
def list_audit(page: int = 1, size: int = 20):
    return paginate(list(reversed(STORE["audit"])), page, size)


# ---- organizations / RBAC / API keys ----
@app.post("/api/v1/orgs", tags=["admin"])
def create_org(spec: dict, authorization: str = Header("")):
    email, _, _ = _ctx(authorization)
    item = {"id": len(STORE["orgs"]) + 1, "name": spec.get("name", ""),
            "slug": spec.get("slug", spec.get("name", "").lower().replace(" ", "-"))}
    STORE["orgs"].append(item)
    STORE["memberships"].append({"org_id": item["id"], "email": email, "role": "owner"})
    _audit(email, "org.create", item["name"])
    return item


@app.get("/api/v1/orgs", tags=["admin"])
def list_orgs():
    return {"items": STORE["orgs"]}


@app.get("/api/v1/roles", tags=["admin"])
def roles_matrix():
    from .services.rbac import MATRIX
    return {"roles": {k: sorted(v) for k, v in MATRIX.items()}}


@app.post("/api/v1/memberships", tags=["admin"])
def add_member(spec: dict, authorization: str = Header("")):
    email, org, _ = _need(authorization, "users")
    item = {"org_id": spec.get("org_id", org), "email": spec.get("email"),
            "role": spec.get("role", "viewer")}
    STORE["memberships"].append(item)
    _audit(email, "member.add", f"{item['email']}->{item['role']}")
    return item


@app.post("/api/v1/apikeys", tags=["admin"])
def create_apikey(spec: dict, authorization: str = Header("")):
    import hashlib as _h
    import secrets as _s
    email, org, _ = _need(authorization, "configure")
    raw = "wi_" + _s.token_urlsafe(32)
    item = {"id": len(STORE["apikeys"]) + 1, "org_id": spec.get("org_id", org),
            "name": spec.get("name", ""), "key_hash": _h.sha256(raw.encode()).hexdigest(),
            "scopes": spec.get("scopes", ["read"]), "revoked": False}
    STORE["apikeys"].append(item)
    _audit(email, "apikey.create", item["name"])
    return {**item, "key": raw}  # shown once


@app.get("/api/v1/apikeys", tags=["admin"])
def list_apikeys():
    return {"items": [{k: v for k, v in x.items() if k != "key_hash"} for x in STORE["apikeys"]]}


@app.post("/api/v1/apikeys/{kid}/revoke", tags=["admin"])
def revoke_apikey(kid: int, authorization: str = Header("")):
    email, _, _ = _need(authorization, "configure")
    k = next((x for x in STORE["apikeys"] if x["id"] == kid), None)
    if not k:
        raise HTTPException(404, "not found")
    k["revoked"] = True
    _audit(email, "apikey.revoke", k["name"])
    return {"ok": True}


# ---- knowledge graph ----
@app.post("/api/v1/graph/nodes", tags=["knowledge"])
def graph_node(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from .services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
    return _g.add_node(STORE["nodes"], spec.get("kind", "company"),
                      spec.get("key", ""), spec.get("name", ""), org)


@app.post("/api/v1/graph/edges", tags=["knowledge"])
def graph_edge(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from .services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
    return _g.add_edge(STORE["edges"], spec.get("src"), spec.get("dst"),
                       spec.get("rel", "RELATED"), spec.get("confidence", 1.0),
                       spec.get("evidence", []), spec.get("at"), org)


@app.get("/api/v1/graph/traverse", tags=["knowledge"])
def graph_traverse(node: int = 0, depth: int = 2, rel: str = "", kind: str = ""):
    from .services import graph as _g
    return {"items": _g.traverse(STORE["nodes"], STORE["edges"], node, depth,
                                rel.split(",") if rel else None,
                                kind.split(",") if kind else None)}


# ---- events / evidence / claims / findings ----
@app.post("/api/v1/events", tags=["knowledge"])
def create_event(spec: dict, authorization: str = Header("")):
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["events"]) + 1, "org": org, **spec}
    STORE["events"].append(item)
    _fire_watchlists(item)
    return item


@app.get("/api/v1/events", tags=["knowledge"])
def list_events(page: int = 1, size: int = 20, type: str = "", severity: str = ""):
    items = [e for e in STORE["events"]
             if (not type or e.get("type") == type) and (not severity or e.get("severity") == severity)]
    return paginate(items, page, size)


@app.post("/api/v1/evidence", tags=["knowledge"])
def create_evidence(spec: dict, authorization: str = Header("")):
    from .services import evidence as _e
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["evidence"]) + 1, "org": org,
            **_e.make_evidence(spec.get("source", ""), spec.get("url", ""),
                               spec.get("content_hash", ""), spec.get("snippet", ""),
                               spec.get("selector", ""), spec.get("method", ""),
                               spec.get("confidence", 1.0))}
    STORE["evidence"].append(item)
    return item


@app.get("/api/v1/evidence", tags=["knowledge"])
def list_evidence(page: int = 1, size: int = 20):
    return paginate(STORE["evidence"], page, size)


@app.post("/api/v1/claims", tags=["knowledge"])
def create_claim(spec: dict, authorization: str = Header("")):
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["claims"]) + 1, "org": org, "status": "UNVERIFIED",
            "confidence": 0.0, **spec}
    STORE["claims"].append(item)
    return item


@app.post("/api/v1/claims/verify", tags=["knowledge"])
def verify_claim(spec: dict):
    from .services import evidence as _e
    out = _e.verify(spec.get("value"), spec.get("evidence", []))
    if spec.get("claim_id"):
        c = next((x for x in STORE["claims"] if x["id"] == spec["claim_id"]), None)
        if c:
            c["status"] = out["status"]
            c["confidence"] = out["confidence"]
    return out


@app.post("/api/v1/contradictions/check", tags=["knowledge"])
def check_contradictions(spec: dict):
    from .services import evidence as _e
    return _e.contradictions(spec.get("evidence", [])) or {"conflict": False}


@app.post("/api/v1/findings", tags=["intelligence"])
def create_finding(spec: dict, authorization: str = Header("")):
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["findings"]) + 1, "org": org, **spec}
    STORE["findings"].append(item)
    return item


@app.get("/api/v1/findings", tags=["intelligence"])
def list_findings(page: int = 1, size: int = 20):
    return paginate(STORE["findings"], page, size)


@app.get("/api/v1/feed", tags=["intelligence"])
def intel_feed(kinds: str = "", limit: int = 50):
    from .services import feed as _f
    return {"items": _f.build(STORE["events"], STORE["findings"], STORE["changes"],
                             STORE["alerts"], kinds.split(",") if kinds else None, limit)}


@app.get("/api/v1/opportunities", tags=["intelligence"])
def opportunities():
    from .services import opportunities as _o
    by_p = {}
    for p in STORE["prices"]:
        by_p.setdefault(p.get("product_id"), []).append(p["price"])
    out = []
    for pid, vals in by_p.items():
        for a in _o.price_anomaly(vals):
            out.append({"type": "PRICE_ANOMALY", "product_id": pid, **a,
                        "evidence": [p.get("job_id") for p in STORE["prices"]
                                     if p.get("product_id") == pid][:5]})
    return {"items": out}


@app.post("/api/v1/ask", tags=["intelligence"])
def nlq_ask(spec: dict):
    from .services import nlq as _n
    plan = _n.to_plan(spec.get("question", ""))
    return {"plan": plan, "answer": _n.answer(plan, STORE),
            "evidence": "prices/changes/entities stores with job provenance"}


# ---- research ----
@app.post("/api/v1/research/plan", tags=["research"])
def research_plan(spec: dict):
    from .services import research as _r
    return _r.plan(spec.get("question", ""))


@app.post("/api/v1/research/runs", tags=["research"])
def research_run(spec: dict, authorization: str = Header("")):
    from .services import research as _r
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["research"]) + 1, "org": org, "status": "planned",
            "sources": [], "job_ids": [], "evidence_ids": [], "analysis": "",
            "ai_provider": "", "ai_model": settings.muse_model,
            "prompt_version": "v1", "config": spec.get("config", {}),
            "question": spec.get("question", ""), "plan": spec.get("plan") or _r.plan(spec.get("question", ""))}
    STORE["research"].append(item)
    _audit(_ctx(authorization)[0], "research.create", item["question"][:120])
    return item


@app.post("/api/v1/research/runs/{rid}/finish", tags=["research"])
def research_finish(rid: int, spec: dict, authorization: str = Header("")):
    from .services import research as _r
    _require_auth(authorization)
    run = next((x for x in STORE["research"] if x["id"] == rid), None)
    if not run:
        raise HTTPException(404, "not found")
    run.update({"status": "done", "analysis": spec.get("analysis", "")[:8000],
                "evidence_ids": spec.get("evidence_ids", run.get("evidence_ids", [])),
                "ai_provider": spec.get("ai_provider", ""), "ai_model": spec.get("ai_model", ""),
                "finished_at": time.time()})
    return {"ok": True, "reproducibility": _r.bundle(run)}


@app.get("/api/v1/research/runs", tags=["research"])
def research_runs(page: int = 1, size: int = 20):
    return paginate(STORE["research"], page, size)


# ---- watchlists ----
@app.post("/api/v1/watchlists", tags=["monitoring"])
def create_watchlist(spec: dict, authorization: str = Header("")):
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["watchlists"]) + 1, "org": org, **spec}
    STORE["watchlists"].append(item)
    return item


@app.get("/api/v1/watchlists", tags=["monitoring"])
def list_watchlists():
    return {"items": STORE["watchlists"]}


@app.delete("/api/v1/watchlists/{wid}", tags=["monitoring"])
def delete_watchlist(wid: int, authorization: str = Header("")):
    _require_auth(authorization)
    STORE["watchlists"][:] = [w for w in STORE["watchlists"] if w["id"] != wid]
    return {"ok": True}


def _fire_watchlists(item: dict):
    from .services import watchlists as _w
    for wid in _w.match(STORE["watchlists"], {"value": item.get("entity_key", ""),
                                              "text": f"{item.get('type','')} {item.get('entity_key','')}"}):
        STORE["alerts"].append({"id": len(STORE["alerts"]) + 1, "rule": "watchlist_hit",
                                "channel": "inapp",
                                "message": f"Watchlist #{wid} hit by {item.get('type')}",
                                "project_id": 0, "is_read": False})


@app.post("/api/v1/watchlists/check", tags=["monitoring"])
def watchlist_check(spec: dict):
    from .services import watchlists as _w
    return {"matches": _w.match(STORE["watchlists"], spec)}


# ---- workflows ----
@app.post("/api/v1/workflows", tags=["monitoring"])
def create_workflow(spec: dict, authorization: str = Header("")):
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["workflows"]) + 1, "org": org, "enabled": True, **spec}
    STORE["workflows"].append(item)
    return item


@app.get("/api/v1/workflows", tags=["monitoring"])
def list_workflows():
    return {"items": STORE["workflows"]}


@app.post("/api/v1/workflows/{wid}/run", tags=["monitoring"])
def workflow_run(wid: int, spec: dict, authorization: str = Header("")):
    from .services import workflows as _w
    _require_auth(authorization)
    wf = next((x for x in STORE["workflows"] if x["id"] == wid and x.get("enabled")), None)
    if not wf:
        raise HTTPException(404, "workflow not found/disabled")
    event = spec.get("event", {})
    log, effects = [], []
    for i, step in enumerate(wf.get("definition", {}).get("steps", [])):
        k = _w.key(wid, i, event)
        if any(r.get("idempotency_key") == k for r in STORE["wfruns"]):
            log.append({"step": i, "skipped": "duplicate"})
            continue
        if not _w.check_condition(step.get("condition", {}), event):
            log.append({"step": i, "skipped": "condition"})
            continue
        eff = _w.run_step(step, event, STORE)
        effects.append(eff)
        log.append({"step": i, "effect": eff})
    run = {"id": len(STORE["wfruns"]) + 1, "workflow_id": wid, "status": "done",
           "context": event, "log": log, "idempotency_key": _w.key(wid, "run", event)}
    STORE["wfruns"].append(run)
    return {"run": run, "effects": effects}


# ---- datasets ----
@app.post("/api/v1/datasets", tags=["datasets"])
def create_dataset(spec: dict, authorization: str = Header("")):
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["datasets"]) + 1, "org": org, "status": "draft", **spec}
    STORE["datasets"].append(item)
    return item


@app.get("/api/v1/datasets", tags=["datasets"])
def list_datasets():
    return {"items": STORE["datasets"]}


@app.post("/api/v1/datasets/{did}/publish", tags=["datasets"])
def dataset_publish(did: int, spec: dict, authorization: str = Header("")):
    from .services import datasets as _d
    _require_auth(authorization)
    rows = spec.get("rows", [])
    v = _d.publish(STORE["dsversions"], did, rows, spec.get("lineage", {}))
    return v


@app.get("/api/v1/datasets/{did}/export", tags=["datasets"])
def dataset_export(did: int, format: str = "csv", version: int = 0):
    from .services import datasets as _d
    vs = [v for v in STORE["dsversions"] if v.get("dataset_id") == did]
    rows = (vs[-1].get("rows", []) if vs else spec_rows(did))
    if version:
        v = next((x for x in vs if x.get("version") == version), None)
        rows = v.get("rows", []) if v else []
    if format == "json":
        return {"rows": rows}
    return {"csv": _d.to_csv(rows)}


def spec_rows(did: int):
    return [p for p in STORE["prices"] if p.get("product_id") == did] or []


# ---- connectors ----
@app.post("/api/v1/connectors", tags=["sources"])
def register_connector(spec: dict, authorization: str = Header("")):
    from .services import connectors as _c
    _, org, _ = _ctx(authorization)
    errs = _c.validate_manifest(spec.get("manifest", {}))
    if errs:
        raise HTTPException(400, "; ".join(errs))
    item = {"id": len(STORE["connectors"]) + 1, "org": org, "enabled": True, **spec}
    STORE["connectors"].append(item)
    return item


@app.get("/api/v1/connectors", tags=["sources"])
def list_connectors():
    return {"items": STORE["connectors"]}


@app.get("/api/v1/connectors/match", tags=["sources"])
def match_connector(capability: str = "", category: str = ""):
    from .services import connectors as _c
    return {"items": _c.match(STORE["connectors"], capability, category)}


# ---- documents ----
@app.post("/api/v1/documents", tags=["knowledge"])
def ingest_document(spec: dict, authorization: str = Header("")):
    from .services import documents as _d
    _, org, _ = _ctx(authorization)
    content = (spec.get("text", "") or "").encode()
    fp = _d.fingerprint(content)
    same = [x for x in STORE["documents"] if x.get("fingerprint") == fp]
    if same:
        return {"duplicate_of": same[0]["id"], "fingerprint": fp}
    ext = _d.extract(spec.get("kind", "txt"), content, spec.get("filename", ""))
    item = {"id": len(STORE["documents"]) + 1, "org": org, "version": 1,
            "fingerprint": fp, "chunks": _d.chunk(ext.get("text", "")) if ext.get("extracted") else [],
            "title": spec.get("title", ""), "kind": spec.get("kind", "txt"),
            "source_url": spec.get("source_url", ""), "doc_metadata": ext.get("meta", {}),
            "extracted": ext.get("extracted"), "reason": ext.get("reason", "")}
    STORE["documents"].append(item)
    return item


@app.get("/api/v1/documents", tags=["knowledge"])
def list_documents(page: int = 1, size: int = 20):
    return paginate(STORE["documents"], page, size)


# ---- webhooks (outgoing) ----
@app.post("/api/v1/webhooks", tags=["monitoring"])
def create_webhook(spec: dict, authorization: str = Header("")):
    _, org, _ = _ctx(authorization)
    item = {"id": len(STORE["webhooks"]) + 1, "org": org, "enabled": True, **spec}
    STORE["webhooks"].append(item)
    return {k: v for k, v in item.items() if k != "secret"}


@app.get("/api/v1/webhooks", tags=["monitoring"])
def list_webhooks():
    return {"items": [{k: v for k, v in w.items() if k != "secret"} for w in STORE["webhooks"]]}


@app.post("/api/v1/webhooks/{wid}/test", tags=["monitoring"])
def webhook_test(wid: int, authorization: str = Header("")):
    from .services import webhooks as _wh
    _require_auth(authorization)
    w = next((x for x in STORE["webhooks"] if x["id"] == wid and x.get("enabled")), None)
    if not w:
        raise HTTPException(404, "not found/disabled")
    out = _wh.deliver(w["url"], "ping", {"webhook_id": wid}, w.get("secret", ""))
    STORE["deliveries"].append({"id": len(STORE["deliveries"]) + 1, "webhook_id": wid,
                                "event": "ping", "status": "ok" if out["ok"] else "failed",
                                "attempts": out.get("attempts", 0),
                                "last_error": out.get("error", ""),
                                "response_status": out.get("status", 0)})
    return out


@app.get("/api/v1/webhooks/deliveries", tags=["monitoring"])
def webhook_deliveries(page: int = 1, size: int = 20):
    return paginate(STORE["deliveries"], page, size)


@app.post("/api/v1/webhooks/deliveries/{did}/replay", tags=["monitoring"])
def webhook_replay(did: int, authorization: str = Header("")):
    from .services import webhooks as _wh
    _require_auth(authorization)
    d = next((x for x in STORE["deliveries"] if x["id"] == did), None)
    if not d:
        raise HTTPException(404, "not found")
    w = next((x for x in STORE["webhooks"] if x["id"] == d["webhook_id"]), None)
    if not w:
        raise HTTPException(404, "webhook gone")
    out = _wh.deliver(w["url"], d["event"], {"replay_of": did}, w.get("secret", ""))
    d.update({"status": "ok" if out["ok"] else "failed",
              "attempts": d.get("attempts", 0) + out.get("attempts", 0)})
    return out


# ---- i18n ----
@app.get("/api/v1/i18n", tags=["admin"])
def get_strings(lang: str = "en"):
    from .i18n.lang import STRINGS, langs
    return {"lang": lang, "strings": STRINGS.get(lang, STRINGS["en"]), "langs": langs()}


# ---- dashboard ----
@app.get("/api/v1/dashboard")
def dashboard():
    return dash.build(STORE["jobs"], STORE["alerts"], STORE["prices"],
                      STORE["health"], {"estimated": sum(
                          j.get("estimated_cost", 0) for j in STORE["jobs"])})
