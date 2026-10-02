# Universal Intelligence Platform v2.0.0

DATA → INFORMATION → KNOWLEDGE → EVIDENCE → INTELLIGENCE → DECISION SUPPORT.

Web/API/document collection (Go engine + Playwright), extraction →
normalization → quality → entity resolution → dedup → temporal snapshots →
change/event detection → knowledge graph → evidence-grounded claims →
research runs → findings → feed → watchlists → alerts → workflows →
datasets → webhooks. AI via provider abstraction (Muse Spark 1.3 default).
MySQL 8.4 + Redis. aaPanel-ready, no Docker.

Persistence is write-through: every mutation commits to MySQL when
reachable, else a SQLite file (`DATA_DIR/webintel.db`), else memory — and
hydrates on boot, so state survives restarts. Additive auto-migration heals
stale dev databases. Tests force in-memory via conftest.

Security: SSRF guard + trusted-egress allowlist, token + scoped/expiring
API-key auth, org isolation on every collection (IDOR-tested), HMAC webhook
ingestion with replay window, per-IP rate limits (429), body-size guard
(413), secret-redacted logs. Set `REQUIRE_AUTH=1` in production.

API surface: 102 versioned paths under `/api/v1` (see `contracts/openapi/openapi.json`):
orgs, roles, memberships, apikeys, projects, targets, jobs, results,
prices, changes, articles, search (+semantic), analytics, intel (compare/reviews/news),
entities, costs, ml (+predict), alerts (+check/send), reports (+export), search, ask, feed (+subscriptions),
opportunities, research, watchlists, workflows, datasets, connectors, documents (+reviews),
webhooks (+ingest/deliveries), i18n, audit, dashboard, health, metrics, browser.

## Quick start (Windows dev / Linux same, minus service files)

```bat
cd source\python
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m pytest tests -q
venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Go collector:

```bat
cd source\go\collector
go test ./...
go build -o ..\..\..\build\linux\collector .\cmd\collector
```

Open http://127.0.0.1:8000/ for the dashboard (real data only).

## Deploy (aaPanel)

See `deploy/aaPanel/README.md` and `deploy/scripts/deploy_aapanel.sh`.
Nginx: `deploy/nginx/webintel.conf`. systemd units: `deploy/systemd/`.

## Live credentials required for

- Bright Data (`BRIGHTDATA_API_KEY`, `BRIGHTDATA_ZONE`) — adapter + `POST /api/v1/brightdata/test` work; live crawl tests skip without creds.
- Muse Spark 1.3 (`MUSE_SPARK_BASE_URL`, `MUSE_SPARK_API_KEY`) — provider + health endpoint work; live chat test requires creds.
- MySQL/Redis URLs for integration runs.

See `docs/MASTER_BUILD_SPEC.md` for the full architecture.
