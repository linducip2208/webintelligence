---
title: System Health
description: Readiness, the system doctor, metrics and what each signal means.
category: Administration
order: 70
slug: administration/system-health
language: en
shots: [27-system-health.png]
---

# System Health

> Readiness, the system doctor, metrics and what each signal means.

Readiness, the system doctor and metrics — and what each check means for operators.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![System health with readiness and the system doctor.](shot:27-system-health.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/operations` | List Operations |
| `GET` | `/api/v1/system/doctor` | System Doctor |
| `GET` | `/api/version` | Api Version |
| `GET` | `/healthz` | Healthz |
| `GET` | `/metrics` | Metrics |
| `GET` | `/readyz` | Readyz |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/system/doctor -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/system/doctor", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/system/doctor", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/search -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#health) — opens the live view in the application.


## Related

- [Users & Roles](/docs/administration/users)
- [Roles & Permissions](/docs/administration/roles)
- [Organizations & Branding](/docs/administration/organizations)
- [API Keys](/docs/administration/api-keys)
- [Settings Guide](/docs/settings)
