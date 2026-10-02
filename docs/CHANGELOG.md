# Changelog

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
