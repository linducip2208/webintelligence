# Web Intelligence Platform — MASTER BUILD SPEC
Version: 1.0.0 | Date: 2026-10-02 | Status: IMPLEMENTED

## 1. Product Vision
Production-grade web-data intelligence platform: collect public web data via
direct HTTP / official APIs / headless browser / own proxies / Bright Data,
validate → normalize → resolve entities → analytics/ML/AI → reports/alerts/
dashboard. Every metric real, every integration functional, cost-aware,
observable, secure, deployable on aaPanel (Linux, Nginx, systemd, no Docker).

Non-goals: no bypass of auth/CAPTCHA/access-controls; no fake dashboards;
no hardcoded providers; no Docker dependency.

## 2. Architecture
```
USER → NGINX/HTTPS → PYTHON/FastAPI → ORCHESTRATOR → REDIS
   → GO COLLECTOR (concurrent HTTP/API/proxy) ─┐
   → PYTHON WORKERS (browser/ETL/AI) ──────────┤
   → COLLECTION STRATEGY (DIRECT→API→BROWSER→OWN_PROXY→BRIGHT_DATA)
   → VALIDATION → NORMALIZATION → MYSQL → ANALYTICS/SEARCH
   → MUSE SPARK 1.3 (provider abstraction) → INTELLIGENCE → REPORTS/ALERTS → DASHBOARD
```
Rationale: Go = high-concurrency I/O collection. Python = API/UI/orchestration/
ETL/analytics/ML/AI/reports/alerts/scheduling/health. Redis = job queue, leases,
heartbeats, pub/sub, cache. MySQL 8.4 = system of record. Contracts versioned
in `contracts/`.

## 3. Python Responsibilities
FastAPI, UI/API, authN/Z, projects/targets, orchestration, DB logic, browser
jobs, ETL, analytics, ML, AI, reports, alerts, scheduling, health. Never imports
Go source. Location: `source/python/app/`.

## 4. Go Responsibilities
Queue consumption (Redis), concurrent HTTP/API/direct/proxy collection,
retries, timeouts, rate limiting, pooling, response+validation metadata,
structured results, metrics, graceful shutdown. No AI/ML/analytics.
Location: `source/go/collector/`. Binary: `build/linux/collector`.

## 5. Redis Architecture
DB0 queue (`webintel:queue:jobs`), DB1 leases/heartbeats
(`webintel:lease:{job}`, `webintel:worker:{id}:hb`), DB2 cache/pubsub
(`webintel:cache:*`, `webintel:events`). Streams or LIST+BRPOPLPUSH with
lease TTL 60s, heartbeat 15s, visibility-timeout recovery, DLQ
`webintel:queue:dlq`, idempotency keys `webintel:idem:{key}` TTL 24h.
Go uses `github.com/redis/go-redis/v9` (optional; falls back to polling-safe
client). Python uses `redis` package.

## 6. MySQL Architecture
MySQL 8.4, InnoDB, utf8mb4. All tables in §DB below with indexes; JSON only for
evidence/attributes/config; provenance columns everywhere
(`source_url, strategy, provider, collector_version, parser_version,
content_hash, retrieved_at`). Migrations: Alembic (`source/python/app/db/
migrations/`) + canonical SQL `source/python/app/db/schema.sql`.
Full-text indexes for search entities; foreign keys with RESTRICT; timestamps
`created_at/updated_at` UTC.

## 7. Playwright/Browser Architecture
Python `browser/` owns lifecycle: pool (default 2 contexts), per-job timeout,
strict CPU/RAM limits, block media/fonts by default, session-per-job,
HAR-less metadata capture (status, final URL, size, ms). Go `internal/browser`
only dispatches browser jobs to Python via Redis (`strategy=BROWSER`), never
drives CDP itself. Service: `webintel-browser.service`.

## 8. Direct HTTP/API Collection
Default path. Go `httpclient` (pooled, keep-alive, 30s default timeout,
max 10MB body, redirect ≤5, User-Agent rotation). Official-API jobs carry
`connector_id + auth ref`; secrets resolved server-side, never in queue payload.
Validation: status/class, content-type allowlist, min/max size, expected-fields
check by parser; HTTP 200 ≠ success.

## 9. Own Proxy Abstraction
`ProxyProvider` interface (`get_proxy/release_proxy/health_check/...`,
sticky sessions, rotation, metrics). `OwnProxyProvider`: static pool / HTTP(S)/
SOCKS5 from env/DB (`OWN_PROXY_URL(S)`, `proxy_pools/endpoints` tables).
Never assumes aaPanel host is residential.

