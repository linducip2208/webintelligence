---
title: Documents
description: Ingest txt, html, csv and pdf into the evidence store.
category: Evidence
order: 20
slug: evidence/documents
language: en
shots: []
---

# Documents

> Ingest txt, html, csv and pdf into the evidence store.

Documents ingest text, HTML, CSV and PDF into the evidence store for claims and research to cite.

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
| `GET` | `/api/v1/datasets` | List Datasets |
| `POST` | `/api/v1/datasets` | Create Dataset |
| `GET` | `/api/v1/datasets/{did}` | Get Dataset |
| `PUT` | `/api/v1/datasets/{did}` | Update Dataset |
| `DELETE` | `/api/v1/datasets/{did}` | Delete Dataset |
| `POST` | `/api/v1/datasets/{did}/archive` | Dataset Archive |
| `GET` | `/api/v1/datasets/{did}/diff` | Dataset Diff |
| `GET` | `/api/v1/datasets/{did}/export` | Dataset Export |
| `POST` | `/api/v1/datasets/{did}/import` | Dataset Import |
| `POST` | `/api/v1/datasets/{did}/publish` | Dataset Publish |
| `POST` | `/api/v1/datasets/{did}/rollback` | Dataset Rollback |
| `GET` | `/api/v1/datasets/{did}/versions` | Dataset Versions |
| `GET` | `/api/v1/documents` | List Documents |
| `POST` | `/api/v1/documents` | Ingest Document |
| `DELETE` | `/api/v1/documents/{did}` | Delete Document |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/documents -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/documents", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/documents", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#documents) — opens the live view in the application.


## Related

- [Evidence](/docs/evidence/evidence)
- [Claims & Verification](/docs/evidence/claims)
- [Data Lineage](/docs/evidence/lineage)
- [Cases](/docs/evidence/cases)
- [Reports](/docs/evidence/reports)
