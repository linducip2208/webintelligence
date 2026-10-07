---
title: Linux Production
description: Service units for API, worker, browser and collector.
category: Deployment
order: 30
slug: deployment/linux
language: en
shots: []
---

# Linux Production

> Service units for API, worker, browser and collector.

Service units for API, worker, browser and collector.

## Prerequisites

- Ubuntu/Debian host
- Python 3.12+
- MySQL 8.4
- systemd

## Steps

### Step 1 — Create a service user

```powershell
sudo useradd -r -m webintel
```

**Expected:** id webintel succeeds.

### Step 2 — Install the app under /opt/webintel

```powershell
copy the repository; python3 -m venv venv; venv/bin/pip install -r source/python/requirements.txt
```

**Expected:** venv/bin/python -m pytest source/python/tests -q passes.

### Step 3 — Install systemd units

```powershell
copy deploy/systemd/*.service to /etc/systemd/system; systemctl daemon-reload
```

**Expected:** systemctl status webintel-api shows active.

### Step 4 — Enable the worker tick

```powershell
TICK_SCHEDULES=1 in the worker unit; systemctl enable --now webintel-worker
```

**Expected:** Schedules execute on time.

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
- [aaPanel Guide](/docs/deployment/aapanel)
- [Nginx & Reverse Proxy](/docs/deployment/nginx)
- [MySQL](/docs/deployment/mysql)
