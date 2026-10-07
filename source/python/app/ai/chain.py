"""Shared AI provider-chain resolution: explicit request first, then the
defaults cascade (user -> org -> system), then built-in fallbacks plus every
enabled database-configured provider.

Database credentials override ambient environment configuration by design:
an explicitly saved provider wins over an env-discovered one. Returns
(chain, use_model, default_used) where default_used names the cascade level
that supplied the head ("explicit", "user", "organization", "system", "").
"""
from __future__ import annotations


def _default_get(repo, scope, org=0, email=""):
    key = {"system": "ai:default:system", "org": f"ai:default:org:{org}",
           "user": f"ai:default:user:{email}"}.get(scope, "")
    try:
        return repo.kv_get(key) if key else None
    except Exception:
        return None


def resolve_default(repo, email="", org=0):
    for scope in ("user", "organization", "system"):
        try:
            d = _default_get(repo, scope, org, email)
        except Exception:
            d = None
        if d and d.get("provider"):
            return scope, d
    return "", {}


ROLES = ("research", "summarization", "classification", "risk", "report")


def resolve_role(repo, role: str):
    """System-level per-use-case default: {provider, model, enabled} or {}."""
    if role not in ROLES:
        return {}
    try:
        d = repo.kv_get(f"ai:usecase:{role}") or {}
    except Exception:
        d = {}
    if d.get("enabled", True) and d.get("provider"):
        return d
    return {}


def build_instance(store, provider_name, model=""):
    """Build a live adapter for an env name or 'db:<name>'. Returns (name, instance)."""
    from .factory import build_provider as _bp
    from . import registry as _reg
    from ..core.crypto import decrypt as _dec
    if provider_name.startswith("db:"):
        row = next((x for x in store.get("ai_providers", [])
                    if x.get("name") == provider_name[3:] and x.get("enabled")), None)
        if not row:
            return provider_name, None
        return row["name"], _bp(row.get("protocol", "chat"), row.get("base_url", ""),
                                _dec(row.get("api_key_enc", "")),
                                row.get("model", "") or model)
    return provider_name, _reg.get(provider_name)


def build_chain(store, repo, registry, provider="", model="", email="", org=0):
    from .factory import fallback_order
    from . import fallback as _fb
    if provider:
        name, inst = build_instance(store, provider, model)
        return [(name, inst)], model, "explicit"
    scope, dflt = resolve_default(repo, email, org)
    chain = []
    use_model = model
    used = ""
    if dflt.get("provider"):
        name, inst = build_instance(store, dflt["provider"], dflt.get("model", "") or model)
        if inst is not None:
            chain.append((name, inst))
            use_model = dflt.get("model", "") or model
            used = {"user": "user", "organization": "organization",
                    "system": "system"}.get(scope, "")
    names = fallback_order() or _fb.default_names(registry)
    seen = {n for n, _ in chain}
    for n in names:
        if n not in seen:
            chain.append((n, registry.get(n)))
            seen.add(n)
    for row in store.get("ai_providers", []):
        if row.get("enabled") and row.get("name") not in seen:
            name, inst = build_instance(store, f"db:{row['name']}", use_model)
            if inst is not None:
                chain.append((name, inst))
                seen.add(name)
    return chain, use_model, used
