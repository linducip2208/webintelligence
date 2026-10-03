"""ops routes (split from main.py; behavior unchanged)."""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from ..shared import (
    HTTPException,
    Header,
    STORE,
    _NONCES,
    _audit,
    _ctx,
    _need,
    _require_auth,
    _visible_by_org,
    os,
    paginate,
    repo,
    time,
)

router = APIRouter()

@router.get("/api/v1/billing/plans", tags=["admin"])
def billing_plans():
    from ...services import entitlements as _e
    return {"plans": _e.PLANS}


@router.get("/api/v1/billing/usage", tags=["admin"])
def billing_usage(authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entitlements as _e
    _, org, _ = _ctx(authorization, x_api_key)
    return _e.usage(STORE, org)


@router.post("/api/v1/billing/plan", tags=["admin"])
def billing_set_plan(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entitlements as _e
    email, org, role = _need(authorization, "configure", x_api_key)
    if role != "owner":
        raise HTTPException(403, "owners only")
    if spec.get("plan") not in _e.PLANS:
        raise HTTPException(400, "unknown plan")
    target_org = spec.get("org_id", org)
    o = next((x for x in STORE["orgs"] if x.get("id") == target_org), None)
    if not o:
        raise HTTPException(404, "organization not found")
    if o["id"] != org and role != "owner":
        raise HTTPException(403, "cross-org denied")
    o["plan"] = spec["plan"]
    repo.sync("orgs", o)
    _audit(email, "billing.plan", f"{target_org}->{spec['plan']}")
    return {"ok": True, "plan": o["plan"]}


# ---- audit ----
@router.get("/api/v1/audit")
def list_audit(page: int = 1, size: int = 20):
    return paginate(list(reversed(STORE["audit"])), page, size)



# ---- organizations / RBAC / API keys ----
@router.post("/api/v1/orgs", tags=["admin"])
def create_org(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _ctx(authorization, x_api_key)
    slug = spec.get("slug", spec.get("name", "").lower().replace(" ", "-"))
    if any(o.get("slug") == slug for o in STORE["orgs"]):
        raise HTTPException(409, "organization slug exists")
    item = {"id": len(STORE["orgs"]) + 1, "name": spec.get("name", ""),
            "slug": slug}
    STORE["orgs"].append(item)
    STORE["memberships"].append({"org_id": item["id"], "email": email, "role": "owner"})
    _audit(email, "org.create", item["name"])
    return item


@router.get("/api/v1/orgs", tags=["admin"])
def list_orgs():
    return {"items": [{k: v for k, v in o.items() if k != "branding"} for o in STORE["orgs"]]}


@router.get("/api/v1/orgs/{oid}/branding", tags=["admin"])
def get_branding(oid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    o = next((x for x in STORE["orgs"] if x.get("id") == oid), None)
    if not o or o.get("id") != org:
        raise HTTPException(404, "organization not found")
    return {"branding": o.get("branding", {})}


@router.put("/api/v1/orgs/{oid}/branding", tags=["admin"])
def set_branding(oid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import commercial as _cm
    email, org, _ = _need(authorization, "configure", x_api_key)
    o = next((x for x in STORE["orgs"] if x.get("id") == oid and x.get("id") == org), None)
    if not o:
        raise HTTPException(404, "organization not found")
    errs = _cm.validate_branding(spec.get("branding", {}))
    if errs:
        raise HTTPException(400, "; ".join(errs))
    o["branding"] = spec["branding"]
    repo.sync("orgs", o)
    _audit(email, "org.branding", o["slug"])
    return {"ok": True}


@router.get("/api/v1/verticals", tags=["admin"])
def list_verticals():
    from ...services import commercial as _cm
    return {"verticals": sorted(_cm.VERTICALS)}


@router.get("/api/v1/verticals/{name}", tags=["admin"])
def get_vertical(name: str):
    from ...services import commercial as _cm
    v = _cm.get_vertical(name)
    if not v:
        raise HTTPException(404, "unknown vertical")
    return {"name": name.lower(), **v}


@router.post("/api/v1/verticals/{name}/apply", tags=["admin"])
def apply_vertical(name: str, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import commercial as _cm
    email, org, _ = _need(authorization, "collect", x_api_key)
    v = _cm.get_vertical(name)
    if not v:
        raise HTTPException(404, "unknown vertical")
    made = []
    for w in v.get("watch", []):
        if any(x.get("kind") == w["kind"] and x.get("value") == w["value"]
               and x.get("org", 1) == org for x in STORE["watchlists"]):
            continue
        item = {"id": len(STORE["watchlists"]) + 1, "org": org, **w}
        STORE["watchlists"].append(item)
        made.append(item["id"])
    _audit(email, "vertical.apply", f"{name}:{made}")
    return {"ok": True, "watchlists": made, "questions": v.get("questions", [])}


@router.get("/api/v1/roles", tags=["admin"])
def roles_matrix():
    from ...services.rbac import MATRIX
    return {"roles": {k: sorted(v) for k, v in MATRIX.items()}}


@router.post("/api/v1/memberships", tags=["admin"])
def add_member(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "users")
    item = {"org_id": spec.get("org_id", org), "email": spec.get("email"),
            "role": spec.get("role", "viewer")}
    STORE["memberships"].append(item)
    _audit(email, "member.add", f"{item['email']}->{item['role']}")
    return item


@router.post("/api/v1/apikeys", tags=["admin"])
def create_apikey(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    import hashlib as _h
    import secrets as _s
    email, org, _ = _need(authorization, "configure")
    raw = "wi_" + _s.token_urlsafe(32)
    item = {"id": len(STORE["apikeys"]) + 1, "org_id": spec.get("org_id", org),
            "name": spec.get("name", ""), "key_hash": _h.sha256(raw.encode()).hexdigest(),
            "scopes": spec.get("scopes", ["read"]), "revoked": False,
            "expires_at": spec.get("expires_at", 0) or 0, "last_used": 0}
    STORE["apikeys"].append(item)
    _audit(email, "apikey.create", item["name"])
    return {**item, "key": raw}  # shown once


@router.get("/api/v1/apikeys", tags=["admin"])
def list_apikeys():
    return {"items": [{k: v for k, v in x.items() if k != "key_hash"} for x in STORE["apikeys"]]}


@router.post("/api/v1/apikeys/{kid}/revoke", tags=["admin"])
def revoke_apikey(kid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _need(authorization, "configure")
    k = next((x for x in STORE["apikeys"] if x["id"] == kid), None)
    if not k:
        raise HTTPException(404, "not found")
    k["revoked"] = True
    repo.sync("apikeys", k)
    _audit(email, "apikey.revoke", k["name"])
    return {"ok": True}



# ---- watchlists ----
@router.post("/api/v1/watchlists", tags=["monitoring"])
def create_watchlist(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _need(authorization, "collect", x_api_key)
    item = {"id": len(STORE["watchlists"]) + 1, "org": org, **spec}
    STORE["watchlists"].append(item)
    return item


@router.get("/api/v1/watchlists", tags=["monitoring"])
def list_watchlists(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return {"items": _visible_by_org(STORE["watchlists"], org)}


@router.delete("/api/v1/watchlists/{wid}", tags=["monitoring"])
def delete_watchlist(wid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _need(authorization, "collect", x_api_key)
    STORE["watchlists"][:] = [w for w in STORE["watchlists"] if w["id"] != wid]
    return {"ok": True}


@router.post("/api/v1/watchlists/check", tags=["monitoring"])
def watchlist_check(spec: dict):
    from ...services import watchlists as _w
    return {"matches": _w.match(STORE["watchlists"], spec)}


@router.post("/api/v1/watchlists/{wid}/evaluate", tags=["monitoring"])
def watchlist_evaluate(wid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Run a watchlist against recent prices/articles/events NOW.
    Matches create alerts (cooldown-guarded)."""
    from ...services import watchlists as _w
    from ...services import alertguard as _ag
    email, org, _ = _need(authorization, "collect", x_api_key)
    w = next((x for x in STORE["watchlists"]
              if x.get("id") == wid and x.get("org", 1) == org), None)
    if not w:
        raise HTTPException(404, "watchlist not found")
    pool = ([{"value": p.get("product_id"), "text": f"{p.get('price')} {p.get('currency')}"}
             for p in STORE["prices"][-200:]] +
            [{"value": a.get("title", ""), "text": a.get("title", "")} for a in STORE["articles"][-200:]] +
            [{"value": e.get("entity_key", ""), "text": e.get("type", "")} for e in STORE["events"][-200:]])
    hits = [it for it in pool if w["id"] in _w.match([w], it)]
    fired = 0
    for h in hits[:20]:
        key = f"watchlist:{wid}:{h['value']}"
        if _ag.should_fire(key, STORE["alert_hist"], 86400):
            STORE["alerts"].append({"id": len(STORE["alerts"]) + 1, "rule": "watchlist_hit",
                                    "channel": "inapp",
                                    "message": f"Watchlist '{w.get('value')}' matched: {h['value']}"[:300],
                                    "project_id": 0, "is_read": False})
            fired += 1
    try:
        repo.kv_set("alert_hist", STORE["alert_hist"])
    except Exception:
        pass
    _audit(email, "watchlist.evaluate", f"{wid}:{len(hits)}")
    return {"matches": len(hits), "alerts": fired}



# ---- workflows ----
@router.post("/api/v1/workflows", tags=["monitoring"])
def create_workflow(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _need(authorization, "collect", x_api_key)
    item = {"id": len(STORE["workflows"]) + 1, "org": org, "enabled": True,
            "version": 1, **{k: v for k, v in spec.items() if k != "version"}}
    STORE["workflows"].append(item)
    return item


@router.put("/api/v1/workflows/{wid}", tags=["monitoring"])
def update_workflow(wid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    wf = next((x for x in STORE["workflows"] if x.get("id") == wid and x.get("org", 1) == org), None)
    if not wf:
        raise HTTPException(404, "workflow not found")
    if "definition" in spec:
        wf["definition"] = spec["definition"]
        wf["version"] = wf.get("version", 1) + 1
    if "enabled" in spec:
        wf["enabled"] = bool(spec["enabled"])
    if "paused" in spec:
        wf["paused"] = bool(spec["paused"])
    if "name" in spec:
        wf["name"] = spec["name"]
    repo.sync("workflows", wf)
    _audit(email, "workflow.update", f"{wid}@v{wf['version']}")
    return wf


@router.post("/api/v1/workflows/{wid}/retry", tags=["monitoring"])
def workflow_retry(wid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Idempotent retry: same event replays to the same idempotency keys,
    returning the ORIGINAL run when nothing new executes."""
    from ...services import workflows as _w
    _, org, _ = _need(authorization, "collect", x_api_key)
    wf = next((x for x in STORE["workflows"]
               if x.get("id") == wid and x.get("enabled") and x.get("org", 1) == org), None)
    if not wf:
        raise HTTPException(404, "workflow not found/disabled")
    if wf.get("paused"):
        raise HTTPException(409, "workflow is paused")
    event = spec.get("event", {})
    run_key = _w.key(wid, "run", event)
    prior = next((r for r in STORE["wfruns"] if r.get("idempotency_key") == run_key), None)
    effects = []
    if prior is None:
        for i, step in enumerate(wf.get("definition", {}).get("steps", [])):
            if not _w.check_condition(step.get("condition", {}), event):
                continue
            effects.append(_w.run_step(step, event, STORE))
        run = {"id": len(STORE["wfruns"]) + 1, "workflow_id": wid, "status": "done",
               "workflow_version": wf.get("version", 1), "context": event,
               "log": effects, "idempotency_key": run_key}
        STORE["wfruns"].append(run)
        return {"run": run, "effects": effects, "replayed": False}
    return {"run": prior, "effects": [], "replayed": True}


@router.post("/api/v1/workflows/{wid}/cancel", tags=["monitoring"])
def workflow_cancel(wid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    run = next((x for x in STORE["wfruns"]
                if x.get("id") == spec.get("run_id") and x.get("workflow_id") == wid), None)
    if not run:
        raise HTTPException(404, "run not found")
    if run.get("status") != "running":
        raise HTTPException(409, f"run is {run.get('status')}, only running runs cancel")
    run["status"] = "cancelled"
    repo.sync("wfruns", run)
    _audit(email, "workflow.cancel", str(run["id"]))
    return {"ok": True}


@router.get("/api/v1/workflows", tags=["monitoring"])
def list_workflows(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return {"items": _visible_by_org(STORE["workflows"], org)}


@router.post("/api/v1/workflows/{wid}/run", tags=["monitoring"])
def workflow_run(wid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import workflows as _w
    _, org, _ = _need(authorization, "collect", x_api_key)
    wf = next((x for x in STORE["workflows"]
               if x["id"] == wid and x.get("enabled") and x.get("org", 1) == org), None)
    if not wf:
        raise HTTPException(404, "workflow not found/disabled")
    if wf.get("paused"):
        raise HTTPException(409, "workflow is paused")
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



# ---- webhooks (outgoing) ----
@router.post("/api/v1/webhooks", tags=["monitoring"])
def create_webhook(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...core.crypto import encrypt
    _, org, _ = _need(authorization, "configure", x_api_key)
    item = {"id": len(STORE["webhooks"]) + 1, "org": org, "enabled": True, **spec}
    if item.get("secret"):
        item["secret"] = encrypt(item["secret"])
    STORE["webhooks"].append(item)
    return {k: v for k, v in item.items() if k != "secret"}


@router.get("/api/v1/webhooks", tags=["monitoring"])
def list_webhooks(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return {"items": [{k: v for k, v in w.items() if k != "secret"}
                      for w in _visible_by_org(STORE["webhooks"], org)]}


@router.post("/api/v1/webhooks/{wid}/test", tags=["monitoring"])
def webhook_test(wid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import webhooks as _wh
    from ...core.crypto import decrypt
    _, org, _ = _need(authorization, "configure", x_api_key)
    w = next((x for x in STORE["webhooks"]
              if x["id"] == wid and x.get("enabled") and x.get("org", 1) == org), None)
    if not w:
        raise HTTPException(404, "not found/disabled")
    out = _wh.deliver(w["url"], "ping", {"webhook_id": wid}, decrypt(w.get("secret", "")))
    STORE["deliveries"].append({"id": len(STORE["deliveries"]) + 1, "webhook_id": wid,
                                "event": "ping", "status": "ok" if out["ok"] else "failed",
                                "attempts": out.get("attempts", 0),
                                "last_error": out.get("error", ""),
                                "response_status": out.get("status", 0)})
    return out


@router.get("/api/v1/webhooks/deliveries", tags=["monitoring"])
def webhook_deliveries(page: int = 1, size: int = 20):
    return paginate(STORE["deliveries"], page, size)


@router.post("/api/v1/webhooks/deliveries/{did}/replay", tags=["monitoring"])
def webhook_replay(did: int, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import webhooks as _wh
    from ...core.crypto import decrypt
    _need(authorization, "configure", x_api_key)
    d = next((x for x in STORE["deliveries"] if x["id"] == did), None)
    if not d:
        raise HTTPException(404, "not found")
    w = next((x for x in STORE["webhooks"] if x["id"] == d["webhook_id"]), None)
    if not w:
        raise HTTPException(404, "webhook gone")
    out = _wh.deliver(w["url"], d["event"], {"replay_of": did}, decrypt(w.get("secret", "")))
    d.update({"status": "ok" if out["ok"] else "failed",
              "attempts": d.get("attempts", 0) + out.get("attempts", 0)})
    repo.sync("deliveries", d)
    return out


# ---- maintenance windows ----
@router.post("/api/v1/maintenance", tags=["monitoring"])
def create_maintenance(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    try:
        starts, ends = float(spec.get("starts_at", 0)), float(spec.get("ends_at", 0))
    except (TypeError, ValueError):
        raise HTTPException(400, "starts_at/ends_at must be epoch seconds")
    if not ends > starts:
        raise HTTPException(400, "ends_at must be after starts_at")
    item = {"id": len(STORE["maintenance"]) + 1, "org": org, "name": spec.get("name", ""),
            "starts_at": starts, "ends_at": ends,
            "suppress_rules": spec.get("suppress_rules", []), "enabled": True}
    STORE["maintenance"].append(item)
    _audit(email, "maintenance.create", item["name"][:120])
    return item


@router.get("/api/v1/maintenance", tags=["monitoring"])
def list_maintenance(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return {"items": [w for w in STORE["maintenance"] if w.get("org", 1) == org]}


@router.post("/api/v1/maintenance/{mid}/disable", tags=["monitoring"])
def disable_maintenance(mid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    w = next((x for x in STORE["maintenance"]
              if x.get("id") == mid and x.get("org", 1) == org), None)
    if not w:
        raise HTTPException(404, "not found")
    w["enabled"] = False
    repo.sync("maintenance", w)
    _audit(email, "maintenance.disable", str(mid))
    return {"ok": True}


# ---- webhook ingestion source (HMAC + timestamp window + nonce dedupe) ----
@router.post("/api/v1/ingest/webhook", tags=["sources"])
def ingest_webhook(spec: dict):
    import hashlib as _h
    import hmac as _hm
    secret = os.getenv("WEBHOOK_INGEST_SECRET", "")
    if not secret:
        raise HTTPException(503, "ingest not configured (WEBHOOK_INGEST_SECRET)")
    body = (spec.get("event", "") + str(spec.get("ts", "")) + spec.get("nonce", "") +
            json_dumps(spec.get("payload", {}))).encode()
    expect = _hm.new(secret.encode(), body, _h.sha256).hexdigest()
    if not _hm.compare_digest(expect, spec.get("signature", "")):
        raise HTTPException(401, "bad signature")
    now = time.time()
    try:
        ts = float(spec.get("ts", 0))
    except (TypeError, ValueError):
        raise HTTPException(400, "bad ts")
    if abs(now - ts) > 300:
        raise HTTPException(401, "stale timestamp (replay window 300s)")
    nonce = spec.get("nonce", "")
    if not nonce or nonce in _NONCES:
        raise HTTPException(409, "duplicate/replayed nonce")
    _NONCES[nonce] = now
    if len(_NONCES) > 10000:
        old = sorted(_NONCES, key=_NONCES.get)[:5000]
        for k in old:
            _NONCES.pop(k, None)
    item = {"id": len(STORE["events"]) + 1, "org": 1, "type": spec.get("event", "webhook"),
            "entity_key": str(spec.get("payload", {}))[:200], "severity": "info",
            "confidence": 0.8, "evidence": [], "observed_at": now}
    STORE["events"].append(item)
    return {"ok": True, "event_id": item["id"]}


def json_dumps(obj):
    import json as _j
    return _j.dumps(obj, sort_keys=True, default=str)


