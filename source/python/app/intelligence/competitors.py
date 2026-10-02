def compare(prices_a, prices_b):
    """Evidence-backed compare. Each item: {price, evidence_id}."""
    def avg(items): return sum(i["price"] for i in items)/len(items) if items else None
    a, b = avg(prices_a), avg(prices_b)
    out = {"a_avg": a, "b_avg": b, "evidence": [i.get("evidence_id") for i in prices_a + prices_b]}
    if a and b: out["diff_pct"] = round((a-b)/b*100, 2)
    return out
