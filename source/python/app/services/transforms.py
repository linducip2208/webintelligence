"""Maltego-style transformations over LOCAL data (graph + recon snapshots).

Each transform: {name, input, output, description, cost, rate_limit}.
Execution is read-only against stored data — new observations are NOT
fetched here (use recon/scan for that). Results reference evidence.
"""
import urllib.parse as _up

TRANSFORMS = [
    {"name": "domain_to_ips", "input": "domain", "output": "ip",
     "description": "Domain → resolved IPs (from recon snapshots)",
     "cost": 0, "rate_limit": "60/min"},
    {"name": "ip_to_domains", "input": "ip", "output": "domain",
     "description": "IP → domains sharing it (reverse pivot)",
     "cost": 0, "rate_limit": "60/min"},
    {"name": "domain_to_cert", "input": "domain", "output": "certificate",
     "description": "Domain → TLS certificate summary", "cost": 0, "rate_limit": "60/min"},
    {"name": "cert_to_domains", "input": "certificate", "output": "domain",
     "description": "Certificate → other domains on it (SAN overlap)",
     "cost": 0, "rate_limit": "60/min"},
    {"name": "domain_to_tech", "input": "domain", "output": "technology",
     "description": "Domain → detected technologies", "cost": 0, "rate_limit": "60/min"},
    {"name": "email_to_domain", "input": "email", "output": "domain",
     "description": "Email → its domain", "cost": 0, "rate_limit": "60/min"},
    {"name": "entity_to_related", "input": "entity", "output": "entity",
     "description": "Entity → related entities via graph",
     "cost": 0, "rate_limit": "60/min"},
    {"name": "domain_to_subdomains", "input": "domain", "output": "subdomain",
     "description": "Domain → observed subdomains (from link data + graph)",
     "cost": 0, "rate_limit": "60/min"},
]


def _targets(store, org):
    return [t for t in store.get("targets", []) if t.get("org", 1) == org]


def _norm_domain(v):
    v = str(v or "").lower().strip().lstrip("*.")
    try:
        return _up.urlsplit(v if "://" in v else "http://" + v).hostname or v
    except Exception:
        return v


def run(store, name, value, org=1):
    """Execute a transform. Returns {ok, results:[{value,kind,evidence}], error?}."""
    t = next((x for x in TRANSFORMS if x["name"] == name), None)
    if not t:
        return {"ok": False, "error": f"unknown transform '{name}'"}
    value = str(value or "").strip()
    if not value:
        return {"ok": False, "error": "value required"}
    try:
        if name == "domain_to_ips":
            return _ok(_domain_ips(store, org, value))
        if name == "ip_to_domains":
            return _ok([{"value": d, "kind": "domain", "evidence": "shared-ip"}
                        for d in _ip_domains(store, org, value)])
        if name == "domain_to_cert":
            return _ok(_domain_cert(store, org, value))
        if name == "cert_to_domains":
            return _ok([{"value": d, "kind": "domain", "evidence": "shared-cert"}
                        for d in _cert_domains(store, org, value)])
        if name == "domain_to_tech":
            return _ok([{"value": x, "kind": "technology", "evidence": "recon"}
                        for x in _domain_tech(store, org, value)])
        if name == "email_to_domain":
            parts = value.split("@")
            if len(parts) != 2 or not parts[1]:
                return {"ok": False, "error": "invalid email"}
            return _ok([{"value": parts[1].lower(), "kind": "domain",
                         "evidence": "email-domain"}])
        if name == "entity_to_related":
            return _ok(_entity_related(store, org, value))
        if name == "domain_to_subdomains":
            return _ok([{"value": s, "kind": "subdomain", "evidence": src}
                        for s, src in _subdomains(store, org, value)])
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    return {"ok": False, "error": "unhandled transform"}


def _ok(results):
    seen, out = set(), []
    for r in results:
        if r["value"] not in seen:
            seen.add(r["value"])
            out.append(r)
    return {"ok": True, "results": out[:100], "count": len(out)}


