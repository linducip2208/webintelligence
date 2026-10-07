---
title: aaPanel Guide
description: Fourteen steps: website to verified dashboard behind HTTPS.
category: Deployment
order: 40
slug: deployment/aapanel
language: en
shots: []
---

# aaPanel Guide

> Fourteen steps: website to verified dashboard behind HTTPS.

Fourteen steps: website to verified dashboard behind HTTPS.

## Prerequisites

- aaPanel installed
- Nginx, MySQL 8.4 and Redis from the app store
- A domain with DNS pointed at the server

## Steps

### Step 1 — Create the website

```powershell
aaPanel > Website > Add site; note the document root.
```

**Expected:** The site serves a placeholder page over HTTP.

### Step 2 — Create the database

```powershell
aaPanel > Database > Add; create user webintel with a strong password.
```

**Expected:** Connection from the terminal succeeds.

### Step 3 — Configure Python

```powershell
aaPanel > App Store > Python: add project pointing at source/python with uvicorn app.main:app.
```

**Expected:** The project starts without tracebacks.

### Step 4 — Configure the Go collector

```powershell
Build on the server (go build) and register a supervisor/systemd entry.
```

**Expected:** Collector process answers its health check.

### Step 5 — Configure Redis

```powershell
Start Redis from the app store; set REDIS_URL in the project environment.
```

**Expected:** readyz lists redis up.

### Step 6 — Configure environment

```powershell
Set DATABASE_URL, SECRET_KEY, CREDENTIALS_KEY, REQUIRE_AUTH=1 in project env.
```

**Expected:** Unauthenticated API calls return 401.

### Step 7 — Configure Nginx

```powershell
Adapt deploy/nginx/webintel.conf; add the aaPanel site; reload nginx.
```

**Expected:** The app answers behind the domain.

### Step 8 — Configure the process manager

```powershell
Keep the Python project plus worker/browser/collector processes supervised.
```

**Expected:** All four show running after a reboot.

### Step 9 — Configure workers

```powershell
Ensure the worker tick runs (supervisor entry with TICK_SCHEDULES=1).
```

**Expected:** A test schedule fires on time.

### Step 10 — Configure HTTPS

```powershell
aaPanel > SSL > Let's Encrypt; enable Force HTTPS and HSTS=1.
```

**Expected:** https://domain/healthz returns ok.

### Step 11 — Start the application

```powershell
Start all supervised processes in order: mysql/redis, api, worker, collector.
```

**Expected:** No process exits in the first five minutes.

### Step 12 — Test /healthz

```powershell
curl https://domain/healthz
```

**Expected:** {"status":"ok"}

### Step 13 — Test /readyz

```powershell
curl https://domain/readyz
```

**Expected:** backend=mysql, all checks listed.

### Step 14 — Test the dashboard

```powershell
Open https://domain/ and sign in.
```

**Expected:** Dashboard loads with version footer and no console errors.

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
- [Nginx & Reverse Proxy](/docs/deployment/nginx)
- [MySQL](/docs/deployment/mysql)
