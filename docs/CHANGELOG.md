# Changelog

## v2.13.0 — intel interchange, hardening, ops
- STIX 2.1 bundle export/validate/import + MISP event export/import
- Pivot transformations (8) + global timeline + graph node/edge listings
- Recon attack-surface: RDAP/WHOIS/reverse-DNS, security headers capture,
  deep scan profile; scan profiles quick/standard/deep
- Collector registry (/collectors) with live health + queue depth
- Granular RBAC names (40+, mapped, backward-compatible), auth login/logout,
  admin password reset (shown once), login throttle 10/min + failed-login audit
- Webhook channels generic/slack/discord; portable SQL backup download
- Mobile off-canvas navigation E2E; security headers middleware;
  Windows .js MIME fix (found by E2E)
- Redis RESP2 compat (real queue/rate-limits on old servers)
- Go tests + vet green; pip-audit clean

## v2.12.0 — management plane + investigations + intel engines
- Full management CRUD: projects/targets/jobs/schedules/alerts/workflows/
  webhooks/connectors/datasets/documents detail pages, bulk ops, CSV export
- Investigations + cases (notes/tasks/members/links/status lifecycles)
- Findings severity/status/priority + triage + bulk; explainable risk engine
- Recon enrichment (DNS/TLS/tech/robots) in every job + infra-correlation
  candidates as reviewable findings
- Custom org-scoped roles (builtin matrix untouched); users disable/enable
- Audit trail on all mutations; IDOR org-scope fixes; security headers;
  Redis RESP2 compat (real queue/rate-limits on old servers)
- Settings area (12 groups), verticals UI, retention/SLA/billing wiring
- Admin UI split to static/js (app.js utils + views.js); 38 views verified
  in Chromium with zero console errors
- 178 versioned API paths; docs/DATA_MODEL.md, docs/COLLECTORS.md,
  docs/WORKFLOWS.md

## v2.11.0
- Dataset versioning fixed (per-dataset numbering; was global)
- Hermetic test isolation (autouse backend flush)
- Maintenance windows + SLA + incidents
- Workflow pause/version/idempotent-retry/cancel
- Connector health persisted, config secrets encrypted
- Research compare + markdown export, report markdown
- Dataset diff/rollback, target test-connection, watchlist evaluation
- Entity aliases, search facets, review queue, lineage, graph path
- 143 API paths, 111 tests green

## v2.10.0
- Redis-LIVE proofs (real server, not assumed)
- Stale-DB auto-migration healing test
- Real Chromium UI E2E (live numbers rendered)
- JS syntax + UI↔OpenAPI consistency gates
- Go benchmarks recorded (289ns / 349ns per op)

## v2.9.0
- APP_ENV production fail-closed (503 envelope, readyz explains, proven)
- Consistent error envelope + request IDs everywhere
- Layered rate limits (7 cost classes × identity, Redis-backed, Retry-After)
- Adversarial SSRF hardening both languages (numeric/IP tricks, DNS-safe)
- Resource-aware RBAC on all mutating routes + negative tests
- Commercial entitlements enforced (plans, quotas, model allowlist, 402)
- Executive dashboard, light mode, backup/restore round-trip test

## v2.8.0
- APP_ENV modes + production fail-closed DB (proven by tests)
- Consistent error envelope `{error:{code,message,request_id}}`
- Layered rate limits (cost classes × identity, Redis-backed, Retry-After)
- Adversarial SSRF hardening (both languages, DNS-safe)
- Resource-aware RBAC on all mutating endpoints + negative tests
- Commercial entitlements enforced server-side (402 quotas)
- Executive dashboard, light mode, toasts
- Backup/restore round-trip test

## v2.6.0
- Real connector execution (RSS/REST paginated/CSV) + test/execute endpoints
- Review queue, lineage explorer, graph shortest-path
- Feature flags (global/org/user), retention runner, PII detect/mask
- System doctor, version endpoint, webintel CLI
- Measured load: 500 req, 363rps, p95 72ms, 0 errors
- Docs: ARCHITECTURE, SECURITY, OPERATIONS, CHANGELOG

## v2.5.0
- Multi-vendor AI (OpenAI/Anthropic/Google/Ollama/Muse/DB), fallback chain,
  usage tracking, prompt registry, injection defense

## v2.4.0
- Go SSRF guard, BLPOP fix, body shipping + extraction-on-ingest,
  live full-chain (MiniRedis + uvicorn + Go binary) incl. restart recovery,
  real Chromium render test, alert ack/resolve, dataset import

## v2.3.0
- Router split, Fernet secrets, DB AI providers, semantic search,
  DB pagination, browser reuse, RUNNING state, reviews, OPERATIONS.md

## v2.1.0 – v2.2.0
- Persistence layer, org isolation, HMAC ingest, rate limits, mega-E2E,
  analytics/intel/graph/evidence/research/watchlists/workflows/datasets
