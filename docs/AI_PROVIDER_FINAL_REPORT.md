# Web Intelligence — AI Provider Final Report

_Catalog: 19 presets, all adapter-backed. Inventory here: {'total': 2, 'configured': 1, 'connected': 0, 'failed': 0, 'disabled': 0}._

## Status model (honest, enforced)

- NOT CONFIGURED: no key saved and none in environment.
- CONFIGURED: credential present (database or environment).
- CONNECTED: a live test passed.
- FAILED: a live test failed (code kept, secret never kept).
- DISABLED: administratively off.
- Configuration alone is never displayed as Connected.

## Credential sources

- DATABASE: Fernet-encrypted `api_key_enc`, masked in every response.
- ENVIRONMENT: discovered from vendor key variables, never copied to the DB.
- LOCAL: Ollama without a key; models discovered from the daemon.
- Precedence: explicit request → user → org → system default → environment fallbacks → enabled database providers; per-role routing for research/summarization/classification/risk/report.

## Verified behaviors

- Listing/detail/test responses contain no key material (asserted).
- Live tests probe auth/discovery/model with latency; failures are structured codes, never tracebacks or secrets.
- Test All runs sequentially (rate-limit safe) with a summary.
- Empty chain answers 502 AI analysis is not configured.
- Fallback usage is reported (`fallbacks_tried`, `default_used`).
- Research analyze resolves explicit → role → cascade → fallbacks + DB.

## This environment

- Configured credentials: 1; connected: 0.
- No vendor keys present here — the UI shows the honest empty state.
