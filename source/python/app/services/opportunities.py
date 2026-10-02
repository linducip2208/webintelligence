"""Opportunity/anomaly detectors on real histories — stdlib."""
try:
    from ..analytics.stats import mean, stdev
except ImportError:
    from analytics.stats import mean, stdev
def price_anomaly(prices: list, z=3.0):
    if len(prices) < 5: return []
    m, s = mean(prices), stdev(prices)
    if not s: return []
    return [{"index": i, "price": p, "z": round((p - m) / s, 2)} for i, p in enumerate(prices) if abs((p - m) / s) >= z]
def burst(counts: list, factor=3.0):
    """counts per bucket; flag buckets >= factor * median."""
    if not counts: return []
    med = sorted(counts)[len(counts)//2] or 1
    return [i for i, c in enumerate(counts) if c >= factor * med]
