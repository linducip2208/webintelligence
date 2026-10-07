"""OpenCode Go model discovery: fetch the gateway's model catalog and
normalize per-model metadata. Never hardcodes the catalog: the gateway is
the truth, this module is the translator.

Endpoint: GO_MODELS_URL, else {base_url}/models. Each entry keeps its own
protocol/endpoint when the gateway declares them; otherwise the gateway
default (responses) applies. Unknown shapes are skipped openly, never
invented.
"""
import os as _os

KNOWN_PROTOCOLS = ("chat", "responses", "anthropic", "google")


def models_url(base_url: str) -> str:
    override = (_os.getenv("GO_MODELS_URL", "") or "").strip()
    if override:
        return override
    return (base_url or "").rstrip("/") + "/models"


def normalize(entry: dict, base_url: str, default_protocol: str = "responses") -> dict | None:
    if not isinstance(entry, dict):
        return None
    mid = str(entry.get("id") or entry.get("model") or entry.get("name") or "").strip()
    if not mid:
        return None
    proto = str(entry.get("protocol") or entry.get("api") or "").lower()
    if proto not in KNOWN_PROTOCOLS:
        proto = default_protocol if default_protocol in KNOWN_PROTOCOLS else "responses"
    endpoint = str(entry.get("endpoint") or entry.get("base_url") or "").strip() or None
    caps = [c for c in (entry.get("capabilities") or []) if isinstance(c, str)][:20]
    out = {"id": mid, "protocol": proto, "endpoint": endpoint,
           "display_name": str(entry.get("display_name") or mid),
           "capabilities": caps, "source": "GO_MODELS_URL" if _os.getenv("GO_MODELS_URL") else "REMOTE DISCOVERED"}
    for flag in ("vision", "tools", "reasoning", "streaming", "json"):
        if flag in entry:
            out[flag] = bool(entry[flag])
    return out


def discover(base_url: str, headers: dict, timeout: int = 30,
             default_protocol: str = "responses", limit: int = 200) -> dict:
    """-> {models:[...], count, source} or {models:[], error:{...}}."""
    from .http import get_json, AIError
    from . import diagnose as _dg
    try:
        r = get_json(models_url(base_url), headers or {}, timeout)
    except AIError as e:
        code, msg = _dg.normalize_error(e)
        return {"models": [], "error": {"code": code, "message": msg}}
    data = r.get("data", r)
    raw = data.get("data") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        raw = data.get("models") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return {"models": [], "error": {"code": "PROTOCOL_ERROR",
                                        "message": "Model catalog has no list shape."}}
    models = []
    for entry in raw[:limit]:
        n = normalize(entry if isinstance(entry, dict) else {"id": entry},
                      base_url, default_protocol)
        if n:
            models.append(n)
    return {"models": models, "count": len(models),
            "source": "GO_MODELS_URL" if _os.getenv("GO_MODELS_URL") else "REMOTE DISCOVERED"}
