"""Dataset lifecycle: version/fingerprint/lineage/export — stdlib."""
import hashlib, json
def fingerprint(rows: list) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()
def publish(versions: list, dataset_id: int, rows: list, lineage: dict):
    fp = fingerprint(rows)
    own = [v for v in versions if v.get("dataset_id") == dataset_id]
    if own and own[-1].get("fingerprint") == fp:
        return own[-1]  # unchanged: no new version
    v = {"id": len(versions)+1, "dataset_id": dataset_id, "version": (own[-1].get("version", 0) + 1) if own else 1,
         "row_count": len(rows), "fingerprint": fp, "lineage": lineage,
         "rows": (rows or [])[:10000]}
    versions.append(v); return v
def to_csv(rows: list):
    if not rows: return ""
    cols = sorted({k for r in rows for k in r})
    lines = [",".join(cols)]
    for r in rows: lines.append(",".join(f'"{str(r.get(c, ""))}"' for c in cols))
    return "\\n".join(lines) + "\\n"
def diff(old_rows: list, new_rows: list, key=""):
    """Added/removed rows between versions (by fingerprint or full-row match)."""
    def fp(r):
        if key and isinstance(r, dict) and key in r: return f"k:{r[key]}"
        return "r:" + fingerprint([r])
    old, new = {fp(r) for r in old_rows}, {fp(r) for r in new_rows}
    return {"added": len(new - old), "removed": len(old - new), "unchanged": len(old & new)}
