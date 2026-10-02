"""Normalization helpers — stdlib only."""
import re
CUR = {"$": "USD", "rp": "IDR", "€": "EUR", "£": "GBP", "¥": "JPY"}
def parse_price(text: str):
    if not text: return (None, None)
    t = text.strip()
    cur = None
    for sym, code in CUR.items():
        if sym.lower() in t.lower(): cur = code; break
    m = re.search(r"[\d][\d.,]*", t.replace(" ", ""))
    if not m: return (None, cur)
    num = m.group(0)
    if num.count(",") == 1 and num.count(".") == 0: num = num.replace(",", ".")
    num = num.replace(",", "")
    try: return (float(num), cur or "USD")
    except ValueError: return (None, cur)
def clean_text(s: str, limit=2000):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s[:limit]
