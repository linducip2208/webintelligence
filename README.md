# Web Intelligence Platform v1.0.0

Production-grade web-data intelligence: direct-first collection (Go),
browser fallback (Playwright/Python), proxy abstraction (own + Bright Data),
validation → normalization → MySQL → analytics/ML → Muse Spark 1.3 AI →
reports/alerts/dashboard. Deploys on aaPanel without Docker.

## Quick start (Windows dev / Linux same, minus service files)

```bat
cd source\python
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m pytest tests -q
venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Go collector:

```bat
cd source\go\collector
go test ./...
go build -o ..\..\..\build\linux\collector .\cmd\collector
```

Open http://127.0.0.1:8000/ for the dashboard (real data only).

## Deploy (aaPanel)

See `deploy/aaPanel/README.md` and `deploy/scripts/deploy_aapanel.sh`.
Nginx: `deploy/nginx/webintel.conf`. systemd units: `deploy/systemd/`.

## Live credentials required for

- Bright Data (`BRIGHTDATA_API_KEY`, `BRIGHTDATA_ZONE`) — adapter + `POST /api/v1/brightdata/test` work; live crawl tests skip without creds.
- Muse Spark 1.3 (`MUSE_SPARK_BASE_URL`, `MUSE_SPARK_API_KEY`) — provider + health endpoint work; live chat test requires creds.
- MySQL/Redis URLs for integration runs.

See `docs/MASTER_BUILD_SPEC.md` for the full architecture.
