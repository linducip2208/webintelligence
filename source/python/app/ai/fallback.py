"""Provider fallback: try providers in order, record each failure. stdlib only."""
import time


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
