"""Knowledge graph ops on dict stores — stdlib only.
Nodes: {id,kind,key,name}. Edges: {id,src,dst,rel,confidence,evidence,valid_from,valid_to}.
History preserved: superseding an edge closes the old one (valid_to) instead of delete.
"""
def add_node(nodes, kind, key, name="", org=1):
    for n in nodes:
        if n.get("org") == org and n.get("kind") == kind and n.get("key") == key:
            return n
    n = {"id": len(nodes) + 1, "org": org, "kind": kind, "key": key, "name": name or key}
    nodes.append(n); return n
def add_edge(edges, src, dst, rel, confidence=1.0, evidence=None, at=None, org=1):
    for e in edges:
        if e.get("org")==org and e.get("src")==src and e.get("dst")==dst and e.get("rel")==rel and not e.get("valid_to"):
            e["valid_to"] = at  # close history, keep truth
    e = {"id": len(edges)+1, "org": org, "src": src, "dst": dst, "rel": rel,
         "confidence": confidence, "evidence": evidence or [], "valid_from": at, "valid_to": None}
    edges.append(e); return e
def traverse(nodes, edges, start_id, depth=2, rels=None, kinds=None, at=None, limit=200):
    seen, out, frontier = {start_id}, [], [(start_id, 0)]
    by_id = {n["id"]: n for n in nodes}
    while frontier and len(out) < limit:
        cur, d = frontier.pop(0)
        if d >= depth: continue
        for e in edges:
            if e.get("valid_to") and at and str(e["valid_to"]) < str(at): continue
            if rels and e.get("rel") not in rels: continue
            nxt = e["dst"] if e.get("src")==cur else (e["src"] if e.get("dst")==cur else None)
            if nxt is None or nxt in seen: continue
            nd = by_id.get(nxt)
            if kinds and nd and nd.get("kind") not in kinds: continue
            seen.add(nxt); out.append({"edge": e, "node": nd}); frontier.append((nxt, d+1))
    return out
