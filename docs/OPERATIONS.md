# Operations — backup, recovery, troubleshooting (matches actual repo layout)

## Layout (aaPanel)
`/www/wwwroot/web-intelligence/` ← repo root.
- `source/python/` app (venv: `source/python/venv`), `build/linux/collector` → `collector/webintel-collector`
- `runtime/logs`, `runtime/cache`, `data/` (SQLite fallback + raw bodies + vectors.json)

## Services
`webintel-api` (uvicorn :8000), `webintel-worker` (`python -m app.workers`),
`webintel-browser` (`python -m app.browser.worker`), `webintel-collector` (Go).
Nginx HTTPS → 127.0.0.1:8000 (see `deploy/nginx/webintel.conf`).

## Scripts (`deploy/scripts/`, `chmod +x`)
| script | purpose |
|---|---|
| `deploy_aapanel.sh` | full install: venv, deps, Go build, systemd enable |
| `backup.sh` | `runtime/backups/<date>/db.sql + config.tar.gz + data.tar.gz`, 14-day retention |
| `restore.sh <dir>` | restore DB + config, restart services |
| `status.sh` | service states + `/healthz` + `/readyz` |

## Environment
Copy `.env.example` → `.env`. Required in prod: `SECRET_KEY`,
`REQUIRE_AUTH=1`, `DATABASE_URL` (MySQL 8.4), `REDIS_URL`.
Optional: `BRIGHTDATA_*`, `MUSE_SPARK_*`, `SMTP_*`, `ALERT_WEBHOOK_URL`,
`WEBHOOK_INGEST_SECRET`, `CREDENTIALS_KEY` (enables Fernet secret encryption;
without it secrets store as `plain:` + warning log), `OWN_PROXY_URLS`,
`TRUSTED_EGRESS_CIDRS`, `RATE_LIMIT_PER_MIN` (default 240), `MAX_BODY_BYTES`.

## Migrations
`cd source/python && python -m app.db.migrations.env` (create_all + additive
column migration). Schema also verified by `tests/integration/test_db_live.py`.

## Dumb-but-important notes
- Persistence order: MySQL → `DATA_DIR/webintel.db` (SQLite) → memory.
  Tests always use in-memory (conftest).
- Audit hot window: last 5000 entries in memory; full history in DB.
- Webhook nonce window: 300s, 10k nonce cap.
- Browser launches once per worker process and is reused.

## Troubleshooting
| symptom | check |
|---|---|
| `/readyz` degraded | per-check detail names the backend (redis/mysql/proxy/AI) |
| 429s | `RATE_LIMIT_PER_MIN` / shared egress IP |
| 413 | `MAX_BODY_BYTES` |
| mirror failures | stderr `repo-mirror-failed` lines include table + SQL error |
| collector idle | Redis reachable? `QUEUE` name match? API `/api/v1/results` reachable? |
