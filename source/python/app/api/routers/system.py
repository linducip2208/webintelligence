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
        _audit(creds.get("email", "?"), "auth.login.failed", "bad credentials")
        raise HTTPException(401, "bad credentials")
    _audit(creds.get("email", ""), "auth.login", "ok")
    return {"token": tok.issue(creds["email"], _secret()), "email": creds["email"]}


@router.post("/api/v1/auth/logout")
def logout(authorization: str = Header(""), x_api_key: str = Header("")):
    """Bearer tokens are stateless HMAC: logout discards the client token
    and records the event. API keys are revoked via apikeys/{id}/revoke."""
    email, _, _ = _ctx(authorization, x_api_key)
    _audit(email, "auth.logout", "ok")
    return {"ok": True}


@router.post("/api/v1/users/{addr}/reset-password", tags=["admin"])
def reset_password(addr: str, authorization: str = Header(""), x_api_key: str = Header("")):
    """Admin-initiated reset: sets a random password, returned ONCE for
    out-of-band delivery. No email infrastructure required on-server."""
    import secrets as _s
    email, _, _ = _need(authorization, "configure")
    if addr == "admin@local":
        raise HTTPException(409, "built-in account: change via server console")
    try:
        from ...models.entities import User
        from ...core.security import hash_password
        s = repo._session()
        u = s.query(User).filter_by(email=addr).first()
        if not u:
            s.close()
            raise HTTPException(404, "user not found")
        temp = "wi-" + _s.token_urlsafe(12)
        u.password_hash = hash_password(temp)
        s.commit()
        s.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"reset failed: {e}"[:200])
    _audit(email, "user.reset-password", addr)
    return {"ok": True, "temp_password": temp,
            "warning": "shown once — deliver out-of-band, user should ask admin for rotation"}


@router.get("/api/v1/auth/providers", tags=["admin"])
def auth_providers():
    from ...auth.oidc import from_env
    return {"providers": [p.status() for p in from_env().values()]}


@router.post("/api/v1/auth/oidc/login", tags=["admin"])
def oidc_login(spec: dict):
    from ...auth.oidc import from_env
    oidc = from_env()["oidc"]
    if not oidc.configured:
        raise HTTPException(501, "oidc not configured (set OIDC_ISSUER/OIDC_CLIENT_ID)")
    try:
        url = oidc.login_url(spec.get("redirect_uri", ""), spec.get("state", ""))
    except Exception as e:
        raise HTTPException(502, f"oidc discovery failed: {e}"[:300])
    return {"login_url": url}


@router.post("/api/v1/auth/oidc/callback", tags=["admin"])
def oidc_callback(spec: dict):
    from ...auth.oidc import from_env
    if not from_env()["oidc"].configured:
        raise HTTPException(501, "oidc not configured (set OIDC_ISSUER/OIDC_CLIENT_ID)")
    if not spec.get("code") or not spec.get("state"):
        raise HTTPException(400, "code and state required")
    # code exchange happens against the real IdP only when configured;
    # without a live round-trip we refuse instead of minting tokens.
    raise HTTPException(502, "oidc callback requires live IdP exchange")


@router.get("/healthz")
def healthz():
    return {"status": "ok", "version": "1.0.0"}


