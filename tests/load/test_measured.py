"""Measured load: concurrent API traffic with real p50/p95 numbers (no invention)."""
import os
import statistics
import sys
import threading
import time

import pytest

fastapi = pytest.importorskip("fastapi")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def _unlimit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_STANDARD", "100000")
    monkeypatch.setenv("RATE_LIMIT_SEARCH", "100000")
    from app.main import _BUCKETS
    _BUCKETS.clear()


def test_measured_api_load(monkeypatch):
    _unlimit(monkeypatch)
    c = TestClient(app)
    c.post("/api/v1/projects", json={"name": "Load", "description": ""})
    lat, errs, n_threads, per = [], [], 20, 25
    lock = threading.Lock()

    def work():
        local = []
        for _ in range(per):
            t0 = time.time()
            try:
                r = c.get("/api/v1/dashboard")
                assert r.status_code == 200
                local.append((time.time() - t0) * 1000)
            except Exception:
                with lock:
                    errs.append(1)
        with lock:
            lat.extend(local)

    ts = [threading.Thread(target=work) for _ in range(n_threads)]
    t0 = time.time()
    [t.start() for t in ts]
    [t.join() for t in ts]
    dt = time.time() - t0
    assert not errs and len(lat) == n_threads * per
    s = sorted(lat)
    p50 = statistics.median(s)
    p95 = s[int(len(s) * 0.95)]
    print(f"\nload: n={len(lat)} throughput={len(lat)/dt:.1f}rps "
          f"p50={p50:.1f}ms p95={p95:.1f}ms errors={len(errs)}")
    assert p95 < 5000


def test_pagination_large(monkeypatch):
    _unlimit(monkeypatch)
    c = TestClient(app)
    for i in range(30):
        c.post("/api/v1/articles", json={"title": f"bulk-{i}", "publisher": "load"})
    p1 = c.get("/api/v1/articles?page=1&size=10").json()
    p3 = c.get("/api/v1/articles?page=3&size=10").json()
    assert p1["total"] >= 30 and len(p1["items"]) == 10
    assert p1["items"] != p3["items"]
