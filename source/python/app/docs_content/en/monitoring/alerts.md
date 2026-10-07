---
title: Alerts
description: Acknowledge, resolve, bulk-triage and escalate alerts into incidents.
category: Monitoring
order: 20
slug: monitoring/alerts
language: en
shots: [21-alert.png]
---

# Alerts

> Acknowledge, resolve, bulk-triage and escalate alerts into incidents.

Alerts queue human attention with severity and a full acknowledge/resolve lifecycle, including bulk operations and incidents.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Alert queue with acknowledge and resolve actions.](shot:21-alert.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/alerts` | List Alerts |
| `POST` | `/api/v1/alerts` | Create Alert |
| `POST` | `/api/v1/alerts/bulk` | Alerts Bulk |
| `POST` | `/api/v1/alerts/check` | Alert Check |
| `GET` | `/api/v1/alerts/incidents` | Alert Incidents |
| `GET` | `/api/v1/alerts/{alert_id}` | Get Alert |
| `POST` | `/api/v1/alerts/{alert_id}/ack` | Alert Ack |
| `POST` | `/api/v1/alerts/{alert_id}/resolve` | Alert Resolve |
| `POST` | `/api/v1/alerts/{alert_id}/send` | Alert Send |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/alerts -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/alerts", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/alerts", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/alerts -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#alerts) — opens the live view in the application.


## Related

- [Watchlists](/docs/monitoring/watchlists)
- [Workflows](/docs/monitoring/workflows)
- [Outbound Webhooks](/docs/monitoring/webhooks)
