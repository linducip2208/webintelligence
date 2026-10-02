import json, sys, datetime, re
_SECRET = re.compile(r"(api[_-]?key|password|passwd|secret|token|authorization|bearer|cookie)", re.I)


def _redact(obj):
    if isinstance(obj, dict):
        return {k: ("***" if _SECRET.search(str(k)) else _redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    if isinstance(obj, str) and len(obj) > 32 and _looks_secret(obj):
        return "***"
    return obj


def _looks_secret(s: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_\-+/=]{32,}", s))


def log(event, **kw):
    rec = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "event": event, **_redact(kw)}
    sys.stdout.write(json.dumps(rec, default=str) + "\n")
