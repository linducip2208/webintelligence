---
title: External APIs
description: Scoped API keys for outside clients and HMAC-signed inbound ingestion.
category: Integrations
order: 40
slug: integrations/external-apis
language: en
shots: [34-external-apis.png, 28-api.png]
---

# External APIs

> Scoped API keys for outside clients and HMAC-signed inbound ingestion.

Outside clients authenticate with scoped keys; inbound events arrive HMAC-signed.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Outside-client integration with key management.](shot:34-external-apis.png)

![API keys and external integration endpoints.](shot:28-api.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/apikeys` | List Apikeys |
| `POST` | `/api/v1/apikeys` | Create Apikey |
| `POST` | `/api/v1/apikeys/{kid}/revoke` | Revoke Apikey |
| `POST` | `/api/v1/ingest/webhook` | Ingest Webhook |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/apikeys -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/apikeys", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/apikeys", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/apikeys -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#external-apis) — opens the live view in the application.


## Related

- [STIX 2.1](/docs/integrations/stix)
- [MISP](/docs/integrations/misp)
- [Security Tools](/docs/integrations/security-tools)
- [AI Overview](/docs/integrations/ai)
