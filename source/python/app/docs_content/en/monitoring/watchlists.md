---
title: Watchlists
description: Watch keywords, companies and domains; evaluate on demand.
category: Monitoring
order: 10
slug: monitoring/watchlists
language: en
shots: [20-watchlist.png]
---

# Watchlists

> Watch keywords, companies and domains; evaluate on demand.

Watchlists subscribe to keywords, companies and domains. Evaluation runs on demand or on schedule.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Watchlist entries evaluated against new intelligence.](shot:20-watchlist.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/watchlists` | List Watchlists |
| `POST` | `/api/v1/watchlists` | Create Watchlist |
| `POST` | `/api/v1/watchlists/check` | Watchlist Check |
| `PUT` | `/api/v1/watchlists/{wid}` | Update Watchlist |
| `DELETE` | `/api/v1/watchlists/{wid}` | Delete Watchlist |
| `POST` | `/api/v1/watchlists/{wid}/evaluate` | Watchlist Evaluate |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/watchlists -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/watchlists", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/watchlists", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/watchlists -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#watchlists) — opens the live view in the application.


## Related

- [Alerts](/docs/monitoring/alerts)
- [Workflows](/docs/monitoring/workflows)
- [Outbound Webhooks](/docs/monitoring/webhooks)
