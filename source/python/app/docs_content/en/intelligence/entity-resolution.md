---
title: Entity Resolution
description: Resolve, merge, split and reject: turn noisy mentions into confident identities.
category: Intelligence
order: 20
slug: intelligence/entity-resolution
language: en
shots: []
---

# Entity Resolution

> Resolve, merge, split and reject: turn noisy mentions into confident identities.

Resolution merges duplicate mentions, splits wrong merges and rejects noise — with confidence recorded at every step.

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
| `POST` | `/api/v1/entities/merge` | Entity Merge |
| `POST` | `/api/v1/entities/reject` | Entity Reject |
| `POST` | `/api/v1/entities/resolve` | Entity Resolve |
| `POST` | `/api/v1/entities/split` | Entity Split |


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
curl -X POST http://127.0.0.1:8000/api/v1/entities/resolve -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#entities) — opens the live view in the application.


## Related

- [Entities](/docs/intelligence/entities)
- [Intelligence Graph](/docs/intelligence/graph)
- [Pivoting & Transforms](/docs/intelligence/pivoting)
- [Findings](/docs/intelligence/findings)
- [Indicators](/docs/intelligence/indicators)
