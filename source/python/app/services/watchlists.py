"""Watchlist matching — stdlib."""
def match(watchlists: list, item: dict):
    """item: {kind,value,text}. Returns matched watchlist ids."""
    hits = []
    blob = f"{item.get('value','')} {item.get('text','')}".lower()
    for w in watchlists:
        v = (w.get("value") or "").lower()
        if w.get("kind") == "keyword" and v and v in blob: hits.append(w["id"])
        elif w.get("kind") in ("company","product","brand","domain") and v and v == (item.get("value") or "").lower():
            hits.append(w["id"])
    return hits
