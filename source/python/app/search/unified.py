"""Unified intelligence search: one engine for keyword, exact, semantic and
hybrid modes. No AI required for any mode (semantic uses hashed lexical
vectors, honestly labeled). Every collection is org-scoped: one org can
never see another's records.

Result shape (stable, additive):
  {id, kind, title, subtitle, score, risk, status, source, seen, updated_at,
   open, route, investigation_id, target_id}
plus legacy passthroughs (name/domain/url/value) so older clients keep working.
"""
from __future__ import annotations

import re as _re
import time as _time

SEVERITY_RISK = {"critical": 90, "high": 75, "medium": 50, "low": 25, "info": 10,
                 "informational": 10}


def _org(rows, org):
    return [r for r in (rows or []) if r.get("org", 1) == org]


def _epoch(v):
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        import datetime as _dt
        return _dt.datetime.fromisoformat(str(v)).timestamp()
    except Exception:
        return 0.0


def _risk_of(kind, it):
    if isinstance(it.get("risk"), (int, float)):
        return float(it["risk"])
    sev = str(it.get("severity") or "").lower()
    if sev in SEVERITY_RISK:
        return float(SEVERITY_RISK[sev])
    return None


def _base(kind, it, title, subtitle="", open_kind=None, route=None):
    risk = _risk_of(kind, it)
    seen = it.get("last_seen") or it.get("updated_at") or it.get("created_at") or it.get("at") or 0
    iid = it.get("id")
    return {
        "id": iid, "kind": kind, "title": str(title or "")[:200],
        "subtitle": str(subtitle or "")[:300], "score": 0.0, "risk": risk,
        "status": it.get("status") or "",
        "source": it.get("source") or it.get("collector") or it.get("source_type") or "",
        "seen": seen, "updated_at": it.get("updated_at") or it.get("created_at") or seen,
        "open": open_kind, "route": route,
        "investigation_id": it.get("investigation_id"),
        "target_id": it.get("target_id"),
        # legacy passthroughs for older clients
        "name": it.get("name"), "domain": it.get("domain"), "url": it.get("url"),
        "value": it.get("value"),
    }


def harvest(store, org):
    """All searchable records, org-scoped and normalized (unscored)."""
    out = []
    for it in _org(store.get("investigations"), org):
        out.append(_base("investigation", it, it.get("title"),
                         f"{it.get('status', '')} · {(it.get('description') or '')[:120]}".strip(" ·"),
                         "investigation", f"#investigation/{it.get('id')}"))
    for it in _org(store.get("targets"), org):
        out.append(_base("target", it, it.get("domain") or it.get("url"),
                         (it.get("url") or ""), "target", f"#target/{it.get('id')}"))
    for it in _org(store.get("entities"), org):
        out.append(_base("entity", it, it.get("name") or it.get("domain"),
                         f"{it.get('kind', '')} · conf {it.get('confidence', '')}".strip(" ·"),
                         "entity", f"#entity/{it.get('id')}"))
    for it in _org(store.get("findings"), org):
        blob = " ".join(str(it.get(k, "")) for k in ("kind", "type", "category", "title"))
        ind = bool(_re.search(r"indicator|ioc|domain|^ip$|url|hash|cert|malware|phish", blob, _re.I))
        out.append(_base("indicator" if ind else "finding", it, it.get("title"),
                         f"{it.get('severity', '')} · conf {it.get('confidence', '')}".strip(" ·"),
                         "finding", None))
    for it in _org(store.get("cases"), org):
        out.append(_base("case", it, it.get("title"),
                         f"{it.get('status', '')}", "case", f"#case/{it.get('id')}"))
    for it in _org(store.get("evidence"), org):
        out.append(_base("evidence", it, (it.get("snippet") or it.get("url") or f"evidence #{it.get('id')}"),
                         f"{it.get('source', '')}", None, "#evidence"))
    for it in _org(store.get("documents"), org):
        out.append(_base("document", it, it.get("title") or f"document #{it.get('id')}",
                         f"{it.get('kind', '')}", None, "#documents"))
    for it in _org(store.get("articles"), org):
        out.append(_base("article", it, it.get("title"),
                         f"{it.get('publisher', '')}", None, None))
    for it in _org(store.get("events"), org):
        out.append(_base("event", it, it.get("title") or it.get("type") or it.get("entity_key"),
                         f"{it.get('type', '')}", None, "#timeline"))
    for it in _org(store.get("watchlists"), org):
        out.append(_base("watchlist", it, it.get("value"),
                         f"{it.get('kind', '')}", None, "#watchlists"))
    for it in _org(store.get("claims"), org):
        out.append(_base("claim", it, it.get("value") or it.get("text"),
                         "", None, "#evidence"))
    return out


def _tokens(q):
    return [t for t in _re.findall(r"[a-z0-9]{2,}", q.lower()) if t]


def _text(it):
    return " ".join(str(it.get(k) or "") for k in
                    ("title", "subtitle", "name", "domain", "url", "value")).lower()


def _score(it, terms, q):
    text = _text(it)
    if not text.strip():
        return 0.0
    score = 0.0
    for field in ("title", "name", "domain", "url", "value"):
        v = str(it.get(field) or "").lower()
        if not v:
            continue
        if v == q:
            score += 100.0
        elif v.startswith(q):
            score += 50.0
    hits = sum(1 for t in terms if t in text)
    if q and q in text:
        hits += 1
    score += 10.0 * hits
    if it.get("risk") is not None:
        score += min(float(it["risk"]), 100.0) / 50.0  # 0..2 relevance nudge
    seen = _epoch(it.get("seen"))
    if seen:
        age_days = max(0.0, (_time.time() - seen) / 86400.0)
        score += max(0.0, 2.0 - age_days / 30.0)  # fresher sorts slightly higher
    return round(score, 3)


