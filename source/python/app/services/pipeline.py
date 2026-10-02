"""End-to-end collection pipeline — stdlib only, DB-agnostic (dicts in/out).

run_job(job, target, last_state) -> bundle with raw/validation/normalized/
changes/alerts/cost records. Wired to STORE/DB by main.py and workers.
"""
import hashlib
import re
import time
import urllib.request

try:  # package context: app.services.pipeline
    from ..core.ssrf import validate_url
except ImportError:  # flat test context: services on sys.path
    from core.ssrf import validate_url
from . import decision as dec
from . import cost as costeng
from . import change as changedet
from . import quality as qual
from . import normalize as norm
from . import targets as tgt

MAX_BODY = 10_000_000


def _trusted():
    import os
    return [x.strip() for x in os.getenv("TRUSTED_EGRESS_CIDRS", "").split(",") if x.strip()]


def fetch_direct(url: str, timeout_s: int = 30, trusted_cidrs: list = None) -> dict:
    validate_url(url, trusted_cidrs if trusted_cidrs is not None else _trusted())
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 WebIntel/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            body = r.read(MAX_BODY + 1)
            ms = (time.time() - t0) * 1000
            return {"ok": True, "http_status": r.status,
                    "content_type": r.headers.get("Content-Type", ""),
                    "url": r.geturl(), "body": body, "latency_ms": round(ms, 2)}
    except Exception as e:
        return {"ok": False, "http_status": 0, "content_type": "",
                "url": url, "body": b"", "latency_ms": round((time.time() - t0) * 1000, 2),
                "error": str(e)[:300]}


def extract_prices(html: bytes):
    try:
        text = html.decode("utf-8", "ignore")
    except Exception:
        return []
    out = []
    for m in re.finditer(r"([$€£¥]|Rp)\s?[\d][\d.,]*", text):
        v, cur = norm.parse_price(m.group(0))
        if v is not None:
            out.append({"price": v, "currency": cur, "raw": m.group(0)[:64]})
    # dedupe, keep top 20
    seen, uniq = set(), []
    for p in out:
        k = (p["price"], p["currency"])
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    return uniq[:20]


def run_job(job: dict, target: dict, last_prices: list, policy: dec.Policy,
            providers: dict, timeout_s: int = 30, trusted_cidrs: list = None) -> dict:
    """Full pipeline for one job. last_prices: previous normalized prices for target."""
    t0 = time.time()
    engine = dec.Engine()
    plan = engine.decide(target, policy, providers)
    strategy = plan["plan"][0] if plan["plan"] else "DIRECT_HTTP"
    if strategy in ("BROWSER", "OWN_PROXY", "BRIGHT_DATA"):
        return {"job_id": job.get("job_id"), "status": "deferred",
                "strategy": strategy, "plan": plan,
                "note": f"{strategy} handled by dedicated worker/collector, not inline"}

    fetched = fetch_direct(job["url"], timeout_s, trusted_cidrs)
    body = fetched["body"]
    h = hashlib.sha256(body).hexdigest() if body else ""
    ok, diag = dec.validate_result(
        fetched["http_status"], fetched["content_type"], len(body),
        ["price"], bool(body), 0.9 if body else 0.0)
    prices = extract_prices(body) if ok else []
    q = qual.score({"price": prices[0]["price"] if prices else None,
                    "url": job["url"]}, ["price", "url"]) if prices else qual.score({}, ["price"])
    prev = last_prices[-1] if last_prices else None
    change_kind = "NEW"
    if prev and prices:
        if abs(prices[0]["price"] - prev["price"]) > 1e-9:
            change_kind = "CHANGED"
        else:
            change_kind = "UNCHANGED"
    alerts = []
    if change_kind == "CHANGED":
        pct = abs(prices[0]["price"] - prev["price"]) / abs(prev["price"]) * 100 if prev["price"] else 0
        alerts.append({"rule": "price_changed", "channel": "inapp",
                       "message": f"Price {prev['price']} -> {prices[0]['price']} "
                                  f"({pct:.1f}%) at {job['url']}"})
    cost = costeng.estimate(strategy)
    prof = tgt.record_attempt(dict(target.get("profile", {})), strategy, ok,
                              fetched["latency_ms"], cost)
    ms = round((time.time() - t0) * 1000, 2)
    return {
        "job_id": job.get("job_id"), "status": "success" if ok else "failed",
        "strategy": strategy, "plan": plan, "http_status": fetched["http_status"],
        "content_hash": h, "content_size": len(body),
        "latency_ms": fetched["latency_ms"], "duration_ms": ms,
        "diagnostics": diag, "quality": q, "prices": prices,
        "change": change_kind, "alerts": alerts, "cost": cost,
        "target_profile": prof,
    }


def ingest_body(job: dict, body: bytes, last_prices: list):
    """Extraction leg for collector-delivered bodies: parse → prices →
    change vs last → alerts. Returns (prices, change_kind, alerts)."""
    prices = extract_prices(body or b"")
    prev = last_prices[-1] if last_prices else None
    change_kind = "NEW"
    if prev and prices:
        change_kind = ("CHANGED" if abs(prices[0]["price"] - prev["price"]) > 1e-9
                       else "UNCHANGED")
    alerts = []
    if change_kind == "CHANGED":
        pct = (abs(prices[0]["price"] - prev["price"]) / abs(prev["price"]) * 100
               if prev["price"] else 0)
        alerts.append({"rule": "price_changed", "channel": "inapp",
                       "message": f"Price {prev['price']} -> {prices[0]['price']} "
                                  f"({pct:.1f}%) at {job.get('url', '')}"})
    return prices, change_kind, alerts
