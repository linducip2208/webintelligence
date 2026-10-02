"""Intelligence feed builder from real events/findings/changes/alerts — stdlib."""
def build(events, findings, changes, alerts, kinds=None, limit=50):
    items = []
    for e in events: items.append({"kind": e.get("type", "event").upper(), "at": e.get("observed_at"),
        "title": f"{e.get('type')}: {e.get('entity_key')}", "ref": {"event": e.get("id")}})
    for f in findings: items.append({"kind": "RESEARCH_FINDING", "at": f.get("created_at"),
        "title": f.get("title"), "ref": {"finding": f.get("id")}})
    for c in changes:
        k = {"NEW": "PRODUCT_LAUNCH", "CHANGED": "CONTENT_CHANGE"}.get(c.get("kind"), "CONTENT_CHANGE")
        items.append({"kind": k, "at": c.get("at"), "title": f"{c.get('kind')} on target {c.get('target_id')}",
                      "ref": {"target": c.get("target_id")}})
    for a in alerts: items.append({"kind": "ALERT", "at": a.get("at"), "title": a.get("message"),
        "ref": {"alert": a.get("id")}})
    if kinds: items = [i for i in items if i["kind"] in kinds]
    items.sort(key=lambda x: str(x.get("at") or ""), reverse=True)
    return items[:limit]
