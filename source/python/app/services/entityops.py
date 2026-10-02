"""Entity MERGE/SPLIT/REJECT/REVIEW with history — stdlib. Never silent."""
def merge(entities: list, history: list, keep_id: int, drop_id: int, actor="system"):
    keep = next((e for e in entities if e.get("id") == keep_id), None)
    drop = next((e for e in entities if e.get("id") == drop_id), None)
    if not keep or not drop: return {"ok": False, "error": "entity not found"}
    drop["merged_into"] = keep_id
    keep.pop("_review", None)
    history.append({"op": "MERGE", "keep": keep_id, "drop": drop_id, "actor": actor})
    return {"ok": True, "entity": keep}
def split(entities: list, history: list, entity_id: int, parts: list, actor="system"):
    src = next((e for e in entities if e.get("id") == entity_id), None)
    if not src: return {"ok": False, "error": "entity not found"}
    made = []
    for p in parts:
        item = {"id": max([e.get("id", 0) for e in entities] + [0]) + 1, **p, "split_from": entity_id}
        entities.append(item); made.append(item)
    src["split_into"] = [m["id"] for m in made]
    history.append({"op": "SPLIT", "src": entity_id, "parts": [m["id"] for m in made], "actor": actor})
    return {"ok": True, "entities": made}
def reject(history: list, entity_id: int, reason="", actor="system"):
    history.append({"op": "REJECT", "entity": entity_id, "reason": reason, "actor": actor})
    return {"ok": True}
