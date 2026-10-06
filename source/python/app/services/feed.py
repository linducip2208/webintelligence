"""Intelligence feed builder from real events/findings/changes/alerts — stdlib.

Rules: newest first (epoch-normalized sort, mixed ISO/float timestamps),
deduplicated (same kind+subject collapses to the latest, with a repeat
count), titles enriched with human names (target domain, not bare ids).
Never invents items; an empty store yields an empty feed.
"""
import time


def _epoch(v):
    try:
        if v is None or v == "":
            return 0
        if isinstance(v, (int, float)):
            return float(v)
        import datetime as _dt
        s = str(v).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = _dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            return time.mktime(d.timetuple())
        return d.timestamp()
    except Exception:
        return 0


def _ago(ts, now=None):
    now = now or time.time()
    s = max(0, now - ts)
    if s < 90:
        return "just now"
    if s < 3600:
        return f"{int(s // 60)}m ago"
    if s < 86400:
        return f"{int(s // 3600)}h ago"
    return f"{int(s // 86400)}d ago"


def build(events, findings, changes, alerts, kinds=None, limit=50, targets=None):
    now = time.time()
    tname = {t.get("id"): (t.get("domain") or t.get("url", "")[:60])
             for t in (targets or [])}
    raw = []
    for e in events:
        raw.append({"kind": str(e.get("type", "event")).upper(),
                    "at": _epoch(e.get("observed_at")),
                    "title": f"{e.get('type')}: {e.get('entity_key', '')}",
                    "ref": {"event": e.get("id")}})
    for f in findings:
        sev = str(f.get("severity", "info") or "info").upper()
        raw.append({"kind": "RESEARCH_FINDING", "at": _epoch(f.get("created_at")),
                    "title": f"[{sev}] {f.get('title', '')}",
                    "ref": {"finding": f.get("id")}})
    for c in changes:
        k = {"NEW": "PRODUCT_LAUNCH", "CHANGED": "CONTENT_CHANGE"}.get(
            c.get("kind"), "CONTENT_CHANGE")
        tid = c.get("target_id")
        who = tname.get(tid, f"target {tid}")
        raw.append({"kind": k, "at": _epoch(c.get("at")),
                    "title": f"{c.get('kind')} on {who}",
                    "ref": {"target": tid, "change": c.get("id")},
                    "_group": (k, tid)})
    for a in alerts:
        sev = str(a.get("severity", "info") or "info").upper()
        raw.append({"kind": "ALERT", "at": _epoch(a.get("created_at", a.get("at", 0))),
                    "title": f"[{sev}] {a.get('rule')}: {(a.get('message') or '')[:120]}",
                    "ref": {"alert": a.get("id")}})
    if kinds:
        raw = [i for i in raw if i["kind"] in kinds]
    # dedupe: same grouped subject -> latest wins, count repeats
    seen, items = {}, []
    for it in sorted(raw, key=lambda x: x["at"], reverse=True):
        g = it.pop("_group", None) or (it["kind"], str(it.get("ref")))
        if g in seen:
            seen[g]["repeats"] += 1
            continue
        it["repeats"] = 1
        seen[g] = it
        items.append(it)
    for it in items:
        if it["repeats"] > 1:
            it["title"] = f"({it['repeats']}×) {it['title']} — latest {_ago(it['at'], now)}"
    items.sort(key=lambda x: x["at"], reverse=True)
    return items[:limit]


def subscribed(items: list, subs: list):
    """subs: [{kinds:[...], keywords:[...]}]. Item passes if kind matches and any keyword in title."""
    out = []
    for it in items:
        for s in subs:
            if s.get("kinds") and it["kind"] not in s["kinds"]:
                continue
            kws = [k.lower() for k in s.get("keywords", [])]
            if kws and not any(k in (it.get("title") or "").lower() for k in kws):
                continue
            out.append(it)
            break
    return out
