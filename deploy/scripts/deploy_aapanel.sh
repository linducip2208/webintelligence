#!/usr/bin/env bash
set -euo pipefail
# aaPanel deploy: Ubuntu/Debian. Run as root.
ROOT=/www/wwwroot/web-intelligence
python3 -m venv $ROOT/source/python/venv
$ROOT/source/python/venv/bin/pip install -r $ROOT/source/python/requirements.txt
mkdir -p $ROOT/collector $ROOT/runtime/logs $ROOT/runtime/cache $ROOT/data/raw
(cd $ROOT/source/go/collector && go build -o $ROOT/collector/webintel-collector ./cmd/collector)
cp deploy/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now webintel-api webintel-collector webintel-worker webintel-browser
echo OK
