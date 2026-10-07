---
title: Outbound Webhooks
description: Deliver events to your systems; inspect deliveries and replay failures.
category: Monitoring
order: 40
slug: monitoring/webhooks
language: en
shots: []
---

# Outbound Webhooks

> Deliver events to your systems; inspect deliveries and replay failures.

Outbound webhooks deliver events to your systems with delivery logs and replay for failures.

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
| `GET` | `/api/v1/webhooks` | List Webhooks |
| `POST` | `/api/v1/webhooks` | Create Webhook |
| `GET` | `/api/v1/webhooks/deliveries` | Webhook Deliveries |
| `POST` | `/api/v1/webhooks/deliveries/{did}/replay` | Webhook Replay |
| `GET` | `/api/v1/webhooks/{wid}` | Get Webhook |
| `PUT` | `/api/v1/webhooks/{wid}` | Update Webhook |
| `DELETE` | `/api/v1/webhooks/{wid}` | Delete Webhook |
| `POST` | `/api/v1/webhooks/{wid}/disable` | Disable Webhook |
| `POST` | `/api/v1/webhooks/{wid}/enable` | Enable Webhook |
| `POST` | `/api/v1/webhooks/{wid}/test` | Webhook Test |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/webhooks -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/webhooks", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/webhooks", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/webhooks -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#webhooks) — opens the live view in the application.


## Related

- [Watchlists](/docs/monitoring/watchlists)
- [Alerts](/docs/monitoring/alerts)
- [Workflows](/docs/monitoring/workflows)
