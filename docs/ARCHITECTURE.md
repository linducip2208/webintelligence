# Architecture (as implemented)

```
browser UI (static/, local Tabler, no CDN) ──NGINX──▶ FastAPI (source/python/app)
                                     ├─ version.py       APP_VERSION single source
                                     ├─ api/shared.py    store+auth+execution
                                     ├─ api/routers/{system,catalog,collection,intel,
                                     │                 knowledge,ops,cases,docs,settings}.py
                                     ├─ services/*       pure engines (tested)
                                     ├─ search/unified.py one ranked engine, 4 modes
                                     ├─ ai/*             presets/factory/chain/diagnose/
                                     │                   privacy/go_discovery
                                     └─ db/repo.py       write-through repository (+KV)
        ┌─ Redis ──▶ Go collector (build/linux/collector) ─▶ POST /api/v1/results
        └─ workers.py / browser/worker.py ──▶ same results endpoint
MySQL 8.4 (prod) / SQLite file (dev) / memory (tests). Contracts versioned.
```

Persistence: every STORE append auto-mirrors to SQLAlchemy; in-place
mutations call `repo.sync`; boot hydrates from DB (restart-safe). KV store
backs feature flags, AI defaults/roles/privacy, UI defaults. DB-level
LIMIT/OFFSET pagination for prices/events.

Auth: login tokens (HMAC) + scoped/expiring API keys; org isolation enforced
in every collection reader/writer including entities and search
(IDOR-tested). `REQUIRE_AUTH=1` in prod.

AI: 19 data-driven presets; env discovery for every vendor key; encrypted
DB credentials (masked everywhere); shared chain builder (explicit →
use-case role → user → org → system → env fallbacks → enabled DB);
per-role routing; privacy policy with redaction; live test + discovery +
sync; inventory with source badges; usage/cost tracking; injection defense
on the evidence path. No vendor hardcoded; no key ever leaves the server.

Docs: server-rendered portal at `/docs` (Markdown sources + sanitizer +
search index), 36 Playwright screenshots with manifest, generated coverage
reports. Frontend: hash-routed views, contextual help, empty/error states,
EN/ID/AR with RTL, WIB display, light/dark/system + density/layout.

See MASTER_BUILD_SPEC.md (design), OPERATIONS.md (run), FINAL_AUDIT.md (proof).
