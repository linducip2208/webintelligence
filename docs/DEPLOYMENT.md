# Deployment (aaPanel, no Docker)

Target: Ubuntu/Debian + aaPanel. See `deploy/aaPanel/README.md` (steps),
`deploy/scripts/deploy_aapanel.sh` (install), `deploy/nginx/webintel.conf`.

Services (`deploy/systemd/`): webintel-api (uvicorn :8000), webintel-worker
(`python -m app.workers`), webintel-browser (`python -m app.browser.worker`),
webintel-collector (Go binary `collector/webintel-collector`).

Verify after deploy: `bash deploy/scripts/status.sh` (services + /healthz +
/readyz). Logs: `runtime/logs` (configure uvicorn `--log-config` as needed).
Restart: `systemctl restart webintel-*`. Upgrade: pull, rebuild Go binary,
`pip install -r requirements.txt`, restart. Rollback: previous git SHA +
rebuild (stateless code; data stays in MySQL).
