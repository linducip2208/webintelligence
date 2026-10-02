"""Descriptive/time-series/price/anomaly/correlation — stdlib only."""
import math
def mean(xs): return sum(xs)/len(xs) if xs else 0.0
def stdev(xs):
    if len(xs) < 2: return 0.0
    m = mean(xs); return math.sqrt(sum((x-m)**2 for x in xs)/(len(xs)-1))
def anomaly_marks(series):
    """Return indices where |z|>=3."""
    m, s = mean(series), stdev(series)
    if s == 0: return []
    return [i for i, x in enumerate(series) if abs((x-m)/s) >= 3]
def pct_change(old, new):
    if not old: return None
    return round((new-old)/abs(old)*100, 2)
def moving_avg(xs, w=3):
    return [round(sum(xs[max(0, i-w+1):i+1]) / len(xs[max(0, i-w+1):i+1]), 4) for i in range(len(xs))]
def growth(xs):
    return [None] + [pct_change(xs[i-1], xs[i]) for i in range(1, len(xs))]
def volatility(prices):
    m = mean(prices)
    return round(stdev(prices)/m, 4) if m else 0.0
def pearson(a, b):
    n = min(len(a), len(b))
    if n < 2: return 0.0
    a, b = a[:n], b[:n]
    ma, mb = mean(a), mean(b)
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b))
    return round(num/den, 4) if den else 0.0
def kmeans1d(xs, k=2, iters=20):
    if not xs: return []
    lo, hi = min(xs), max(xs)
    centers = [lo, hi][:k]
    for _ in range(iters):
        groups = [[] for _ in centers]
        for x in xs: groups[min(range(len(centers)), key=lambda i: abs(x-centers[i]))].append(x)
        centers = [mean(g) if g else c for g, c in zip(groups, centers)]
    labels = [min(range(len(centers)), key=lambda i: abs(x-centers[i])) for x in xs]
    return labels
