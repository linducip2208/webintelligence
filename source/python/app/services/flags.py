"""Feature flags: global/org/user scoped. Stored in KV (persisted).
Flags gate real behavior (ai chat, research, browser strategy)."""


def repo_get(repo, k):
    get = getattr(repo, "kv_get", None)
    if callable(get):
        try:
            return get(k)
        except Exception:
            return None
    return None
DEFAULTS = {"ai": True, "research": True, "browser": True, "webhooks": True}


def key(name, scope="global", ref=""):
    return f"flag:{scope}:{ref}:{name}" if scope != "global" else f"flag:global:{name}"


def is_enabled(repo, name, org=0, email=""):
    for sc, ref in (("user", email), ("org", str(org)), ("global", "")):
        v = repo_get(repo, key(name, sc, ref))
        if v is not None:
            return bool(v.get("on", True))
    return DEFAULTS.get(name, True)


def set_flag(repo, name, on, scope="global", ref=""):
    repo.kv_set(key(name, scope, ref), {"on": bool(on)})
    return {"name": name, "scope": scope, "ref": ref, "on": bool(on)}
