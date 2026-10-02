def build(jobs, alerts, prices, health, costs):
    ok = sum(1 for j in jobs if j.get("status") == "success")
    fail = sum(1 for j in jobs if j.get("status") == "failed")
    return {
        "jobs_total": len(jobs),
        "jobs_success": ok,
        "jobs_failed": fail,
        "alerts_open": sum(1 for a in alerts if not a.get("is_read")),
        "price_points": len(prices),
        "health": health,
        "costs": costs,
    }
