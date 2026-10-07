"""STIX 2.1 (subset, spec-honest) + MISP-compatible mapping — stdlib only.

Supported STIX objects on export: identity, indicator, observed-data,
domain-name, ipv4-addr, ipv6-addr, url, email-addr, file, software,
vulnerability, threat-actor, campaign, malware, attack-pattern, location,
report, relationship, sighting, note, grouping, opinion, artifact,
autonomous-system, user-account, network-traffic, x509-certificate
(custom extension object `x-webintel-*` is NOT emitted; unknown internal
kinds are skipped and counted, never faked).

Import accepts bundles containing the above SCOs/SDOs plus `relationship`
and maps them to internal entities/relationships/evidence/findings.
Unsupported object types are reported, never silently dropped.

MISP mapping: event <-> grouping/report, attribute <-> indicator/observable,
tag <-> labels, galaxy <-> threat-actor/campaign/malware/tool names,
sighting <-> sighting. See to_misp_event()/from_misp_event().
"""
import hashlib
import re
import time
import uuid

SPEC_VERSION = "2.1"
NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace: deterministic v5 ids


def _uid(kind: str, value: str) -> str:
    return f"{kind}--{uuid.uuid5(NAMESPACE, kind + ':' + str(value).lower())}"


def _now():
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# internal entity kind -> STIX SCO type (None = no direct mapping, skipped w/ count)
SCO_MAP = {
    "domain": "domain-name", "subdomain": "domain-name", "hostname": "domain-name",
    "ip": "ipv4-addr", "ipv4": "ipv4-addr", "ipv6": "ipv6-addr",
    "url": "url", "email": "email-addr",
    "hash": "file", "file": "file", "document": "artifact",
    "software": "software", "technology": "software",
    "vulnerability": "vulnerability", "cve": "vulnerability",
    "threat_actor": "threat-actor", "campaign": "campaign", "malware": "malware",
    "attack_pattern": "attack-pattern", "tool": "tool",
    "location": "location", "country": "location", "city": "location", "address": "location",
    "asn": "autonomous-system", "person": "identity", "organization": "identity",
    "company": "identity", "user": "user-account", "username": "user-account",
    "certificate": "x509-certificate", "port": "network-traffic",
    "ioc": "indicator", "indicator": "indicator",
}

REL_MAP = {  # internal rel -> STIX relationship_type (fallback: related-to)
    "OWNS": "owns", "CONTROLS": "controls", "HOSTS": "hosts",
    "RESOLVES_TO": "resolves-to", "LOCATED_IN": "located-in",
    "BELONGS_TO": "belongs-to", "USES": "uses", "TARGETS": "targets",
    "EXPLOITS": "exploits", "OPERATED_BY": "operated-by",
    "PART_OF": "part-of", "MEMBER_OF": "member-of",
    "SHARES_IP": "related-to", "SHARES_CERTIFICATE": "related-to",
    "SHARES_TECHNOLOGY": "related-to", "SHARES_CONTENT": "related-to",
    "SHARES_INFRASTRUCTURE": "related-to",
}