@router.get("/readyz")
def readyz():
    db_ok = repo.available
    checks = [
        healthsvc.check("api", True),
        healthsvc.check("redis", redis_status()["ok"], "connected" if redis_status()["ok"] else "memory fallback"),
        healthsvc.check("database", db_ok,
                        f"backend={repo.backend}" + (f": {repo.boot_error}" if not db_ok else "")),
        healthsvc.check("own_proxy", bool(settings.own_proxy_urls)),
        healthsvc.check("brightdata", bright.configured),
        healthsvc.check("ai", bool(settings.muse_base_url and settings.muse_api_key)),
    ]
    live = [c for c in checks if c["name"] in ("api", "redis", "database")]
    status = "healthy" if all(c["status"] == "up" for c in live) else "degraded"
    try:
        STORE["health"].append({"at": time.time(), "status": status,
                                "checks": {c["name"]: c["status"] for c in checks}})
    except Exception:
        pass
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
    from ...ai.http import estimate_tokens, messages_text
    email0, org0, _ = _ctx(authorization, x_api_key)
    if not _fl.is_enabled(repo, "ai", org0, email0):
        raise HTTPException(403, "ai disabled by feature flag")
    _require_auth(authorization, x_api_key)
    messages = list(spec.get("messages", []))
    model = spec.get("model", "")
    provider = spec.get("provider", "")
    import os as _o
    try:
        max_chars = int(_o.getenv("MAX_AI_CHARS", "200000") or 200000)
    except ValueError:
        max_chars = 200000
    if sum(len(str(m.get("content", ""))) for m in messages) > max_chars:
        raise HTTPException(413, "ai context too large")
    if spec.get("evidence"):
        messages = messages + [{"role": "user",
                                "content": _safe.wrap_evidence(spec["evidence"])}]
    from ...services import entitlements as _e
    _, _, _ = _need(authorization, "ai", x_api_key)
    okq, why = _e.check(STORE, org0, "ai_tokens",
                        estimate_tokens(messages_text(messages)) + 2000)
    if not okq:
        raise HTTPException(402, why)
    use_model = model or settings.muse_model
    chain = []
    db_name = provider[3:] if provider.startswith("db:") else provider
    dbp = next((x for x in STORE["ai_providers"]
                if x.get("name") == db_name and x.get("enabled")), None) if provider else None
    if dbp:
        from ...core.crypto import decrypt
        from ...ai.factory import build_provider as _bp
        chain = [(dbp["name"], _bp(dbp.get("protocol", "chat"),
             dbp.get("base_url", ""), decrypt(dbp.get("api_key_enc", "")),
             dbp.get("model", "") or use_model))]
        use_model = dbp.get("model", "") or use_model
    elif provider:
        p0 = aireg.get(provider)
        if not p0:
            raise HTTPException(404, f"unknown provider {provider}")
        chain = [(provider, p0)]
    else:
        names = fallback_order() or _fb.default_names(aireg)
        chain = [(n, aireg.get(n)) for n in names]
        # Enabled DB-configured providers join the default chain too, so
        # every AI added via Settings works without naming it explicitly.
        seen = {n for n, _ in chain}
        from ...core.crypto import decrypt as _dec
        from ...ai.factory import build_provider as _bp2
        for row in STORE["ai_providers"]:
            if not row.get("enabled") or row.get("name") in seen:
                continue
            try:
                chain.append((row["name"], _bp2(
                    row.get("protocol", "chat"), row.get("base_url", ""),
                    _dec(row.get("api_key_enc", "")), row.get("model", ""))))
            except Exception:
                continue
    org_plan = next((o.get("plan", "starter") for o in STORE["orgs"] if o.get("id") == org0), "starter")
    allowed = _e.PLANS.get(org_plan, _e.PLANS["starter"]).get("allowed_models", [])
    if allowed != ["*"]:
        allowed = list(allowed) + [x.strip() for x in
                    (_o.getenv("AI_EXTRA_MODELS", "") or "").split(",") if x.strip()]
    if use_model and allowed != ["*"] and use_model not in allowed:
        raise HTTPException(403, f"model {use_model} not in plan {org_plan}")
    out = _fb.chat_fallback(chain, messages, use_model)
    out["org"] = org0
    _record_usage(out, spec.get("prompt_version", ""))
    inc("AI_requests")
    return out


