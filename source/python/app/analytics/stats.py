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
def percentile(xs, p):
    if not xs: return None
    s = sorted(xs); k = (len(s) - 1) * min(max(p, 0), 100) / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 4)
def distribution(xs, bins=5):
    if not xs: return []
    lo, hi = min(xs), max(xs)
    if hi == lo: return [{"range": [lo, hi], "count": len(xs)}]
    w = (hi - lo) / bins
    out = [{"range": [round(lo + i * w, 4), round(lo + (i + 1) * w, 4)], "count": 0} for i in range(bins)]
    for x in xs:
        i = min(int((x - lo) / w), bins - 1)
        out[i]["count"] += 1
    return out
def cagr(first, last, periods):
    if not first or not periods or first <= 0 or last <= 0: return None
    return round((last / first) ** (1 / periods) - 1, 4)
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
