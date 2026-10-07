"""collection routes (split from main.py; behavior unchanged)."""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from ..shared import (
    HTTPException,
    Header,
    JobIn,
    STORE,
    _apply_result,
    _audit,
    _check_url,
    _ctx,
    _execute_job,
    _providers,
    _require_auth,
    _sorted,
    _visible_by_org,
    bright,
    costeng,
    dec,
    get_redis,
    inc,
    paginate,
    repo,
    sched,
    time,
    uuid,
    _need,
)

router = APIRouter()

# ---- collection jobs ----
@router.post("/api/v1/jobs")
def create_job(j: JobIn, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entitlements as _e
    email, org, _ = _need(authorization, "collect", x_api_key)
    ok, why = _e.check(STORE, org, "jobs")
    if not ok:
        raise HTTPException(402, why)
    _check_url(j.url)
    engine = dec.Engine()
    brow_ok, _ = _e.check(STORE, org, "browser")
    policy = dec.Policy(allow_browser=brow_ok, allow_brightdata=bright.configured)
    target = next((t for t in STORE["targets"]
                   if t["id"] == j.target_id and t.get("org", 1) == org), None)
    if j.target_id and not target:
        raise HTTPException(404, "target not found in your organization")
    target = target or {"url": j.url}
    plan = engine.decide(target, policy, _providers())
    job = {"job_id": uuid.uuid4().hex, "trace_id": uuid.uuid4().hex,
           "project_id": j.project_id, "target_id": j.target_id, "url": j.url,
           "strategy": j.strategy, "plan": plan, "status": "queued",
           "created_at": time.time(), "org": org,
           "profile": j.profile if j.profile in ("quick", "standard", "deep") else "standard",
           "estimated_cost": costeng.estimate(plan["plan"][0] if plan["plan"] else "DIRECT_HTTP")}
    STORE["jobs"].append(job)
    _audit(email, "job.create", job["job_id"])
    r = get_redis()
    if r is not None:
        try:
            from ...orchestration.orchestrator import enqueue

            enqueue(r, {"schema_version": "1.0", "job_id": job["job_id"],
                        "target_id": str(j.target_id), "url": j.url,
                        "strategy": j.strategy, "timeout_ms": 30000})
        except Exception:
            pass
    inc("jobs_total")
    return job


@router.get("/api/v1/jobs")
def list_jobs(page: int = 1, size: int = 20, status: str = "", sort: str = "", order: str = "asc",
              authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [x for x in STORE["jobs"] if x.get("org", 1) == org]
    if status:
        items = [x for x in items if x["status"] == status]
    return paginate(_sorted(items, sort, order), page, size)


@router.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str, authorization: str = Header(""), x_api_key: str = Header("")):
    """Scan/job detail: status, attempts, extracted prices, changes, alerts, errors."""
    _, org, _ = _ctx(authorization, x_api_key)
    job = next((j for j in STORE["jobs"]
                if j.get("job_id") == job_id and j.get("org", 1) == org), None)
    if not job:
        raise HTTPException(404, "job not found")
    attempts = [a for a in STORE.get("attempts", []) if a.get("job_id") == job_id]
    prices = [p for p in STORE["prices"] if p.get("job_id") == job_id]
    changes = [c for c in STORE["changes"] if c.get("target_id") == job.get("target_id")]
    return {**job,
            "attempts": attempts,
            "prices": prices,
            "changes": changes,
            "price_count": len(prices)}


@router.delete("/api/v1/jobs/{job_id}")
def delete_job(job_id: str, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    job = next((j for j in STORE["jobs"]
                if j.get("job_id") == job_id and j.get("org", 1) == org), None)
    if not job:
        raise HTTPException(404, "job not found")
    if job.get("status") == "running":
        raise HTTPException(409, "cannot delete a running job")
    STORE["jobs"][:] = [j for j in STORE["jobs"] if j.get("job_id") != job_id]
    _audit(email, "job.delete", job_id[:16])
    return {"ok": True}


@router.post("/api/v1/jobs/{job_id}/run")
def run_job_now(job_id: str, authorization: str = Header(""), x_api_key: str = Header("")):
    """Execute the full pipeline inline: fetch → validate → normalize →
    change-detect → alerts. BROWSER/proxy legs stay deferred to workers."""
    email, org, _ = _need(authorization, "collect", x_api_key)
    job = next((j for j in STORE["jobs"]
                if j.get("job_id") == job_id and j.get("org", 1) == org), None)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] not in ("queued", "failed"):
        raise HTTPException(409, f"job is {job['status']}")
    job["status"] = "running"
    repo.sync("jobs", job)
    _audit(email, "job.run", job_id[:16])
    try:
        return _execute_job(job)
    except Exception as e:
        job["status"] = "failed"
        repo.sync("jobs", job)
        raise HTTPException(500, f"execution failed: {e}"[:300])


@router.post("/api/v1/results")
def ingest_result(res: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Go collector / Python worker result ingestion (contracts/results/result.json)."""
    email, org, _ = _need(authorization, "collect", x_api_key)
    if res.get("schema_version") != "1.0" or not res.get("job_id"):
        raise HTTPException(400, "bad result contract")
    job = next((j for j in STORE["jobs"]
                if j.get("job_id") == res["job_id"] and j.get("org", 1) == org), None)
    if not job:
        raise HTTPException(404, "unknown job_id")
    bundle = {"job_id": res["job_id"], "status": res.get("status", "failed"),
              "strategy": res.get("strategy", ""), "content_hash": res.get("content_hash", ""),
              "content_size": res.get("content_size", 0),
              "diagnostics": res.get("diagnostics", {}),
              "prices": [], "alerts": [], "change": None, "cost": 0}
    if res.get("content_b64") and res.get("status") == "success":
        try:
            import base64 as _b64
            body = _b64.b64decode(res["content_b64"])
            from ...services import pipeline as _pipe
            from ...core.deps import data_dir
            if res.get("content_hash"):
                try:
                    path = os.path.join(data_dir(), "raw", res["content_hash"])
                    if not os.path.exists(path):
                        open(path, "wb").write(body)
                except Exception:
                    pass
            last = [p for p in STORE["prices"] if p.get("product_id") == job["target_id"]][-3:]
            prices, change, alerts = _pipe.ingest_body(job, body, last)
            bundle.update({"prices": prices, "change": change, "alerts": alerts})
        except Exception:
            pass
    _audit(email, "job.result", f"{res['job_id'][:16]}:{bundle.get('status')}")
    return _apply_result(bundle, job["url"], job["project_id"], job["target_id"])



# ---- data listings ----
@router.get("/api/v1/prices")
def list_prices(page: int = 1, size: int = 20, product_id: int = 0, sort: str = "", order: str = "asc",
                authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    cmap = {"price": "price", "observed_at": "observed_ts", "product_id": "product_id"}
    if product_id:
        t = next((x for x in STORE["targets"] if x.get("id") == product_id), None)
        if (t and t.get("org", 1) != org) or (t is None and org != 1):
            raise HTTPException(404, "not found")
        return repo.page("prices", page, size, sort, order,
                         filters={"product_id": product_id}, colmap=cmap)
    tids = [t["id"] for t in STORE["targets"] if t.get("org", 1) == org]
    known = {t.get("id") for t in STORE["targets"]}
    res = repo.page("prices", page, size, sort, order,
                    in_filters={"product_id": tids} if tids else None, colmap=cmap)
    if not tids:
        return res
    # pre-org legacy rows whose target is unknown stay visible to org 1
    extra = [p for p in STORE["prices"] if p.get("product_id") not in known]
    if org == 1 and extra and page == 1 and not sort:
        res["items"] = (extra + res["items"])[:size]
        res["total"] += len(extra)
    return res


@router.get("/api/v1/articles")
def list_articles(page: int = 1, size: int = 20,
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["articles"], org), page, size)


@router.post("/api/v1/articles")
def create_article(a: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    item = {"id": len(STORE["articles"]) + 1, "org": org, **a}
    STORE["articles"].append(item)
    _audit(email, "article.create", (a.get("title", "") or "")[:120])
    return item


@router.delete("/api/v1/articles/{aid}")
def delete_article(aid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    a = next((x for x in STORE["articles"] if x.get("id") == aid), None)
    if not a or _visible_by_org([a], org) != [a]:
        raise HTTPException(404, "article not found")
    STORE["articles"][:] = [x for x in STORE["articles"] if x.get("id") != aid]
    _audit(email, "article.delete", str(aid))
    return {"ok": True}


@router.get("/api/v1/reviews")
def list_reviews(page: int = 1, size: int = 20, product_id: int = 0,
                 authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    tids = {t["id"] for t in STORE["targets"] if t.get("org", 1) == org}
    items = [r for r in STORE["reviews"]
             if r.get("product_id") in tids and (not product_id or r.get("product_id") == product_id)]
    return paginate(items, page, size)


@router.get("/api/v1/changes")
def list_changes(page: int = 1, size: int = 20,
                 authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["changes"], org, "target"), page, size)


@router.get("/api/v1/search")
def search(q: str = "", scope: str = "all", mode: str = "hybrid", kind: str = "",
           limit: int = 20, offset: int = 0, risk_min: float = None,
           risk_max: float = None, source: str = "", date_from: str = "",
           date_to: str = "", investigation_id: int = None,
           confidence_min: float = None, confidence_max: float = None,
           status: str = "",
           authorization: str = Header(""), x_api_key: str = Header("")):
    """Unified intelligence search: keyword, exact, semantic and hybrid modes
    over one engine. Org-scoped; no AI required for any mode. Legacy callers
    using q/scope keep the {items, facets} shape plus total/mode."""
    from ...search.unified import unified_search
    _, org, _ = _ctx(authorization, x_api_key)
    kinds = None
    if kind:
        kinds = [kind]
    elif scope and scope != "all":
        kinds = [scope]
    items, total = unified_search(STORE, org, q, mode=mode, kinds=kinds,
                                 limit=limit, offset=offset, risk_min=risk_min,
                                 risk_max=risk_max, source=source or "",
                                 date_from=date_from or "", date_to=date_to or "",
                                 investigation_id=investigation_id,
                                 confidence_min=confidence_min,
                                 confidence_max=confidence_max,
                                 status=status or "")
    facets = {}
    for it in items:
        facets[it.get("kind", "?")] = facets.get(it.get("kind", "?"), 0) + 1
    return {"items": items, "facets": facets, "total": total, "mode": mode,
            "offset": offset}



@router.post("/api/v1/reviews/import", tags=["intelligence"])
def reviews_import(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...analytics.ml import sentiment
    email, org, _ = _need(authorization, "collect", x_api_key)
    n = 0
    for r in spec.get("reviews", [])[:1000]:
        t = next((x for x in STORE["targets"] if x.get("id") == r.get("product_id")), None)
        if t and t.get("org", 1) != org:
            continue
        item = {"id": len(STORE["reviews"]) + 1, "product_id": r.get("product_id"),
                "rating": r.get("rating"), "text": (r.get("text", "") or "")[:5000],
                "sentiment": sentiment(r.get("text", ""))}
        STORE["reviews"].append(item)
        n += 1
    _audit(email, "reviews.import", str(n))
    return {"imported": n}


@router.get("/api/v1/reviews/summary", tags=["intelligence"])
def reviews_summary(product_id: int = 0,
                    authorization: str = Header(""), x_api_key: str = Header("")):
    from ...intelligence.reviews import analyze
    _, org, _ = _ctx(authorization, x_api_key)
    tids = {t["id"] for t in STORE["targets"] if t.get("org", 1) == org}
    items = [r for r in STORE["reviews"]
             if r.get("product_id") in tids and (not product_id or r.get("product_id") == product_id)]
    out = analyze(items)
    out["product_id"] = product_id
    return out


# ---- schedules + worker ----
@router.post("/api/v1/schedules")
def create_schedule(s: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _need(authorization, "collect", x_api_key)
    item = {"id": len(STORE["schedules"]) + 1, "status": "active",
            "next_run": sched.next_run(s.get("kind", "interval"),
                                       s.get("every_min", 60),
                                       cron=s.get("cron", "")).isoformat(), **s}
    STORE["schedules"].append(item)
    _audit(email, "schedule.create", str(item["id"]))
    return item


@router.get("/api/v1/schedules")
def list_schedules(page: int = 1, size: int = 20,
                   authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["schedules"], org, "project"), page, size)


@router.get("/api/v1/schedules/{sid}")
def get_schedule(sid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    s = next((x for x in STORE["schedules"] if x.get("id") == sid), None)
    if not s or _visible_by_org([s], org, "project") != [s]:
        raise HTTPException(404, "schedule not found")
    return s


@router.put("/api/v1/schedules/{sid}")
def update_schedule(sid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    s = next((x for x in STORE["schedules"] if x.get("id") == sid), None)
    if not s or _visible_by_org([s], org, "project") != [s]:
        raise HTTPException(404, "schedule not found")
    for f in ("kind", "cron", "url"):
        if f in spec and spec[f] is not None:
            s[f] = str(spec[f])[:2000]
    for f in ("every_min", "project_id", "target_id"):
        if f in spec and spec[f] is not None:
            try:
                s[f] = int(spec[f])
            except (TypeError, ValueError):
                raise HTTPException(400, f"{f} must be an integer")
    if "status" in spec:
        if spec["status"] not in ("active", "paused"):
            raise HTTPException(400, "status must be active|paused")
        s["status"] = spec["status"]
    s["next_run"] = sched.next_run(s.get("kind", "interval"),
                                   s.get("every_min", 60),
                                   cron=s.get("cron", "")).isoformat()
    repo.sync("schedules", s)
    _audit(email, "schedule.update", str(sid))
    return s


@router.delete("/api/v1/schedules/{sid}")
def delete_schedule(sid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    s = next((x for x in STORE["schedules"] if x.get("id") == sid), None)
    if not s or _visible_by_org([s], org, "project") != [s]:
        raise HTTPException(404, "schedule not found")
    STORE["schedules"][:] = [x for x in STORE["schedules"] if x.get("id") != sid]
    _audit(email, "schedule.delete", str(sid))
    return {"ok": True}


@router.post("/api/v1/schedules/{sid}/enable")
def enable_schedule(sid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    s = next((x for x in STORE["schedules"] if x.get("id") == sid), None)
    if not s or _visible_by_org([s], org, "project") != [s]:
        raise HTTPException(404, "schedule not found")
    s["status"] = "active"
    repo.sync("schedules", s)
    _audit(email, "schedule.enable", str(sid))
    return {"ok": True}


@router.post("/api/v1/schedules/{sid}/disable")
def disable_schedule(sid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    s = next((x for x in STORE["schedules"] if x.get("id") == sid), None)
    if not s or _visible_by_org([s], org, "project") != [s]:
        raise HTTPException(404, "schedule not found")
    s["status"] = "paused"
    repo.sync("schedules", s)
    _audit(email, "schedule.disable", str(sid))
    return {"ok": True}


@router.post("/api/v1/schedules/{sid}/run")
def run_schedule_now(sid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Run one schedule immediately: creates a collection job from it."""
    import datetime
    email, org, _ = _need(authorization, "collect", x_api_key)
    s = next((x for x in STORE["schedules"] if x.get("id") == sid), None)
    if not s or _visible_by_org([s], org, "project") != [s]:
        raise HTTPException(404, "schedule not found")
    if not s.get("url"):
        raise HTTPException(400, "schedule has no url")
    job = {"job_id": uuid.uuid4().hex, "trace_id": uuid.uuid4().hex,
           "project_id": s.get("project_id", 1), "target_id": s.get("target_id", 1),
           "url": s.get("url", ""), "strategy": "AUTO",
           "plan": {"plan": ["DIRECT_HTTP"], "reasons": ["manual-schedule-run"]},
           "status": "queued", "created_at": time.time(), "org": org,
           "estimated_cost": 0.0001}
    STORE["jobs"].append(job)
    now = datetime.datetime.utcnow()
    s["last_run"] = now.isoformat()
    s["next_run"] = sched.next_run(s.get("kind", "interval"),
                                   s.get("every_min", 60),
                                   cron=s.get("cron", "")).isoformat()
    repo.sync("schedules", s)
    _audit(email, "schedule.run", f"{sid}:{job['job_id'][:8]}")
    inc("jobs_total")
    return job


@router.post("/api/v1/worker/tick")
def worker_tick(authorization: str = Header(""), x_api_key: str = Header("")):
    """Execute due schedules: creates collection jobs. Called by systemd
    worker or cron; also powers the UI 'Run scheduler' button."""
    _need(authorization, "collect", x_api_key)
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
                   "status": "queued", "created_at": time.time(), "estimated_cost": 0.0001,
                   "org": next((t.get("org", 1) for t in STORE["targets"]
                                if t.get("id") == s.get("target_id")), 1)}
            if job["url"]:
                STORE["jobs"].append(job)
                fired.append(job["job_id"])
                _audit(authorization[:12] if authorization else "anon",
                       "job.scheduled", job["job_id"])
            s["last_run"] = now.isoformat()
            s["next_run"] = sched.next_run(s.get("kind", "interval"),
                                           s.get("every_min", 60),
                                           cron=s.get("cron", "")).isoformat()
            repo.sync("schedules", s)
    inc("jobs_total", len(fired))
    return {"fired": fired}



# ---- job lifecycle: cancel / retry / dead-letter ----
@router.post("/api/v1/jobs/{job_id}/cancel", tags=["jobs"])
def cancel_job(job_id: str, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    job = next((j for j in STORE["jobs"]
                if j.get("job_id") == job_id and j.get("org", 1) == org), None)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] not in ("queued",):
        raise HTTPException(409, f"cannot cancel job in status {job['status']}")
    job["status"] = "cancelled"
    repo.sync("jobs", job)
    _audit(email, "job.cancel", job_id)
    return job


@router.post("/api/v1/jobs/{job_id}/retry", tags=["jobs"])
def retry_job(job_id: str, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    job = next((j for j in STORE["jobs"]
                if j.get("job_id") == job_id and j.get("org", 1) == org), None)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] not in ("failed", "cancelled"):
        raise HTTPException(409, f"cannot retry job in status {job['status']}")
    job["status"] = "queued"
    job["retries"] = job.get("retries", 0) + 1
    repo.sync("jobs", job)
    _audit(email, "job.retry", job_id)
    return job


@router.get("/api/v1/dlq", tags=["jobs"])
def dead_letters():
    """Dead-letter queue depth (Redis when available, else empty — honest)."""
    r = get_redis()
    if r is None:
        return {"items": [], "backend": "none"}
    try:
        n = r.llen("webintel:queue:dlq")
        return {"items": [], "depth": n, "backend": "redis",
                "note": "depth only; use redis-cli to inspect payloads"}
    except Exception as e:
        return {"items": [], "backend": "error", "detail": str(e)[:200]}


