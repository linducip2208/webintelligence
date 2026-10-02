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
@router.post("/api/v1/reports")
def build_report(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    _require_auth(authorization, x_api_key)
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
                [p.get("job_id") for p in STORE["prices"]][:50], str(analysis)[:4000])
    _, _org2, _ = _ctx(authorization, x_api_key)
    item = {"id": len(STORE["reports"]) + 1, "org": _org2, **rep}
    STORE["reports"].append(item)
    return item


@router.get("/api/v1/reports")
def list_reports(page: int = 1, size: int = 20,
                 authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return paginate(_visible_by_org(STORE["reports"], org), page, size)



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
    _require_auth(authorization, x_api_key)
    item = build_alert(a.rule, a.message, a.project_id, a.channel) | {
        "id": len(STORE["alerts"]) + 1}
    STORE["alerts"].append(item)
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
    from ...analytics.stats import mean, volatility, anomaly_marks, pct_change
    pts = [p for p in STORE["prices"] if not product_id or p.get("product_id") == product_id]
    vals = [p["price"] for p in pts]
    marks = anomaly_marks(vals) if len(vals) > 3 else []
    return {"count": len(vals), "avg": mean(vals) if vals else None,
            "min": min(vals) if vals else None, "max": max(vals) if vals else None,
            "volatility": volatility(vals) if len(vals) > 1 else 0.0,
            "change_pct": pct_change(vals[0], vals[-1]) if len(vals) > 1 else None,
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
    _require_auth(authorization, x_api_key)
    from ...services.entity_resolution import score, decide
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
        best.pop("_review", None)
        return {"verdict": "LINK", "entity": best, "score": best_s}
    best["_review"] = True
    repo.sync("entities", best)
    return {"verdict": "REVIEW", "entity": best, "score": best_s}


@router.get("/api/v1/entities")
def list_entities(page: int = 1, size: int = 20):
    return paginate(STORE["entities"], page, size)



@router.post("/api/v1/alerts/{alert_id}/ack", tags=["alerts"])
def alert_ack(alert_id: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _ctx(authorization, x_api_key)
    a = next((x for x in STORE["alerts"] if x.get("id") == alert_id), None)
    if not a:
        raise HTTPException(404, "alert not found")
    a["acked"] = True
    a["is_read"] = True
    repo.sync("alerts", a)
    _audit(email, "alert.ack", str(alert_id))
    return {"ok": True}


@router.post("/api/v1/alerts/{alert_id}/resolve", tags=["alerts"])
def alert_resolve(alert_id: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, _, _ = _ctx(authorization, x_api_key)
    a = next((x for x in STORE["alerts"] if x.get("id") == alert_id), None)
    if not a:
        raise HTTPException(404, "alert not found")
    a["resolved"] = True
    a["is_read"] = True
    a["resolution"] = (spec.get("note", "") or "")[:500]
    repo.sync("alerts", a)
    _audit(email, "alert.resolve", str(alert_id))
    return {"ok": True}


# ---- costs & budgets ----
@router.get("/api/v1/costs/summary")
def costs_summary():
    return costeng.summary(STORE["jobs"])


@router.post("/api/v1/costs/budget")
def set_budget(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    _require_auth(authorization, x_api_key)
    STORE["budgets"][str(spec.get("project_id", 1))] = float(spec.get("limit", 0))
    repo.set_budget(spec.get("project_id", 1), float(spec.get("limit", 0)))
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
    _require_auth(authorization, x_api_key)
    from ...analytics.ml import register
    register(spec.get("name", "model"), spec.get("version", "v1"),
             spec.get("metrics", {}))
    return {"ok": True}


@router.get("/api/v1/ml/models")
def ml_models():
    from ...analytics.ml import REGISTRY
    return {"models": REGISTRY}



# ---- alert delivery ----
@router.post("/api/v1/alerts/{alert_id}/send")
def alert_send(alert_id: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
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



# ---- entity operations + explorer ----
@router.post("/api/v1/entities/merge", tags=["entities"])
def entity_merge(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import entityops as _o
    email, _, _ = _need(authorization, "configure")
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
    email, _, _ = _need(authorization, "configure")
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
    email, _, _ = _need(authorization, "configure")
    _audit(email, "entity.reject", str(spec.get("entity_id")))
    return _o.reject(STORE["entity_history"], spec.get("entity_id"),
                     spec.get("reason", ""), email)


@router.get("/api/v1/entities/history", tags=["entities"])
def entity_history():
    return {"items": STORE["entity_history"]}


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
def entity_detail(eid: int):
    """Rich explorer: overview, timeline, relationships, events, changes, evidence."""
    e = next((x for x in STORE["entities"] if x.get("id") == eid), None)
    if not e:
        raise HTTPException(404, "not found")
    key = e.get("domain") or e.get("name", "")
    nodes = [n for n in STORE["nodes"] if key and (n.get("key") == key or n.get("name") == e.get("name"))]
    node_ids = {n["id"] for n in nodes}
    rels = [x for x in STORE["edges"] if x.get("src") in node_ids or x.get("dst") in node_ids]
    evts = [v for v in STORE["events"] if key and key.lower() in str(v.get("entity_key", "")).lower()]
    ev = [x for x in STORE["evidence"] if key and key.lower() in (x.get("url", "") + x.get("snippet", "")).lower()]
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
    _require_auth(authorization, x_api_key)
    out = _c.correlate_price_sources(spec.get("series_by_source", {}))
    saved = []
    if spec.get("save"):
        for co in out:
            f = _c.to_finding(co, spec.get("evidence_ids", []))
            f["id"] = len(STORE["findings"]) + 1
            STORE["findings"].append(f)
            saved.append(f["id"])
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
    return sub


@router.get("/api/v1/feed/personalized", tags=["intelligence"])
def feed_personal(authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import feed as _f
    email, _, _ = _ctx(authorization, x_api_key)
    mine = [s for s in STORE["feed_subs"] if s.get("owner") == email]
    items = _f.build(STORE["events"], STORE["findings"], STORE["changes"], STORE["alerts"])
    return {"items": _f.subscribed(items, mine)}



# ---- alert threshold check ----
@router.post("/api/v1/alerts/check", tags=["alerts"])
def alert_check(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import alertguard as _ag
    _require_auth(authorization, x_api_key)
    out = _ag.check_threshold(spec.get("value", 0), spec.get("op", "gt"), spec.get("threshold", 0))
    if out.get("fired") and _ag.should_fire(spec.get("rule", "threshold"), STORE["alert_hist"],
                                            spec.get("cooldown_s", 3600)):
        repo.kv_set("alert_hist", STORE["alert_hist"])
        item = {"id": len(STORE["alerts"]) + 1, "rule": spec.get("rule", "threshold"),
                "channel": "inapp", "message": out["message"], "project_id": spec.get("project_id", 0),
                "severity": spec.get("severity", "info"), "is_read": False}
        STORE["alerts"].append(item)
        out["alert_id"] = item["id"]
    return out


