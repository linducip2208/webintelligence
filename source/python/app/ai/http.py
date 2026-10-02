"""Shared HTTP + token/cost helpers for AI providers (stdlib only)."""
import json
import time
import urllib.request


class AIError(RuntimeError):
    pass


def post_json(url: str, headers: dict, payload: dict, timeout: int = 60):
    t0 = time.time()
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            return {"status": r.status, "data": json.loads(raw or "{}"),
                    "latency_ms": round((time.time() - t0) * 1000, 2)}
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()[:500]
        except Exception:
            detail = ""
        raise AIError(f"http {e.code}: {detail}")
    except Exception as e:
        raise AIError(str(e)[:300])


def get_json(url: str, headers: dict, timeout: int = 30):
    t0 = time.time()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"status": r.status,
                    "data": json.loads(r.read().decode() or "{}"),
                    "latency_ms": round((time.time() - t0) * 1000, 2)}
    except urllib.error.HTTPError as e:
        raise AIError(f"http {e.code}")
    except Exception as e:
        raise AIError(str(e)[:300])


def estimate_tokens(text: str) -> int:
    """Heuristic token estimate (~4 chars/token). Labeled estimate, not metered."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def messages_text(messages: list) -> str:
    out = []
    for m in messages or []:
        c = m.get("content", "")
        out.append(c if isinstance(c, str) else json.dumps(c, default=str))
    return "\n".join(out)
