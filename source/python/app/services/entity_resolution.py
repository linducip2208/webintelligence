"""Entity resolution — stdlib only."""
import re, difflib
def norm(s: str) -> str: return re.sub(r"[^a-z0-9]+", "", (s or "").lower())
def score(a: dict, b: dict) -> float:
    if a.get("domain") and a.get("domain") == b.get("domain") and a.get("domain"): return 0.99
    for k in ("gtin", "sku", "mpn"):
        if a.get(k) and a.get(k) == b.get(k): return 0.98
    na, nb = norm(a.get("name","")), norm(b.get("name",""))
    if na and na == nb: return 0.95
    if na and nb: return round(difflib.SequenceMatcher(None, na, nb).ratio(), 3)
    return 0.0
def decide(s: float) -> str:
    if s >= 0.87: return "LINK"
    if s >= 0.70: return "REVIEW"
    return "NEW"
