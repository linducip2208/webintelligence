"""Explainable risk scoring — deterministic, factor-based, no AI magic.

score = min(100, sum of factor points). Every factor carries its points,
reason, and evidence references so analysts can see WHY a score moved.
Weights are documented constants, overridable per call.

Factors (points):
- critical_open_finding: +25 each (cap 50)
- high_open_finding: +15 each (cap 30)
- unresolved_alert: +8 each (cap 24), critical alert +15 (cap 30)
- recent_hostile_change (CHANGED/REMOVED ≤30d): +10 each (cap 20)
- shared_infrastructure (entity linked to 2+ distinct peers): +12 (cap 24)
- failed_collections (recent failures without success): +5 (cap 10)
- credential_evidence (leak/credential evidence linked): +20 (cap 20)
"""
import time

SEV_POINTS = {"critical": 25, "high": 15, "medium": 6, "low": 2, "info": 0}
SEV_CAP = {"critical": 50, "high": 30}
WINDOW_S = 30 * 86400


def _fresh(ts, now=None):
    now = now or time.time()
    try:
        return (now - float(ts or 0)) <= WINDOW_S
    except (TypeError, ValueError):
        return False


def _sev_of(x):
    return str(x.get("severity", "info") or "info").lower()


def _open_findings(store, org, link_key=None, link_id=None):
    out = []
    for f in store.get("findings", []):
        if f.get("org", 1) != org or f.get("status") in ("RESOLVED", "FALSE_POSITIVE"):
            continue
        if link_key is not None and link_id not in (f.get(link_key) or []):
            continue
        out.append(f)
    return out


def _unresolved_alerts(store, org, project_id=None):
    projs = {p.get("id"): p.get("org", 1) for p in store.get("projects", [])}
    out = []
    for a in store.get("alerts", []):
        if a.get("resolved"):
            continue
        if project_id is not None and a.get("project_id") != project_id:
            continue
        owner = projs.get(a.get("project_id"))
        if owner is not None and owner != org:
            continue
        out.append(a)
    return out


def _score_findings(findings):
    pts, factors = 0, []
    by_sev = {}
    for f in findings:
        by_sev.setdefault(_sev_of(f), []).append(f)
    for sev, items in by_sev.items():
        per, cap = SEV_POINTS.get(sev, 0), SEV_CAP.get(sev, 6 * len(items))
        got = min(per * len(items), cap if sev in SEV_CAP else per * len(items))
        if got:
            pts += got
            factors.append({"name": f"{len(items)}x {sev} open finding(s)",
                            "points": got,
                            "why": f"{len(items)} unresolved finding(s) with severity {sev}",
                            "evidence": [{"finding_id": i.get("id"),
                                          "title": (i.get("title") or "")[:120]} for i in items[:5]]})
    return pts, factors


def _score_alerts(alerts):
    pts, factors = 0, []
    crit = [a for a in alerts if _sev_of(a) == "critical"]
    other = [a for a in alerts if _sev_of(a) != "critical"]
    if crit:
        got = min(15 * len(crit), 30)
        pts += got
        factors.append({"name": f"{len(crit)}x critical unresolved alert(s)", "points": got,
                        "why": "critical alerts demand immediate attention",
                        "evidence": [{"alert_id": a.get("id"),
                                      "rule": a.get("rule", "")} for a in crit[:5]]})
    if other:
        got = min(8 * len(other), 24)
        pts += got
        factors.append({"name": f"{len(other)}x unresolved alert(s)", "points": got,
                        "why": "open alert backlog raises exposure",
                        "evidence": [{"alert_id": a.get("id"),
                                      "rule": a.get("rule", "")} for a in other[:5]]})
    return pts, factors


