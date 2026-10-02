"""Background worker: drains Redis queues and executes the pipeline.

- `webintel:queue:jobs` (Go/Python collection jobs): direct-fetch via the
  pipeline, then POST the result bundle to /api/v1/results.
- Due schedules: handled in-API via POST /api/v1/worker/tick (cron/systemd
  calls it, or run this process with TICK_SCHEDULES=1).

Run: python -m app.workers   (systemd: webintel-worker.service)
"""
import json
import os
import time
import urllib.request

from .core.logging import log

API = os.getenv("API_BASE", "http://127.0.0.1:8000")
TOKEN = os.getenv("API_TOKEN", "")


def _post(path: str, payload: dict):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(API + path, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    from .core.deps import get_redis
    from .services import pipeline as pipe
    from .services import decision as dec

    log("worker-boot", api=API)
    r = get_redis()
    if r is None:
        log("worker-no-redis-retry-loop")
    while True:
        try:
            if r is not None:
                item = r.blpop("webintel:queue:jobs", timeout=5)
                if item:
                    job = json.loads(item[1])
                    log("worker-job", job_id=job.get("job_id"))
                    res = pipe.run_job(
                        {"job_id": job.get("job_id"), "url": job.get("url", "")},
                        {"url": job.get("url", "")}, [],
                        dec.Policy(), {"own_proxy": {"healthy": True},
                                       "brightdata": {"healthy": True,
                                                      "configured": False}})
                    bundle = {"schema_version": "1.0", "job_id": job.get("job_id"),
                              "status": res.get("status", "failed"),
                              "strategy": res.get("strategy", "DIRECT_HTTP"),
                              "http_status": res.get("http_status", 0),
                              "content_hash": res.get("content_hash", ""),
                              "content_size": res.get("content_size", 0),
                              "retrieved_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                              "parse_status": "ok" if res.get("status") == "success" else "failed",
                              "diagnostics": res.get("diagnostics", {})}
                    try:
                        _post("/api/v1/results", bundle)
                        log("worker-result-posted", job_id=job.get("job_id"))
                    except Exception as e:
                        log("worker-post-failed", error=str(e)[:200])
                        r.rpush("webintel:queue:dlq", json.dumps(bundle))
            if os.getenv("TICK_SCHEDULES", "") == "1":
                try:
                    _post("/api/v1/worker/tick", {})
                except Exception as e:
                    log("worker-tick-failed", error=str(e)[:200])
                time.sleep(55)
        except Exception as e:
            log("worker-error", error=str(e)[:200])
            time.sleep(5)


if __name__ == "__main__":
    main()
