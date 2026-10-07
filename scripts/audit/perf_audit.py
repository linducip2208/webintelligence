"""Measure baseline endpoint latencies and write docs/PERFORMANCE_AUDIT.md.

Real numbers from this machine via TestClient (in-memory backend, seeded
records). Not production hardware figures — a regression baseline.
Run: python scripts/audit/perf_audit.py
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.version import APP_VERSION  # noqa: E402

c = TestClient(app)


def seed():
    p = c.post("/api/v1/projects", json={"name": "Perf", "description": ""}).json()
    for i in range(5):
        t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": f"p{i}.example",
                                            "url": f"https://p{i}.example/x"}).json()
    c.post("/api/v1/entities/resolve", json={"candidate": {"name": "Perf Corp"}})
    c.post("/api/v1/findings", json={"kind": "OBS", "title": "Perf finding"})
    c.post("/api/v1/admin/demo/seed", json={}).status_code  # best effort
    return p


def bench(label, fn, rounds=5):
    ts = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t0) * 1000)
    ts.sort()
    return label, round(ts[len(ts) // 2], 1), round(max(ts), 1)


def main():
    seed()
    rows = [
        bench("dashboard", lambda: c.get("/api/v1/dashboard")),
        bench("search keyword", lambda: c.get("/api/v1/search", params={"q": "perf"})),
        bench("search hybrid", lambda: c.get("/api/v1/search", params={"q": "perf", "mode": "hybrid"})),
        bench("entities list", lambda: c.get("/api/v1/entities?size=100")),
        bench("graph traverse", lambda: c.get("/api/v1/graph/nodes?size=100")),
        bench("findings list", lambda: c.get("/api/v1/findings?size=100")),
        bench("risk target", lambda: c.get("/api/v1/risk/target/1")),
        bench("healthz", lambda: c.get("/healthz")),
        bench("readyz", lambda: c.get("/readyz")),
        bench("ai inventory", lambda: c.get("/api/v1/ai/credentials/inventory")),
        bench("ai health", lambda: c.get("/api/v1/ai/health")),
        bench("docs search", lambda: c.get("/api/v1/docs/search", params={"q": "risk"})),
        bench("docs page", lambda: c.get("/docs/en/intelligence/risk")),
        bench("settings system", lambda: c.get("/api/v1/settings/system")),
    ]
    L = [f"# Web Intelligence — Performance Audit (baseline, app v{APP_VERSION})", "",
         "_Median/max of 5 in-process runs (TestClient, in-memory backend). "
         "Regression baseline only — not production hardware figures._", "",
         "| Endpoint | Median ms | Max ms | Budget |",
         "|---|---|---|---|"]
    over = 0
    for label, med, mx in rows:
        budget = 250 if "docs" not in label and "risk" not in label else 1000
        ok = med <= budget
        over += not ok
        L.append(f"| {label} | {med} | {mx} | {budget} ms ({'OK' if ok else 'OVER'}) |")
    L += ["",
          "## Notes",
          "",
          "- Pagination enforced on list endpoints (max size 100).",
          "- Graph traversal bounded (depth + limit); full universe never loads by default.",
          "- AI health aggregate performs no live calls; tests are explicit buttons.",
          "- Docs screenshots lazy-load with dimensions (no layout shift).",
          ""]
    open(os.path.join(ROOT, "docs", "PERFORMANCE_AUDIT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"perf audit: {len(rows)} endpoints, {over} over budget")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
