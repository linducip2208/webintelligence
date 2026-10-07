---
title: Windows Development
description: Venv to running server on Windows, including Laragon MySQL.
category: Deployment
order: 20
slug: deployment/windows
language: en
shots: []
---

# Windows Development

> Venv to running server on Windows, including Laragon MySQL.

Venv to running server on Windows, including Laragon MySQL.

## Prerequisites

- Python 3.12+
- MySQL via Laragon (or any MySQL 8.4)
- PowerShell

## Steps

### Step 1 — Create the database

```powershell
mysql -u root -e "CREATE DATABASE IF NOT EXISTS webintel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

**Expected:** Database webintel exists.

### Step 2 — Install dependencies

```powershell
cd source\python
pip install -r requirements.txt
pip install "bcrypt==4.0.1"
```

**Expected:** No install errors; pytest collects.

### Step 3 — Point at MySQL once

```powershell
setx DATABASE_URL "mysql+pymysql://webintel:PASSWORD@127.0.0.1:3306/webintel"
```

**Expected:** Reopen the terminal so the variable applies.

### Step 4 — Run the server

```powershell
cd source\python
python -m uvicorn app.main:app --port 8000
```

**Expected:** GET /readyz shows backend=mysql.

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
- [Linux Production](/docs/deployment/linux)
- [aaPanel Guide](/docs/deployment/aapanel)
- [Nginx & Reverse Proxy](/docs/deployment/nginx)
- [MySQL](/docs/deployment/mysql)
