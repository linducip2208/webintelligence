# Web Intelligence — Security Audit

_Generated from live suite runs (app v2.14.0). UNVERIFIED means the control needs an environment this machine cannot provide — never a silent PASS._

| Control | Evidence | Result |
|---|---|---|
| RBAC roles/permissions | `tests/security/test_rbac.py` | PASS |
| Security headers, redaction, guards | `tests/security/test_hardening.py` | PASS |
| Auth/IDOR/isolation | `tests/security/test_security.py` | PASS |
| Search org isolation | `test_search_modes.py::test_org_isolation` + entity isolation | PASS |
| AI key masking / no-leak | `test_ai_registry.py` + `test_round3.py` masking assertions | PASS |
| No dead handlers/endpoints/routes | `test_frontend_audit.py` (479 fns, 345 calls) | PASS |
| Contract sync | `test_openapi_sync.py` | PASS |
| Version consistency | `test_version_consistency.py` | PASS |
| Secret scan (tree) | `scripts/audit/secret_scan.py` | PASS |

## Manually verified (code-read, this session)

| Control | Finding |
|---|---|
| SSRF guard | `core/ssrf.py`: scheme/host/DNS-rebinding/private-range checks; provider endpoints validated; loopback only for local presets or TRUSTED_EGRESS_CIDRS |
| Provider secrets | Fernet-encrypted at rest (`api_key_enc`); masked in every response; decrypted in memory only for live calls; scrubbed diagnose errors |
| Evidence deletion | no delete endpoint exists — nothing to audit |
| AI prompt injection | collected content wrapped as untrusted DATA (`ai/safety.py`), never as instructions |
| Rate limits | per-identity buckets, Redis-backed when available, 429 + Retry-After |
| Body limits | MAX_BODY_BYTES → 413 with request IDs |

## UNVERIFIED (needs credentials/services not present here)

- Live Bright Data crawl; live vendor AI chat (keys absent).
- MySQL-backed persistence runs (SQLite exercised instead).
- TLS-terminating HTTPS (deployment-time; HSTS opt-in verified in code).
