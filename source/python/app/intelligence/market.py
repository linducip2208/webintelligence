from ..analytics.stats import mean, volatility
def summarize(prices):
    return {"count": len(prices), "avg": mean(prices) if prices else None,
            "min": min(prices) if prices else None, "max": max(prices) if prices else None,
            "volatility": volatility(prices) if len(prices) > 1 else 0.0}
