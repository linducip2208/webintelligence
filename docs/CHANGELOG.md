# Changelog

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
