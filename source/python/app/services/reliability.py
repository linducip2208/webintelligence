"""Source reliability from ACTUAL history — never fabricated. stdlib only.
inputs: attempts [{ok, latency_ms, completeness, at}], returns scored profile.
No history -> {score: None} (honest unknown), never a fake number.
"""
def score(attempts: list):
    if not attempts: return {"score": None, "reason": "no history"}
    n = len(attempts)
    ok = sum(1 for a in attempts if a.get("ok"))
    lat = [a.get("latency_ms", 0) for a in attempts if a.get("latency_ms") is not None]
    comp = [a.get("completeness", 1.0) for a in attempts]
    succ = ok / n
    avg_lat = sum(lat) / len(lat) if lat else 0
    lat_score = max(0.0, 1 - avg_lat / 30000)
    comp_score = sum(comp) / len(comp) if comp else 1.0
    # stability: fraction of consecutive same-status pairs
    stab = 1.0
    if n > 1:
        same = sum(1 for i in range(1, n) if bool(attempts[i].get("ok")) == bool(attempts[i-1].get("ok")))
        stab = same / (n - 1)
    overall = round(0.45 * succ + 0.2 * lat_score + 0.2 * comp_score + 0.15 * stab, 3)
    return {"score": overall, "success_rate": round(succ, 3), "attempts": n,
            "avg_latency_ms": round(avg_lat, 1), "completeness": round(comp_score, 3),
            "stability": round(stab, 3)}
