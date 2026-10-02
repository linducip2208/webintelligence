"""Natural-language data query → VALIDATED structured plan — stdlib.
The plan references only allowed datasets/fields; answer() enforces limits.
No raw SQL is ever generated or executed.
"""
import re
ALLOWED = {
    "prices": {"fields": {"product_id", "price", "currency", "observed_at"}, "max_limit": 100},
    "entities": {"fields": {"kind", "name", "domain"}, "max_limit": 50},
    "changes": {"fields": {"target_id", "kind"}, "max_limit": 100},
    "all": {"fields": set(), "max_limit": 20},
}
def to_plan(question: str):
    q = (question or "").lower()
    if re.search(r"price.*(increas|rose|up|higher)|increased in price", q):
        return {"intent": "price_increases", "dataset": "prices", "params": {"direction": "up"}}
    if re.search(r"new|enter|launch", q) and re.search(r"compan|competitor|market", q):
        return {"intent": "new_entrants", "dataset": "entities", "params": {"kind": "company"}}
    if re.search(r"chang|differ|monitor", q) and re.search(r"website|site|page", q):
        return {"intent": "site_changes", "dataset": "changes", "params": {}}
    if re.search(r"similar pric|compare pric", q):
        return {"intent": "price_compare", "dataset": "prices", "params": {}}
    return {"intent": "search", "dataset": "all", "params": {"q": question}}
def validate(plan: dict):
    """Reject plans touching non-allowlisted datasets/fields or huge limits."""
    ds = plan.get("dataset")
    if ds not in ALLOWED: return {"ok": False, "error": f"dataset not allowed: {ds}"}
    params = plan.get("params", {}) or {}
    try:
        limit = int(params.get("limit", ALLOWED[ds]["max_limit"]))
    except (TypeError, ValueError): return {"ok": False, "error": "bad limit"}
    if limit < 1 or limit > ALLOWED[ds]["max_limit"]:
        return {"ok": False, "error": f"limit out of range 1..{ALLOWED[ds]['max_limit']}"}
    fields = params.get("fields")
    if fields and (set(fields) - ALLOWED[ds]["fields"]):
        return {"ok": False, "error": f"fields not allowed: {sorted(set(fields) - ALLOWED[ds]['fields'])}"}
    plan = dict(plan); plan["params"] = dict(params, limit=limit)
    return {"ok": True, "plan": plan}
def answer(plan: dict, store: dict):
    v = validate(plan)
    if not v["ok"]: return {"error": v["error"]}
    plan = v["plan"]
    limit = plan["params"]["limit"]
    i = plan.get("intent")
    if i == "price_increases":
        by_p = {}
        for p in store.get("prices", []): by_p.setdefault(p.get("product_id"), []).append(p["price"])
        return [{"product_id": k, "first": v[0], "last": v[-1],
                 "pct": round((v[-1]-v[0])/abs(v[0])*100, 2) if v[0] else 0}
                for k, v in by_p.items() if len(v) > 1 and v[-1] > v[0]][:limit]
    if i == "site_changes":
        return [c for c in store.get("changes", []) if c.get("kind") == "CHANGED"][:limit]
    if i == "new_entrants":
        return [e for e in store.get("entities", []) if e.get("kind") == "company"][-limit:]
    return []
