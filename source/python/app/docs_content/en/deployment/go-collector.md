---
title: Go Collector
description: Build, configure and run the concurrent collection engine.
category: Deployment
order: 90
slug: deployment/go-collector
language: en
shots: []
---

# Go Collector

> Build, configure and run the concurrent collection engine.

Build, configure and run the concurrent collection engine.

## Prerequisites

- Go 1.21+

## Steps

### Step 1 — Test

```powershell
cd source/go/collector
go test ./...
```

**Expected:** All packages pass.

### Step 2 — Build

```powershell
go build -o ../../../build/linux/collector ./cmd/collector
```

**Expected:** The binary appears under build/linux.

### Step 3 — Run supervised

```powershell
Register under systemd/supervisor alongside the API and worker.
```

**Expected:** Results arrive via POST /api/v1/results.

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
