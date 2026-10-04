"""Provider fallback: try providers in order, record each failure. stdlib only."""
import time

_PREFERRED = ("muse-spark", "openai", "anthropic", "google", "ollama")


def default_names(reg):
    """Fallback order derived from the live registry — never a frozen list.

    Preferred vendors first (if registered), then any other registered
    provider (custom/DB-added) alphabetically, so newly added providers
    join the chain with zero code changes.
    """
    have = set(reg.names())
    return [n for n in _PREFERRED if n in have] + sorted(have - set(_PREFERRED))


def chat_fallback(providers: list, messages: list, model: str = ""):
    """providers: [(name, provider)]. Returns response or aggregated error."""
    errors = []
    for name, p in providers:
        if p is None:
            errors.append({"provider": name, "error": "not-registered"})
            continue
        t0 = time.time()
        try:
            out = p.chat(messages, model)
        except Exception as e:
            errors.append({"provider": name, "error": str(e)[:200]})
            continue
        if out.get("error"):
            errors.append({"provider": name, "error": out["error"][:200],
                           "latency_ms": round((time.time() - t0) * 1000, 2)})
            continue
        out["provider"] = name
        out["fallbacks_tried"] = [e["provider"] for e in errors]
        return out
    return {"error": "all providers failed", "attempts": errors}
