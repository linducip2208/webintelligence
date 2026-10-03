"""Alert lifecycle helpers: SLA deadlines, maintenance suppression, incidents."""
import time

SLA_SECONDS = {"critical": 3600, "high": 4 * 3600, "medium": 24 * 3600,
               "low": 72 * 3600, "info": 72 * 3600}


def sla_due(severity: str, now=None):
    return (now or time.time()) + SLA_SECONDS.get((severity or "info").lower(), 72 * 3600)


def suppressed(windows: list, rule: str, org: int, now=None):
    now = now or time.time()
    for w in windows:
        if not w.get("enabled", True) or w.get("org", 1) != org:
            continue
        if w.get("starts_at", 0) <= now <= w.get("ends_at", 0):
            rules = w.get("suppress_rules", [])
            if not rules or rule in rules:
                return w
    return None


def incidents(alerts: list, now=None):
    now = now or time.time()
    open_a = [a for a in alerts if not a.get("resolved")]
    groups = {}
    for a in open_a:
        k = (a.get("rule"), a.get("project_id", 0))
        groups.setdefault(k, []).append(a)
    sev_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
    out = []
    for (rule, pid), items in groups.items():
        sevs = [str(i.get("severity", "info")).lower() for i in items]
        top = max(sevs, key=lambda s: sev_rank.get(s, 0))
        breached = sum(1 for i in items if i.get("sla_due") and i["sla_due"] < now and not i.get("acked"))
        out.append({"rule": rule, "project_id": pid, "count": len(items),
                    "severity": top, "sla_breached": breached,
                    "oldest": min((i.get("at", 0) or 0) for i in items),
                    "sample": items[0].get("message", "")[:200]})
    return sorted(out, key=lambda g: (-sev_rank.get(g["severity"], 0), -g["count"]))
