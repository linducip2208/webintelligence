"""Target intelligence bookkeeping — stdlib only."""
def record_attempt(profile: dict, strategy: str, ok: bool, latency_ms: float, cost: float):
    profile["attempts"] = profile.get("attempts", 0) + 1
    sb = profile.setdefault("success_by_strategy", {})
    if ok:
        profile["successes"] = profile.get("successes", 0) + 1
        sb[strategy] = sb.get(strategy, 0) + 1
    else: profile["failures"] = profile.get("failures", 0) + 1
    n = profile["attempts"]
    profile["avg_latency_ms"] = round(((profile.get("avg_latency_ms", 0.0) * (n-1)) + latency_ms) / n, 2)
    profile["avg_cost"] = round(((profile.get("avg_cost", 0.0) * (n-1)) + cost) / n, 6)
    return profile
def preferred_strategy(profile: dict):
    sb = profile.get("success_by_strategy", {})
    if not sb: return profile.get("preferred_strategy", "DIRECT_HTTP")
    return max(sb, key=sb.get)
