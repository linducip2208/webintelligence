"""catalog routes (split from main.py; behavior unchanged)."""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from ..shared import (
    HTTPException,
    Header,
    ProjectIn,
    STORE,
    TargetIn,
    _audit,
    _check_url,
    _ctx,
    _porg,
    _sorted,
    _torg,
    _visible_by_org,
    inc,
    paginate,
    repo,
    _need,
)

router = APIRouter()

# ---- projects ----
@router.post("/api/v1/projects")
def create_project(p: ProjectIn, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entitlements as _e
    email, org, _ = _need(authorization, "collect", x_api_key)
    ok, why = _e.check(STORE, org, "projects")
    if not ok:
        raise HTTPException(402, why)
    item = {"id": len(STORE["projects"]) + 1, "org": org, "name": p.name, "description": p.description}
    STORE["projects"].append(item)
    inc("projects_total")
    _audit(email, "project.create", item["name"])
    return item

@router.get("/api/v1/projects")
def list_projects(page: int = 1, size: int = 20, q: str = "", sort: str = "", order: str = "asc",
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [x for x in STORE["projects"] if x.get("org", 1) == org]
    if q:
        items = [x for x in items if q.lower() in x["name"].lower()]
    return paginate(_sorted(items, sort, order), page, size)


def _project_detail(pid: int, org: int):
    p = next((x for x in STORE["projects"] if x.get("id") == pid and x.get("org", 1) == org), None)
    if not p:
        return None
    tids = [t["id"] for t in STORE["targets"] if t.get("project_id") == pid]
    jobs = [j for j in STORE["jobs"] if j.get("project_id") == pid]
    return {**p, "targets": tids,
            "target_count": len(tids), "job_count": len(jobs),
            "jobs_success": sum(1 for j in jobs if j.get("status") == "success"),
            "jobs_failed": sum(1 for j in jobs if j.get("status") == "failed"),
            "report_count": sum(1 for r in STORE["reports"] if r.get("project") == p.get("name") or r.get("project_id") == pid),
            "alert_count": sum(1 for a in STORE["alerts"] if a.get("project_id") == pid)}


@router.get("/api/v1/projects/{pid}")
def get_project(pid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    d = _project_detail(pid, org)
    if not d:
        raise HTTPException(404, "project not found")
    return d


@router.put("/api/v1/projects/{pid}")
def update_project(pid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    p = next((x for x in STORE["projects"] if x.get("id") == pid and x.get("org", 1) == org), None)
    if not p:
        raise HTTPException(404, "project not found")
    if "name" in spec and spec["name"]:
        p["name"] = spec["name"][:200]
    if "description" in spec:
        p["description"] = (spec["description"] or "")[:2000]
    repo.sync("projects", p)
    _audit(email, "project.update", p["name"][:120])
    return p


@router.delete("/api/v1/projects/{pid}")
def delete_project(pid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    p = next((x for x in STORE["projects"] if x.get("id") == pid and x.get("org", 1) == org), None)
    if not p:
        raise HTTPException(404, "project not found")
    blocking = [t["id"] for t in STORE["targets"] if t.get("project_id") == pid]
    blocking += [j.get("job_id", "") for j in STORE["jobs"] if j.get("project_id") == pid]
    if blocking:
        raise HTTPException(409, f"project has {len(blocking)} targets/jobs; delete them first")
    STORE["projects"][:] = [x for x in STORE["projects"] if x.get("id") != pid]
    _audit(email, "project.delete", p["name"][:120])
    return {"ok": True}



# ---- targets ----
@router.post("/api/v1/targets")
def create_target(t: TargetIn, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entitlements as _e
    email, org, _ = _need(authorization, "collect", x_api_key)
    ok, why = _e.check(STORE, org, "targets")
    if not ok:
        raise HTTPException(402, why)
    _check_url(t.url)
    item = t.model_dump() | {"id": len(STORE["targets"]) + 1, "org": org, "attempts": 0,
                             "successes": 0, "failures": 0}
    STORE["targets"].append(item)
    _audit(email, "target.create", t.url[:120])
    return item


@router.get("/api/v1/targets")
def list_targets(page: int = 1, size: int = 20, q: str = "", sort: str = "", order: str = "asc",
                 authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [x for x in STORE["targets"] if x.get("org", 1) == org]
    if q:
        items = [x for x in items if q.lower() in (x["domain"] + x["url"]).lower()]
    return paginate(_sorted(items, sort, order), page, size)


def _target_detail(tid: int, org: int):
    t = next((x for x in STORE["targets"] if x.get("id") == tid and x.get("org", 1) == org), None)
    if not t:
        return None
    jobs = [j for j in STORE["jobs"] if j.get("target_id") == tid]
    prices = [p for p in STORE["prices"] if p.get("product_id") == tid][-50:]
    changes = [c for c in STORE["changes"] if c.get("target_id") == tid][-20:]
    alerts = [a for a in STORE["alerts"]
              if a.get("project_id") == t.get("project_id")][-20:]
    last = next((j for j in reversed(jobs)), None)
    return {**t, "job_count": len(jobs),
            "last_scan": (last.get("finished_at") or last.get("created_at")) if last else None,
            "last_status": last.get("status") if last else None,
            "recent_jobs": [{k: j.get(k) for k in ("job_id", "status", "strategy", "created_at", "finished_at", "estimated_cost")} for j in jobs[-10:]],
            "recent_prices": prices, "recent_changes": changes, "recent_alerts": alerts}


@router.get("/api/v1/targets/{tid}")
def get_target(tid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    d = _target_detail(tid, org)
    if not d:
        raise HTTPException(404, "target not found")
    return d


@router.put("/api/v1/targets/{tid}")
def update_target(tid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    t = next((x for x in STORE["targets"] if x.get("id") == tid and x.get("org", 1) == org), None)
    if not t:
        raise HTTPException(404, "target not found")
    if "url" in spec and spec["url"]:
        _check_url(spec["url"])
        t["url"] = spec["url"][:2000]
    for f in ("domain", "source_type", "country", "language"):
        if f in spec and spec[f] is not None:
            t[f] = str(spec[f])[:200]
    if "tags" in spec:
        t["tags"] = [str(x)[:80] for x in (spec["tags"] or [])][:20]
    if "notes" in spec:
        t["notes"] = str(spec["notes"] or "")[:2000]
    repo.sync("targets", t)
    _audit(email, "target.update", t["url"][:120])
    return t


@router.delete("/api/v1/targets/{tid}")
def delete_target(tid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    t = next((x for x in STORE["targets"] if x.get("id") == tid and x.get("org", 1) == org), None)
    if not t:
        raise HTTPException(404, "target not found")
    njobs = sum(1 for j in STORE["jobs"] if j.get("target_id") == tid)
    if njobs:
        raise HTTPException(409, f"target has {njobs} jobs; delete them first")
    STORE["targets"][:] = [x for x in STORE["targets"] if x.get("id") != tid]
    _audit(email, "target.delete", t["url"][:120])
    return {"ok": True}


@router.post("/api/v1/targets/bulk-delete")
def bulk_delete_targets(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    deleted, skipped = [], {}
    for tid in (spec.get("ids") or [])[:500]:
        t = next((x for x in STORE["targets"] if x.get("id") == tid and x.get("org", 1) == org), None)
        if not t:
            skipped[tid] = "not found"
            continue
        if any(j.get("target_id") == tid for j in STORE["jobs"]):
            skipped[tid] = "has jobs"
            continue
        STORE["targets"][:] = [x for x in STORE["targets"] if x.get("id") != tid]
        deleted.append(tid)
    _audit(email, "target.bulk-delete", f"{len(deleted)} ok, {len(skipped)} skipped")
    return {"ok": True, "deleted": deleted, "skipped": skipped}



# ---- connectors ----
@router.post("/api/v1/connectors", tags=["sources"])
def register_connector(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import connectors as _c
    from ...services import entitlements as _e
    email, org, _ = _need(authorization, "collect", x_api_key)
    ok, why = _e.check(STORE, org, "connectors")
    if not ok:
        raise HTTPException(402, why)
    errs = _c.validate_manifest(spec.get("manifest", {}))
    if errs:
        raise HTTPException(400, "; ".join(errs))
    item = {"id": len(STORE["connectors"]) + 1, "org": org, "enabled": True, **spec}
    STORE["connectors"].append(item)
    _audit(email, "connector.register", item.get("name", "")[:120])
    return item


@router.get("/api/v1/connectors", tags=["sources"])
def list_connectors(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    def _safe(c):
        cfg = {k: ("***" if any(w in k.lower() for w in ("key", "secret", "token", "password")) else v)
               for k, v in (c.get("config", {}) or {}).items()}
        return {**c, "config": cfg}
    return {"items": [_safe(c) for c in _visible_by_org(STORE["connectors"], org)]}


@router.get("/api/v1/connectors/match", tags=["sources"])
def match_connector(capability: str = "", category: str = ""):
    from ...services import connectors as _c
    return {"items": _c.match(STORE["connectors"], capability, category)}


def _safe_connector(c: dict) -> dict:
    cfg = {k: ("***" if any(w in k.lower() for w in ("key", "secret", "token", "password")) else v)
           for k, v in (c.get("config", {}) or {}).items()}
    return {**c, "config": cfg}


@router.get("/api/v1/connectors/{cid}", tags=["sources"])
def get_connector(cid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    c = next((x for x in STORE["connectors"] if x.get("id") == cid and x.get("org", 1) == org), None)
    if not c:
        raise HTTPException(404, "connector not found")
    return _safe_connector(c)


@router.put("/api/v1/connectors/{cid}", tags=["sources"])
def update_connector(cid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import connectors as _c
    email, org, _ = _need(authorization, "configure", x_api_key)
    c = next((x for x in STORE["connectors"] if x.get("id") == cid and x.get("org", 1) == org), None)
    if not c:
        raise HTTPException(404, "connector not found")
    if "manifest" in spec:
        errs = _c.validate_manifest(spec["manifest"])
        if errs:
            raise HTTPException(400, "; ".join(errs))
        c["manifest"] = spec["manifest"]
    for f in ("name", "category", "version"):
        if f in spec and spec[f] is not None:
            c[f] = str(spec[f])[:200]
    if "enabled" in spec:
        c["enabled"] = bool(spec["enabled"])
    if "config" in spec and isinstance(spec["config"], dict):
        cfg = dict(c.get("config", {}) or {})
        for k, v in spec["config"].items():
            if v == "***":
                continue  # masked value means keep existing secret
            cfg[k] = v
        c["config"] = cfg
    repo.sync("connectors", c)
    _audit(email, "connector.update", c.get("name", "")[:120])
    return _safe_connector(c)


@router.delete("/api/v1/connectors/{cid}", tags=["sources"])
def delete_connector(cid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    c = next((x for x in STORE["connectors"] if x.get("id") == cid and x.get("org", 1) == org), None)
    if not c:
        raise HTTPException(404, "connector not found")
    STORE["connectors"][:] = [x for x in STORE["connectors"] if x.get("id") != cid]
    _audit(email, "connector.delete", c.get("name", "")[:120])
    return {"ok": True}


@router.post("/api/v1/connectors/{cid}/enable", tags=["sources"])
def enable_connector(cid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    c = next((x for x in STORE["connectors"] if x.get("id") == cid and x.get("org", 1) == org), None)
    if not c:
        raise HTTPException(404, "connector not found")
    c["enabled"] = True
    repo.sync("connectors", c)
    _audit(email, "connector.enable", c.get("name", "")[:120])
    return {"ok": True}


@router.post("/api/v1/connectors/{cid}/disable", tags=["sources"])
def disable_connector(cid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    c = next((x for x in STORE["connectors"] if x.get("id") == cid and x.get("org", 1) == org), None)
    if not c:
        raise HTTPException(404, "connector not found")
    c["enabled"] = False
    repo.sync("connectors", c)
    _audit(email, "connector.disable", c.get("name", "")[:120])
    return {"ok": True}


@router.post("/api/v1/targets/{tid}/test", tags=["sources"])
def target_test(tid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Real connection test: strategy decision + live direct fetch attempt.
    Updates the persisted target profile (attempts/latency/preferred)."""
    from ...services import pipeline as _pipe
    from ...services import targets as _tgt
    from ...services import decision as _dec
    email, org, _ = _need(authorization, "collect", x_api_key)
    t = next((x for x in STORE["targets"]
              if x.get("id") == tid and x.get("org", 1) == org), None)
    if not t:
        raise HTTPException(404, "target not found")
    engine = _dec.Engine()
    plan = engine.decide(t, _dec.Policy(), {"own_proxy": {"healthy": True},
                                            "brightdata": {"healthy": False,
                                                           "configured": False}})
    fetched = _pipe.fetch_direct(t["url"], timeout_s=20)
    ok = fetched.get("ok") and fetched.get("http_status") == 200
    prof = _tgt.record_attempt(t.get("profile", {}), plan["plan"][0] if plan["plan"] else "DIRECT_HTTP",
                               ok, fetched.get("latency_ms", 0), 0.0)
    t["profile"] = prof
    t["attempts"] = prof.get("attempts", 0)
    t["successes"] = prof.get("successes", 0)
    t["failures"] = prof.get("failures", 0)
    t["preferred_strategy"] = _tgt.preferred_strategy(prof)
    repo.sync("targets", t)
    _audit(email, "target.test", t["url"][:120])
    return {"ok": ok, "http_status": fetched.get("http_status"),
            "latency_ms": fetched.get("latency_ms"),
            "strategy": plan["plan"][0] if plan["plan"] else None,
            "profile": {k: prof.get(k) for k in ("attempts", "successes", "failures")},
            "error": fetched.get("error", "")}


@router.post("/api/v1/connectors/{cid}/test", tags=["sources"])
def connector_test(cid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...connectors.runners import execute
    email, org, _ = _need(authorization, "collect", x_api_key)
    c = next((x for x in STORE["connectors"]
              if x.get("id") == cid and x.get("org", 1) == org), None)
    if not c:
        raise HTTPException(404, "connector not found")
    out = execute(c)
    import time as _t
    c["health"] = {"last_run": _t.time(), "ok": bool(out.get("ok")),
                   "count": len(out.get("items", [])), "error": out.get("error", "")[:200]}
    repo.sync("connectors", c)
    _audit(email, "connector.test", f"{c.get('name', '')}:{out.get('ok')}"[:120])
    return {"ok": out.get("ok", False), "count": len(out.get("items", [])),
            "error": out.get("error", ""), "sample": out.get("items", [])[:3]}


@router.post("/api/v1/connectors/{cid}/execute", tags=["sources"])
def connector_execute(cid: int, spec: dict, authorization: str = Header(""),
                      x_api_key: str = Header("")):
    from ...connectors.runners import execute
    from ...services import datasets as _d
    email, org, _ = _need(authorization, "collect", x_api_key)
    c = next((x for x in STORE["connectors"]
              if x.get("id") == cid and x.get("org", 1) == org), None)
    if not c:
        raise HTTPException(404, "connector not found")
    out = execute(c)
    if not out.get("ok"):
        _audit(email, "connector.execute.failed", c.get("name", ""))
        return out
    saved = {}
    if spec.get("save_articles"):
        n = 0
        for it in out.get("items", [])[:200]:
            STORE["articles"].append({"id": len(STORE["articles"]) + 1, "org": org,
                                      "publisher": c.get("name", ""),
                                      "title": it.get("title", ""),
                                      "url": it.get("url", "")})
            n += 1
        saved["articles"] = n
    if spec.get("save_dataset"):
        ds = {"id": len(STORE["datasets"]) + 1, "org": org, "name": spec.get("dataset", c.get("name", "")),
              "kind": "connector", "status": "published"}
        STORE["datasets"].append(ds)
        v = _d.publish(STORE["dsversions"], ds["id"], out.get("items", [])[:2000],
                       {"source": "connector", "connector_id": cid})
        saved["dataset_version"] = v["version"]
    _audit(email, "connector.execute", f"{c.get('name')}:{len(out.get('items', []))}")
    out["saved"] = saved
    import time as _t
    c["health"] = {"last_run": _t.time(), "ok": bool(out.get("ok")),
                   "count": len(out.get("items", [])), "error": out.get("error", "")[:200]}
    repo.sync("connectors", c)
    return out


