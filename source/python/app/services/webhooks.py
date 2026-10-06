"""Outgoing webhook signing + delivery with retry — stdlib."""
import hashlib, hmac, json, time, urllib.request
CHANNELS = ("generic", "slack", "discord")


def format_payload(channel: str, event: str, payload: dict) -> dict:
    """Channel adapters: same event, receiver-native shape. Secrets are
    never part of the payload (HMAC header only)."""
    if channel == "slack":
        text = f"[WebIntel:{event}] " + json.dumps(payload, default=str)[:3000]
        return {"text": text}
    if channel == "discord":
        content = f"**WebIntel:{event}** " + json.dumps(payload, default=str)[:1800]
        return {"content": content}
    return {"event": event, "payload": payload}


def sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def deliver(url: str, event: str, payload: dict, secret="", timeout=10, tries=3,
            channel: str = "generic"):
    body = json.dumps(format_payload(channel or "generic", event, payload),
                      default=str).encode()
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
