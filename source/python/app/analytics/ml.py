"""Tiny modular ML — stdlib only (optional sklearn never required)."""
from .stats import mean
REGISTRY = {}
def register(name, version, metrics):
    REGISTRY[name] = {"version": version, "metrics": metrics}
def forecast_ewma(series, alpha=0.3):
    if not series: return None
    e = series[0]
    for x in series[1:]: e = alpha*x + (1-alpha)*e
    return round(e, 4)
def forecast_linear(series):
    n = len(series)
    if n < 2: return series[-1] if series else None
    mx = (n-1)/2; my = mean(series)
    den = sum((i-mx)**2 for i in range(n))
    slope = sum((i-mx)*(y-my) for i, y in enumerate(series))/den if den else 0
    return round(my + slope*(n-mx), 4)
def sentiment(text):
    t = (text or "").lower()
    pos = sum(w in t for w in ("good","great","love","excellent","awesome","recommend"))
    neg = sum(w in t for w in ("bad","terrible","hate","awful","broken","refund"))
    if pos > neg: return "positive"
    if neg > pos: return "negative"
    return "neutral"
