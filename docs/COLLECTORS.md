# Collectors (as implemented)

## Paths
1. **Direct inline** (`services/pipeline.py::run_job` via `POST /jobs/{id}/run`):
   fetch → validate → normalize → quality → price extract → change detect →
   **recon enrichment** → alerts → cost → target learning. BROWSER/proxy legs
   return `deferred` for dedicated workers.
2. **Go collector** (`source/go/collector` → `POST /api/v1/results`):
   concurrent HTTP/API collection with retries, rate limits, pooling, SSRF
   guard (`internal/ssrf`), structured result contract `schema_version 1.0`.
3. **Python workers** (`app/workers.py`, browser `browser/worker.py`):
   Redis queue drain → pipeline → same results endpoint → DLQ on failure.
4. **Connectors** (`connectors/runners.py`): RSS / paginated REST / CSV,
   SSRF-guarded, 5MB cap, optional save to articles/datasets.

## Recon enrichment (`services/recon.py`, stdlib only)
Runs inside every inline job (bounded, best-effort, never raises):
- **DNS**: resolved IPs (cap 10) for the target host
- **TLS**: certificate subject/issuer/SAN/validity + correlation key
  (HTTPS only; plain HTTP recorded as no-TLS)
- **HTTP meta** from the fetched body: title, tech fingerprints
  (WordPress/jQuery/React/Next/Vue/Angular/Bootstrap/Cloudflare/…),
  internal/external link counts + domains, forms/scripts counts,
  `robots.txt` presence + sitemap hint (port-preserving URL)
- Snapshot stored on the target row + as an `evidence` record
  (`source=recon`, content hash), so every claim stays sourced.

## Scheduling & reliability (`services/scheduler.py`, `POST /worker/tick`)
once/interval/hourly/daily/weekly/cron/event triggers; next/last run,
retries, idempotency keys, lease heartbeats, DLQ (`webintel:queue:dlq`),
restart recovery (orphan leases requeued on boot).

## Safety
- SSRF guard on every fetch (loopback/private/link-local/metadata/DNS
  tricks blocked; `TRUSTED_EGRESS_CIDRS` allowlist; localhost only when an
  admin explicitly allows it, e.g. local Ollama or test stubs).
- No credential theft, no auth/CAPTCHA bypass, no exploitation — collection
  is read-only against public/authorized targets; robots.txt/ToS respected.
- Timeouts everywhere (fetch 30s, recon legs 5–8s), 10MB body cap,
  per-IP rate limits (429 + Retry-After).

## Browser (Playwright)
Pooled contexts (default 2), per-job timeout, media/font blocking,
session-per-job, metadata capture (status/final URL/size/ms),
graceful pool status at `GET /api/v1/browser/health`.
