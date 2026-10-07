---
title: Settings
description: General, security, collectors, scheduler, notifications, storage, flags and billing.
category: Administration
order: 50
slug: administration/settings
language: en
shots: [26-settings.png]
---

# Settings

> General, security, collectors, scheduler, notifications, storage, flags and billing.

One settings surface for general, security, collectors, scheduler, notifications, AI, storage, flags and billing.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Administration settings: security, collectors, scheduler and storage.](shot:26-settings.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/admin/backup` | Admin Backup |
| `GET` | `/api/v1/admin/data-quality` | Data Quality |
| `POST` | `/api/v1/admin/data-quality/fix` | Data Quality Fix |
| `POST` | `/api/v1/admin/demo/purge` | Demo Purge |
| `POST` | `/api/v1/admin/demo/seed` | Demo Seed |
| `GET` | `/api/v1/admin/first-run` | First Run State |
| `POST` | `/api/v1/admin/retention/run` | Retention Run |
| `POST` | `/api/v1/billing/plan` | Billing Set Plan |
| `GET` | `/api/v1/billing/plans` | Billing Plans |
| `GET` | `/api/v1/billing/usage` | Billing Usage |
| `POST` | `/api/v1/costs/budget` | Set Budget |
| `GET` | `/api/v1/costs/budget/check` | Budget Check |
| `GET` | `/api/v1/costs/summary` | Costs Summary |
| `GET` | `/api/v1/flags` | Flags List |
| `POST` | `/api/v1/flags` | Flags Set |
| `GET` | `/api/v1/settings/defaults` | Settings Defaults Get |
| `PATCH` | `/api/v1/settings/defaults` | Settings Defaults Patch |
| `POST` | `/api/v1/settings/reset` | Settings Reset |
| `GET` | `/api/v1/settings/system` | Settings System |
| `GET` | `/api/v1/verticals` | List Verticals |
| `GET` | `/api/v1/verticals/{name}` | Get Vertical |
| `POST` | `/api/v1/verticals/{name}/apply` | Apply Vertical |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/dashboard -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/dashboard", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/dashboard", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/admin/retention/run -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Verification

- The new or changed record is visible in the list view.
- `GET /api/v1/audit?size=20` shows the action with your identity.
- Related views (graph, timeline, feed) reflect the change.

## Troubleshooting

- Empty list: run collection first — the platform shows real data only.
- 401: sign in or supply a key; see [Authentication](/docs/security/authentication).
- 429: slow down; see [Rate Limits](/docs/api/rate-limits).

> **Try it:** [Open in application](/#settings) — opens the live view in the application.


## Related

- [Users & Roles](/docs/administration/users)
- [Roles & Permissions](/docs/administration/roles)
- [Organizations & Branding](/docs/administration/organizations)
- [API Keys](/docs/administration/api-keys)
- [Settings Guide](/docs/settings)