## 10. Bright Data Integration
`BrightDataProvider` implements same interface + scraper/crawl/structured-data
adapter (`collectors/brightdata.py`, Go `internal/proxy/brightdata.go`).
Config from env/DB: `BRIGHTDATA_API_KEY, BRIGHTDATA_ZONE, BRIGHTDATA_ENDPOINT`.
Endpoints: test-connection, health, usage, errors surfaced in UI. No hardcode.
Without creds: adapter + validation + skipped-live-tests; documented.

## 11. Collection Decision Engine
`services/decision.py` (`CollectionDecisionEngine`). Escalation:
DIRECT/API → validate → BROWSER (if JS/render needed) → OWN_PROXY → BRIGHT_DATA
→ failure diagnostics. Inputs: target profile, history, HTTP status/timeout/
redirects/content-type/size, parser success/completeness, rate-limit signals,
latency, cost, geo/browser requirements, provider health, policy
(`collection_policy` per project: max_cost_per_job, allow_browser/proxy/
brightdata, geo). Output: ordered plan + reasons. HTTP 200 never auto-success.

## 12. Target Intelligence
`services/targets.py`. Profile per target: domain/URL/source-type/country/
language/preferred-strategy/attempts/success/fail/avg-latency/avg-cost/
last-success/fail/parser+schema versions. `record_attempt()` updates EWMA;
`preferred_strategy()` learns best recent strategy. Respects robots/ToS; no
control bypass.

## 13. Raw Data Layer
`raw_documents`: source/URL/retrieved_at/strategy/provider/collector+parser
versions/hash/size/status/body-ref. Body stored in `data/raw/{hash}` if
>0 bytes and allowed type; dedupe by `(url, content_hash)`; history preserved.

## 14. Normalization
`services/normalize.py`: products/companies/prices/reviews/articles/offers/
websites/events/search-results → `normalized_entities` + typed tables, each row
with provenance (`raw_document_id`, parser/schema versions). Idempotent
upserts.

## 15. Entity Resolution
`services/entity_resolution.py`: exact → normalized-string → domain/identifiers/
URL/attributes → fuzzy (ratio ≥0.87 auto-link, 0.70–0.87 needs review, else new)
→ optional AI assist. `entity_links` with confidence; never silent merge;
`needs_review` queue.

## 16. Price Intelligence
Prices: price/currency/discount/availability/seller/variant/observed_at.
History, change detection, volatility (stdev/mean), competitor comparison,
alerts (`price_drop_pct`, `back_in_stock`).

## 17. Competitor Intelligence
Track products/prices/offers/content/announcements/launches/reviews/changes;
evidence-backed compare (`intelligence/competitors.py`) — every claim cites
`raw_document_id`.

## 18. Market Intelligence
Category/price trends, review volume, competitor movement, emerging topics
(simple TF over titles), historical windows (`analytics/trends.py`).

## 19. Review Intelligence
Rating/text/date/product/language/topics/sentiment (lexicon + optional AI)/
complaint & praise themes (phrase frequency).

## 20. News Intelligence
Article/publisher/date/title/summary/entities/topics/URL; monitoring +
extractive summary (first 2 sentences) without AI; AI summary only on evidence
selection.

## 21. Website Change Detection
`services/change.py`: hash + field-level compare → NEW/CHANGED/REMOVED/
UNCHANGED; diff stored in `changes`.

## 22. Scheduling
`services/scheduler.py` + `schedules` table: once/interval/hourly/daily/weekly/
cron/event-triggered; next_run/last_run/status/duration/retries/error/cost.
In-process APScheduler-compatible loop; systemd worker runs it.

## 23. Alerts
Rules: price_changed/new_product/unavailable/competitor_change/site_change/
new_article/anomaly/collection_failure/quality_degradation. Channels: in-app
(table), email (SMTP env), webhook (HMAC-signed POST). `alerts/` module.

## 24. Analytics
`analytics/`: descriptive, time-series, price, competitor compare, source
compare, anomaly (z-score ≥3), correlation (pearson), clustering (1-D k-means
k=2 helper). Pure-python, no numpy required.

## 25. ML
`analytics/ml.py`: forecast (EWMA/linear), anomaly, classification (naive
threshold), clustering, entity-match score, sentiment/topic helpers; registry
`ml_models` with version+metrics. scikit-learn optional, never required.

## 26. Muse Spark 1.3 AI Integration
Via `AIProvider` abstraction; model id `muse-spark-1.3` (configurable).
Pipeline: raw → parse → normalize → dedupe → aggregate → select evidence →
AI. Tasks: summarize/compare/explain/detect/generate/answer/investigate-plan/
structured intel. Responses store `evidence_ids`; UI renders citations.