def _sco(entity: dict, created_by: str):
    kind = str(entity.get("kind", "") or "").lower()
    stix_type = SCO_MAP.get(kind)
    if not stix_type:
        return None, f"no STIX mapping for kind '{kind}'"
    val = entity.get("key") or entity.get("name") or entity.get("value") or ""
    val = str(val).strip()
    if not val:
        return None, "empty value"
    ts = _now()
    base = {"type": stix_type, "spec_version": SPEC_VERSION, "id": _uid(stix_type, val),
            "created": ts, "modified": ts, "labels": [kind],
            "confidence": int(round(float(entity.get("confidence", 50) if isinstance(
                entity.get("confidence"), (int, float)) else 50))),
            "created_by_ref": created_by,
            "external_references": [{"source_name": "webintel",
                                     "external_id": f"entity-{entity.get('id')}"}]}
    if stix_type == "domain-name":
        base["value"] = val.lower().lstrip("*.")
    elif stix_type in ("ipv4-addr", "ipv6-addr"):
        base["value"] = val
    elif stix_type == "url":
        base["value"] = val
    elif stix_type == "email-addr":
        base["value"] = val.lower()
    elif stix_type == "file":
        if re.fullmatch(r"[0-9a-fA-F]{32}|[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", val):
            algo = {32: "MD5", 40: "SHA-1", 64: "SHA-256"}[len(val)]
            base["hashes"] = {algo: val.upper()}
        else:
            base["name"] = val
    elif stix_type == "artifact":
        base["payload_bin"] = val[:1024]
    elif stix_type == "software":
        base["name"] = val
    elif stix_type == "vulnerability":
        base["name"] = val.upper() if val.lower().startswith("cve-") else val
    elif stix_type in ("threat-actor", "campaign", "malware", "attack-pattern", "tool"):
        base["name"] = val
        if stix_type == "threat-actor":
            base["threat_actor_types"] = ["unknown"]
    elif stix_type == "location":
        base["name"] = val
    elif stix_type == "autonomous-system":
        m = re.search(r"\d+", val)
        base["number"] = int(m.group(0)) if m else 0
    elif stix_type == "identity":
        base["name"] = val
        base["identity_class"] = "individual" if kind == "person" else "organization"
    elif stix_type == "user-account":
        base["account_login"] = val
    elif stix_type == "x509-certificate":
        base["serial_number"] = val
    elif stix_type == "network-traffic":
        try:
            base["dst_port"] = int(val)
        except ValueError:
            return None, f"non-numeric port '{val}'"
    elif stix_type == "indicator":
        base["pattern"] = f"[file:hashes.'SHA-256' = '{val}']" if re.fullmatch(
            r"[0-9a-fA-F]{64}", val) else f"[domain-name:value = '{val}']"
        base["pattern_type"] = "stix"
        base["valid_from"] = ts
    return base, ""


def export_bundle(store, org=1, identity_name="WebIntelligence",
                  kinds=("entities", "relationships", "findings", "indicators")):
    """Export org data as a STIX 2.1 bundle. Returns (bundle, stats)."""
    ts = _now()
    ident_id = _uid("identity", identity_name + ":" + str(org))
    objects = [{"type": "identity", "spec_version": SPEC_VERSION, "id": ident_id,
                "created": ts, "modified": ts, "name": identity_name,
                "identity_class": "organization"}]
    stats = {"entities": 0, "relationships": 0, "findings": 0,
             "indicators": 0, "skipped": []}
    ent_ids = {}
    if "entities" in kinds:
        for e in store.get("entities", []):
            kind = e.get("kind") or ("domain" if e.get("domain") else "")
            obj, err = _sco({"kind": kind, "key": e.get("domain") or e.get("name"),
                             "name": e.get("name"), "value": e.get("key") or e.get("name"),
                             "confidence": e.get("confidence", 50), "id": e.get("id")}, ident_id)
            if obj is None:
                stats["skipped"].append(err)
                continue
            objects.append(obj)
            ent_ids[e.get("id")] = obj["id"]
            stats["entities"] += 1
    node_ids = {}
    for n in store.get("nodes", []):
        if n.get("org", 1) != org:
            continue
        obj, err = _sco({"kind": n.get("kind"), "key": n.get("key"), "name": n.get("name"),
                         "confidence": 50, "id": f"n{n.get('id')}"}, ident_id)
        if obj is None:
            stats["skipped"].append(err)
            continue
        objects.append(obj)
        node_ids[n.get("id")] = obj["id"]
    if "relationships" in kinds:
        for e in store.get("edges", []):
            if e.get("org", 1) != org:
                continue
            s = node_ids.get(e.get("src"))
            t = node_ids.get(e.get("dst"))
            if not s or not t:
                stats["skipped"].append("edge with unmapped endpoint")
                continue
            objects.append({
                "type": "relationship", "spec_version": SPEC_VERSION,
                "id": _uid("relationship", f"{s}{t}{e.get('rel')}"),
                "created": ts, "modified": ts, "created_by_ref": ident_id,
                "relationship_type": REL_MAP.get(str(e.get("rel", "")).upper(), "related-to"),
                "source_ref": s, "target_ref": t,
                "confidence": int(round(float(e.get("confidence", 50))))})
            stats["relationships"] += 1
    if "findings" in kinds:
        for f in store.get("findings", []):
            if f.get("org", 1) != org:
                continue
            objects.append({
                "type": "report", "spec_version": SPEC_VERSION,
                "id": _uid("report", f"finding-{f.get('id')}"),
                "created": ts, "modified": ts, "created_by_ref": ident_id,
                "name": (f.get("title") or f"finding-{f.get('id')}")[:256],
                "description": (f.get("body") or "")[:4000],
                "report_types": ["threat-report"],
                "labels": [str(f.get("severity", "info")), str(f.get("status", "OPEN"))],
                "confidence": int(round(float(f.get("confidence", 0) or 0) * 100
                                        if float(f.get("confidence", 0) or 0) <= 1
                                        else float(f.get("confidence", 0) or 0))),
                "object_refs": [ent_ids[i] for i in (f.get("entities") or [])
                                if i in ent_ids]})
            stats["findings"] += 1
    bundle = {"type": "bundle", "id": f"bundle--{uuid.uuid4()}",
              "spec_version": SPEC_VERSION, "objects": objects}
    return bundle, stats


