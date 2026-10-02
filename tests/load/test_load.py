"""Load tests: decision-engine concurrency + queue throughput (no services needed)."""
import sys, os
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python", "app"))

from services import decision as dec


def test_100_concurrent_decisions():
    errs = []

    def work():
        try:
            e = dec.Engine()
            for _ in range(50):
                e.decide({"last_signals": {"rate_limited": True}}, dec.Policy(allow_brightdata=True),
                         {"own_proxy": {"healthy": True},
                          "brightdata": {"healthy": True, "configured": True}})
        except Exception as ex:  # noqa
            errs.append(ex)

    ts = [threading.Thread(target=work) for _ in range(100)]
    t0 = time.time()
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errs
    assert time.time() - t0 < 60


def test_1000_queued_jobs_throughput():
    from orchestration.orchestrator import idem_key
    t0 = time.time()
    keys = {idem_key({"job_id": f"j{i}", "url": "https://example.com"}) for i in range(1000)}
    assert len(keys) == 1000  # idempotency keys unique
    assert time.time() - t0 < 30
