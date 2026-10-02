# Troubleshooting & Runbook

| symptom | action |
|---|---|
| `/readyz` degraded | read per-check `detail` (database/redis/proxy/AI) |
| 401 everywhere | `REQUIRE_AUTH=1` without token/key; login again |
| 403 on writes | role/scopes/entitlement exceeded — check `/billing/usage` |
| 402 | quota exceeded — upgrade plan via `/billing/plan` (owner) |
| 429 | wait `Retry-After`; raise `RATE_LIMIT_*` if legitimate |
| jobs stuck queued | Redis down? collector running? DLQ depth? |
| no prices from Go jobs | collector ≥ body-shipping build? check result `content_b64` |
| webhook fails | `/webhooks/deliveries` shows attempts/errors; replay |
| AI errors | `/ai/health` per provider; fallback attempts logged in response |
| disk | `/system/doctor` disk check; retention runner; backup retention 14d |

Runbook (incident): status.sh → readyz → logs → DLQ → replay/ retry jobs →
restore from backup if data loss (BACKUP_RECOVERY.md).
