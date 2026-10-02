#!/usr/bin/env bash
# Restore: DB dump + config. Usage: restore.sh <backup-dir>
set -euo pipefail
ROOT=/www/wwwroot/web-intelligence
IN="${1:?usage: restore.sh <backup-dir>}"
if [ -f "$ROOT/.env" ]; then set -a; . "$ROOT/.env"; set +a; fi
mysql "${DB_NAME:-webintel}" < "$IN/db.sql"
tar -xzf "$IN/config.tar.gz" -C "$ROOT"
systemctl restart webintel-api webintel-worker webintel-collector webintel-browser
echo "restored from $IN"
