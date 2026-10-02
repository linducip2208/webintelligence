# Architecture (as implemented)

```
browser UI (static/) ──NGINX──▶ FastAPI (source/python/app)
                                    ├─ api/shared.py      store+auth+execution
                                    ├─ api/routers/{system,catalog,collection,
                                    │                 intel,knowledge,ops}.py
                                    ├─ services/*         pure engines (tested)
                                    ├─ db/repo.py         write-through repository
                                    └─ ai/*               provider abstraction
        ┌─ Redis ──▶ Go collector (build/linux/collector) ─▶ POST /api/v1/results
        └─ workers.py / browser/worker.py ──▶ same results endpoint
MySQL 8.4 (prod) / SQLite file (dev) / memory (tests). Contracts versioned.
```

Persistence: every STORE append auto-mirrors to SQLAlchemy (35 collections);
in-place mutations call `repo.sync`; boot hydrates from DB (restart-safe).
DB-level LIMIT/OFFSET pagination for prices/events. Full item dicts
round-trip through JSON catch-alls, so API shapes are identical in all modes.

Auth: login tokens (HMAC) + scoped/expiring API keys; org isolation enforced
in every collection reader/writer (IDOR-tested). `REQUIRE_AUTH=1` in prod.

AI: interface + OpenAI/Anthropic/Google/Ollama/Muse/DB-configured providers,
env registry, fallback chain, per-call usage/cost tracking, prompt registry,
injection defense on evidence path. No vendor hardcoded.

See MASTER_BUILD_SPEC.md (design), OPERATIONS.md (run), FINAL_AUDIT.md (proof).
