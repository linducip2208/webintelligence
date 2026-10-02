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
)

router = APIRouter()

# ---- knowledge graph ----
@router.post("/api/v1/graph/nodes", tags=["knowledge"])
def graph_node(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
    return _g.add_node(STORE["nodes"], spec.get("kind", "company"),
                      spec.get("key", ""), spec.get("name", ""), org)


@router.post("/api/v1/graph/edges", tags=["knowledge"])
def graph_edge(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
    edge = _g.add_edge(STORE["edges"], spec.get("src"), spec.get("dst"),
                       spec.get("rel", "RELATED"), spec.get("confidence", 1.0),
                       spec.get("evidence", []), spec.get("at"), org)
    for e in STORE["edges"]:
        if e.get("valid_to"):
            repo.sync("edges", e)
    return edge


@router.get("/api/v1/graph/traverse", tags=["knowledge"])
def graph_traverse(node: int = 0, depth: int = 2, rel: str = "", kind: str = "",
                   authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
    start = next((n for n in STORE["nodes"] if n.get("id") == node), None)
    if node and (not start or start.get("org", 1) != org):
        raise HTTPException(404, "node not found")
    items = _g.traverse(STORE["nodes"], [e for e in STORE["edges"] if e.get("org", 1) == org],
                        node, depth,
                        rel.split(",") if rel else None,
                        kind.split(",") if kind else None)
    return {"items": items}



# ---- events / evidence / claims / findings ----
@router.post("/api/v1/events", tags=["knowledge"])
def create_event(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    item = {"id": len(STORE["events"]) + 1, "org": org, **spec}
    STORE["events"].append(item)
    _fire_watchlists(item)
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
    _, org, _ = _ctx(authorization, x_api_key)
    item = {"id": len(STORE["evidence"]) + 1, "org": org,
            **_e.make_evidence(spec.get("source", ""), spec.get("url", ""),
                               spec.get("content_hash", ""), spec.get("snippet", ""),
                               spec.get("selector", ""), spec.get("method", ""),
                               spec.get("confidence", 1.0))}
    STORE["evidence"].append(item)
    return item


@router.get("/api/v1/evidence", tags=["knowledge"])
def list_evidence(page: int = 1, size: int = 20,
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["evidence"], org), page, size)


@router.post("/api/v1/claims", tags=["knowledge"])
def create_claim(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    item = {"id": len(STORE["claims"]) + 1, "org": org, "status": "UNVERIFIED",
            "confidence": 0.0, **spec}
    STORE["claims"].append(item)
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
    _, org, _ = _ctx(authorization, x_api_key)
    item = {"id": len(STORE["findings"]) + 1, "org": org, **spec}
    STORE["findings"].append(item)
    return item


@router.get("/api/v1/findings", tags=["intelligence"])
def list_findings(page: int = 1, size: int = 20,
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["findings"], org), page, size)


@router.get("/api/v1/feed", tags=["intelligence"])
def intel_feed(kinds: str = "", limit: int = 50):
    from ...services import feed as _f
    return {"items": _f.build(STORE["events"], STORE["findings"], STORE["changes"],
                             STORE["alerts"], kinds.split(",") if kinds else None, limit)}


@router.get("/api/v1/opportunities", tags=["intelligence"])
def opportunities():
    from ...services import opportunities as _o
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
    _, org, _ = _ctx(authorization, x_api_key)
    item = {"id": len(STORE["research"]) + 1, "org": org, "status": "planned",
            "sources": [], "job_ids": [], "evidence_ids": [], "analysis": "",
            "ai_provider": "", "ai_model": settings.muse_model,
            "prompt_version": "v1", "config": spec.get("config", {}),
            "question": spec.get("question", ""), "plan": spec.get("plan") or _r.plan(spec.get("question", ""))}
    STORE["research"].append(item)
    _audit(_ctx(authorization, x_api_key)[0], "research.create", item["question"][:120])
    return item


@router.post("/api/v1/research/runs/{rid}/finish", tags=["research"])
def research_finish(rid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import research as _r
    _, org, _ = _ctx(authorization, x_api_key)
    run = next((x for x in STORE["research"]
                if x["id"] == rid and x.get("org", 1) == org), None)
    if not run:
        raise HTTPException(404, "not found")
    run.update({"status": "done", "analysis": spec.get("analysis", "")[:8000],
                "evidence_ids": spec.get("evidence_ids", run.get("evidence_ids", [])),
                "ai_provider": spec.get("ai_provider", ""), "ai_model": spec.get("ai_model", ""),
                "finished_at": time.time()})
    repo.sync("research", run)
    return {"ok": True, "reproducibility": _r.bundle(run)}


@router.get("/api/v1/research/runs", tags=["research"])
def research_runs(page: int = 1, size: int = 20,
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["research"], org), page, size)



# ---- datasets ----
@router.post("/api/v1/datasets", tags=["datasets"])
def create_dataset(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    item = {"id": len(STORE["datasets"]) + 1, "org": org, "status": "draft", **spec}
    STORE["datasets"].append(item)
    return item


@router.get("/api/v1/datasets", tags=["datasets"])
def list_datasets(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return {"items": _visible_by_org(STORE["datasets"], org)}


@router.post("/api/v1/datasets/{did}/import", tags=["datasets"])
def dataset_import(did: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import datasets as _d
    email, _, _ = _ctx(authorization, x_api_key)
    d = next((x for x in STORE["datasets"] if x.get("id") == did), None)
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
    return v


@router.post("/api/v1/datasets/{did}/publish", tags=["datasets"])
def dataset_publish(did: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import datasets as _d
    _require_auth(authorization, x_api_key)
    rows = spec.get("rows", [])
    v = _d.publish(STORE["dsversions"], did, rows, spec.get("lineage", {}))
    return v


@router.get("/api/v1/datasets/{did}/export", tags=["datasets"])
def dataset_export(did: int, format: str = "csv", version: int = 0):
    from ...services import datasets as _d
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



# ---- documents ----
@router.post("/api/v1/documents", tags=["knowledge"])
def ingest_document(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import documents as _d
    _, org, _ = _ctx(authorization, x_api_key)
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
    STORE["documents"].append(item)
    try:
        from ...search.semantic import get_index
        for i, ch in enumerate(item["chunks"][:50]):
            get_index().add(f"doc:{item['id']}:{i}", ch,
                            {"document": item["id"], "title": item["title"]})
    except Exception:
        pass
    return item


@router.get("/api/v1/documents", tags=["knowledge"])
def list_documents(page: int = 1, size: int = 20,
                   authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["documents"], org), page, size)



# ---- graph SVG (paginated subgraph, never the whole graph) ----
@router.get("/api/v1/graph/render", tags=["knowledge"])
def graph_svg(node: int = 0, depth: int = 1, limit: int = 30, rel: str = "",
              kind: str = "", since: str = "", until: str = "",
              authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import graph as _g
    _, org, _ = _ctx(authorization, x_api_key)
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
    _require_auth(authorization, x_api_key)
    d = next((x for x in STORE["datasets"] if x.get("id") == did), None)
    if not d:
        raise HTTPException(404, "not found")
    d["status"] = "archived"
    repo.sync("datasets", d)
    return {"ok": True}


