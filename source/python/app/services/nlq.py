"""Natural-language data query → structured plan — stdlib, regex intents."""
import re
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
def answer(plan: dict, store: dict):
    i = plan.get("intent")
    if i == "price_increases":
        by_p = {}
        for p in store.get("prices", []): by_p.setdefault(p.get("product_id"), []).append(p["price"])
        return [{"product_id": k, "first": v[0], "last": v[-1],
                 "pct": round((v[-1]-v[0])/abs(v[0])*100, 2) if v[0] else 0}
                for k, v in by_p.items() if len(v) > 1 and v[-1] > v[0]]
    if i == "site_changes":
        return [c for c in store.get("changes", []) if c.get("kind") == "CHANGED"]
    if i == "new_entrants":
        return [e for e in store.get("entities", []) if e.get("kind") == "company"][-10:]
    return []
