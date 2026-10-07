---
title: Playwright & Browser Pool
description: Two-context headless pool, per-job timeouts, media blocking.
category: Deployment
order: 80
slug: deployment/playwright
language: en
shots: []
---

# Playwright & Browser Pool

> Two-context headless pool, per-job timeouts, media blocking.

Two-context headless pool, per-job timeouts, media blocking.

## Prerequisites

- Python environment with requirements installed
- Disk space for Chromium

## Steps

### Step 1 — Install the browser

```powershell
python -m playwright install chromium
```

**Expected:** The browser binary downloads cleanly.

### Step 2 — Check the pool

```powershell
GET /api/v1/browser/health
```

**Expected:** Status up with two contexts and per-job timeout listed.

### Step 3 — Tune blocking

```powershell
Media and font blocking are on by default; relax only for evidence captures that need pixels.
```

**Expected:** Renders stay fast without losing needed detail.

## Verification

- `GET /healthz` returns ok; `GET /readyz` details every backend.
- `GET /api/v1/system/doctor` is green.
- The dashboard loads with the version footer.

## Troubleshooting

- Backend shows sqlite: DATABASE_URL never reached the server process.
- Port in use: an old server is still running — stop it first.
- bcrypt crash: pin `bcrypt==4.0.1`.
- Full catalog: [Common Errors](/docs/troubleshooting/common-errors).

## Related

- [Requirements](/docs/deployment/requirements)
- [Windows Development](/docs/deployment/windows)
- [Linux Production](/docs/deployment/linux)
- [aaPanel Guide](/docs/deployment/aapanel)
- [Nginx & Reverse Proxy](/docs/deployment/nginx)
