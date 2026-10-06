"""knowledge routes (split from main.py; behavior unchanged)."""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from ..shared import (
    HTTPException,
    Header,
    JSONResponse,
    STORE,
    _audit,
    _ctx,
    _fire_watchlists,
    _require_auth,
    _visible_by_org,
    paginate,
    repo,
    settings,
    time,
    _need,
)

router = APIRouter()

# ---- knowledge graph ----
@router.post("/api/v1/graph/nodes", tags=["knowledge"])
def graph_node(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    email, org, _ = _need(authorization, "collect", x_api_key)
    node = _g.add_node(STORE["nodes"], spec.get("kind", "company"),
                       spec.get("key", ""), spec.get("name", ""), org)
    _audit(email, "graph.node.add", str(node.get("id")))
    return node


@router.post("/api/v1/graph/edges", tags=["knowledge"])
def graph_edge(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    email, org, _ = _need(authorization, "collect", x_api_key)
    edge = _g.add_edge(STORE["edges"], spec.get("src"), spec.get("dst"),
                       spec.get("rel", "RELATED"), spec.get("confidence", 1.0),
                       spec.get("evidence", []), spec.get("at"), org)
    for e in STORE["edges"]:
        if e.get("valid_to"):
            repo.sync("edges", e)
    _audit(email, "graph.edge.add", str(edge.get("id")))
    return edge


@router.get("/api/v1/graph/nodes", tags=["knowledge"])
def graph_nodes(q: str = "", kind: str = "", page: int = 1, size: int = 20,
                authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [n for n in STORE["nodes"] if n.get("org", 1) == org]
    if kind:
        items = [n for n in items if n.get("kind") == kind]
    if q:
        ql = q.lower()
        items = [n for n in items
                 if ql in str(n.get("key", "")).lower() or ql in str(n.get("name", "")).lower()]
    return paginate(items, page, size)


@router.get("/api/v1/graph/edges", tags=["knowledge"])
def graph_edges(q: str = "", rel: str = "", page: int = 1, size: int = 20,
                authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [e for e in STORE["edges"] if e.get("org", 1) == org]
    if rel:
        items = [e for e in items if e.get("rel") == rel]
    if q:
        ql = q.lower()
        names = {n["id"]: (n.get("key", ""), n.get("name", "")) for n in STORE["nodes"]}
        items = [e for e in items
                 if ql in str(e.get("rel", "")).lower()
                 or ql in " ".join(str(v) for v in names.get(e.get("src"), ("", ""))).lower()
                 or ql in " ".join(str(v) for v in names.get(e.get("dst"), ("", ""))).lower()]
    return paginate(items, page, size)


@router.get("/api/v1/graph/traverse", tags=["knowledge"])
def graph_traverse(node: int = 0, depth: int = 2, rel: str = "", kind: str = "", at: str = "",
                   authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
    depth = min(max(1, depth), 5)  # traversal cap: no accidental whole-graph loads
    start = next((n for n in STORE["nodes"] if n.get("id") == node), None)
    if node and (not start or start.get("org", 1) != org):
        raise HTTPException(404, "node not found")
    items = _g.traverse(STORE["nodes"], [e for e in STORE["edges"] if e.get("org", 1) == org],
                        node, depth,
                        rel.split(",") if rel else None,
                        kind.split(",") if kind else None, at or None)
    return {"items": items}



# ---- events / evidence / claims / findings ----
@router.post("/api/v1/events", tags=["knowledge"])
def create_event(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    import hashlib as _h
    import time as _t
    email, org, _ = _need(authorization, "collect", x_api_key)
    key = _h.sha256(f"{spec.get('type')}|{spec.get('entity_key', '')}|{spec.get('severity', 'info')}".encode()).hexdigest()[:32]
    now = _t.time()
    dup = next((e for e in STORE["events"]
                if e.get("dedup_key") == key and now - e.get("_ts", 0) < 3600), None)
    if dup:
        return {**dup, "duplicate": True}
    item = {"id": len(STORE["events"]) + 1, "org": org, "dedup_key": key, "_ts": now, **spec}
    STORE["events"].append(item)
    _fire_watchlists(item)
    _audit(email, "event.create", f"{item['id']}:{spec.get('type', '')}"[:120])
    return item


@router.get("/api/v1/events", tags=["knowledge"])
def list_events(page: int = 1, size: int = 20, type: str = "", severity: str = "",
                authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    f = {"org_id": org}
    if type:
        f["type"] = type
    if severity:
        f["severity"] = severity
    return repo.page("events", page, size, "", "asc", filters=f)


@router.post("/api/v1/evidence", tags=["knowledge"])
def create_evidence(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import evidence as _e
    email, org, _ = _need(authorization, "collect", x_api_key)
    item = {"id": len(STORE["evidence"]) + 1, "org": org,
            **_e.make_evidence(spec.get("source", ""), spec.get("url", ""),
                               spec.get("content_hash", ""), spec.get("snippet", ""),
                               spec.get("selector", ""), spec.get("method", ""),
                               spec.get("confidence", 1.0))}
    STORE["evidence"].append(item)
    _audit(email, "evidence.create", str(item["id"]))
    return item


@router.get("/api/v1/evidence", tags=["knowledge"])
def list_evidence(page: int = 1, size: int = 20,
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["evidence"], org), page, size)


@router.post("/api/v1/claims", tags=["knowledge"])
def create_claim(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    item = {"id": len(STORE["claims"]) + 1, "org": org, "status": "UNVERIFIED",
            "confidence": 0.0, **spec}
    STORE["claims"].append(item)
    _audit(email, "claim.create", str(item["id"]))
    return item


@router.post("/api/v1/claims/verify", tags=["knowledge"])
def verify_claim(spec: dict):
    from ...services import evidence as _e
    out = _e.verify(spec.get("value"), spec.get("evidence", []))
    if spec.get("claim_id"):
        c = next((x for x in STORE["claims"] if x["id"] == spec["claim_id"]), None)
        if c:
            c["status"] = out["status"]
            c["confidence"] = out["confidence"]
            repo.sync("claims", c)
    return out


@router.post("/api/v1/contradictions/check", tags=["knowledge"])
def check_contradictions(spec: dict):
    from ...services import evidence as _e
    return _e.contradictions(spec.get("evidence", [])) or {"conflict": False}


@router.post("/api/v1/findings", tags=["intelligence"])
def create_finding(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    item = {"id": len(STORE["findings"]) + 1, "org": org,
            "severity": (spec.get("severity", "info") or "info").lower(),
            "status": (spec.get("status", "OPEN") or "OPEN").upper(),
            "priority": (spec.get("priority", "medium") or "medium").lower(),
            "resolved_at": 0.0, **{k: v for k, v in spec.items()
                                   if k not in ("severity", "status", "priority")}}
    STORE["findings"].append(item)
    _audit(email, "finding.create", str(item["id"]))
    return item


@router.get("/api/v1/findings", tags=["intelligence"])
def list_findings(page: int = 1, size: int = 20, severity: str = "", status: str = "",
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = _visible_by_org(STORE["findings"], org)
    if severity:
        items = [x for x in items if (x.get("severity") or "info").lower() == severity.lower()]
    if status:
        items = [x for x in items if (x.get("status") or "OPEN").upper() == status.upper()]
    return paginate(items, page, size)


FINDING_SEVERITIES = ("info", "low", "medium", "high", "critical")
FINDING_STATUSES = ("OPEN", "CONFIRMED", "FALSE_POSITIVE", "RESOLVED", "ACCEPTED")


@router.put("/api/v1/findings/{fid}", tags=["intelligence"])
def update_finding(fid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    f = next((x for x in STORE["findings"]
              if x.get("id") == fid and x.get("org", 1) == org), None)
    if not f:
        raise HTTPException(404, "finding not found")
    if "title" in spec and spec["title"]:
        f["title"] = str(spec["title"])[:500]
    if "body" in spec:
        f["body"] = str(spec["body"] or "")[:20000]
    if "severity" in spec:
        sev = str(spec["severity"]).lower()
        if sev not in FINDING_SEVERITIES:
            raise HTTPException(400, f"severity must be one of {list(FINDING_SEVERITIES)}")
        f["severity"] = sev
    if "status" in spec:
        st = str(spec["status"]).upper()
        if st not in FINDING_STATUSES:
            raise HTTPException(400, f"status must be one of {list(FINDING_STATUSES)}")
        f["status"] = st
        import time as _t
        f["resolved_at"] = _t.time() if st in ("RESOLVED", "FALSE_POSITIVE") else 0.0
    if "priority" in spec:
        f["priority"] = str(spec["priority"]).lower()[:16]
    repo.sync("findings", f)
    _audit(email, "finding.update", str(fid))
    return f


@router.delete("/api/v1/findings/{fid}", tags=["intelligence"])
def delete_finding(fid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    f = next((x for x in STORE["findings"]
              if x.get("id") == fid and x.get("org", 1) == org), None)
    if not f:
        raise HTTPException(404, "finding not found")
    STORE["findings"][:] = [x for x in STORE["findings"] if x.get("id") != fid]
    _audit(email, "finding.delete", str(fid))
    return {"ok": True}


@router.post("/api/v1/findings/bulk", tags=["intelligence"])
def findings_bulk(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    action = spec.get("action", "")
    if action != "status":
        raise HTTPException(400, "action must be status")
    st = str(spec.get("status", "")).upper()
    if st not in FINDING_STATUSES:
        raise HTTPException(400, f"status must be one of {list(FINDING_STATUSES)}")
    import time as _t
    n = 0
    for fid in spec.get("ids", [])[:500]:
        f = next((x for x in STORE["findings"]
                  if x.get("id") == fid and x.get("org", 1) == org), None)
        if not f:
            continue
        f["status"] = st
        f["resolved_at"] = _t.time() if st in ("RESOLVED", "FALSE_POSITIVE") else 0.0
        repo.sync("findings", f)
        n += 1
    _audit(email, "finding.bulk.status", f"{st}:{n}")
    return {"ok": True, "updated": n}


@router.get("/api/v1/feed", tags=["intelligence"])
def intel_feed(kinds: str = "", limit: int = 50):
    from ...services import feed as _f
    return {"items": _f.build(STORE["events"], STORE["findings"], STORE["changes"],
                             STORE["alerts"], kinds.split(",") if kinds else None, limit,
                             STORE["targets"])}


@router.get("/api/v1/opportunities", tags=["intelligence"])
def opportunities(authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import opportunities as _o
    _, org, _ = _ctx(authorization, x_api_key)
    mine = {"prices": [p for p in STORE["prices"]],
            "targets": [t for t in STORE["targets"] if t.get("org", 1) == org],
            "findings": [f for f in STORE["findings"] if f.get("org", 1) == org],
            "alerts": [a for a in STORE["alerts"]],
            "jobs": [j for j in STORE["jobs"] if j.get("org", 1) == org]}
    return {"items": _o.build(mine, org)}


@router.post("/api/v1/ask", tags=["intelligence"])
def nlq_ask(spec: dict):
    from ...services import nlq as _n
    plan = _n.to_plan(spec.get("question", ""))
    return {"plan": plan, "answer": _n.answer(plan, STORE),
            "evidence": "prices/changes/entities stores with job provenance"}



# ---- research ----
@router.post("/api/v1/research/plan", tags=["research"])
def research_plan(spec: dict):
    from ...services import research as _r
    return _r.plan(spec.get("question", ""))


@router.post("/api/v1/research/runs", tags=["research"])
def research_run(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import research as _r
    _, org, _ = _need(authorization, "research", x_api_key)
    item = {"id": len(STORE["research"]) + 1, "org": org, "status": "planned",
            "sources": [], "job_ids": [], "evidence_ids": [], "analysis": "",
            "ai_provider": "", "ai_model": settings.muse_model,
            "prompt_version": "v1", "config": spec.get("config", {}),
            "question": spec.get("question", ""), "plan": spec.get("plan") or _r.plan(spec.get("question", ""))}
    STORE["research"].append(item)
    _audit(_need(authorization, "research", x_api_key)[0], "research.create", item["question"][:120])
    return item


@router.post("/api/v1/research/runs/{rid}/analyze", tags=["research"])
def research_analyze(rid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Generate evidence-grounded analysis via AI provider chain.
    Without credentials returns an honest error; never fake analysis."""
    from ...ai import fallback as _fb
    from ...ai import safety as _safe
    from ...ai.factory import fallback_order
    from ...ai import registry as _reg
    from ...ai import prompts as _pr
    email, org, _ = _need(authorization, "research", x_api_key)
    run = next((x for x in STORE["research"]
                if x.get("id") == rid and x.get("org", 1) == org), None)
    if not run:
        raise HTTPException(404, "not found")
    ev = [x for x in STORE["evidence"] if x.get("id") in (run.get("evidence_ids") or [])]
    if not ev:
        raise HTTPException(400, "no evidence attached; attach evidence first")
    prompt = _pr.render("summarize_evidence",
                        evidence="\n".join(f"[{e['id']}] {e.get('snippet', '')}" for e in ev))
    messages = [{"role": "user", "content": _safe.wrap_evidence(
        [{"text": f"[{e['id']}] {e.get('snippet', '')} ({e.get('url', '')})"} for e in ev])},
        {"role": "user", "content": prompt}]
    names = fallback_order() or _fb.default_names(_reg)
    out = _fb.chat_fallback([(n, _reg.get(n)) for n in names], messages,
                            run.get("ai_model", ""))
    if out.get("error"):
        raise HTTPException(502, f"ai unavailable: {out['error']}"[:300])
    run.update({"status": "done", "analysis": out.get("text", "")[:8000],
                "ai_provider": out.get("provider", ""),
                "ai_model": out.get("model", ""),
                "prompt_version": "summarize_evidence@v1",
                "finished_at": time.time()})
    repo.sync("research", run)
    _audit(email, "research.analyze", f"{rid}:{out.get('provider', '')}")
    return {"ok": True, "provider": out.get("provider"), "analysis": run["analysis"],
            "reproducibility": {**_r_bundle(run), "prompt": "summarize_evidence@v1"}}


def _r_bundle(run: dict):
    from ...services import research as _r
    return _r.bundle(run)


@router.post("/api/v1/research/runs/{rid}/finish", tags=["research"])
def research_finish(rid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import research as _r
    email, org, _ = _need(authorization, "research", x_api_key)
    run = next((x for x in STORE["research"]
                if x["id"] == rid and x.get("org", 1) == org), None)
    if not run:
        raise HTTPException(404, "not found")
    run.update({"status": "done", "analysis": spec.get("analysis", "")[:8000],
                "evidence_ids": spec.get("evidence_ids", run.get("evidence_ids", [])),
                "ai_provider": spec.get("ai_provider", ""), "ai_model": spec.get("ai_model", ""),
                "finished_at": time.time()})
    repo.sync("research", run)
    _audit(email, "research.finish", str(rid))
    return {"ok": True, "reproducibility": _r.bundle(run)}


@router.get("/api/v1/research/runs", tags=["research"])
def research_runs(page: int = 1, size: int = 20,
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["research"], org), page, size)


@router.get("/api/v1/research/compare", tags=["research"])
def research_compare(a: int = 0, b: int = 0,
                     authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    ra = next((x for x in STORE["research"] if x.get("id") == a and x.get("org", 1) == org), None)
    rb = next((x for x in STORE["research"] if x.get("id") == b and x.get("org", 1) == org), None)
    if not ra or not rb:
        raise HTTPException(404, "run not found")
    ea, eb = set(ra.get("evidence_ids", [])), set(rb.get("evidence_ids", []))
    return {"a": a, "b": b, "same_question": ra.get("question") == rb.get("question"),
            "evidence_overlap": len(ea & eb),
            "evidence_only_a": sorted(ea - eb), "evidence_only_b": sorted(eb - ea),
            "analysis_changed": ra.get("analysis") != rb.get("analysis")}


@router.get("/api/v1/research/runs/{rid}/export", tags=["research"])
def research_export(rid: int, format: str = "json",
                    authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import research as _r
    _, org, _ = _ctx(authorization, x_api_key)
    run = next((x for x in STORE["research"]
                if x.get("id") == rid and x.get("org", 1) == org), None)
    if not run:
        raise HTTPException(404, "not found")
    if format == "markdown":
        ev = [e for e in STORE["evidence"] if e.get("id") in (run.get("evidence_ids") or [])]
        lines = [f"# Research: {run.get('question', '')}", "",
                 f"Status: {run.get('status')} | Model: {run.get('ai_model', '')} "
                 f"| Prompt: {run.get('prompt_version', '')}", "",
                 "## Analysis", run.get("analysis", "") or "_none_", "",
                 "## Evidence"]
        for e in ev:
            lines.append(f"- [{e['id']}] {e.get('source', '')} {e.get('url', '')}")
        lines += ["", "## Limitations",
                  "Evidence-grounded only; unverified claims excluded."]
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("\n".join(lines), media_type="text/markdown")
    return _r.bundle(run)



# ---- datasets ----
@router.post("/api/v1/datasets", tags=["datasets"])
def create_dataset(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    item = {"id": len(STORE["datasets"]) + 1, "org": org, "status": "draft", **spec}
    STORE["datasets"].append(item)
    _audit(email, "dataset.create", item.get("name", "")[:120])
    return item


@router.get("/api/v1/datasets", tags=["datasets"])
def list_datasets(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return {"items": _visible_by_org(STORE["datasets"], org)}


@router.get("/api/v1/datasets/{did}", tags=["datasets"])
def get_dataset(did: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "dataset not found")
    vs = [v for v in STORE["dsversions"] if v.get("dataset_id") == did]
    return {**d, "versions": [{k: val for k, val in v.items() if k != "rows"} for v in vs],
            "version_count": len(vs)}


@router.put("/api/v1/datasets/{did}", tags=["datasets"])
def update_dataset(did: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "dataset not found")
    for f in ("name", "kind", "status"):
        if f in spec and spec[f] is not None:
            d[f] = str(spec[f])[:200]
    repo.sync("datasets", d)
    _audit(email, "dataset.update", str(did))
    return d


@router.delete("/api/v1/datasets/{did}", tags=["datasets"])
def delete_dataset(did: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "dataset not found")
    STORE["datasets"][:] = [x for x in STORE["datasets"] if x.get("id") != did]
    STORE["dsversions"][:] = [v for v in STORE["dsversions"] if v.get("dataset_id") != did]
    _audit(email, "dataset.delete", str(did))
    return {"ok": True}


@router.post("/api/v1/datasets/{did}/import", tags=["datasets"])
def dataset_import(did: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import datasets as _d
    email, org, _ = _need(authorization, "collect", x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "dataset not found")
    rows = spec.get("rows", [])
    if spec.get("csv") and not rows:
        import csv as _csv
        import io as _io
        rows = list(_csv.DictReader(_io.StringIO(spec["csv"])))
    if len(rows) > 10000:
        raise HTTPException(413, "too many rows (max 10000)")
    v = _d.publish(STORE["dsversions"], did, rows,
                   {"source": "import", "by": email, **spec.get("lineage", {})})
    _audit(email, "dataset.import", f"{did}:v{v['version']}")
    return v


@router.post("/api/v1/datasets/{did}/publish", tags=["datasets"])
def dataset_publish(did: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import datasets as _d
    email, org, _ = _need(authorization, "collect", x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "dataset not found")
    rows = spec.get("rows", [])
    v = _d.publish(STORE["dsversions"], did, rows, spec.get("lineage", {}))
    _audit(email, "dataset.publish", f"{did}:v{v['version']}")
    return v


@router.get("/api/v1/datasets/{did}/versions", tags=["datasets"])
def dataset_versions(did: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "dataset not found")
    vs = [v for v in STORE["dsversions"] if v.get("dataset_id") == did]
    return {"items": [{k: val for k, val in v.items() if k != "rows"} for v in vs]}


@router.get("/api/v1/datasets/{did}/diff", tags=["datasets"])
def dataset_diff(did: int, v1: int = 0, v2: int = 0,
                 authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import datasets as _d
    _, org, _ = _ctx(authorization, x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "dataset not found")
    vs = sorted([v for v in STORE["dsversions"] if v.get("dataset_id") == did],
                key=lambda x: x.get("version", 0))
    a = next((x for x in vs if x.get("version") == v1), vs[0] if vs else None)
    b = next((x for x in vs if x.get("version") == v2), vs[-1] if vs else None)
    if not a or not b:
        raise HTTPException(404, "version not found")
    return {"from": a.get("version"), "to": b.get("version"),
            **_d.diff(a.get("rows", []), b.get("rows", []))}


@router.post("/api/v1/datasets/{did}/rollback", tags=["datasets"])
def dataset_rollback(did: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import datasets as _d
    email, org, _ = _need(authorization, "collect", x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "dataset not found")
    src = next((x for x in STORE["dsversions"]
                if x.get("dataset_id") == did and x.get("version") == spec.get("version")), None)
    if not src:
        raise HTTPException(404, "version not found")
    v = _d.publish(STORE["dsversions"], did, src.get("rows", []),
                   {"source": "rollback", "from_version": src.get("version"), "by": email})
    _audit(email, "dataset.rollback", f"{did}->v{v['version']}")
    return v


@router.get("/api/v1/datasets/{did}/export", tags=["datasets"])
def dataset_export(did: int, format: str = "csv", version: int = 0, mask_pii: int = 0):
    from ...services import datasets as _d
    vs = [v for v in STORE["dsversions"] if v.get("dataset_id") == did]
    rows = (vs[-1].get("rows", []) if vs else spec_rows(did))
    if version:
        v = next((x for x in vs if x.get("version") == version), None)
        rows = v.get("rows", []) if v else []
    if mask_pii:
        from ...services import pii as _pii
        rows = [{k: _pii.mask(str(val)) for k, val in r.items()} for r in rows]
    if format == "json":
        return {"rows": rows}
    return {"csv": _d.to_csv(rows)}


def spec_rows(did: int):
    return [p for p in STORE["prices"] if p.get("product_id") == did] or []



# ---- documents ----
@router.post("/api/v1/documents", tags=["knowledge"])
def ingest_document(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import documents as _d
    email, org, _ = _need(authorization, "collect", x_api_key)
    content = (spec.get("text", "") or "").encode()
    fp = _d.fingerprint(content)
    same = [x for x in STORE["documents"] if x.get("fingerprint") == fp]
    if same:
        return {"duplicate_of": same[0]["id"], "fingerprint": fp}
    import os as _o
    filename = _o.path.basename(spec.get("filename", "") or "")[:255]
    ext = _d.extract(spec.get("kind", "txt"), content, filename)
    item = {"id": len(STORE["documents"]) + 1, "org": org, "version": 1,
            "fingerprint": fp, "chunks": _d.chunk(ext.get("text", "")) if ext.get("extracted") else [],
            "title": spec.get("title", ""), "kind": spec.get("kind", "txt"),
            "source_url": spec.get("source_url", ""), "doc_metadata": ext.get("meta", {}),
            "extracted": ext.get("extracted"), "reason": ext.get("reason", "")}
    try:
        from ...services import pii as _pii
        item["doc_metadata"]["pii"] = {k: len(v) for k, v in
                                       _pii.detect(ext.get("text", "")).items()}
    except Exception:
        pass
    STORE["documents"].append(item)
    try:
        from ...search.semantic import get_index
        for i, ch in enumerate(item["chunks"][:50]):
            get_index().add(f"doc:{item['id']}:{i}", ch,
                            {"document": item["id"], "title": item["title"]})
    except Exception:
        pass
    _audit(email, "document.ingest", f"{item['id']}:{item.get('title', '')[:80]}")
    return item


@router.get("/api/v1/lineage/{fid}", tags=["knowledge"])
def lineage(fid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Answer 'where did this come from?': finding -> evidence -> sources/jobs."""
    _, org, _ = _ctx(authorization, x_api_key)
    f = next((x for x in STORE["findings"]
              if x.get("id") == fid and x.get("org", 1) == org), None)
    if not f:
        raise HTTPException(404, "finding not found")
    ev = [x for x in STORE["evidence"] if x.get("id") in (f.get("evidence_ids") or [])]
    jobs = [j for j in STORE["jobs"]
            if j.get("job_id") in {e.get("job_id", "") for e in ev} or
            j.get("job_id") in {p.get("job_id", "") for p in STORE["prices"]}]
    nodes = [n for n in STORE["nodes"]
             if n.get("name") in (f.get("entities") or []) or n.get("key") in (f.get("entities") or [])]
    return {"finding": {"id": f["id"], "title": f.get("title"), "kind": f.get("kind")},
            "evidence": [{"id": e["id"], "source": e.get("source"), "url": e.get("url"),
                          "content_hash": e.get("content_hash")} for e in ev],
            "jobs": [{"job_id": j.get("job_id"), "url": j.get("url"),
                      "strategy": j.get("strategy"), "status": j.get("status")} for j in jobs][:20],
            "entities": [n.get("name") for n in nodes]}


@router.get("/api/v1/documents", tags=["knowledge"])
def list_documents(page: int = 1, size: int = 20,
                   authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["documents"], org), page, size)


@router.post("/api/v1/evidence/{eid}/verify", tags=["knowledge"])
def verify_evidence(eid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Re-fetch the evidence source URL and compare content hash.
    Honest result: match/mismatch/unverifiable (no stored body to compare)."""
    import hashlib as _h
    email, org, _ = _need(authorization, "collect", x_api_key)
    ev = next((x for x in STORE["evidence"] if x.get("id") == eid), None)
    if not ev or _visible_by_org([ev], org) != [ev]:
        raise HTTPException(404, "evidence not found")
    url = (ev.get("url") or "").strip()
    if not url:
        return {"verified": False, "reason": "no source URL stored"}
    try:
        from ...services import pipeline as _pipe
        import os as _o
        trust = [x.strip() for x in _o.getenv("TRUSTED_EGRESS_CIDRS", "").split(",") if x.strip()]
        f = _pipe.fetch_direct(url, timeout_s=20, trusted_cidrs=trust or None)
    except Exception as e:  # noqa: BLE001
        return {"verified": False, "reason": f"fetch failed: {e}"[:200]}
    if not f.get("ok"):
        return {"verified": False, "reason": f.get("error", "fetch failed")}
    current = _h.sha256(f.get("body", b"")).hexdigest()[:32]
    stored = (ev.get("content_hash") or "")[:32]
    match = bool(stored) and current == stored
    _audit(email, "evidence.verify", f"{eid}:{match}")
    return {"verified": match, "stored_hash": stored, "current_hash": current,
            "detail": "hashes match" if match else
                      ("source content changed since capture" if stored else "no stored hash")}


@router.delete("/api/v1/documents/{did}", tags=["knowledge"])
def delete_document(did: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    d = next((x for x in STORE["documents"] if x.get("id") == did), None)
    if not d or _visible_by_org([d], org) != [d]:
        raise HTTPException(404, "document not found")
    STORE["documents"][:] = [x for x in STORE["documents"] if x.get("id") != did]
    _audit(email, "document.delete", str(did))
    return {"ok": True}



# ---- transformations (pivot over local data) ----
@router.get("/api/v1/transforms", tags=["knowledge"])
def transform_catalog():
    from ...services import transforms as _t
    return {"transforms": _t.TRANSFORMS}


@router.post("/api/v1/transforms/run", tags=["knowledge"])
def transform_run(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import transforms as _t
    email, org, _ = _need(authorization, "research", x_api_key)
    out = _t.run(STORE, spec.get("name", ""), spec.get("value", ""), org)
    if not out.get("ok"):
        raise HTTPException(400, out.get("error", "transform failed"))
    _audit(email, "transform.run", f"{spec.get('name')}:{len(out['results'])}")
    return out


# ---- unified timeline ----
@router.get("/api/v1/timeline", tags=["knowledge"])
def timeline(types: str = "", since: float = 0, until: float = 0, q: str = "",
             size: int = 100, authorization: str = Header(""), x_api_key: str = Header("")):
    """Chronological intelligence timeline across collections."""
    import time as _t
    _, org, _ = _ctx(authorization, x_api_key)
    want = {t.strip() for t in types.split(",") if t.strip()} or None
    until = until or _t.time() + 1
    evs = []

    def ts(v, *keys):
        for k in keys:
            x = v.get(k)
            if isinstance(x, (int, float)) and x:
                return x
        ca = v.get("created_at")
        if isinstance(ca, str):
            try:
                import datetime as _dt
                return _dt.datetime.fromisoformat(ca).timestamp()
            except Exception:
                return 0
        return 0

    def keep(kind, at, title, ref):
        if want and kind not in want:
            return
        if not (since <= at <= until):
            return
        if q and q.lower() not in f"{title} {ref}".lower():
            return
        evs.append({"kind": kind, "at": at, "title": title[:200], "ref": ref})

    for j in STORE["jobs"]:
        if j.get("org", 1) != org:
            continue
        keep("scan", ts(j, "finished_at", "created_at"), f"scan {j.get('status')}", j.get("url", ""))
    for f in STORE["findings"]:
        if f.get("org", 1) == org:
            keep("finding", ts(f), f.get("title", ""), f"finding:{f.get('id')}")
    for a in STORE["alerts"]:
        keep("alert", ts(a), f"[{a.get('rule')}] {a.get('message', '')}"[:200],
             f"alert:{a.get('id')}")
    for e in STORE["events"]:
        if e.get("org", 1) == org:
            keep("event", ts(e, "observed_at"), f"{e.get('type')}: {e.get('entity_key', '')}",
                 f"event:{e.get('id')}")
    for c in STORE["changes"]:
        keep("change", ts(c, "at"), f"{c.get('kind')} on target {c.get('target_id')}", "")
    for ev in STORE["evidence"]:
        if ev.get("org", 1) == org:
            keep("evidence", ts(ev), f"{ev.get('source')}: {(ev.get('url') or ev.get('snippet', ''))[:120]}", "")
    evs.sort(key=lambda x: x["at"], reverse=True)
    return {"items": evs[:max(1, min(size, 500))], "total": len(evs)}


# ---- STIX 2.1 / MISP interop ----
@router.post("/api/v1/stix/validate", tags=["intel"])
def stix_validate(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import stix as _sx
    _, _, _ = _ctx(authorization, x_api_key)
    errs = _sx.validate_bundle(spec.get("bundle", {}))
    return {"valid": not errs, "errors": errs}


@router.post("/api/v1/stix/export", tags=["intel"])
def stix_export(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import stix as _sx
    email, org, _ = _need(authorization, "research", x_api_key)
    kinds = spec.get("kinds") or ("entities", "relationships", "findings", "indicators")
    bundle, stats = _sx.export_bundle(STORE, org,
                                     spec.get("identity", "WebIntelligence"), tuple(kinds))
    _audit(email, "stix.export", str(len(bundle["objects"])))
    return {"bundle": bundle, "stats": stats}


@router.post("/api/v1/stix/import", tags=["intel"])
def stix_import(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import stix as _sx
    email, org, _ = _need(authorization, "research", x_api_key)
    out = _sx.import_bundle(STORE, spec.get("bundle", {}), org,
                            spec.get("source", "stix-import"))
    if not out.get("ok"):
        raise HTTPException(400, "; ".join(out.get("errors", ["invalid bundle"])))
    _audit(email, "stix.import", str(out["created"]))
    return out


@router.get("/api/v1/misp/export", tags=["intel"])
def misp_export(authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import stix as _sx
    email, org, _ = _need(authorization, "research", x_api_key)
    ev = _sx.to_misp_event(STORE, org)
    _audit(email, "misp.export", str(len(ev["Event"]["Attribute"])))
    return ev


@router.post("/api/v1/misp/import", tags=["intel"])
def misp_import(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import stix as _sx
    email, org, _ = _need(authorization, "research", x_api_key)
    out = _sx.from_misp_event(STORE, spec.get("event", {}), org)
    _audit(email, "misp.import", str(out))
    return out


@router.get("/api/v1/graph/path", tags=["knowledge"])
def graph_path(src: int = 0, dst: int = 0, rel: str = "",
               authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
    mine = {n["id"] for n in STORE["nodes"] if n.get("org", 1) == org}
    if src not in mine or dst not in mine:
        raise HTTPException(404, "node not found")
    edges = [e for e in STORE["edges"] if e.get("org", 1) == org]
    hops = _g.path(STORE["nodes"], edges, src, dst, rel.split(",") if rel else None)
    if not hops:
        return {"path": [], "connected": False}
    return {"path": [{"node": h["node"]["name"] if h.get("node") else None,
                      "via": h["via"]} for h in hops], "connected": True}


# ---- graph SVG (paginated subgraph, never the whole graph) ----
@router.get("/api/v1/graph/render", tags=["knowledge"])
def graph_svg(node: int = 0, depth: int = 1, limit: int = 30, rel: str = "",
              kind: str = "", since: str = "", until: str = "",
              authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
    depth, limit = min(max(1, depth), 4), min(max(1, limit), 100)
    start = next((n for n in STORE["nodes"] if n.get("id") == node), None) if node else None
    if node and (not start or start.get("org", 1) != org):
        raise HTTPException(404, "node not found")
    edges = [e for e in STORE["edges"] if e.get("org", 1) == org]
    if rel:
        edges = [e for e in edges if e.get("rel") in rel.split(",")]
    if since:
        edges = [e for e in edges if str(e.get("valid_from") or "") >= since]
    if until:
        edges = [e for e in edges if not e.get("valid_to") or str(e["valid_to"]) <= until]
    kinds = kind.split(",") if kind else None
    items = _g.traverse(STORE["nodes"], edges, node, depth, None, kinds, limit=limit)[:limit]
    by_id = {n["id"]: n for n in STORE["nodes"]}
    cx, parts = 200, []
    ids = [node] + [it["node"]["id"] for it in items if it.get("node")]
    pos = {nid: (60 + (i % 6) * 120, 60 + (i // 6) * 110) for i, nid in enumerate(ids)}
    for it in items:
        e = it["edge"]
        x1, y1 = pos.get(e["src"], (60, 60))
        x2, y2 = pos.get(e["dst"], (200, 60))
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#3b82f6"/>'
                     f'<text x="{(x1+x2)//2}" y="{(y1+y2)//2}" fill="#9fb0c9" font-size="10">{e["rel"]}</text>')
    for nid, (x, y) in pos.items():
        n = by_id.get(nid, {"name": nid, "kind": "?"})
        parts.append(f'<circle cx="{x}" cy="{y}" r="22" fill="#1b2942" stroke="#e6edf3"/>'
                     f'<text x="{x}" y="{y+4}" fill="#e6edf3" font-size="9" text-anchor="middle">'
                     f'{str(n.get("name", nid))[:10]}</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{max(200, len(pos)//6*110+120)}">' + "".join(parts) + "</svg>"
    return JSONResponse(content={"svg": svg, "nodes": len(pos), "truncated": len(items) == limit},
                        media_type="application/json")



# ---- dataset archive ----
@router.post("/api/v1/datasets/{did}/archive", tags=["datasets"])
def dataset_archive(did: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    d = next((x for x in STORE["datasets"]
              if x.get("id") == did and x.get("org", 1) == org), None)
    if not d:
        raise HTTPException(404, "not found")
    d["status"] = "archived"
    repo.sync("datasets", d)
    _audit(email, "dataset.archive", str(did))
    return {"ok": True}