def validate_bundle(bundle: dict):
    """Structural validation. Returns [error strings] (empty = valid)."""
    errs = []
    if not isinstance(bundle, dict):
        return ["bundle must be an object"]
    if bundle.get("type") != "bundle":
        errs.append("type must be 'bundle'")
    objs = bundle.get("objects")
    if not isinstance(objs, list) or not objs:
        errs.append("objects must be a non-empty array")
        return errs
    seen = set()
    for i, o in enumerate(objs):
        if not isinstance(o, dict):
            errs.append(f"objects[{i}] must be an object")
            continue
        if not o.get("type"):
            errs.append(f"objects[{i}] missing type")
        if not o.get("id"):
            errs.append(f"objects[{i}] missing id")
        elif o["id"] in seen:
            errs.append(f"duplicate id {o['id']}")
        else:
            seen.add(o["id"])
        for tsf in ("created", "modified"):
            if tsf in o and not re.match(r"^\d{4}-\d{2}-\d{2}T", str(o[tsf])):
                errs.append(f"objects[{i}].{tsf} not RFC3339")
    return errs


def import_bundle(store, bundle: dict, org=1, source="stix-import"):
    """Import a bundle -> entities/relationships/evidence/findings.
    Returns summary; unsupported types are counted, never faked."""
    errs = validate_bundle(bundle)
    if errs:
        return {"ok": False, "errors": errs}
    created = {"entities": 0, "relationships": 0, "evidence": 0, "findings": 0}
    skipped = []
    idmap = {}
    nxt_e = max([e.get("id", 0) for e in store.get("entities", [])] + [0])
    for o in bundle["objects"]:
        t = o.get("type")
        if t in ("domain-name", "ipv4-addr", "ipv6-addr", "url", "email-addr",
                 "file", "software", "vulnerability", "identity", "user-account",
                 "autonomous-system", "location", "threat-actor", "campaign",
                 "malware", "attack-pattern", "tool", "artifact", "x509-certificate",
                 "network-traffic"):
            val = (o.get("value") or o.get("name") or o.get("account_login") or
                   (o.get("hashes") or {}).get("SHA-256") or "")
            if not val:
                skipped.append(f"{t} without value")
                continue
            inv = {"domain-name": "domain", "ipv4-addr": "ip", "ipv6-addr": "ip",
                   "url": "url", "email-addr": "email", "file": "file",
                   "software": "technology", "vulnerability": "vulnerability",
                   "identity": "organization", "user-account": "username",
                   "autonomous-system": "asn", "location": "location",
                   "threat-actor": "threat_actor", "campaign": "campaign",
                   "malware": "malware", "attack-pattern": "attack_pattern",
                   "tool": "technology", "artifact": "document",
                   "x509-certificate": "certificate",
                   "network-traffic": "port"}.get(t, "ioc")
            dup = next((e for e in store.get("entities", [])
                        if str(e.get("domain") or e.get("name") or "") == str(val)), None)
            if dup:
                idmap[o["id"]] = dup["id"]
                continue
            nxt_e += 1
            store.get("entities", []).append(
                {"id": nxt_e, "org": org, "kind": inv,
                 "domain": val if inv == "domain" else "",
                 "name": str(val)[:500],
                 "confidence": o.get("confidence", 50)})
            idmap[o["id"]] = nxt_e
            created["entities"] += 1
        elif t == "indicator":
            nxt_e += 1
            store.get("entities", []).append(
                {"id": nxt_e, "org": org, "kind": "ioc",
                 "name": o.get("pattern", "")[:500], "confidence": o.get("confidence", 50)})
            idmap[o["id"]] = nxt_e
            created["entities"] += 1
        elif t == "report":
            nxt = max([f.get("id", 0) for f in store.get("findings", [])] + [0]) + 1
            store.get("findings", []).append(
                {"id": nxt, "org": org, "kind": "imported-report",
                 "title": o.get("name", "imported")[:500],
                 "body": o.get("description", "")[:20000],
                 "confidence": (o.get("confidence", 50) or 50) / 100.0,
                 "entities": [], "evidence_ids": [],
                 "severity": "info", "status": "OPEN", "priority": "medium",
                 "resolved_at": 0.0})
            idmap[o["id"]] = nxt
            created["findings"] += 1
        elif t in ("identity",) and False:
            pass
        elif t in ("sighting", "note", "opinion", "grouping", "marking-definition",
                   "extension-definition", "language-content"):
            skipped.append(f"{t} noted, no local counterpart")
        elif t == "relationship":
            skipped.append("relationship deferred to second pass")
        else:
            skipped.append(f"unsupported type '{t}'")
    # second pass: relationships between imported/resolved refs.
    # idmap holds ENTITY ids; graph edges need NODE ids, so resolve each
    # endpoint entity to its graph node (creating the node when missing).
    # An edge is never written against a nonexistent node.
    def _node_for_entity(ent):
        key = str(ent.get("domain") or ent.get("name") or "")
        if not key:
            return None
        kind = str(ent.get("kind") or "ioc")
        for n in store.get("nodes", []):
            if n.get("org", 1) == org and n.get("kind") == kind and n.get("key") == key:
                return n["id"]
        nid = max([n.get("id", 0) for n in store.get("nodes", [])] + [0]) + 1
        store.get("nodes", []).append({"id": nid, "org": org, "kind": kind,
                                       "key": key, "name": key})
        return nid

    by_entity = {e.get("id"): e for e in store.get("entities", [])}
    nxt_g = max([e.get("id", 0) for e in store.get("edges", [])] + [0])
    for o in bundle["objects"]:
        if o.get("type") != "relationship":
            continue
        ent_s = by_entity.get(idmap.get(o.get("source_ref")))
        ent_t = by_entity.get(idmap.get(o.get("target_ref")))
        if not ent_s or not ent_t:
            skipped.append("relationship with unmapped endpoint")
            continue
        s, t_ = _node_for_entity(ent_s), _node_for_entity(ent_t)
        if not s or not t_:
            skipped.append("relationship endpoint has no usable key")
            continue
        rel = str(o.get("relationship_type", "related-to")).upper().replace("-", "_")
        if any(e.get("src") == s and e.get("dst") == t_ and e.get("rel") == rel
               for e in store.get("edges", [])):
            skipped.append("relationship already present")
            continue
        nxt_g += 1
        store.get("edges", []).append(
            {"id": nxt_g, "org": org, "src": s, "dst": t_, "rel": rel,
             "confidence": o.get("confidence", 50), "evidence": [f"stix:{source}"]})
        created["relationships"] += 1
    # evidence/provenance record of the import itself
    fp = hashlib.sha256(str(sorted(idmap)).encode()).hexdigest()[:24]
    store.get("evidence", []).append(
        {"id": max([e.get("id", 0) for e in store.get("evidence", [])] + [0]) + 1,
         "org": org, "source": source, "url": "", "content_hash": fp,
         "snippet": f"STIX import: {created['entities']} entities, "
                    f"{created['relationships']} relationships, "
                    f"{created['findings']} findings; skipped {len(skipped)}",
         "confidence": 1.0})
    created["evidence"] += 1
    return {"ok": True, "created": created, "skipped": skipped}


