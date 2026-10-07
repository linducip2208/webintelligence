---
title: Nginx & Reverse Proxy
description: HTTPS termination, subdirectory hosting and header hardening.
category: Deployment
order: 50
slug: deployment/nginx
language: en
shots: []
---

# Nginx & Reverse Proxy

> HTTPS termination, subdirectory hosting and header hardening.

HTTPS termination, subdirectory hosting and header hardening.

## Prerequisites

- Nginx installed
- The app listening on 127.0.0.1:8000
- TLS certificate (Let's Encrypt via aaPanel or certbot)

## Steps

### Step 1 — Install the site config

```powershell
Copy deploy/nginx/webintel.conf to the Nginx sites directory; adjust server_name.
```

**Expected:** nginx -t reports success.

### Step 2 — Proxy to uvicorn

```powershell
proxy_pass http://127.0.0.1:8000 with forwarded headers preserved.
```

**Expected:** The dashboard loads through the domain.

### Step 3 — Terminate HTTPS

```powershell
Listen 443 ssl; redirect 80 to 443; set HSTS=1 in app env.
```

**Expected:** http:// redirects; https:// serves with HSTS header.

### Step 4 — Support subdirectories

```powershell
If hosting under /intel/, set the proxy prefix and DOCS_BASE_URL for canonical links.
```

**Expected:** Docs canonical URLs use the public prefix.

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
- [MySQL](/docs/deployment/mysql)
