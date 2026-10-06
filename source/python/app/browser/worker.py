"""Playwright browser worker (requires `pip install playwright && playwright install chromium`).

The browser launches ONCE and is reused across jobs (new context per job);
crashes trigger a relaunch. Never one browser process per request.
"""
import threading

POOL_SIZE = 2
BLOCKED = ("*.mp4", "*.woff2", "*.png", "*.jpg")
_LOCK = threading.Lock()
_PW = {"p": None, "browser": None}


def _browser():
    from playwright.sync_api import sync_playwright
    with _LOCK:
        b = _PW["browser"]
        try:
            if b is not None and b.is_connected():
                return b
        except Exception:
            pass
        if _PW["p"] is None:
            _PW["p"] = sync_playwright().start()
        _PW["browser"] = _PW["p"].chromium.launch(
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        return _PW["browser"]


def pool_status():
    try:
        import playwright  # noqa: F401
        installed = True
    except ImportError:
        installed = False
    alive = False
    try:
        alive = _PW["browser"] is not None and _PW["browser"].is_connected()
    except Exception:
        pass
    return {"installed": installed, "pool": POOL_SIZE, "browser_alive": alive,
            "reused": True}


def fetch(url, timeout_ms=30000, trusted_cidrs=None):
    try:
        import playwright  # noqa: F401
    except ImportError:
        return {"ok": False, "error": "playwright-not-installed"}
    try:
        from ..core.ssrf import validate_url
        import os as _o
        trust = trusted_cidrs if trusted_cidrs is not None else [
            x.strip() for x in _o.getenv("TRUSTED_EGRESS_CIDRS", "").split(",") if x.strip()]
        validate_url(url, trust or None)
    except Exception as e:
        from ..core.ssrf import SSRFError
        if isinstance(e, SSRFError):
            return {"ok": False, "error": f"ssrf-blocked: {e}"}
        raise
    try:
        b = _browser()
    except Exception as e:
        return {"ok": False, "error": f"browser-launch-failed: {e}"[:300]}
    try:
        ctx = b.new_context(user_agent="Mozilla/5.0 WebIntel/1.0")
        pg = ctx.new_page()
        try:
            resp = pg.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            html = pg.content()
            out = {"ok": True, "http_status": resp.status if resp else 0,
                   "url": pg.url, "size": len(html), "html": html}
        except Exception as e:
            out = {"ok": False, "error": str(e)[:300]}
        finally:
            try:
                ctx.close()
            except Exception:
                pass
        return out
    except Exception as e:
        with _LOCK:
            try:
                if _PW["browser"] is not None:
                    _PW["browser"].close()
            except Exception:
                pass
            _PW["browser"] = None
        return {"ok": False, "error": f"browser-crash-recovered: {e}"[:300]}


def main():
    """Poll Redis for BROWSER jobs; render via Playwright; write back results."""
    import json
    import time
    from ..core.logging import log

    log("browser-worker-boot", pool=POOL_SIZE)
    try:
        import redis as redislib
        from ..core.config import settings

        r = redislib.Redis.from_url(settings.redis_url, protocol=2)
    except Exception as e:
        log("browser-worker-no-redis", error=str(e))
        return
    while True:
        item = r.blpop("webintel:queue:browser", timeout=5)
        if not item:
            continue
        try:
            job = json.loads(item[1])
            out = fetch(job.get("url", ""), job.get("timeout_ms", 30000))
            out.update({"job_id": job.get("job_id"), "strategy": "BROWSER"})
            r.rpush("webintel:queue:results", json.dumps(out))
            log("browser-job-done", job_id=job.get("job_id"), ok=out.get("ok"))
        except Exception as e:
            log("browser-job-error", error=str(e))
        time.sleep(0.1)


if __name__ == "__main__":
    main()