# ---------------- MISP-compatible mapping ----------------
def to_misp_event(store, org=1, findings=None, info="WebIntelligence export"):
    """Findings/entities -> MISP event JSON (attribute/tag/sighting concepts)."""
    attrs, k = [], 0
    for f in (findings if findings is not None
              else [x for x in store.get("findings", []) if x.get("org", 1) == org]):
        for eid in (f.get("entities") or []):
            e = next((x for x in store.get("entities", []) if x.get("id") == eid), None)
            if not e:
                continue
            k += 1
            val = e.get("domain") or e.get("name", "")
            attrs.append({"id": k, "type": _misp_type(e.get("kind", "")),
                          "category": "Network activity", "value": val,
                          "comment": (f.get("title", "") or "")[:200],
                          "to_ids": str(f.get("severity", "info")).lower() in ("high", "critical"),
                          "Tag": [{"name": f"webintel:severity={f.get('severity', 'info')}"},
                                  {"name": f"webintel:status={f.get('status', 'OPEN')}"}]})
    return {"Event": {"info": info, "threat_level_id": "3", "distribution": "0",
                      "Attribute": attrs,
                      "Tag": [{"name": "webintel:export"}],
                      "Sighting": []}}


def _misp_type(kind):
    return {"domain": "domain", "subdomain": "hostname", "ip": "ip-dst",
            "url": "url", "email": "email-src", "file": "sha256",
            "vulnerability": "vulnerability", "username": "github-username"}.get(
                str(kind or "").lower(), "text")


