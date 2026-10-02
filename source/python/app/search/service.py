def search(db_items: dict, query: str, scope="all", limit=20):
    q = (query or "").lower()
    out = []
    for kind, items in db_items.items():
        if scope != "all" and scope != kind: continue
        for it in items:
            blob = " ".join(str(v) for v in it.values()).lower()
            if q in blob: out.append({"kind": kind, **it})
    return out[:limit]
