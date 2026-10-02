def paginate(items, page=1, size=20):
    page = max(1, page); size = max(1, min(100, size))
    total = len(items); start = (page - 1) * size
    return {"items": items[start:start+size], "total": total, "page": page, "size": size}
