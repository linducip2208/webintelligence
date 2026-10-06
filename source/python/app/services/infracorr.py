"""Infrastructure correlation — candidate findings, never silent merges.

Groups targets by shared infrastructure signals (IP, certificate, content,
technology) and emits OPEN findings an analyst can CONFIRM or mark
FALSE_POSITIVE. Every candidate carries confidence, reason, and evidence.
Idempotent: an identical open candidate is never duplicated.
"""
import hashlib

SIGNALS = (
    ("SHARES_IP", 0.7, "same resolved IP address"),
    ("SHARES_CERTIFICATE", 0.8, "same TLS certificate"),
    ("SHARES_TECHNOLOGY", 0.6, "same technology stack (2+ shared)"),
    ("SHARES_CONTENT", 0.75, "identical page content hash"),
)


def _snapshots(store, org):
    """Latest recon snapshot per target: {target_id: recon}."""
    snaps = {}
    for t in store.get("targets", []):
        if t.get("org", 1) != org:
            continue
        r = t.get("recon") or {}
        if r.get("ok") or r.get("dns") or r.get("tls") or r.get("http"):
            snaps[t["id"]] = r
    return snaps


def _sig_key(signal, members):
    return hashlib.sha256(
        (signal + ":" + ",".join(str(m) for m in sorted(members))).encode()
    ).hexdigest()[:24]


def correlate(store, org=1):
    """Return candidate finding dicts (caller persists). Pure function."""
    snaps = _snapshots(store, org)
    groups = {}  # (signal, value) -> set(target_id)
    for tid, r in snaps.items():
        for ip in (r.get("dns") or {}).get("ips", []) or []:
            groups.setdefault(("SHARES_IP", ip), set()).add(tid)
        ck = (r.get("tls") or {}).get("cert_key")
        if (r.get("tls") or {}).get("ok") and ck:
            groups.setdefault(("SHARES_CERTIFICATE", ck), set()).add(tid)
        tech = tuple(sorted((r.get("http") or {}).get("tech", []) or []))
        if len(tech) >= 2:
            groups.setdefault(("SHARES_TECHNOLOGY", "|".join(tech)), set()).add(tid)
        ch = (r.get("http") or {}).get("content_hash")
        if ch:
            groups.setdefault(("SHARES_CONTENT", ch), set()).add(tid)
    cands = []
    for (signal, value), members in groups.items():
        if len(members) < 2:
            continue
        conf = next(c for s, c, _ in SIGNALS if s == signal)
        reason = next(d for s, _, d in SIGNALS if s == signal)
        cands.append({"signal": signal, "confidence": conf, "reason": reason,
                      "value": value if signal != "SHARES_CONTENT" else value[:16] + "…",
                      "members": sorted(members), "key": _sig_key(signal, members)})
    return sorted(cands, key=lambda c: -c["confidence"])


def materialize(store, org=1):
    """Create OPEN candidate findings for new correlations. Returns created."""
    created = []
    existing = {f.get("title", "") for f in store.get("findings", [])
                if f.get("org", 1) == org and f.get("status") == "OPEN"}
    nxt = max([f.get("id", 0) for f in store.get("findings", [])] + [0])
    for c in correlate(store, org):
        names = []
        for tid in c["members"]:
            t = next((x for x in store.get("targets", []) if x.get("id") == tid), None)
            names.append(t.get("domain", f"target-{tid}") if t else f"target-{tid}")
        title = f"[{c['signal']}] {', '.join(names[:4])}" + ("…" if len(names) > 4 else "")
        if title in existing:
            continue
        nxt += 1
        created.append({
            "id": nxt, "org": org, "kind": "infra-correlation", "title": title,
            "body": f"Candidate {c['signal']}: {c['reason']} "
                    f"(value {c['value']}). Confidence {c['confidence']}. "
                    "Confirm after manual review; mark FALSE_POSITIVE if unrelated.",
            "confidence": c["confidence"], "entities": list(c["members"]),
            "evidence_ids": [], "severity": "medium", "status": "OPEN",
            "priority": "medium", "resolved_at": 0.0,
            "correlation_key": c["key"], "correlation_signal": c["signal"]})
    for f in created:
        store.get("findings", []).append(f)
    return created
