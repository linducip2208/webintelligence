"""Playwright browser worker (requires `pip install playwright && playwright install chromium`)."""
POOL_SIZE = 2
BLOCKED = ("*.mp4", "*.woff2", "*.png", "*.jpg")
def fetch(url, timeout_ms=30000):
    try: from playwright.sync_api import sync_playwright
    except ImportError: return {"ok": False, "error": "playwright-not-installed"}
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = b.new_context(user_agent="Mozilla/5.0 WebIntel/1.0")
        pg = ctx.new_page()
        try:
            resp = pg.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            html = pg.content()
            out = {"ok": True, "http_status": resp.status if resp else 0, "url": pg.url, "size": len(html), "html": html}
        except Exception as e: out = {"ok": False, "error": str(e)}
        finally: b.close()
        return out


def main():
    """Poll Redis for BROWSER jobs; render via Playwright; write back results."""
    import json
    import time
    from ..core.logging import log

    log("browser-worker-boot", pool=POOL_SIZE)
    try:
        import redis as redislib
        from ..core.config import settings

        r = redislib.Redis.from_url(settings.redis_url)
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
