---
title: Organizations & Branding
description: Isolate data per organization and apply white-label branding.
category: Administration
order: 30
slug: administration/organizations
language: en
shots: []
---

# Organizations & Branding

> Isolate data per organization and apply white-label branding.

Organizations isolate data and carry white-label branding.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/orgs` | List Orgs |
| `POST` | `/api/v1/orgs` | Create Org |
| `GET` | `/api/v1/orgs/{oid}/branding` | Get Branding |
| `PUT` | `/api/v1/orgs/{oid}/branding` | Set Branding |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/orgs -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/orgs", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/orgs", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/orgs -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#users) — opens the live view in the application.


## Related

- [Users & Roles](/docs/administration/users)
- [Roles & Permissions](/docs/administration/roles)
- [API Keys](/docs/administration/api-keys)
- [Settings Guide](/docs/settings)
- [Settings](/docs/administration/settings)
