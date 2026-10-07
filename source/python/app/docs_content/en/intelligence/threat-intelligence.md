---
title: Threat Intelligence
description: Consume the intelligence feed: subscriptions, personalized views and threat context.
category: Intelligence
order: 90
slug: intelligence/threat-intelligence
language: en
shots: []
---

# Threat Intelligence

> Consume the intelligence feed: subscriptions, personalized views and threat context.

Threat intelligence arrives through the feed, subscriptions and STIX/MISP exchange.

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
| `GET` | `/api/v1/analytics/prices` | Analytics Prices |
| `GET` | `/api/v1/analytics/quality` | Analytics Quality |
| `GET` | `/api/v1/analytics/trends` | Analytics Trends |
| `GET` | `/api/v1/articles` | List Articles |
| `POST` | `/api/v1/articles` | Create Article |
| `DELETE` | `/api/v1/articles/{aid}` | Delete Article |
| `POST` | `/api/v1/correlate/prices` | Correlate Prices |
| `GET` | `/api/v1/feed` | Intel Feed |
| `GET` | `/api/v1/feed/personalized` | Feed Personal |
| `POST` | `/api/v1/feed/subscriptions` | Feed Subscribe |
| `POST` | `/api/v1/intel/competitors/compare` | Intel Compare |
| `POST` | `/api/v1/intel/news/summarize` | Intel News |
| `POST` | `/api/v1/intel/reviews` | Intel Reviews |
| `GET` | `/api/v1/opportunities` | Opportunities |
| `GET` | `/api/v1/prices` | List Prices |
| `POST` | `/api/v1/quality/score` | Quality Score |
| `GET` | `/api/v1/reviews` | List Reviews |
| `POST` | `/api/v1/reviews/import` | Reviews Import |
| `GET` | `/api/v1/reviews/queue` | Review Queue |
| `GET` | `/api/v1/reviews/summary` | Reviews Summary |
| `POST` | `/api/v1/stix/export` | Stix Export |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/feed -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/feed", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/feed", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/feed/subscriptions -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#threat) — opens the live view in the application.


## Related

- [Entities](/docs/intelligence/entities)
- [Entity Resolution](/docs/intelligence/entity-resolution)
- [Intelligence Graph](/docs/intelligence/graph)
- [Pivoting & Transforms](/docs/intelligence/pivoting)
- [Findings](/docs/intelligence/findings)
