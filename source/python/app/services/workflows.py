"""Generic workflow engine: trigger→condition→action — stdlib, idempotent."""
import hashlib, json
ACTIONS = ("create_alert", "webhook", "tag", "run_collection", "run_analysis")
def key(wf_id, step, context: dict):
    return hashlib.sha256(f"{wf_id}:{step}:{json.dumps(context, sort_keys=True)}".encode()).hexdigest()[:32]
def check_condition(cond: dict, event: dict) -> bool:
    if not cond: return True
    for k, v in cond.items():
        if str(event.get(k)) != str(v): return False
    return True
def run_step(step: dict, event: dict, store: dict):
    """Executes one action; store provides alerts/webhooks/jobs lists. Returns effect record."""
    a = step.get("action")
    if a not in ACTIONS: return {"ok": False, "error": f"unknown action {a}"}
    params = step.get("params", {})
    if a == "create_alert":
        import time as _t
        item = {"id": len(store.get("alerts", [])) + 1, "rule": params.get("rule", "workflow"),
                "message": params.get("message", str(event))[:500], "channel": params.get("channel", "inapp"),
                "project_id": params.get("project_id", 0), "is_read": False,
                "severity": params.get("severity", "info"),
                "sla_due": _t.time() + 72 * 3600}
        store.setdefault("alerts", []).append(item)
        return {"ok": True, "alert_id": item["id"]}
    if a == "tag":
        store.setdefault("tags", {})[str(params.get("entity"))] = params.get("tag")
        return {"ok": True}
    if a == "run_collection":
        job = {"url": params.get("url", event.get("url", "")), "strategy": "AUTO"}
        store.setdefault("wf_jobs", []).append(job)
        return {"ok": True, "job": job}
    if a == "webhook":
        store.setdefault("wf_webhooks", []).append({"url": params.get("url"), "event": event})
        return {"ok": True, "queued": True}
    store.setdefault("wf_analysis", []).append({"event": event, "kind": params.get("kind", "generic")})
    return {"ok": True}
