"""Cross-source correlation: findings only with actual shared evidence. stdlib."""
def shared_entities(items_a: list, items_b: list):
    ea = {e for it in items_a for e in (it.get("entities") or [])}
    eb = {e for it in items_b for e in (it.get("entities") or [])}
    return sorted(ea & eb)
def correlate_price_sources(series_by_source: dict):
    """series_by_source: {source: [prices]}. Returns conflict/agreement findings."""
    out = []
    srcs = list(series_by_source)
    for i in range(len(srcs)):
        for j in range(i + 1, len(srcs)):
            a, b = series_by_source[srcs[i]], series_by_source[srcs[j]]
            if not a or not b: continue
            la, lb = a[-1], b[-1]
            if abs(la - lb) < 1e-9:
                out.append({"type": "AGREEMENT", "sources": [srcs[i], srcs[j]], "value": la})
            else:
                out.append({"type": "CONFLICT", "sources": [srcs[i], srcs[j]],
                            "values": {srcs[i]: la, srcs[j]: lb}})
    return out
def to_finding(corr: dict, evidence_ids: list):
    return {"kind": corr["type"], "title": f"{corr['type']}: {corr['sources']}",
            "body": str(corr.get("values", corr.get("value"))),
            "entities": [], "evidence_ids": evidence_ids, "confidence": 0.7}
