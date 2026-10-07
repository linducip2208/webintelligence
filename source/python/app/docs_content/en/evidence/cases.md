---
title: Cases
description: From investigation to case: notes, tasks, members, links, evidence and reports.
category: Evidence
order: 50
slug: evidence/cases
language: en
shots: [18-case.png]
---

# Cases

> From investigation to case: notes, tasks, members, links, evidence and reports.

Cases in practice.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Case workspace with notes, tasks and linked objects.](shot:18-case.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/cases` | List Cases |
| `POST` | `/api/v1/cases` | Create Case |
| `GET` | `/api/v1/cases/{cid}` | Get Case |
| `PUT` | `/api/v1/cases/{cid}` | Update Case |
| `DELETE` | `/api/v1/cases/{cid}` | Delete Case |
| `POST` | `/api/v1/cases/{cid}/links` | Case Link |
| `POST` | `/api/v1/cases/{cid}/notes` | Case Note |
| `POST` | `/api/v1/cases/{cid}/tasks` | Case Task Add |
| `POST` | `/api/v1/cases/{cid}/tasks/{tid}/toggle` | Case Task Toggle |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/cases -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/cases", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/cases", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/cases -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#cases) — opens the live view in the application.


## Related

- [Evidence](/docs/evidence/evidence)
- [Documents](/docs/evidence/documents)
- [Claims & Verification](/docs/evidence/claims)
- [Data Lineage](/docs/evidence/lineage)
- [Reports](/docs/evidence/reports)
