"""intel routes (split from main.py; behavior unchanged)."""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from ..shared import (
    AlertRuleIn,
    HTTPException,
    Header,
    JSONResponse,
    STORE,
    _audit,
    _ctx,
    _need,
    _porg,
    _providers,
    _require_auth,
    _sorted,
    _visible_by_org,
    build_alert,
    changedet,
    costeng,
    dec,
    muse,
    os,
    paginate,
    qual,
    repo,
    settings,
)

router = APIRouter()

# ---- reports ----
def _report_context(project_name: str, org: int):
    """Real report context: findings, entities, timeline, risk, recommendations."""
    from ...services import risk as _risk
    findings = [f for f in STORE["findings"]
                if f.get("org", 1) == org and f.get("status") not in ("RESOLVED", "FALSE_POSITIVE")][:20]
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: sev_rank.get(str(f.get("severity", "info")).lower(), 5))
    entities = STORE["entities"][:50]
    kinds = {}
    for e in entities:
        kinds[e.get("kind", "?")] = kinds.get(e.get("kind", "?"), 0) + 1
    tl = sorted(
        [{"at": c.get("at", 0), "text": f"{c.get('kind')} target {c.get('target_id')}"}
         for c in STORE["changes"][-20:]] +
        [{"at": a.get("created_at", 0) or 0, "text": f"[{a.get('rule')}] {(a.get('message') or '')[:80]}"}
         for a in STORE["alerts"][-20:]],
        key=lambda x: str(x["at"]), reverse=True)[:15]
    risks = []
    for t in [x for x in STORE["targets"] if x.get("org", 1) == org][:20]:
        try:
            r = _risk.score_target(STORE, t["id"], org)
            if r.get("score", 0) >= 25:
                risks.append({"target": t.get("domain"), "score": r["score"], "level": r["level"]})
        except Exception:
            continue
    risks.sort(key=lambda r: -r["score"])
    recs = []
    if any(str(f.get("severity", "")).lower() in ("critical", "high") for f in findings):
        recs.append("Triage critical/high findings immediately (confirm or mark false-positive).")
    if any(not a.get("acked") for a in STORE["alerts"]):
        recs.append("Acknowledge open alerts to meet SLA windows.")
    if risks:
        recs.append(f"Review top-risk asset {risks[0]['target']} (risk {risks[0]['score']}).")
    recs.append("Re-run collection on stale targets to keep evidence fresh.")
    crit = sum(1 for f in findings if str(f.get("severity", "")).lower() == "critical")
    summary = (f"Project '{project_name or 'all'}': {len(findings)} open findings "
               f"({crit} critical), {len(entities)} entities tracked, "
               f"{len(risks)} assets at medium risk or above. "
               f"Coverage from {len(STORE['jobs'])} collection jobs.")
    return {"executive_summary": summary,
            "scope": f"project={project_name or 'all'}",
            "risk_summary": "; ".join(f"{r['target']}: {r['score']} ({r['level']})"
                                     for r in risks[:5]) or "no elevated asset risk",
            "key_findings": [f"{f.get('severity', 'info').upper()}: {f.get('title', '')}"[:200]
                             for f in findings[:10]],
            "entities": [f"{k}: {v}" for k, v in sorted(kinds.items())],
            "timeline": [f"{e['at']}: {e['text']}"[:200] for e in tl],
            "recommendations": recs}


@router.post("/api/v1/reports")
def build_report(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _org0, _ = _need(authorization, "research", x_api_key)
    from ...reports.builder import build
    from ...intelligence.market import summarize

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
                [p.get("job_id") for p in STORE["prices"]][:50], str(analysis)[:4000],
                _report_context(spec.get("project", ""), _org0))
    _, _org2, _ = _need(authorization, "research", x_api_key)
    item = {"id": len(STORE["reports"]) + 1, "org": _org2, **rep}
    STORE["reports"].append(item)
    _audit(email, "report.create", str(item["id"]))
    return item


@router.get("/api/v1/reports")
def list_reports(page: int = 1, size: int = 20,
                 authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["reports"], org), page, size)


