"""Cost engine — stdlib only."""
COSTS = {"DIRECT_HTTP": 0.0001, "OFFICIAL_API": 0.0002, "BROWSER": 0.01, "OWN_PROXY": 0.002, "BRIGHT_DATA": 0.05}
def estimate(strategy, pages=1, ai_in=0, ai_out=0, ai_rate_in=1.5e-6, ai_rate_out=6e-6):
    c = COSTS.get(strategy, 0.001) * pages + ai_in * ai_rate_in + ai_out * ai_rate_out
    return round(c, 6)
def per_record(total_cost, n_ok): return round(total_cost / n_ok, 6) if n_ok else None
def per_1k(total_cost, n_ok): return round(total_cost / n_ok * 1000, 4) if n_ok else None
def within_budget(cost, budget): return cost <= budget
