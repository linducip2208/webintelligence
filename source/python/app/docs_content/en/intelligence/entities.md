---
title: Entities
description: Browse people, companies, domains, IPs, emails and technologies with confidence scores.
category: Intelligence
order: 10
slug: intelligence/entities
language: en
shots: [13-entities.png]
---

# Entities

> Browse people, companies, domains, IPs, emails and technologies with confidence scores.

Entities are the people, companies, domains, IPs, emails and technologies under investigation — each with a confidence score.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Entity list with kinds and confidence scores.](shot:13-entities.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/entities` | List Entities |
| `GET` | `/api/v1/entities/history` | Entity History |
| `POST` | `/api/v1/entities/merge` | Entity Merge |
| `POST` | `/api/v1/entities/reject` | Entity Reject |
| `POST` | `/api/v1/entities/resolve` | Entity Resolve |
| `POST` | `/api/v1/entities/split` | Entity Split |
| `GET` | `/api/v1/entities/{eid}` | Entity Detail |
| `POST` | `/api/v1/entities/{eid}/aliases` | Entity Alias |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/entities -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/entities", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/entities", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/entities/merge -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

- [Entity Resolution](/docs/intelligence/entity-resolution)
- [Intelligence Graph](/docs/intelligence/graph)
- [Pivoting & Transforms](/docs/intelligence/pivoting)
- [Findings](/docs/intelligence/findings)
- [Indicators](/docs/intelligence/indicators)