## 27. AI Provider Abstraction
`ai/base.py`: `AIProvider.chat/structured_output/stream/health_check/
list_models/usage/cost_estimate`. Registry `ai/registry.py`. Providers:
`muse_provider.py` (OpenAI-compatible `/v1/chat/completions`, works for
Muse Spark 1.3 endpoint), `openai_compat.py` generic. DB: `ai_providers,
ai_models, ai_usage`. Creds encrypted (Fernet, `CREDENTIALS_KEY`).

## 28. Cost Tracking
`services/cost.py`: collection/proxy/brightdata/browser/AI-tokens/report/
project costs; estimate vs actual; cost per success/1k records; budgets
(`budgets` in project config) enforced pre-dispatch.

## 29. Search
`search/service.py`: MySQL FULLTEXT over projects/targets/companies/products/
articles/reviews/documents/reports/insights; single `search(query, scope)`
API; pagination.

## 30. Semantic Search Abstraction
`search/embeddings.py` (`EmbeddingProvider`) + `search/vector_store.py`
(`VectorStore`); default `NoopEmbedding`/`MySQLVectorStore` (holds schema,
cosine in python); Pinecone/Milvus/Qdrant adapters addable without logic
change. MySQL remains primary.

## 31. Report Builder
`reports/builder.py`: market/competitor/product/price/review/site/executive
reports; outputs web/PDF (reportlab optional → fallback HTML)/CSV/JSON/XLSX
(openpyxl optional → fallback CSV). Every report: methodology/coverage/
timestamps/evidence/charts(tables+SVG)/AI-analysis/limitations.

## 32. Dashboard
`api/dashboard.py` aggregates only real DB/Redis data: active jobs,
success/fail, workers, target/provider health, recent changes, price moves,
alerts, AI insights, quality, costs. Empty-state when no data — never fake.

## 33. Admin
Routes under `/api/v1/*` + static UI `app/static/` (vanilla JS, no build):
dashboard/projects/targets/sources/connectors/jobs/workers/proxies/brightdata/
browser/quality/entities/products/prices/reviews/news/analytics/ml/ai/reports/
alerts/schedules/health/logs/settings. Each list: search/filter/pagination/
sort/validation/errors/empty/loading; audit trail on mutations.

## 34. System Health
`services/health.py`: API/worker/browser/collector/redis/mysql/proxy/brightdata/
AI checks → `system_health`; UI + `/healthz` + `/readyz`.

## 35. Observability
Structlog-style JSON logs (`core/logging.py`) with trace/job/target/strategy/
provider/worker/timestamps/duration/status. Metrics (`core/metrics.py`):
jobs_total/success/failed/latency/queue_depth/parser/proxy/provider failures/
AI requests/tokens/cost. `/metrics` Prometheus text.

## 36. Security
bcrypt passwords, session+JWT API tokens, Fernet secret encryption, log
redaction, Pydantic validation, SSRF guard (`core/ssrf.py`: blocks localhost/
private/loopback/link-local/metadata IP + dangerous schemes; allowlist via
`TRUSTED_EGRESS_CIDRS`), URL validation, rate limits, audit logs.

## 37. Reliability
Retry exp-backoff+jitter, circuit breaker (`core/reliability.py`), DLQ,
idempotency keys, graceful shutdown, worker heartbeat, Redis leases, dedupe,
restart recovery (requeue orphan leases on boot).

## 38. Repository Structure
As created (see README). Source vs build separated:
`source/go/collector → build/linux/collector`; python runs from source via venv.

## 39. aaPanel Deployment
Prod root `/www/wwwroot/web-intelligence`. Python `python/venv`,
Go `collector/webintel-collector`, runtime `runtime/logs|cache`.
systemd: webintel-api/worker/browser/collector. Nginx HTTPS → 127.0.0.1:8000.
Go not public. Scripts in `deploy/scripts/`, docs `deploy/aaPanel/README.md`.

## 40. Testing
Unit (parsers/validators/strategy/cost/proxy/URL), integration (mysql/redis/
go-python/brightdata/AI — live-gated), E2E (project→…→alert), load
(100 conc/1k/10k queued/restart recovery), security (SSRF/auth/secrets/
injection/URL/size). `pytest` + `go test ./...`.

## 41. Acceptance Criteria
All §FINAL ACCEPTANCE checks green; no dead routes/menu; no placeholders;
README + this spec current.
