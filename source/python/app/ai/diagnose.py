"""Real provider diagnostics: connection test + model discovery.

Never accepts, returns, logs, or echoes API keys — callers pass a built
provider whose credential already lives server-side. Error messages are
normalized to stable codes and scrubbed of secret-like material.
"""
import re
import time

SECRET_PATTERNS = [
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"\boc_sk_[A-Za-z0-9_\-]+"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]+"),
    re.compile(r"(api[_-]?key['\"\s:=]+)\S+", re.IGNORECASE),
    re.compile(r"([?&]key=)[^&\s]+"),
]


def scrub(text: str) -> str:
    out = str(text or "")
    for rx in SECRET_PATTERNS:
        out = rx.sub(lambda m: (m.group(1) if m.lastindex else "") + "[redacted]", out)
    return out[:500]


def normalize_error(err: Exception | str) -> tuple[str, str]:
    """-> (code, safe_message). Codes: AUTHENTICATION_FAILED, ACCESS_DENIED,
    ENDPOINT_OR_MODEL_NOT_FOUND, TIMEOUT, RATE_LIMITED, PROVIDER_UNAVAILABLE,
    CONNECTION_TIMEOUT, INVALID_CONFIGURATION."""
    raw = scrub(err if isinstance(err, str) else str(err))
    low = raw.lower()
    m = re.search(r"http\s+(\d{3})", low)
    code = int(m.group(1)) if m else 0
    if code == 401 or "unauthorized" in low or "invalid api" in low or "invalid x-api-key" in low:
        return "AUTHENTICATION_FAILED", "Invalid API credentials."
    if code == 403 or "forbidden" in low or "access denied" in low:
        return "ACCESS_DENIED", "Access denied by the provider."
    if code == 404 or "not found" in low or "unknown model" in low or "model_not_found" in low:
        return "ENDPOINT_OR_MODEL_NOT_FOUND", "Endpoint or model not found."
    if code == 408:
        return "TIMEOUT", "Provider timed out."
    if code == 429 or "rate limit" in low or "too many requests" in low:
        return "RATE_LIMITED", "Provider rate limit exceeded."
    if code and 500 <= code <= 599:
        return "PROVIDER_UNAVAILABLE", f"Provider unavailable (HTTP {code})."
    if "timed out" in low or "timeout" in low:
        return "CONNECTION_TIMEOUT", "Connection timed out."
    if "connection refused" in low or "unreachable" in low or "name resolution" in low \
            or "nodename nor servname" in low or "getaddrinfo failed" in low:
        return "PROVIDER_UNAVAILABLE", "Provider endpoint unreachable."
    if "ssrf" in low or "blocked" in low or "bad url" in low or "scheme not allowed" in low:
        return "INVALID_CONFIGURATION", "Endpoint rejected by security policy."
    if "not-configured" in low or "missing" in low or "required" in low:
        return "INVALID_CONFIGURATION", "Provider configuration incomplete."
    return "PROVIDER_UNAVAILABLE", raw or "Provider request failed."


def discover(provider, limit: int = 100) -> dict:
    """Real model discovery via the adapter. Never invents metadata."""
    try:
        out = provider.list_models()
    except Exception as e:  # noqa: BLE001
        code, msg = normalize_error(e)
        return {"models": [], "discovery": False, "manual_entry": True,
                "error": {"code": code, "message": msg}}
    if isinstance(out, dict) and "error" in out:
        manual = "not supported" in str(out["error"]).lower() or "ai.google.dev" in str(out["error"])
        if manual:
            return {"models": [], "discovery": False, "manual_entry": True,
                    "note": "Model discovery is not supported by this provider."}
        code, msg = normalize_error(out["error"])
        return {"models": [], "discovery": False, "manual_entry": True,
                "error": {"code": code, "message": msg}}
    ids = out.get("models", []) if isinstance(out, dict) else []
    models = [{"id": str(i)} for i in (ids or [])[:limit]]
    return {"models": models, "discovery": True, "manual_entry": False,
            "count": len(models)}


def test_provider(provider, name: str = "", model: str = "") -> dict:
    """Full structured test: auth check, model availability, latency.

    Uses only metadata endpoints (/models or a minimal probe) — no text
    generation, no token burn.
    """
    t0 = time.time()
    base = {"name": name or getattr(provider, "name", "provider"),
            "protocol": _protocol_of(provider)}
    if not getattr(provider, "configured", False):
        return {"success": False, "provider": base,
                "connection": {"authenticated": False, "latency_ms": 0},
                "model": {"selected": model or "", "available": False},
                "models": [],
                "error": {"code": "INVALID_CONFIGURATION",
                          "message": "Provider configuration incomplete (endpoint/key missing).",
                          "suggested_action": "Check the endpoint and API key, then test again."}}
    try:
        health = provider.health_check()
    except Exception as e:  # noqa: BLE001
        code, msg = normalize_error(e)
        return _fail(base, model, t0, code, msg)
    if not health.get("ok"):
        code, msg = normalize_error(health.get("reason") or health.get("error") or "failed")
        return _fail(base, model, t0, code, msg)
    latency = round((time.time() - t0) * 1000, 2)
    disc = discover(provider)
    selected = model or getattr(provider, "model", "")
    available = None
    if selected and disc.get("discovery"):
        ids = [m["id"] for m in disc["models"]]
        available = selected in ids
    result = {"success": True, "provider": base,
              "connection": {"authenticated": True, "latency_ms": latency},
              "model": {"selected": selected or "", "available": available},
              "models": disc["models"],
              "message": "Connection successful"}
    if available is False:
        result["success"] = False
        result["error"] = {"code": "ENDPOINT_OR_MODEL_NOT_FOUND",
                           "message": f"Model '{selected}' not offered by this endpoint.",
                           "suggested_action": "Pick a model from the discovered list."}
        result.pop("message", None)
    return result


def _fail(base, model, t0, code, msg):
    return {"success": False, "provider": base,
            "connection": {"authenticated": code not in ("INVALID_CONFIGURATION",),
                           "latency_ms": round((time.time() - t0) * 1000, 2)},
            "model": {"selected": model or "", "available": False},
            "models": [],
            "error": {"code": code, "message": msg,
                      "suggested_action": _suggest(code)}}


def _suggest(code: str) -> str:
    return {"AUTHENTICATION_FAILED": "Check the API key and try again.",
            "ACCESS_DENIED": "Verify the key has access to this model/endpoint.",
            "ENDPOINT_OR_MODEL_NOT_FOUND": "Check the endpoint URL and model name.",
            "TIMEOUT": "Retry; check network/provider load.",
            "RATE_LIMITED": "Wait and retry.",
            "PROVIDER_UNAVAILABLE": "Check the endpoint URL and network connectivity.",
            "CONNECTION_TIMEOUT": "Check network connectivity and firewall.",
            "INVALID_CONFIGURATION": "Complete the endpoint, key, and protocol fields."}.get(code, "")


def _protocol_of(provider) -> str:
    cls = type(provider).__name__
    return {"ResponsesProvider": "responses",
            "AnthropicProvider": "anthropic",
            "GoogleProvider": "google"}.get(cls, "chat")
