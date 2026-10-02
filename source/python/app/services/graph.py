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
            if at:
                vf, vt = e.get("valid_from"), e.get("valid_to")
                if vf and str(vf) > str(at):
                    continue  # did not exist yet at T
                if vt and str(vt) <= str(at):
                    continue  # already superseded at T
            if rels and e.get("rel") not in rels: continue
            nxt = e["dst"] if e.get("src")==cur else (e["src"] if e.get("dst")==cur else None)
            if nxt is None or nxt in seen: continue
            nd = by_id.get(nxt)
            if kinds and nd and nd.get("kind") not in kinds: continue
            seen.add(nxt); out.append({"edge": e, "node": nd}); frontier.append((nxt, d+1))
    return out
def path(nodes, edges, src_id, dst_id, rels=None, limit=500):
    """BFS shortest path (undirected). Returns node/edge hops or []."""
    adj = {}
    for e in edges:
        if rels and e.get("rel") not in rels: continue
        adj.setdefault(e.get("src"), []).append((e.get("dst"), e))
        adj.setdefault(e.get("dst"), []).append((e.get("src"), e))
    prev, seen, frontier, n = {}, {src_id}, [src_id], 0
    while frontier and n < limit:
        cur = frontier.pop(0); n += 1
        if cur == dst_id: break
        for nxt, e in adj.get(cur, []):
            if nxt not in seen:
                seen.add(nxt); prev[nxt] = (cur, e); frontier.append(nxt)
    if dst_id not in prev and dst_id != src_id: return []
    hops, cur = [], dst_id
    by_id = {x["id"]: x for x in nodes}
    while cur != src_id:
        par, e = prev[cur]
        hops.append({"node": by_id.get(cur), "via": e.get("rel") if e else None})
        cur = par
    hops.append({"node": by_id.get(src_id), "via": None})
    return list(reversed(hops))
