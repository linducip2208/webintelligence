"""AI privacy policy: which providers may receive evidence, and what gets
redacted first. Stored in repo KV (persisted), enforced in ai_chat and
research_analyze. Modes:

- any (default): any configured provider.
- approved_only: only providers named in `approved`.
- local_only: only local providers (Ollama / local presets).

Redaction applies to evidence text before it is wrapped as untrusted DATA:
PII patterns and secret-like patterns are masked. Raw credentials are never
sent regardless of policy (enforced structurally: keys live server-side).
"""
MODES = ("any", "approved_only", "local_only")
KEY = "ai:privacy"
DEFAULTS = {"mode": "any", "redact_pii": True, "redact_secrets": True,
            "approved": []}


def get_policy(repo):
    try:
        saved = repo.kv_get(KEY, {}) or {}
    except Exception:
        saved = {}
    out = dict(DEFAULTS)
    out.update({k: v for k, v in saved.items() if k in DEFAULTS})
    if out["mode"] not in MODES:
        out["mode"] = "any"
    out["approved"] = [str(x) for x in (out["approved"] or []) if str(x).strip()]
    out["redact_pii"] = bool(out["redact_pii"])
    out["redact_secrets"] = bool(out["redact_secrets"])
    return out


def set_policy(repo, spec: dict):
    policy = dict(DEFAULTS)
    if "mode" in spec:
        if spec["mode"] not in MODES:
            raise ValueError("mode must be any|approved_only|local_only")
        policy["mode"] = spec["mode"]
    for flag in ("redact_pii", "redact_secrets"):
        if flag in spec:
            policy[flag] = bool(spec[flag])
    if "approved" in spec:
        if not isinstance(spec["approved"], list):
            raise ValueError("approved must be a list of provider names")
        policy["approved"] = [str(x) for x in spec["approved"] if str(x).strip()]
    repo.kv_set(KEY, policy)
    return get_policy(repo)


def is_local_provider(name: str, preset_id: str = "") -> bool:
    if (name or "") == "ollama":
        return True
    if preset_id:
        try:
            from .presets import get_preset
            p = get_preset(preset_id)
            if p:
                return bool(p.get("local"))
        except Exception:
            pass
    return False


def check(policy: dict, provider_name: str, preset_id: str = "") -> tuple[bool, str]:
    """(allowed, reason). Never raises."""
    mode = (policy or {}).get("mode", "any")
    if mode == "local_only" and not is_local_provider(provider_name, preset_id):
        return False, "privacy policy local_only: cloud provider blocked"
    if mode == "approved_only" and provider_name not in (policy.get("approved") or []):
        return False, "privacy policy approved_only: provider not approved"
    return True, ""


def redact_evidence(policy: dict, texts: list[str]) -> list[str]:
    out = []
    for t in texts or []:
        s = str(t or "")
        if (policy or {}).get("redact_pii", True):
            try:
                from ..services import pii as _pii
                s = _pii.mask(s)
            except Exception:
                pass
        if (policy or {}).get("redact_secrets", True):
            try:
                from . import diagnose as _dg
                s = _dg.scrub(s)
            except Exception:
                pass
        out.append(s)
    return out


def redact_items(policy: dict, items):
    """Redact text-ish fields of evidence items (dicts or strings)."""
    out = []
    for it in items or []:
        if isinstance(it, dict):
            it = dict(it)
            for k in ("text", "snippet", "content", "value"):
                if isinstance(it.get(k), str):
                    it[k] = redact_evidence(policy, [it[k]])[0]
            out.append(it)
        else:
            out.append(redact_evidence(policy, [it])[0])
    return out
