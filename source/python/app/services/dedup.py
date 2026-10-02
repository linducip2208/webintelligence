"""Dedup: URL canonicalization + content fingerprint + near-dup — stdlib."""
import hashlib, urllib.parse, re
TRACK = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","gclid","fbclid","ref","sessionid"}
def canonical_url(url: str) -> str:
    p = urllib.parse.urlparse((url or "").strip())
    host = (p.hostname or "").lower()
    if host.startswith("www."): host = host[4:]
    qs = sorted((k, v) for k, v in urllib.parse.parse_qsl(p.query) if k.lower() not in TRACK)
    path = p.path.rstrip("/") or "/"
    return urllib.parse.urlunparse((p.scheme.lower() or "https", host, path, "", urllib.parse.urlencode(qs), ""))
def fingerprint(text: str) -> str:
    t = re.sub(r"\s+", " ", (text or "").lower()).strip()
    return hashlib.sha256(t.encode()).hexdigest()
def jaccard(a: str, b: str) -> float:
    ta, tb = set(re.findall(r"[a-z0-9]{3,}", (a or "").lower())), set(re.findall(r"[a-z0-9]{3,}", (b or "").lower()))
    if not ta or not tb: return 0.0
    return round(len(ta & tb) / len(ta | tb), 3)
