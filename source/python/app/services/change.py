"""Change detection — stdlib only."""
import hashlib
def sha(s: bytes | str) -> str:
    b = s.encode() if isinstance(s, str) else s
    return hashlib.sha256(b).hexdigest()
def classify(old_hash, new_hash, old_fields, new_fields):
    if old_hash is None: return "NEW"
    if new_hash is None: return "REMOVED"
    if old_hash == new_hash and (old_fields or {}) == (new_fields or {}): return "UNCHANGED"
    return "CHANGED"
def field_diff(old: dict, new: dict):
    out = {}
    for k in sorted(set(old) | set(new)):
        if old.get(k) != new.get(k): out[k] = {"old": old.get(k), "new": new.get(k)}
    return out