def _apply_filters(items, kinds=None, risk_min=None, risk_max=None, source=None,
                   date_from=None, date_to=None):
    if kinds:
        items = [i for i in items if i["kind"] in kinds]
    if risk_min is not None:
        items = [i for i in items if i["risk"] is not None and i["risk"] >= risk_min]
    if risk_max is not None:
        items = [i for i in items if i["risk"] is not None and i["risk"] <= risk_max]
    if source:
        s = source.lower()
        items = [i for i in items if s in str(i.get("source") or "").lower()]
    df, dt = _epoch(date_from) if date_from else 0, _epoch(date_to) if date_to else 0
    if df:
        items = [i for i in items if _epoch(i.get("seen")) >= df or _epoch(i.get("updated_at")) >= df]
    if dt:
        items = [i for i in items if (_epoch(i.get("seen")) or _epoch(i.get("updated_at"))) <= dt]
    return items


def keyword_search(store, org, q, kinds=None, limit=20, offset=0, **filters):
    items = harvest(store, org)
    q = (q or "").lower().strip()
    terms = _tokens(q)
    scored = []
    for it in items:
        s = _score(it, terms, q)
        if s > 0:
            it = dict(it, score=s)
            scored.append(it)
    scored.sort(key=lambda i: (-i["score"], -(i["risk"] or 0)))
    scored = _apply_filters(scored, kinds, **filters)
    return scored, len(scored)


def exact_search(store, org, q, kinds=None, limit=20, offset=0, **filters):
    items = harvest(store, org)
    q = (q or "").lower().strip()
    out = []
    for it in items:
        for field in ("title", "name", "domain", "url", "value"):
            if str(it.get(field) or "").lower() == q:
                out.append(dict(it, score=100.0))
                break
    out = _apply_filters(out, kinds, **filters)
    return out, len(out)


def semantic_search(store, org, q, kinds=None, limit=20, offset=0, **filters):
    from .semantic import get_index
    idx = get_index()
    hits = idx.search(q or "", max(1, min(50, limit + offset)))
    by_doc = {}
    for it in _org(store.get("documents"), org):
        by_doc[it["id"]] = it
    out = []
    for h in hits:
        ref = h.get("ref") or {}
        doc = by_doc.get(ref.get("document"))
        if doc is None:
            continue
        norm = _base("document", doc, doc.get("title") or h.get("text", "")[:120],
                     (h.get("text") or "")[:200], None, "#documents")
        norm["score"] = round(float(h.get("score", 0)) * 100.0, 3)
        out.append(norm)
    out = _apply_filters(out, kinds, **filters)
    return out, len(out)


def unified_search(store, org, q, mode="hybrid", kinds=None, limit=20, offset=0,
                   investigation_id=None, **filters):
    """mode: keyword | exact | semantic | hybrid (default). Returns (page, total)."""
    mode = (mode or "hybrid").lower()
    if mode not in ("keyword", "exact", "semantic", "hybrid"):
        mode = "keyword"
    if not (q or "").strip():
        return [], 0
    limit = max(1, min(100, int(limit or 20)))
    offset = max(0, int(offset or 0))
    if mode == "keyword":
        items, total = keyword_search(store, org, q, kinds, limit, offset, **filters)
    elif mode == "exact":
        items, total = exact_search(store, org, q, kinds, limit, offset, **filters)
    elif mode == "semantic":
        items, total = semantic_search(store, org, q, kinds, limit, offset, **filters)
    else:
        kw, _ = keyword_search(store, org, q, kinds, 100, 0, **filters)
        sem, _ = semantic_search(store, org, q, kinds, 100, 0, **filters)
        seen_ids = {(i["kind"], i["id"]) for i in kw}
        merged = list(kw)
        for s in sem:
            if (s["kind"], s["id"]) not in seen_ids:
                merged.append(dict(s, score=round(s["score"] / 10.0, 3)))
        merged.sort(key=lambda i: (-i["score"], -(i["risk"] or 0)))
        items, total = merged, len(merged)
    if investigation_id is not None:
        inv = next((x for x in _org(store.get("investigations"), org)
                    if x.get("id") == investigation_id), None)
        if inv is None:
            return [], 0
        tids = set(inv.get("target_ids") or [])
        eids = set(inv.get("entity_ids") or [])
        case_ids = {c.get("id") for c in _org(store.get("cases"), org)
                    if investigation_id in (c.get("investigation_ids") or [])}

        def _rel(it):
            k = it["kind"]
            if k == "investigation":
                return it["id"] == investigation_id
            if k == "target":
                return it["id"] in tids
            if k == "entity":
                return it["id"] in eids
            if k == "case":
                return it["id"] in case_ids
            return False

        items = [i for i in items if _rel(i)]
        total = len(items)
    return items[offset:offset + limit], total


def search(db_items, query, scope="all", limit=20):
    """Legacy compat: substring search over caller-provided slices."""
    q = (query or "").lower()
    out = []
    kinds = None if scope == "all" else [scope]
    for kind, items in (db_items or {}).items():
        if kinds and kind not in kinds:
            continue
        for it in items or []:
            blob = " ".join(str(v) for v in it.values()).lower()
            if q in blob:
                out.append({"kind": kind, **it})
    return out[:limit]
