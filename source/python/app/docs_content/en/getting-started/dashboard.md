---
title: Using the Dashboard
description: Read the hero dashboard: KPIs, trends, risk, graph preview and activity — all real data.
category: Getting Started
order: 15
slug: getting-started/dashboard
language: en
shots: [02-dashboard.png]
---

# Using the Dashboard

> Read the hero dashboard: KPIs, trends, risk, graph preview and activity — all real data.

## Reading the dashboard

The dashboard answers one question: **what needs my attention right now?** Every number comes from live data — a zero means nothing has happened yet, not that something is broken.

![Dashboard](shot:02-dashboard.png)

### What to do

1. Open `/` and press **Refresh** to reload all cards.
2. Scan the KPI row: jobs (success/failed), open alerts, price points, opportunities, data quality, AI calls.
3. Check **Overall Risk** and **Recent Alerts** first — they are ordered by severity.
4. Open the **Intelligence Graph** preview, then **Explore** for the full view.
5. Read **Intelligence Activity** for the latest feed events with Asia/Jakarta (WIB) timestamps.

### What to check

- Footer shows the real application version from `GET /api/version`.
- Language switcher (English / Indonesia / العربية) re-labels navigation; Arabic flips the layout to RTL.
- Theme button cycles light → dark → system; light is the default.

### Common mistake

Treating an empty dashboard as an error. On a fresh database it is correct: create a project, add a target, run a job — then refresh. See [5 Minutes to First Result](/docs/getting-started/5-minute-investigation).

## Related

- [Using Projects, Targets & Sources](/docs/investigations/sources)
- [Collection states](/docs/investigations/collection)
- [System Health](/docs/administration/system-health)


## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Web Intelligence hero dashboard with KPIs, trends, risk and activity.](shot:02-dashboard.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dashboard` | Dashboard |
| `GET` | `/api/v1/feed` | Intel Feed |
| `GET` | `/api/v1/feed/personalized` | Feed Personal |
| `POST` | `/api/v1/feed/subscriptions` | Feed Subscribe |


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

> **Try it:** [Open in application](/#dashboard) — opens the live view in the application.


## Related

- [Web Intelligence Documentation](/docs/index)
- [What Is Web Intelligence?](/docs/getting-started/overview)
- [Sign In & Authentication](/docs/getting-started/login)
- [Your First Investigation](/docs/getting-started/first-investigation)
- [5 Minutes to First Result](/docs/getting-started/5-minute-investigation)
