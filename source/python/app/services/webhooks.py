"""Outgoing webhook signing + delivery with retry — stdlib."""
import hashlib, hmac, json, time, urllib.request
def sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
def deliver(url: str, event: str, payload: dict, secret="", timeout=10, tries=3):
    body = json.dumps({"event": event, "payload": payload}, default=str).encode()
    last = ""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers={
                "Content-Type": "application/json", "X-WebIntel-Event": event,
                "X-WebIntel-Signature": sign(secret, body)})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return {"ok": True, "status": r.status, "attempts": i + 1}
        except Exception as e:
            last = str(e)[:200]; time.sleep(min(2 ** i, 8))
    return {"ok": False, "error": last, "attempts": tries}