def _org_alert(aid: int, org: int):
    a = next((x for x in STORE["alerts"] if x.get("id") == aid), None)
    if not a:
        return None
    if _visible_by_org([a], org, "project") != [a]:
        return None
    return a


@router.get("/api/v1/reports/{rep_id}")
def get_report(rep_id: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    r = next((x for x in STORE["reports"] if x.get("id") == rep_id), None)
    if not r or _visible_by_org([r], org) != [r]:
        raise HTTPException(404, "report not found")
    return r


@router.delete("/api/v1/reports/{rep_id}")
def delete_report(rep_id: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    r = next((x for x in STORE["reports"] if x.get("id") == rep_id), None)
    if not r or _visible_by_org([r], org) != [r]:
        raise HTTPException(404, "report not found")
    STORE["reports"][:] = [x for x in STORE["reports"] if x.get("id") != rep_id]
    _audit(email, "report.delete", str(rep_id))
    return {"ok": True}


@router.post("/api/v1/reports/{rep_id}/regenerate")
def regenerate_report(rep_id: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Regenerate: rebuild the same report kind/project from current data."""
    from ...reports.builder import build
    from ...intelligence.market import summarize
    email, org, _ = _need(authorization, "research", x_api_key)
    src = next((x for x in STORE["reports"] if x.get("id") == rep_id), None)
    if not src or _visible_by_org([src], org) != [src]:
        raise HTTPException(404, "report not found")
    pid = src.get("product_id", 0)
    prices = [p["price"] for p in STORE["prices"] if not pid or p.get("product_id") == pid]
    analysis = summarize(prices)
    rep = build(src.get("kind", "price"), src.get("project", ""), prices,
                [p.get("job_id") for p in STORE["prices"]][:50], str(analysis)[:4000],
                _report_context(src.get("project", ""), org))
    item = {"id": len(STORE["reports"]) + 1, "org": org, **rep}
    STORE["reports"].append(item)
    _audit(email, "report.regenerate", f"{rep_id}->{item['id']}")
    return item



# ---- strategy / validation helpers ----
@router.post("/api/v1/strategy/decide")
def decide_strategy(target: dict, policy: dict = {}):
    engine = dec.Engine()
    p = dec.Policy(**{k: v for k, v in policy.items()
                       if k in ("allow_browser", "allow_proxy", "allow_brightdata",
                                "max_cost_per_job", "geo", "require_js")})
    return engine.decide(target, p, _providers())


@router.post("/api/v1/quality/score")
def quality_score(record: dict, required: list = []):
    return qual.score(record, required)


@router.post("/api/v1/changes/classify")
def classify_change(old_hash: str = None, new_hash: str = None,
                    old: dict = {}, new: dict = {}):
    kind = changedet.classify(old_hash, new_hash, old, new)
    return {"kind": kind, "diff": changedet.field_diff(old, new)}



# ---- alerts ----
@router.post("/api/v1/alerts")
def create_alert(a: AlertRuleIn, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import alertlife as _al
    email, _, _ = _need(authorization, "alert", x_api_key)
    item = build_alert(a.rule, a.message, a.project_id, a.channel) | {
        "id": len(STORE["alerts"]) + 1, "severity": "info",
        "sla_due": _al.sla_due("info")}
    STORE["alerts"].append(item)
    _audit(email, "alert.create", f"{item['rule']}:{item['id']}")
    return item


@router.get("/api/v1/alerts")
def list_alerts(page: int = 1, size: int = 20, sort: str = "", order: str = "asc",
                authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_sorted(_visible_by_org(STORE["alerts"], org, "project"), sort, order), page, size)



@router.get("/api/v1/search/semantic", tags=["search"])
def search_semantic(q: str = "", k: int = 5):
    from ...search.semantic import get_index
    if not q:
        return {"items": [], "method": "hashed-token vectors (non-neural)"}
    return {"items": get_index().search(q, max(1, min(20, k))),
            "method": "hashed-token vectors (non-neural)"}


# ---- analytics ----
@router.get("/api/v1/analytics/prices")
def analytics_prices(product_id: int = 0):
    from ...analytics.stats import (mean, volatility, anomaly_marks, pct_change,
                                    percentile, distribution, moving_avg)
    pts = [p for p in STORE["prices"] if not product_id or p.get("product_id") == product_id]
    vals = [p["price"] for p in pts]
    marks = anomaly_marks(vals) if len(vals) > 3 else []
    return {"count": len(vals), "avg": mean(vals) if vals else None,
            "min": min(vals) if vals else None, "max": max(vals) if vals else None,
            "volatility": volatility(vals) if len(vals) > 1 else 0.0,
            "change_pct": pct_change(vals[0], vals[-1]) if len(vals) > 1 else None,
            "p50": percentile(vals, 50), "p90": percentile(vals, 90),
            "distribution": distribution(vals),
            "moving_avg": moving_avg(vals)[-10:] if vals else [],
            "anomalies": [{"index": i, "price": vals[i]} for i in marks],
            "history": pts[-100:]}


@router.get("/api/v1/analytics/trends")
def analytics_trends():
    from ...analytics.trends import emerging_topics
    titles = [a.get("title", "") for a in STORE["articles"]]
    return {"topics": emerging_topics(titles),
            "review_volume": len([1 for _ in STORE["prices"]]),
            "articles": len(STORE["articles"])}


@router.get("/api/v1/analytics/quality")
def analytics_quality():
    from ...services.quality import score
    recs = [{"price": p.get("price"), "url": "job:" + str(p.get("job_id", ""))} for p in STORE["prices"]]
    req = ["price", "url"]
    scores = [score(r, req)["overall"] for r in recs] if recs else []
    return {"records": len(recs), "avg_overall": round(sum(scores) / len(scores), 3) if scores else None,
            "required": req}



# ---- intelligence ----
@router.post("/api/v1/intel/competitors/compare")
def intel_compare(spec: dict):
    from ...intelligence.competitors import compare
    return compare(spec.get("a", []), spec.get("b", []))


@router.post("/api/v1/intel/reviews")
def intel_reviews(spec: dict):
    from ...intelligence.reviews import analyze
    return analyze(spec.get("reviews", []))


@router.post("/api/v1/intel/news/summarize")
def intel_news(spec: dict):
    from ...intelligence.news import summarize_article
    return summarize_article(spec.get("title", ""), spec.get("body", ""))



# ---- entities ----
@router.post("/api/v1/entities/resolve")
def entity_resolve(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "collect", x_api_key)
    from ...services.entity_resolution import score, decide
    cand = spec.get("candidate", {})
    best, best_s = None, -1.0
    for e in STORE["entities"]:
        if e.get("org", 1) != org:
            continue
        s = score(cand, e)
        if s > best_s:
            best, best_s = e, s
    verdict = decide(best_s) if best else "NEW"
    if verdict == "NEW":
        item = {"id": len(STORE["entities"]) + 1, "org": org, **cand}
        STORE["entities"].append(item)
        _audit(email, "entity.resolve.new", str(item["id"]))
        return {"verdict": "NEW", "entity": item, "score": 0.0}
    if verdict == "LINK":
        best.pop("_review", None)
        return {"verdict": "LINK", "entity": best, "score": best_s}
    best["_review"] = True
    repo.sync("entities", best)
    return {"verdict": "REVIEW", "entity": best, "score": best_s}


@router.get("/api/v1/entities")
def list_entities(page: int = 1, size: int = 20,
                  authorization: str = Header(""), x_api_key: str = Header("")):
    from ..shared import paginate
    _, org, _ = _ctx(authorization, x_api_key)
    items = [x for x in STORE["entities"] if x.get("org", 1) == org]
    return paginate(items, page, size)



@router.post("/api/v1/alerts/{alert_id}/ack", tags=["alerts"])
def alert_ack(alert_id: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "alert", x_api_key)
    a = _org_alert(alert_id, org)
    if not a:
        raise HTTPException(404, "alert not found")
    a["acked"] = True
    a["is_read"] = True
    repo.sync("alerts", a)
    _audit(email, "alert.ack", str(alert_id))
    return {"ok": True}


@router.post("/api/v1/alerts/{alert_id}/resolve", tags=["alerts"])
def alert_resolve(alert_id: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "alert", x_api_key)
    a = _org_alert(alert_id, org)
    if not a:
        raise HTTPException(404, "alert not found")
    a["resolved"] = True
    a["is_read"] = True
    a["resolution"] = (spec.get("note", "") or "")[:500]
    repo.sync("alerts", a)
    _audit(email, "alert.resolve", str(alert_id))
    return {"ok": True}


@router.post("/api/v1/alerts/bulk", tags=["alerts"])
def alerts_bulk(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "alert", x_api_key)
    action = spec.get("action", "ack")
    if action not in ("ack", "resolve", "read"):
        raise HTTPException(400, "action must be ack|resolve|read")
    n = 0
    for aid in spec.get("ids", [])[:500]:
        a = _org_alert(aid, org)
        if not a:
            continue
        if action == "ack":
            a["acked"] = True
        elif action == "resolve":
            a["resolved"] = True
        a["is_read"] = True
        repo.sync("alerts", a)
        n += 1
    _audit(email, f"alert.bulk.{action}", str(n))
    return {"ok": True, "updated": n}


# ---- costs & budgets ----
@router.get("/api/v1/costs/summary")
def costs_summary():
    return costeng.summary(STORE["jobs"])


@router.post("/api/v1/costs/budget")
def set_budget(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _need(authorization, "configure", x_api_key)
    STORE["budgets"][str(spec.get("project_id", 1))] = float(spec.get("limit", 0))
    repo.set_budget(spec.get("project_id", 1), float(spec.get("limit", 0)))
    _audit(email, "budget.set", f"{spec.get('project_id', 1)}:{spec.get('limit', 0)}")
    return {"ok": True, "budgets": STORE["budgets"]}


@router.get("/api/v1/costs/budget/check")
def budget_check(project_id: int = 1):
    spent = sum(j.get("actual_cost", 0) or j.get("estimated_cost", 0)
                for j in STORE["jobs"] if j.get("project_id") == project_id)
    limit = STORE["budgets"].get(str(project_id))
    return {"spent": round(spent, 6), "limit": limit,
            "over": limit is not None and spent > limit}



# ---- ML registry ----
@router.post("/api/v1/ml/register")
def ml_register(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _need(authorization, "configure", x_api_key)
    from ...analytics.ml import register
    register(spec.get("name", "model"), spec.get("version", "v1"),
             spec.get("metrics", {}))
    _audit(email, "ml.register", f"{spec.get('name', 'model')}:{spec.get('version', 'v1')}")
    return {"ok": True}


@router.get("/api/v1/ml/models")
def ml_models():
    from ...analytics.ml import REGISTRY
    return {"models": REGISTRY}



# ---- alert delivery ----
@router.post("/api/v1/alerts/{alert_id}/send")
def alert_send(alert_id: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "alert", x_api_key)
    a = next((x for x in STORE["alerts"] if x.get("id") == alert_id), None)
    if not a:
        raise HTTPException(404, "alert not found")
    po = _porg(a.get("project_id"))
    if po is not None and po != org:
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
                repo.sync("alerts", a)
                _audit(email, "alert.send", f"{alert_id}:webhook:{r.status}")
                return {"delivered": True, "status": r.status}
        except Exception as e:
            a["delivery_error"] = str(e)[:200]
            repo.sync("alerts", a)
            _audit(email, "alert.send.failed", f"{alert_id}:{str(e)[:80]}")
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
            repo.sync("alerts", a)
            _audit(email, "alert.send", f"{alert_id}:email")
            return {"delivered": True}
        except Exception as e:
            a["delivery_error"] = str(e)[:200]
            repo.sync("alerts", a)
            _audit(email, "alert.send.failed", f"{alert_id}:{str(e)[:80]}")
            return {"delivered": False, "error": str(e)[:200]}
    a["is_read"] = False
    repo.sync("alerts", a)
    _audit(email, "alert.send", f"{alert_id}:inapp")
    return {"delivered": True, "channel": "inapp"}



# ---- report export ----
@router.get("/api/v1/reports/{rep_id}/export")
def report_export(rep_id: int, format: str = "json",
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    r = next((x for x in STORE["reports"]
              if x.get("id") == rep_id and x.get("org", 1) == org), None)
    if not r:
        raise HTTPException(404, "report not found")
    if format == "csv":
        from ...reports.builder import to_csv
        return JSONResponse(content={"csv": to_csv(r)})
    if format == "markdown":
        from ...reports.builder import to_markdown
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(to_markdown(r), media_type="text/markdown")
    if format == "html":
        from ...reports.builder import to_html
        from fastapi.responses import HTMLResponse
        return HTMLResponse(to_html(r))
    if format == "pdf":
        try:
            from ...reports.builder import to_pdf
            from fastapi.responses import Response
            return Response(content=to_pdf(r), media_type="application/pdf",
                            headers={"Content-Disposition": f"attachment; filename=report-{rep_id}.pdf"})
        except ImportError:
            raise HTTPException(501, "pdf requires reportlab (pip install reportlab)")
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
            from ...reports.builder import to_csv
            return {"fallback": "csv", "csv": to_csv(r)}
    return r



def _org_entity(eid: int, org: int):
    e = next((x for x in STORE["entities"] if x.get("id") == eid), None)
    if not e or e.get("org", 1) != org:
        return None
    return e


# ---- entity operations + explorer ----
@router.post("/api/v1/entities/merge", tags=["entities"])
def entity_merge(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entityops as _o
    email, org, _ = _need(authorization, "configure", x_api_key)
    if not _org_entity(spec.get("keep_id"), org) or not _org_entity(spec.get("drop_id"), org):
        raise HTTPException(404, "entity not found in your organization")
    out = _o.merge(STORE["entities"], STORE["entity_history"],
                   spec.get("keep_id"), spec.get("drop_id"), email)
    if not out["ok"]:
        raise HTTPException(404, out["error"])
    repo.sync("entities", out["entity"])
    _audit(email, "entity.merge", f"{spec.get('keep_id')}<-{spec.get('drop_id')}")
    return out


@router.post("/api/v1/entities/split", tags=["entities"])
def entity_split(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entityops as _o
    email, org, _ = _need(authorization, "configure", x_api_key)
    if not _org_entity(spec.get("entity_id"), org):
        raise HTTPException(404, "entity not found in your organization")
    out = _o.split(STORE["entities"], STORE["entity_history"],
                   spec.get("entity_id"), spec.get("parts", []), email)
    if not out["ok"]:
        raise HTTPException(404, out["error"])
    for ent in out["entities"]:
        repo.sync("entities", ent)
    _audit(email, "entity.split", str(spec.get("entity_id")))
    return out


@router.post("/api/v1/entities/reject", tags=["entities"])
def entity_reject(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entityops as _o
    email, org, _ = _need(authorization, "configure", x_api_key)
    if not _org_entity(spec.get("entity_id"), org):
        raise HTTPException(404, "entity not found in your organization")
    _audit(email, "entity.reject", str(spec.get("entity_id")))
    return _o.reject(STORE["entity_history"], spec.get("entity_id"),
                     spec.get("reason", ""), email)


@router.get("/api/v1/entities/history", tags=["entities"])
def entity_history(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    own = {x.get("id") for x in STORE["entities"] if x.get("org", 1) == org}
    return {"items": [h for h in STORE["entity_history"]
                      if h.get("keep") in own or h.get("drop") in own or h.get("src") in own]}


@router.post("/api/v1/entities/{eid}/aliases", tags=["entities"])
def entity_alias(eid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    e = _org_entity(eid, org)
    if not e:
        raise HTTPException(404, "entity not found")
    aliases = e.get("aliases", [])
    if spec.get("alias") and spec["alias"] not in aliases:
        aliases.append(spec["alias"])
    e["aliases"] = aliases
    repo.sync("entities", e)
    _audit(email, "entity.alias", f"{eid}:{spec.get('alias', '')}"[:120])
    return {"ok": True, "aliases": aliases}


@router.get("/api/v1/reviews/queue", tags=["entities"])
def review_queue(authorization: str = Header(""), x_api_key: str = Header("")):
    """Human-in-the-loop queue: REVIEW entities, UNVERIFIED/CONFLICTED claims,
    low-confidence findings. Approve/reject via entity ops + claim verify."""
    _, org, _ = _ctx(authorization, x_api_key)
    pending_entities = [e for e in STORE["entities"] if e.get("_review")]
    claims = [c for c in STORE["claims"]
              if c.get("org", 1) == org and c.get("status") in ("UNVERIFIED", "CONFLICTED")]
    low = [f for f in STORE["findings"]
           if f.get("org", 1) == org and (f.get("confidence") or 0) < 0.5]
    return {"entities": pending_entities, "claims": claims, "findings": low,
            "counts": {"entities": len(pending_entities), "claims": len(claims),
                       "findings": len(low)}}


@router.get("/api/v1/entities/{eid}", tags=["entities"])
def entity_detail(eid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    """Rich explorer: overview, timeline, relationships, events, changes, evidence."""
    _, org, _ = _ctx(authorization, x_api_key)
    e = _org_entity(eid, org)
    if not e:
        raise HTTPException(404, "not found")
    key = e.get("domain") or e.get("name", "")
    nodes = [n for n in STORE["nodes"] if n.get("org", 1) == org and key
             and (n.get("key") == key or n.get("name") == e.get("name"))]
    node_ids = {n["id"] for n in nodes}
    rels = [x for x in STORE["edges"] if x.get("org", 1) == org
            and (x.get("src") in node_ids or x.get("dst") in node_ids)]
    evts = [v for v in STORE["events"] if key and key.lower() in str(v.get("entity_key", "")).lower()]
    ev = [x for x in STORE["evidence"] if x.get("org", 1) == org and key
          and key.lower() in (x.get("url", "") + x.get("snippet", "")).lower()]
    from ...services import temporal as _t
    return {"entity": e, "timeline": _t.timeline(STORE["history"], f"price:{eid}"),
            "graph_nodes": nodes, "relationships": rels, "events": evts,
            "evidence": ev, "history": [h for h in STORE["entity_history"]
                                        if h.get("keep") == eid or h.get("drop") == eid or h.get("src") == eid]}



# ---- finding explorer ----
@router.get("/api/v1/findings/{fid}", tags=["intelligence"])
def finding_detail(fid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    f = next((x for x in STORE["findings"]
              if x.get("id") == fid and x.get("org", 1) == org), None)
    if not f:
        raise HTTPException(404, "not found")
    ev = [x for x in STORE["evidence"] if x.get("id") in (f.get("evidence_ids") or [])]
    rel_events = [v for v in STORE["events"]
                  if set(v.get("entities", [])) & set(f.get("entities", []))]
    return {"finding": f, "evidence": ev, "related_events": rel_events,
            "why": f"belief rests on {len(ev)} evidence record(s); "
                   f"confidence {f.get('confidence')}"}



# ---- reliability / correlation / prediction ----
@router.get("/api/v1/reliability/targets", tags=["sources"])
def target_reliability(target_id: int = 0):
    from ...services import reliability as _r
    atts = [a for a in STORE["attempts"] if not target_id or a.get("target_id") == target_id]
    return _r.score(atts)


@router.post("/api/v1/correlate/prices", tags=["intelligence"])
def correlate_prices(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import correlate as _c
    email, _, _ = _need(authorization, "research", x_api_key)
    out = _c.correlate_price_sources(spec.get("series_by_source", {}))
    saved = []
    if spec.get("save"):
        for co in out:
            f = _c.to_finding(co, spec.get("evidence_ids", []))
            f["id"] = len(STORE["findings"]) + 1
            STORE["findings"].append(f)
            saved.append(f["id"])
        _audit(email, "correlate.save", str(saved)[:200])
    return {"correlations": out, "saved_findings": saved}


@router.post("/api/v1/ml/predict", tags=["ml"])
def ml_predict(spec: dict):
    from ...services import predict as _p
    return _p.predict(spec.get("series", []), spec.get("model", "ewma"),
                      spec.get("features"))



# ---- feed subscriptions ----
@router.post("/api/v1/feed/subscriptions", tags=["intelligence"])
def feed_subscribe(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _ctx(authorization, x_api_key)
    sub = {"id": len(STORE["feed_subs"]) + 1, "owner": email, **spec}
    STORE["feed_subs"].append(sub)
    _audit(email, "feed.subscribe", str(sub["id"]))
    return sub


@router.get("/api/v1/feed/personalized", tags=["intelligence"])
def feed_personal(authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import feed as _f
    email, _, _ = _ctx(authorization, x_api_key)
    mine = [s for s in STORE["feed_subs"] if s.get("owner") == email]
    items = _f.build(STORE["events"], STORE["findings"], STORE["changes"], STORE["alerts"],
                   None, 200, STORE["targets"])
    return {"items": _f.subscribed(items, mine)}



# ---- alert threshold check ----
@router.post("/api/v1/alerts/check", tags=["alerts"])
def alert_check(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import alertguard as _ag
    from ...services import alertlife as _al
    email, org, _ = _need(authorization, "alert", x_api_key)
    out = _ag.check_threshold(spec.get("value", 0), spec.get("op", "gt"), spec.get("threshold", 0))
    if out.get("fired"):
        win = _al.suppressed(STORE.get("maintenance", []), spec.get("rule", "threshold"), org)
        if win:
            out["suppressed_by"] = win.get("name", win.get("id"))
            return out
    if out.get("fired") and _ag.should_fire(spec.get("rule", "threshold"), STORE["alert_hist"],
                                            spec.get("cooldown_s", 3600)):
        repo.kv_set("alert_hist", STORE["alert_hist"])
        item = {"id": len(STORE["alerts"]) + 1, "rule": spec.get("rule", "threshold"),
                "channel": "inapp", "message": out["message"], "project_id": spec.get("project_id", 0),
                "severity": spec.get("severity", "info"), "is_read": False,
                "sla_due": _al.sla_due(spec.get("severity", "info"))}
        STORE["alerts"].append(item)
        out["alert_id"] = item["id"]
        _audit(email, "alert.check.fire", f"{item['rule']}:{item['id']}")
    return out


@router.get("/api/v1/alerts/incidents", tags=["alerts"])
def alert_incidents(authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import alertlife as _al
    _, org, _ = _ctx(authorization, x_api_key)
    mine = [a for a in STORE["alerts"]
            if (lambda o: o is None or o == org)(_porg(a.get("project_id")))]
    return {"incidents": _al.incidents(mine)}


# NOTE: detail route sits after /incidents and /bulk so literals win.
@router.get("/api/v1/alerts/{alert_id}", tags=["alerts"])
def get_alert(alert_id: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    a = _org_alert(alert_id, org)
    if not a:
        raise HTTPException(404, "alert not found")
    return a


# ---- explainable risk ----
@router.get("/api/v1/risk/target/{tid}", tags=["intelligence"])
def risk_target(tid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import risk as _risk
    _, org, _ = _ctx(authorization, x_api_key)
    out = _risk.score_target(STORE, tid, org)
    if "error" in out:
        raise HTTPException(404, out["error"])
    return out


@router.get("/api/v1/risk/entity/{eid}", tags=["intelligence"])
def risk_entity(eid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import risk as _risk
    _, org, _ = _ctx(authorization, x_api_key)
    out = _risk.score_entity(STORE, eid, org)
    if "error" in out:
        raise HTTPException(404, out["error"])
    return out


