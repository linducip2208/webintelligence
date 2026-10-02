"""Dataset lifecycle: version/fingerprint/lineage/export — stdlib."""
import hashlib, json
def fingerprint(rows: list) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()
def publish(versions: list, dataset_id: int, rows: list, lineage: dict):
    fp = fingerprint(rows)
    if versions and versions[-1].get("fingerprint") == fp:
        return versions[-1]  # unchanged: no new version
    v = {"id": len(versions)+1, "dataset_id": dataset_id, "version": len(versions)+1,
         "row_count": len(rows), "fingerprint": fp, "lineage": lineage,
         "rows": (rows or [])[:10000]}
    versions.append(v); return v
def to_csv(rows: list):
    if not rows: return ""
    cols = sorted({k for r in rows for k in r})
    lines = [",".join(cols)]
    for r in rows: lines.append(",".join(f'"{str(r.get(c, ""))}"' for c in cols))
    return "\n".join(lines) + "\n"
