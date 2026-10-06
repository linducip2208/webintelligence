"""Opportunity/anomaly detectors on real histories — stdlib."""
import datetime as _dtm
import time
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


def _day(ts):
    try:
        import datetime as _dt
        if isinstance(ts, (int, float)) and ts:
            return _dt.datetime.utcfromtimestamp(float(ts)).strftime("%Y-%m-%d")
        s = str(ts or "")
        return s[:10] if len(s) >= 10 and s[4] == "-" else ""
    except Exception:
        return ""


def build(store: dict, org: int = 1, now: float = None):
    """Meaningful, actionable opportunities. Every item: type/title/why/
    evidence/confidence/action/severity. Real data only — empty when calm."""
    now = now or time.time()
    out = []

    def add(o):
        o.setdefault("confidence", 0.7)
        out.append(o)

    # 1. price anomalies (existing detector, now with why/action)
    by_p = {}
    for p in store.get("prices", []):
        by_p.setdefault(p.get("product_id"), []).append(p)
    for pid, pts in by_p.items():
        for a in price_anomaly([x["price"] for x in pts]):
            add({"type": "PRICE_ANOMALY", "severity": "medium",
                 "title": f"Price anomaly on target {pid}: {a['price']} (z={a['z']})",
                 "why": "Price moved ≥3σ from its own history — possible repricing, sale, or data error.",
                 "evidence": [{"job_id": (pts[a["index"]].get("job_id") or "")[:8]}],
                 "confidence": 0.75, "action": "Open target prices and verify against the live page.",
                 "ref": {"target": pid}})
    # 2. certificates expiring ≤30d (from recon snapshots)
    for t in store.get("targets", []):
        if t.get("org", 1) != org:
            continue
        na = ((t.get("recon") or {}).get("tls") or {}).get("not_after", "")
        try:
            import datetime as _dt
            exp = _dt.datetime.fromisoformat(str(na).replace("Z", "+00:00")).timestamp() \
                if na else 0
        except Exception:
            exp = 0
        if exp and 0 < exp - now <= 30 * 86400:
            days = int((exp - now) // 86400)
            add({"type": "CERT_EXPIRING", "severity": "high" if days <= 7 else "medium",
                 "title": f"Certificate for {t.get('domain')} expires in {days}d",
                 "why": "Expiring certificates cause outages and break monitoring trust.",
                 "evidence": [{"target": t.get("id")}],
                 "confidence": 0.95, "action": "Renew the certificate, then re-scan.",
                 "ref": {"target": t.get("id")}})
    # 3. open high/critical findings
    for f in store.get("findings", []):
        if f.get("org", 1) != org or f.get("status") in ("RESOLVED", "FALSE_POSITIVE"):
            continue
        if str(f.get("severity", "")).lower() in ("high", "critical"):
            add({"type": "HIGH_FINDING", "severity": str(f.get("severity")).lower(),
                 "title": f"Open {f.get('severity')} finding: {(f.get('title') or '')[:100]}",
                 "why": "Unresolved severe findings need analyst triage.",
                 "evidence": [{"finding": f.get("id")}],
                 "confidence": 0.9, "action": "Open the finding, confirm or resolve it.",
                 "ref": {"finding": f.get("id")}})
    # 4. unresolved critical alerts
    for a in store.get("alerts", []):
        if a.get("resolved") or str(a.get("severity", "")).lower() != "critical":
            continue
        add({"type": "CRITICAL_ALERT", "severity": "critical",
             "title": f"Critical alert unacknowledged: {(a.get('message') or '')[:100]}",
             "why": "Critical alerts should be acknowledged quickly (SLA).",
             "evidence": [{"alert": a.get("id")}],
             "confidence": 0.9, "action": "Acknowledge or resolve the alert.",
             "ref": {"alert": a.get("id")}})
    # 5. fresh targets that just started producing (onboarding wins)
    for t in store.get("targets", []):
        if t.get("org", 1) != org:
            continue
        created = _day(t.get("created_at"))
        today = _day(now)
        if created and today and abs((_dtm.datetime.strptime(today, "%Y-%m-%d") -
                                      _dtm.datetime.strptime(created, "%Y-%m-%d")).days) <= 7:
            jobs_ok = sum(1 for j in store.get("jobs", [])
                          if j.get("target_id") == t.get("id") and j.get("status") == "success")
            if jobs_ok:
                add({"type": "NEW_ASSET_ONLINE", "severity": "info",
                     "title": f"New target producing intel: {t.get('domain')}",
                     "why": "Recently added target already yields successful collections.",
                     "evidence": [{"target": t.get("id")}],
                     "confidence": 0.8,
                     "action": "Review its recon, attach it to a watchlist or case.",
                     "ref": {"target": t.get("id")}})
    # 6. stale targets (no success in 30d)
    for t in store.get("targets", []):
        if t.get("org", 1) != org:
            continue
        jobs = [j for j in store.get("jobs", []) if j.get("target_id") == t.get("id")]
        if jobs and not any(j.get("status") == "success" for j in jobs[-5:]):
            add({"type": "STALE_TARGET", "severity": "low",
                 "title": f"No successful collection lately: {t.get('domain')}",
                 "why": "Monitoring blind spot — recent jobs all failed or stalled.",
                 "evidence": [{"target": t.get("id")}],
                 "confidence": 0.7, "action": "Test the target, then re-run a scan.",
                 "ref": {"target": t.get("id")}})
    sev_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    out.sort(key=lambda o: (sev_rank.get(o.get("severity", "info"), 5), o.get("type", "")))
    return out