def _record_usage(out: dict, prompt_version: str = ""):
    try:
        name = out.get("provider", "muse-spark")
        p = aireg.get(name)
        cost = p.estimate_cost(out.get("input_tokens", 0), out.get("output_tokens", 0)) if p else 0.0
        STORE["ai_usage"].append({"provider": name, "model": out.get("model", ""),
                                  "org": out.get("org", 1),
                                  "prompt_version": prompt_version,
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


@router.get("/api/v1/collectors", tags=["admin"])
def collector_registry():
    """Live collector/plugin registry: every collection path with health,
    capabilities, version, and enablement — the plugin SDK surface."""
    import os as _o
    from ...services import connectors as _c
    cols = []
    gobin = None
    for cand in ("build/linux/collector", "build/windows/collector.exe",
                 "source/go/collector"):
        if _o.path.exists(cand) or _o.path.exists("/app/" + cand):
            gobin = cand
            break
    try:
        from ...browser.worker import pool_status
        brow = pool_status()
    except Exception as e:  # noqa: BLE001
        brow = {"installed": False, "error": str(e)[:160]}
    try:
        depth = None
        from ..shared import get_redis as _gr
        r = _gr()
        if r is not None:
            depth = int(r.llen("webintel:queue:jobs") or 0)
    except Exception:
        depth = None
    cols.append({"name": "go-collector", "kind": "binary",
                 "description": "High-concurrency HTTP/API collector (Go). Posts to /results.",
                 "version": "1.0", "enabled": True, "healthy": gobin is not None,
                 "last_run": "", "binary": gobin or "not built (go build ./...)",
                 "capabilities": ["http", "api", "concurrent", "retries", "rate-limit"],
                 "queue_depth": depth})
    cols.append({"name": "browser", "kind": "playwright",
                 "description": "Headless browser pool for JS-rendered pages.",
                 "version": "1.0", "enabled": bool(brow.get("installed", False)),
                 "healthy": bool(brow.get("pool") or brow.get("installed")),
                 "last_run": "", "capabilities": ["render", "screenshot", "metadata"],
                 "pool": {k: v for k, v in brow.items() if k != "error"},
                 "error": brow.get("error", "")})
    cols.append({"name": "pipeline-inline", "kind": "python",
                 "description": "Inline pipeline: fetch→validate→normalize→recon→alerts.",
                 "version": "1.0", "enabled": True, "healthy": True, "last_run": "",
                 "capabilities": ["http", "prices", "changes", "recon", "alerts"]})
    for c in STORE["connectors"]:
        h = c.get("health", {}) if isinstance(c.get("health"), dict) else {}
        cols.append({"name": c.get("name", ""), "kind": "connector",
                     "description": f"{c.get('category', '')} connector",
                     "version": c.get("version", "1"),
                     "enabled": bool(c.get("enabled", True)),
                     "healthy": bool(h.get("ok", False)), "last_run": h.get("last_run", ""),
                     "capabilities": ((c.get("manifest") or {}).get("capabilities", []) or []),
                     "connector_id": c.get("id")})
    return {"collectors": cols}


@router.post("/api/v1/admin/backup", tags=["admin"])
def admin_backup(authorization: str = Header(""), x_api_key: str = Header("")):
    """Portable SQL dump of every app table (CREATE + INSERTs), generated in
    Python so it works without mysqldump. Download via /admin/backup/download.
    Secrets (password hashes, key hashes, encrypted blobs) dump as-is — the
    FILE must be stored securely; it is never served except here."""
    from ...db import repo as _repo_mod
    email, _, _ = _need(authorization, "configure", x_api_key)
    eng = repo.engine
    if eng is None:
        raise HTTPException(503, "database unavailable")
    import datetime as _dt
    from sqlalchemy import inspect as _insp, text as _tx
    from sqlalchemy.schema import CreateTable as _CT
    insp = _insp(eng)
    parts = ["-- WebIntel backup " + _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
             "SET FOREIGN_KEY_CHECKS=0;"]
    tables = 0
    with eng.connect() as conn:
        for t in sorted(insp.get_table_names()):
            if t.startswith("alembic"):
                continue
            tables += 1
            cols = [c["name"] for c in insp.get_columns(t)]
            parts.append(f"DROP TABLE IF EXISTS `{t}`;")
            try:
                ddl = str(_CT(_repo_mod.Base.metadata.tables[t]).compile(dialect=eng.dialect))
                parts.append(ddl.rstrip(";") + ";")
            except Exception:
                pass
            parts.append(f"-- table {t} ({len(cols)} cols)")
            rows = conn.execute(_tx(f"SELECT * FROM `{t}`")).fetchall()
            for r in rows:
                vals = []
                for v in r:
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, bool):
                        vals.append("1" if v else "0")
                    elif isinstance(v, (int, float)):
                        vals.append(str(v))
                    else:
                        vals.append("'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'")
                parts.append(f"INSERT INTO `{t}` ({', '.join(f'`{c}`' for c in cols)}) "
                             f"VALUES ({', '.join(vals)});")
    parts.append("SET FOREIGN_KEY_CHECKS=1;")
    sql = "\n".join(parts)
    try:
        repo.kv_set("backup:last",
                    {"at": _dt.datetime.utcnow().isoformat() + "Z",
                     "tables": tables, "bytes": len(sql.encode())})
    except Exception:
        pass
    _audit(email, "admin.backup", f"{tables} tables")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(sql, media_type="application/sql",
                            headers={"Content-Disposition":
                                     "attachment; filename=webintel-backup.sql"})


@router.get("/api/v1/admin/data-quality", tags=["admin"])
def data_quality(authorization: str = Header(""), x_api_key: str = Header("")):
    """Detect duplicates, orphans, missing provenance, stale data, broken refs."""
    _, org, _ = _ctx(authorization, x_api_key)
    issues = []
    seen_fp, dup_docs = set(), []
    for d in STORE["documents"]:
        if d.get("org", 1) != org:
            continue
        if d.get("fingerprint") in seen_fp:
            dup_docs.append(d.get("id"))
        else:
            seen_fp.add(d.get("fingerprint"))
    if dup_docs:
        issues.append({"kind": "duplicate_documents", "count": len(dup_docs),
                       "ids": dup_docs[:50], "fixable": False,
                       "note": "same fingerprint ingested twice; review before dedupe"})
    node_ids = {n["id"] for n in STORE["nodes"] if n.get("org", 1) == org}
    orphans = [e["id"] for e in STORE["edges"]
               if e.get("org", 1) == org and
               (e.get("src") not in node_ids or e.get("dst") not in node_ids)]
    if orphans:
        issues.append({"kind": "orphan_relationships", "count": len(orphans),
                       "ids": orphans[:50], "fixable": True,
                       "note": "edges pointing to missing nodes"})
    noprove = [e["id"] for e in STORE["evidence"]
               if e.get("org", 1) == org and not (e.get("url") or e.get("snippet"))]
    if noprove:
        issues.append({"kind": "evidence_without_provenance", "count": len(noprove),
                       "ids": noprove[:50], "fixable": False,
                       "note": "evidence with neither URL nor snippet"})
    import time as _t
    stale = [t["id"] for t in STORE["targets"]
             if t.get("org", 1) == org and (t.get("attempts", 0) or 0) == 0]
    if stale:
        issues.append({"kind": "never_scanned_targets", "count": len(stale),
                       "ids": stale[:50], "fixable": False,
                       "note": "targets with zero collection attempts"})
    return {"issues": issues, "total": sum(i["count"] for i in issues)}


@router.post("/api/v1/admin/data-quality/fix", tags=["admin"])
def data_quality_fix(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Apply safe automatic fixes only (orphan edges). Destructive or
    ambiguous fixes are reported, never executed silently."""
    email, org, _ = _need(authorization, "configure", x_api_key)
    kind = spec.get("kind", "")
    fixed = 0
    if kind == "orphan_relationships":
        node_ids = {n["id"] for n in STORE["nodes"] if n.get("org", 1) == org}
        before = len(STORE["edges"])
        STORE["edges"][:] = [e for e in STORE["edges"]
                             if e.get("org", 1) != org or
                             (e.get("src") in node_ids and e.get("dst") in node_ids)]
        fixed = before - len(STORE["edges"])
    else:
        raise HTTPException(400, "kind must be orphan_relationships")
    _audit(email, "data-quality.fix", f"{kind}:{fixed}")
    return {"ok": True, "fixed": fixed}


@router.get("/api/v1/admin/first-run", tags=["admin"])
def first_run_state():
    """First-run detection: true when no projects and no targets exist."""
    np = len(STORE.get("projects", []))
    nt = len(STORE.get("targets", []))
    demo = any((p.get("name") or "").startswith("DEMO") for p in STORE.get("projects", []))
    return {"first_run": np == 0 and nt == 0, "projects": np, "targets": nt,
            "demo_present": demo}


@router.post("/api/v1/admin/demo/seed", tags=["admin"])
def demo_seed(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Load a clearly-labeled DEMO workspace (Acme). All items carry
    demo:true and live in one DEMO project. Refuses when already present
    unless force:true. For evaluation only — purge anytime."""
    email, org, _ = _need(authorization, "configure", x_api_key)
    if any((p.get("name") or "").startswith("DEMO") and p.get("org", 1) == org
           for p in STORE.get("projects", [])) and not spec.get("force"):
        raise HTTPException(409, "demo workspace exists (use force:true or purge first)")
    nid = lambda coll: max([x.get("id", 0) for x in STORE.get(coll, [])] + [0]) + 1
    p = {"id": nid("projects"), "org": org, "name": "DEMO — Acme Workspace",
         "description": "DEMO DATA for evaluation. Safe to delete via Purge demo data.",
         "demo": True}
    STORE["projects"].append(p)
    tids = {}
    for domain in ("acme.example", "www.acme.example", "api.acme.example", "mail.acme.example"):
        t = {"id": nid("targets"), "org": org, "project_id": p["id"], "domain": domain,
             "url": f"https://{domain}", "source_type": "website",
             "attempts": 3, "successes": 3, "failures": 0, "demo": True,
             "recon": {"ok": True, "host": domain, "at": time.time(),
                       "dns": {"ok": True, "ips": ["203.0.113.10"]},
                       "tls": {"ok": True, "issuer": {"O": "Demo CA"},
                               "san": [domain], "cert_key": "demo-cert-1"},
                       "http": {"ok": True, "title": f"{domain} home",
                                "tech": ["nginx", "jQuery"],
                                "links_total": 12, "links_internal": 10,
                                "links_external": 2, "link_domains": ["cdn.example"],
                                "forms": 1, "scripts": 3, "robots_txt": True}}}
        STORE["targets"].append(t)
        tids[domain] = t["id"]
    eids = {}
    for kind, name, dom in (("company", "Acme Corporation", ""), ("domain", "acme.example", "acme.example"),
                            ("email", "admin@acme.example", ""), ("ip", "203.0.113.10", ""),
                            ("technology", "nginx", ""), ("vulnerability", "CVE-2024-0001", "")):
        e = {"id": nid("entities"), "org": org, "kind": kind, "name": name, "domain": dom,
             "confidence": 80, "demo": True}
        STORE["entities"].append(e)
        eids[(kind, name)] = e["id"]
    nids = {}
    for kind, key, name in (("company", "acme", "Acme Corporation"),
                            ("domain", "acme.example", "acme.example"),
                            ("ip", "203.0.113.10", "203.0.113.10")):
        n = {"id": nid("nodes"), "org": org, "kind": kind, "key": key, "name": name, "demo": True}
        STORE["nodes"].append(n)
        nids[key] = n["id"]
    for src, dst, rel in (("acme", "acme.example", "OWNS"),
                          ("acme.example", "203.0.113.10", "RESOLVES_TO")):
        STORE["edges"].append({"id": nid("edges"), "org": org, "src": nids[src], "dst": nids[dst],
                                "rel": rel, "confidence": 90, "evidence": ["demo"], "demo": True})
    ev = {"id": nid("evidence"), "org": org, "source": "demo", "url": "https://acme.example",
          "content_hash": "demo-evidence-1", "snippet": "Demo evidence record", "confidence": 1.0,
          "demo": True}
    STORE["evidence"].append(ev)
    f1 = {"id": nid("findings"), "org": org, "kind": "demo", "title": "Demo: exposed admin panel",
          "body": "Demo finding for evaluation.", "confidence": 0.8,
          "entities": [eids[("company", "Acme Corporation")]], "evidence_ids": [ev["id"]],
          "severity": "high", "status": "OPEN", "priority": "high", "resolved_at": 0.0, "demo": True}
    f2 = dict(f1, id=nid("findings") + 1, title="Demo: outdated jQuery (resolved)",
              severity="medium", status="RESOLVED")
    STORE["findings"].append(f1)
    STORE["findings"].append(f2)
    STORE["watchlists"].append({"id": nid("watchlists"), "org": org, "kind": "keyword",
                                "value": "acme", "demo": True})
    STORE["alerts"].append({"id": nid("alerts"), "org": org, "rule": "new_product",
                            "message": "Demo alert: new asset acme.example",
                            "channel": "inapp", "project_id": p["id"], "is_read": False,
                            "severity": "info", "demo": True})
    inv = {"id": nid("investigations"), "org": org, "title": "DEMO: Acme exposure review",
           "description": "Demo investigation.", "status": "investigating", "priority": "medium",
           "owner_email": email, "member_emails": [], "tags": ["demo"],
           "target_ids": list(tids.values()),
           "entity_ids": [eids[("company", "Acme Corporation")], eids[("domain", "acme.example")]],
           "finding_ids": [f1["id"]], "evidence_ids": [ev["id"]],
           "notes": [{"by": email, "at": time.time(), "text": "Demo note"}], "tasks": [],
           "demo": True}
    STORE["investigations"].append(inv)
    case = {"id": nid("cases"), "org": org, "title": "DEMO: Acme case",
            "description": "Demo case.", "status": "INVESTIGATING", "priority": "medium",
            "assignee": email, "member_emails": [], "tags": ["demo"],
            "investigation_ids": [inv["id"]],
            "entity_ids": [eids[("company", "Acme Corporation")]],
            "finding_ids": [f1["id"]], "evidence_ids": [ev["id"]], "alert_ids": [],
            "notes": [], "tasks": [], "demo": True}
    STORE["cases"].append(case)
    repo.sync("projects", p)
    _audit(email, "demo.seed", f"project:{p['id']}")
    return {"ok": True, "project_id": p["id"], "demo": True,
            "counts": {"targets": len(tids), "entities": len(eids), "findings": 2}}


@router.post("/api/v1/admin/demo/purge", tags=["admin"])
def demo_purge(authorization: str = Header(""), x_api_key: str = Header("")):
    """Delete every demo-tagged record (project-scoped to caller's org)."""
    email, org, _ = _need(authorization, "configure", x_api_key)
    removed = {}
    for coll in ("projects", "targets", "entities", "nodes", "edges", "evidence",
                 "findings", "watchlists", "alerts", "investigations", "cases",
                 "schedules", "jobs", "reports", "datasets", "documents"):
        items = STORE.get(coll, [])
        keep = [x for x in items
                if not (x.get("demo") and x.get("org", 1) == org)]
        if len(keep) != len(items):
            removed[coll] = len(items) - len(keep)
            STORE[coll][:] = keep
    _audit(email, "demo.purge", str(removed))
    return {"ok": True, "removed": removed}


@router.get("/api/v1/ai/provider-presets", tags=["admin"])
def ai_provider_presets():
    """Backend-driven catalog for the Add-Provider flow (single source of
    truth; the UI renders from this, nothing is duplicated in frontend)."""
    from ...ai.presets import list_presets
    return {"presets": list_presets()}


def _public_provider(p: dict) -> dict:
    """Provider row safe for API responses: never includes key material."""
    return {k: v for k, v in p.items() if k != "api_key_enc"}


def _validate_endpoint(base_url: str, preset_id: str = ""):
    """SSRF validation for provider endpoints. Loopback is allowed ONLY for
    local presets (Ollama); everything else must be public HTTPS/DNS-safe."""
    from ...core.ssrf import validate_url, SSRFError
    from ...ai.presets import get_preset
    import os as _o
    if not base_url or len(base_url) > 2048:
        raise HTTPException(400, "base_url required")
    trust = [x.strip() for x in _o.getenv("TRUSTED_EGRESS_CIDRS", "").split(",") if x.strip()]
    preset = get_preset(preset_id or "") if preset_id else None
    if preset and preset.get("local"):
        trust = trust + ["127.0.0.0/8", "::1/128"]
    try:
        validate_url(base_url, trust or None)
    except SSRFError as e:
        raise HTTPException(400, f"endpoint rejected: {e}")


def _record_test(p: dict, result: dict):
    """Persist non-secret test metadata only (status/latency/code)."""
    import time as _t
    conn = result.get("connection", {})
    err = result.get("error", {})
    p["last_tested_at"] = _t.time()
    p["last_test_status"] = "passed" if result.get("success") else "failed"
    p["last_test_latency_ms"] = conn.get("latency_ms", 0)
    p["last_test_error"] = err.get("code", "") if err else ""
    try:
        repo.sync("ai_providers", p)
    except Exception:
        pass


def _run_test(base_url: str, protocol: str, api_key: str, model: str,
              name: str = "") -> dict:
    """Real backend test: build adapter -> connect -> auth -> discover ->
    verify model -> structured result. Secrets never leave the server."""
    from ...ai.factory import build_provider as _bp
    from ...ai import diagnose as _dg
    try:
        prov = _bp(protocol, base_url, api_key or "", model or "")
    except Exception as e:  # noqa: BLE001
        code, msg = _dg.normalize_error(f"build failed: {e}")
        return {"success": False, "provider": {"name": name, "protocol": protocol},
                "connection": {"authenticated": False, "latency_ms": 0},
                "model": {"selected": model or "", "available": False},
                "models": [], "error": {"code": code, "message": msg}}
    return _dg.test_provider(prov, name, model or "")


@router.post("/api/v1/ai/providers/db", tags=["admin"])
def ai_provider_create(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...core.crypto import encrypt
    from ...ai.presets import valid_protocol
    email, _, _ = _need(authorization, "configure")
    if not spec.get("name") or not spec.get("base_url"):
        raise HTTPException(400, "name and base_url required")
    if any(x.get("name") == spec["name"] for x in STORE["ai_providers"]):
        raise HTTPException(409, "provider exists")
    proto = (spec.get("protocol", "chat") or "chat").lower()
    if not valid_protocol(proto):
        raise HTTPException(400, "protocol must be chat|responses|anthropic|google")
    _validate_endpoint(spec["base_url"], spec.get("preset", ""))
    item = {"id": max([x.get("id", 0) for x in STORE["ai_providers"]] + [0]) + 1,
            "name": spec["name"], "preset": spec.get("preset", ""),
            "base_url": spec["base_url"], "protocol": proto,
            "api_key_enc": encrypt(spec.get("api_key", "")),
            "model": spec.get("model", ""), "enabled": True,
            "last_tested_at": 0.0, "last_test_status": "untested",
            "last_test_latency_ms": 0.0, "last_test_error": ""}
    STORE["ai_providers"].append(item)
    _audit(email, "ai.provider.create", item["name"])
    return _public_provider(item)


@router.get("/api/v1/ai/providers/db", tags=["admin"])
def ai_provider_list():
    # Configured providers only; key material never leaves the server.
    return {"items": [_public_provider(x) for x in STORE["ai_providers"]]}


@router.get("/api/v1/ai/providers/db/{pid}", tags=["admin"])
def ai_provider_detail(pid: int):
    p = next((x for x in STORE["ai_providers"] if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "not found")
    return _public_provider(p)


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


@router.post("/api/v1/ai/providers/db/{pid}/enable", tags=["admin"])
def ai_provider_enable(pid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _need(authorization, "configure")
    p = next((x for x in STORE["ai_providers"] if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "not found")
    p["enabled"] = True
    repo.sync("ai_providers", p)
    _audit(email, "ai.provider.enable", p["name"])
    return {"ok": True}


@router.post("/api/v1/ai/providers/db/{pid}/test", tags=["admin"])
def ai_provider_test(pid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Live test of a SAVED provider: decrypt server-side, real connect +
    auth + discovery + model verify. Structured result, key never returned."""
    from ...core.crypto import decrypt
    email, _, _ = _need(authorization, "configure")
    p = next((x for x in STORE["ai_providers"] if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "not found")
    try:
        key = decrypt(p.get("api_key_enc", ""))
    except Exception as e:  # noqa: BLE001
        from ...ai import diagnose as _dg
        code, msg = _dg.normalize_error(f"key unreadable: {e}")
        return {"success": False, "provider": {"name": p.get("name", "")},
                "connection": {"authenticated": False, "latency_ms": 0},
                "model": {"selected": p.get("model", ""), "available": False},
                "models": [], "error": {"code": code, "message": msg}}
    if not key:
        return {"success": False, "provider": {"name": p.get("name", "")},
                "connection": {"authenticated": False, "latency_ms": 0},
                "model": {"selected": p.get("model", ""), "available": False},
                "models": [],
                "error": {"code": "INVALID_CONFIGURATION",
                          "message": "No API key saved for this provider.",
                          "suggested_action": "Set the API key, then test again."}}
    _validate_endpoint(p.get("base_url", ""), p.get("preset", ""))
    result = _run_test(p.get("base_url", ""), p.get("protocol", "chat"),
                       key, p.get("model", ""), p.get("name", ""))
    _record_test(p, result)
    _audit(email, "ai.provider.test", f"{p['name']}:{result.get('success')}")
    return result


@router.post("/api/v1/ai/providers/db/test", tags=["admin"])
def ai_provider_test_unsaved(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Live test of an UNSAVED configuration (Add flow): nothing persisted,
    key used once server-side and discarded. Same structured result."""
    from ...ai.presets import valid_protocol
    _, _, _ = _need(authorization, "configure")
    base_url, protocol = spec.get("base_url", ""), (spec.get("protocol", "chat") or "chat").lower()
    if not valid_protocol(protocol):
        raise HTTPException(400, "protocol must be chat|responses|anthropic|google")
    _validate_endpoint(base_url, spec.get("preset", ""))
    return _run_test(base_url, protocol, spec.get("api_key", ""),
                     spec.get("model", ""), spec.get("name", "unsaved"))


@router.post("/api/v1/ai/providers/db/models", tags=["admin"])
def ai_provider_discover_unsaved(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Model discovery for an unsaved configuration (nothing persisted)."""
    from ...ai.factory import build_provider as _bp
    from ...ai import diagnose as _dg
    from ...ai.presets import valid_protocol
    _, _, _ = _need(authorization, "configure")
    protocol = (spec.get("protocol", "chat") or "chat").lower()
    if not valid_protocol(protocol):
        raise HTTPException(400, "protocol must be chat|responses|anthropic|google")
    _validate_endpoint(spec.get("base_url", ""), spec.get("preset", ""))
    try:
        prov = _bp(protocol, spec.get("base_url", ""), spec.get("api_key", ""),
                   spec.get("model", ""))
        return _dg.discover(prov)
    except Exception as e:  # noqa: BLE001
        code, msg = _dg.normalize_error(e)
        return {"models": [], "discovery": False, "manual_entry": True,
                "error": {"code": code, "message": msg}}


@router.post("/api/v1/ai/providers/db/{pid}/models", tags=["admin"])
def ai_provider_discover_saved(pid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Model discovery for a saved provider (key decrypted server-side)."""
    from ...core.crypto import decrypt
    from ...ai.factory import build_provider as _bp
    from ...ai import diagnose as _dg
    _, _, _ = _need(authorization, "configure")
    p = next((x for x in STORE["ai_providers"] if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "not found")
    try:
        key = decrypt(p.get("api_key_enc", ""))
    except Exception as e:  # noqa: BLE001
        code, msg = _dg.normalize_error(f"key unreadable: {e}")
        return {"models": [], "discovery": False, "manual_entry": True,
                "error": {"code": code, "message": msg}}
    try:
        prov = _bp(p.get("protocol", "chat"), p.get("base_url", ""), key,
                   p.get("model", ""))
        return _dg.discover(prov)
    except Exception as e:  # noqa: BLE001
        code, msg = _dg.normalize_error(e)
        return {"models": [], "discovery": False, "manual_entry": True,
                "error": {"code": code, "message": msg}}


@router.post("/api/v1/ai/providers/db/{pid}", tags=["admin"])
def ai_provider_update(pid: int, spec: dict, authorization: str = Header(""),
                       x_api_key: str = Header("")):
    return _ai_provider_apply(pid, spec, authorization, x_api_key)


@router.put("/api/v1/ai/providers/db/{pid}", tags=["admin"])
def ai_provider_replace(pid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    return _ai_provider_apply(pid, spec, authorization, x_api_key)


def _ai_provider_apply(pid: int, spec: dict, authorization: str, x_api_key: str):
    """Update base_url/protocol/model/api_key/preset/enabled (key
    re-encrypted at rest, never returned)."""
    from ...core.crypto import encrypt
    from ...ai.presets import valid_protocol
    email, _, _ = _need(authorization, "configure")
    p = next((x for x in STORE["ai_providers"] if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "not found")
    if "base_url" in spec:
        _validate_endpoint(spec["base_url"], spec.get("preset", p.get("preset", "")))
        p["base_url"] = spec["base_url"]
    if "model" in spec:
        p["model"] = spec["model"]
    if "protocol" in spec:
        proto = (spec["protocol"] or "chat").lower()
        if not valid_protocol(proto):
            raise HTTPException(400, "protocol must be chat|responses|anthropic|google")
        p["protocol"] = proto
    if "preset" in spec:
        p["preset"] = spec["preset"]
    if "enabled" in spec:
        p["enabled"] = bool(spec["enabled"])
    if "api_key" in spec:
        p["api_key_enc"] = encrypt(spec["api_key"])
    repo.sync("ai_providers", p)
    _audit(email, "ai.provider.update", p["name"])
    return _public_provider(p)


@router.delete("/api/v1/ai/providers/db/{pid}", tags=["admin"])
def ai_provider_delete(pid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _need(authorization, "configure")
    p = next((x for x in STORE["ai_providers"] if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "not found")
    STORE["ai_providers"][:] = [x for x in STORE["ai_providers"] if x.get("id") != pid]
    try:
        repo.delete("ai_providers", pid)
    except Exception:
        pass
    _audit(email, "ai.provider.delete", p["name"])
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

