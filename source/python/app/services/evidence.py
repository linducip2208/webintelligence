"""Evidence + claim verification + contradictions — stdlib only."""
def make_evidence(source, url, content_hash, snippet="", selector="", method="", confidence=1.0):
    return {"source": source, "url": url, "content_hash": content_hash, "snippet": snippet[:500],
            "selector": selector, "method": method, "confidence": confidence}
def verify(value, evidence_values: list):
    """evidence_values: [{value, source, reliability(0-1), at}]."""
    if not evidence_values: return {"status": "UNVERIFIED", "confidence": 0.0, "reasons": ["no evidence"]}
    agree = [e for e in evidence_values if str(e.get("value")) == str(value)]
    if agree and not [e for e in evidence_values if str(e.get("value")) != str(value)]:
        conf = round(sum(e.get("reliability", 0.5) for e in agree) / len(agree), 3)
        return {"status": "VERIFIED", "confidence": conf, "reasons": [f"{len(agree)} sources agree"]}
    if agree:
        return {"status": "CONFLICTED", "confidence": 0.5,
                "reasons": ["sources disagree; see contradiction check"]}
    return {"status": "CONFLICTED", "confidence": 0.3, "reasons": ["no source supports claim value"]}
def contradictions(evidence_values: list):
    groups = {}
    for e in evidence_values: groups.setdefault(str(e.get("value")), []).append(e)
    if len(groups) < 2: return None
    ranked = sorted(groups.items(), key=lambda kv: sum(x.get("reliability", 0.5) for x in kv[1]), reverse=True)
    return {"conflict": True, "values": {k: len(v) for k, v in groups.items()},
            "preferred": ranked[0][0], "note": "preferred by reliability weight; not auto-selected as fact"}
