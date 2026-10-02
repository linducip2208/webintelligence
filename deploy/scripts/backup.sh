#!/usr/bin/env bash
# Backup: MySQL dump + config + runtime data. Run via cron on aaPanel.
set -euo pipefail
ROOT=/www/wwwroot/web-intelligence
OUT=$ROOT/runtime/backups/$(date +%F_%H%M)
mkdir -p "$OUT"
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
mysqldump --single-transaction "${DB_NAME:-webintel}" > "$OUT/db.sql" || echo "WARN: mysqldump failed"
tar -czf "$OUT/config.tar.gz" -C "$ROOT" .env deploy/nginx 2>/dev/null || true
tar -czf "$OUT/data.tar.gz" -C "$ROOT" data 2>/dev/null || true
find "$ROOT/runtime/backups" -maxdepth 1 -type d -mtime +14 -exec rm -rf {} + || true
echo "backup -> $OUT"