def score_target(store, target_id, org=1, now=None):
    """Explainable risk for one target. Returns score/level/factors/at."""
    now = now or time.time()
    t = next((x for x in store.get("targets", []) if x.get("id") == target_id), None)
    if not t or t.get("org", 1) != org:
        return {"error": "target not found"}
    pts, factors = 0, []
    findings = [f for f in _open_findings(store, org)
                if target_id in (f.get("entities") or []) or
                str(target_id) in [str(e) for e in (f.get("evidence_ids") or [])] or
                f.get("project_id") == t.get("project_id")]
    # findings linked by entity id OR same project (weak link, half weight)
    direct = [f for f in findings if target_id in (f.get("entities") or [])]
    inherited = [f for f in findings if f not in direct]
    for group, w in ((direct, 1.0), (inherited, 0.5)):
        if not group:
            continue
        gp, gf = _score_findings(group)
        gp = int(gp * w)
        if gp:
            pts += gp
            for fac in gf:
                fac = dict(fac)
                fac["points"] = int(fac["points"] * w)
                if w < 1:
                    fac["name"] += " (same project)"
                factors.append(fac)
    ap, af = _score_alerts(_unresolved_alerts(store, org, t.get("project_id")))
    pts += ap
    factors += af
    changes = [c for c in store.get("changes", [])
               if c.get("target_id") == target_id and c.get("kind") in ("CHANGED", "REMOVED")]
    recent = [c for c in changes if _fresh(c.get("at", c.get("observed_at", 0)), now)]
    if recent:
        got = min(10 * len(recent), 20)
        pts += got
        factors.append({"name": f"{len(recent)}x recent hostile change(s)", "points": got,
                        "why": "CHANGED/REMOVED site changes in the last 30 days",
                        "evidence": [{"change_id": c.get("id"), "kind": c.get("kind")} for c in recent[:5]]})
    jobs = [j for j in store.get("jobs", []) if j.get("target_id") == target_id]
    fails = [j for j in jobs if j.get("status") == "failed"]
    oks = [j for j in jobs if j.get("status") == "success"]
    if fails and not oks:
        pts += 5
        factors.append({"name": "collection failing, no success yet", "points": 5,
                        "why": f"{len(fails)} failed job(s), zero successes — blind spot",
                        "evidence": [{"job_id": (j.get("job_id") or "")[:8]} for j in fails[:5]]})
    score = min(100, pts)
    return {"target_id": target_id, "score": score, "level": _level(score),
            "factors": factors, "at": now}


def score_entity(store, entity_id, org=1, now=None):
    """Explainable risk for one entity: findings, relationships, shared infra."""
    now = now or time.time()
    e = next((x for x in store.get("entities", []) if x.get("id") == entity_id), None)
    if not e:
        return {"error": "entity not found"}
    pts, factors = 0, []
    findings = [f for f in _open_findings(store, org)
                if entity_id in (f.get("entities") or [])]
    fp, ff = _score_findings(findings)
    pts += fp
    factors += ff
    key = e.get("domain") or e.get("name", "")
    nodes = [n for n in store.get("nodes", [])
             if key and (n.get("key") == key or n.get("name") == e.get("name"))]
    node_ids = {n["id"] for n in nodes}
    rels = [x for x in store.get("edges", [])
            if x.get("src") in node_ids or x.get("dst") in node_ids]
    peers = {x.get("dst") for x in rels if x.get("src") in node_ids}
    peers |= {x.get("src") for x in rels if x.get("dst") in node_ids}
    peers.discard(None)
    if len(peers) >= 2:
        got = min(12 + 2 * (len(peers) - 2), 24)
        pts += got
        factors.append({"name": f"linked infrastructure ({len(peers)} peers)", "points": got,
                        "why": "entity shares relationships with multiple distinct peers",
                        "evidence": [{"relationship": r.get("rel"),
                                      "confidence": r.get("confidence")} for r in rels[:5]]})
    cred_hits = [x for x in store.get("evidence", [])
                 if key and key.lower() in (x.get("url", "") + x.get("snippet", "")).lower()
                 and any(w in (x.get("snippet", "") + x.get("source", "")).lower()
                         for w in ("leak", "breach", "credential", "password", "expos"))]
    if cred_hits:
        pts += 20
        factors.append({"name": "possible credential/leak exposure", "points": 20,
                        "why": f"{len(cred_hits)} evidence record(s) mention leaks/credentials",
                        "evidence": [{"evidence_id": x.get("id"),
                                      "source": x.get("source", "")} for x in cred_hits[:5]]})
    score = min(100, pts)
    return {"entity_id": entity_id, "score": score, "level": _level(score),
            "factors": factors, "at": now,
            "relationships": len(rels), "linked_findings": len(findings)}


def _level(score):
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    if score > 0:
        return "low"
    return "none"