def _recon_of(store, org, domain):
    for t in _targets(store, org):
        if _norm_domain(t.get("domain", "")) != domain:
            continue
        r = t.get("recon") or {}
        if r.get("ok") or r.get("dns"):
            return r, t
    return {}, None


def _domain_ips(store, org, domain):
    domain = _norm_domain(domain)
    r, t = _recon_of(store, org, domain)
    ips = (r.get("dns") or {}).get("ips", []) or []
    return [{"value": ip, "kind": "ip",
             "evidence": f"target:{t['id']}" if t else "recon"} for ip in ips]


def _ip_domains(store, org, ip):
    out = []
    for t in _targets(store, org):
        ips = ((t.get("recon") or {}).get("dns") or {}).get("ips", []) or []
        if ip in ips:
            out.append(t.get("domain", ""))
    return sorted({d for d in out if d})


def _domain_cert(store, org, domain):
    domain = _norm_domain(domain)
    r, t = _recon_of(store, org, domain)
    tls = r.get("tls") or {}
    if not tls.get("ok"):
        return []
    return [{"value": f"issuer={tls.get('issuer', {})} san={len(tls.get('san', []))}",
             "kind": "certificate", "evidence": f"target:{t['id']}" if t else "recon"}]


def _cert_domains(store, org, cert_key_or_issuer):
    out = []
    for t in _targets(store, org):
        tls = (t.get("recon") or {}).get("tls") or {}
        if not tls.get("ok"):
            continue
        blob = f"{tls.get('issuer', {})} {tls.get('san', [])} {tls.get('cert_key', '')}"
        if cert_key_or_issuer.lower() in blob.lower():
            out.append(t.get("domain", ""))
    return sorted({d for d in out if d})


def _domain_tech(store, org, domain):
    r, _ = _recon_of(store, org, _norm_domain(domain))
    return (r.get("http") or {}).get("tech", []) or []


def _entity_related(store, org, ref):
    try:
        eid = int(ref)
    except (TypeError, ValueError):
        eid = None
    e = None
    if eid is not None:
        e = next((x for x in store.get("entities", []) if x.get("id") == eid), None)
    if e is None:
        key = str(ref).lower()
        e = next((x for x in store.get("entities", [])
                  if str(x.get("domain") or x.get("name") or "").lower() == key), None)
    if e is None:
        return []
    key = (e.get("domain") or e.get("name") or "").lower()
    nodes = [n for n in store.get("nodes", [])
             if str(n.get("key", "")).lower() == key or
             str(n.get("name", "")).lower() == str(e.get("name", "")).lower()]
    ids = {n["id"] for n in nodes}
    out = []
    for edge in store.get("edges", []):
        other = edge.get("dst") if edge.get("src") in ids else (
            edge.get("src") if edge.get("dst") in ids else None)
        if other is None:
            continue
        n = next((x for x in nodes if x.get("id") == other),
                 next((x for x in store.get("nodes", []) if x.get("id") == other), None))
        if n:
            out.append({"value": n.get("name") or n.get("key"), "kind": n.get("kind", "entity"),
                        "evidence": f"{edge.get('rel')} (conf {edge.get('confidence')})"})
    return out


def _subdomains(store, org, domain):
    domain = _norm_domain(domain)
    found = {}
    for t in _targets(store, org):
        for src in [t.get("domain", "")] + list(
                ((t.get("recon") or {}).get("http") or {}).get("link_domains", []) or []):
            s = _norm_domain(src)
            if s and s != domain and (s.endswith("." + domain)):
                found[s] = f"target:{t.get('id')}"
    for n in store.get("nodes", []):
        s = _norm_domain(n.get("key", "") or "")
        if s and s != domain and s.endswith("." + domain):
            found[s] = f"node:{n.get('id')}"
    return sorted(found.items())
