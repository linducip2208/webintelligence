---
title: MySQL
description: Create the database, wire DATABASE_URL, and understand write-through fallback.
category: Deployment
order: 60
slug: deployment/mysql
language: en
shots: []
---

# MySQL

> Create the database, wire DATABASE_URL, and understand write-through fallback.

Create the database, wire DATABASE_URL, and understand write-through fallback.

## Prerequisites

- MySQL 8.4 reachable
- Root access once

## Steps

### Step 1 — Create database and user

```powershell
CREATE DATABASE IF NOT EXISTS webintel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'webintel'@'%' IDENTIFIED BY 'STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON webintel.* TO 'webintel'@'%';
FLUSH PRIVILEGES;
```

**Expected:** Login as webintel works.

### Step 2 — Wire the app

```powershell
DATABASE_URL="mysql+pymysql://webintel:STRONG_PASSWORD@127.0.0.1:3306/webintel"
```

**Expected:** GET /readyz reports backend=mysql.

### Step 3 — Understand fallback

```powershell
Without MySQL the app writes to DATA_DIR/webintel.db (SQLite), then memory — check readyz after any move.
```

**Expected:** You can state which backend is active right now.

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
