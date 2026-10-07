---
title: Redis
description: Queues and rate limits with Redis — and graceful behavior without it.
category: Deployment
order: 70
slug: deployment/redis
language: en
shots: []
---

# Redis

> Queues and rate limits with Redis — and graceful behavior without it.

Queues and rate limits with Redis — and graceful behavior without it.

## Prerequisites

- A host for Redis (aaPanel app store or standalone)

## Steps

### Step 1 — Start Redis

```powershell
Install and start; default 127.0.0.1:6379 is fine for single-host.
```

**Expected:** redis-cli ping returns PONG.

### Step 2 — Point the app

```powershell
REDIS_URL="redis://127.0.0.1:6379/0"
```

**Expected:** readyz lists redis up; rate limits share across processes.

### Step 3 — Know the fallback

```powershell
Without Redis, queues and buckets live in memory per process — fine for dev, wrong for replicas.
```

**Expected:** Single-process dev behaves identically.

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
