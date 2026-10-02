"""Temporal snapshots: current/previous/timeline/first/last seen — stdlib."""
def record(history: list, key: str, state: dict, at: str):
    """Append snapshot; returns (kind, prev_state). kind in NEW/CHANGED/UNCHANGED."""
    snaps = [h for h in history if h.get("key") == key]
    if not snaps:
        history.append({"key": key, "state": state, "at": at})
        return ("NEW", None)
    prev = snaps[-1]
    kind = "UNCHANGED" if prev["state"] == state else "CHANGED"
    history.append({"key": key, "state": state, "at": at})
    return (kind, prev["state"])
def timeline(history: list, key: str):
    snaps = [h for h in history if h.get("key") == key]
    if not snaps: return {}
    return {"first_seen": snaps[0]["at"], "last_seen": snaps[-1]["at"],
            "versions": len(snaps), "changes": sum(
                1 for i in range(1, len(snaps)) if snaps[i]["state"] != snaps[i-1]["state"])}
