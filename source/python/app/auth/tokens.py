"""Token auth — stdlib HMAC tokens, no dependency required."""
import base64
import hashlib
import hmac
import json
import time

TTL = 12 * 3600


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _ub64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def issue(email: str, secret: str, ttl: int = TTL) -> str:
    body = json.dumps({"sub": email, "exp": int(time.time()) + ttl}).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return _b64(body) + "." + _b64(sig)


def verify(token: str, secret: str):
    try:
        b, s = token.split(".")
        body = _ub64(b)
        expect = hmac.new(secret.encode(), body, hashlib.sha256).digest()
        if not hmac.compare_digest(expect, _ub64(s)):
            return None
        payload = json.loads(body)
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("sub")
    except Exception:
        return None