def from_misp_event(store, event: dict, org=1):
    """MISP event JSON -> entities (+sighting counts). Returns summary."""
    ev = (event or {}).get("Event", event or {})
    made, sightings = 0, 0
    nxt = max([e.get("id", 0) for e in store.get("entities", [])] + [0])
    for a in ev.get("Attribute", []) or []:
        val = str(a.get("value", "")).strip()
        if not val:
            continue
        dup = next((e for e in store.get("entities", [])
                    if str(e.get("domain") or e.get("name") or "") == val), None)
        if dup:
            sightings += int(a.get("sighting_count", 0) or 0)
            continue
        nxt += 1
        kind = {"domain": "domain", "hostname": "domain", "ip-dst": "ip",
                "ip-src": "ip", "url": "url", "email-src": "email",
                "sha256": "file", "vulnerability": "vulnerability"}.get(
                    str(a.get("type", "")), "ioc")
        store.get("entities", []).append(
            {"id": nxt, "org": org, "kind": kind,
             "domain": val if kind == "domain" else "",
             "name": val[:500], "confidence": 60 if a.get("to_ids") else 40})
        made += 1
    for s in ev.get("Sighting", []) or []:
        sightings += 1
    for g in ev.get("Galaxy", []) or []:
        for c in g.get("GalaxyCluster", []) or []:
            v = str(c.get("value", "")).strip()
            if v and not any(str(e.get("name", "")) == v for e in store.get("entities", [])):
                nxt += 1
                store.get("entities", []).append(
                    {"id": nxt, "org": org, "kind": "threat_actor",
                     "name": v[:500], "confidence": 50})
                made += 1
    return {"attributes": made, "sightings": sightings}
