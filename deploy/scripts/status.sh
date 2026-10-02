#!/usr/bin/env bash
# Status + health of all services and endpoints.
set -u
for s in webintel-api webintel-worker webintel-browser webintel-collector; do
  printf "%-22s %s\n" "$s" "$(systemctl is-active $s 2>/dev/null || echo unknown)"
done
curl -sf http://127.0.0.1:8000/healthz && echo " api: ok" || echo " api: FAIL"
curl -sf http://127.0.0.1:8000/readyz || echo " readyz: FAIL"
