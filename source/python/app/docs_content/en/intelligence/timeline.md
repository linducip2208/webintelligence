---
title: Timeline
description: Every event in chronological order with filters — the story of an investigation.
category: Intelligence
order: 80
slug: intelligence/timeline
language: en
shots: [16-timeline.png]
---

# Timeline

> Every event in chronological order with filters — the story of an investigation.

The timeline orders every event chronologically so the story of an investigation reads top to bottom.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Chronological event timeline of the investigation.](shot:16-timeline.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/events` | List Events |
| `POST` | `/api/v1/events` | Create Event |
| `GET` | `/api/v1/timeline` | Timeline |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/timeline -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/timeline", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/timeline", {headers: {Authorization: "Bearer TOKEN"}});
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

> **Try it:** [Open in application](/#timeline) — opens the live view in the application.


## Related

- [Entities](/docs/intelligence/entities)
- [Entity Resolution](/docs/intelligence/entity-resolution)
- [Intelligence Graph](/docs/intelligence/graph)
- [Pivoting & Transforms](/docs/intelligence/pivoting)
- [Findings](/docs/intelligence/findings)
