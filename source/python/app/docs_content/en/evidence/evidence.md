---
title: Evidence
description: Every claim points at evidence: source, timestamp, integrity and provenance.
category: Evidence
order: 10
slug: evidence/evidence
language: en
shots: [17-evidence.png]
---

# Evidence

> Every claim points at evidence: source, timestamp, integrity and provenance.

Evidence is preserved source material: URL, timestamp, hash and snippet. Cite it — screenshots of the UI are not evidence.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Evidence records with source, timestamp and integrity.](shot:17-evidence.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/evidence` | List Evidence |
| `POST` | `/api/v1/evidence` | Create Evidence |
| `POST` | `/api/v1/evidence/{eid}/verify` | Verify Evidence |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/evidence -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/evidence", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/evidence", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/evidence -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#evidence) — opens the live view in the application.


## Related

- [Documents](/docs/evidence/documents)
- [Claims & Verification](/docs/evidence/claims)
- [Data Lineage](/docs/evidence/lineage)
- [Cases](/docs/evidence/cases)
- [Reports](/docs/evidence/reports)
