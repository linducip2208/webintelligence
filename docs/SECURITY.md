# Security (as implemented + tested)

- SSRF: Python `core/ssrf` + Go `internal/ssrf` (resolve-then-validate,
  loopback/private/link-local/metadata blocked, redirect recheck,
  `TRUSTED_EGRESS_CIDRS` allowlist). Tested incl. 169.254 + localhost.
- AuthN/Z: bcrypt passwords, HMAC login tokens, hashed-at-rest API keys with
  scopes/expiry/revocation/last-used; RBAC matrix; 401/403 enforced
  (middleware + handlers). Tested: bad login, bad/expired/revoked keys, IDOR.
- Tenant isolation: org filter on all collections + cross-org guards (404).
- Webhooks: HMAC-SHA256 signatures, 300s timestamp window, nonce dedupe,
  secrets encrypted at rest (Fernet when `CREDENTIALS_KEY` set).
- Injection: ORM-bound queries only (tested with SQLi payloads); UI escapes
  output; upload filenames sanitized; CSV capped 10k rows; bodies capped 10MB
  (413); rate limits per IP (429).
- Secrets: never in logs (redaction tested), never in API responses
  (key_hash/secret/api_key_enc stripped — tested), `.env` git-ignored.
- AI: external content sanitized + wrapped as untrusted DATA before providers.
- Management plane: every mutating endpoint audited (actor/action/ref);
  destructive ops require `configure`; custom org-scoped roles enforced in
  `_need`; membership changes guard self/last-owner; alert ack/resolve and
  dataset publish/import/archive are org-scoped (IDOR-tested).
- HTTP hardening: `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: same-origin`, `X-Frame-Options: SAMEORIGIN` on all
  responses; opt-in `Strict-Transport-Security` via `HSTS=1`. No strict CSP
  by design (dashboard uses inline handlers) — documented, not an oversight.
- AI provider keys + webhook secrets + connector secrets: Fernet-encrypted
  at rest, never returned by list/detail/test/discovery APIs, masked (`***`)
  in UI, scrubbed from error messages.

Production: set `REQUIRE_AUTH=1`, `SECRET_KEY`, `CREDENTIALS_KEY`,
`DATABASE_URL`, `REDIS_URL`. `/api/v1/system/doctor` reports posture.
