---
title: Connectors
description: RSS, paginated REST and CSV connectors: match, test and execute into articles and datasets.
category: Discovery
order: 50
slug: discovery/connectors
language: en
shots: []
---

# Connectors

> RSS, paginated REST and CSV connectors: match, test and execute into articles and datasets.

Connectors ingest RSS, paginated REST and CSV on a schedule. Test before executing; execute writes articles and datasets.

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
| `GET` | `/api/v1/connectors` | List Connectors |
| `POST` | `/api/v1/connectors` | Register Connector |
| `GET` | `/api/v1/connectors/match` | Match Connector |
| `GET` | `/api/v1/connectors/{cid}` | Get Connector |
| `PUT` | `/api/v1/connectors/{cid}` | Update Connector |
| `DELETE` | `/api/v1/connectors/{cid}` | Delete Connector |
| `POST` | `/api/v1/connectors/{cid}/disable` | Disable Connector |
| `POST` | `/api/v1/connectors/{cid}/enable` | Enable Connector |
| `POST` | `/api/v1/connectors/{cid}/execute` | Connector Execute |
| `POST` | `/api/v1/connectors/{cid}/test` | Connector Test |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/connectors -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/connectors", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/connectors", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/connectors -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#connectors) — opens the live view in the application.


## Related

- [Targets](/docs/discovery/targets)
- [Reconnaissance](/docs/discovery/reconnaissance)
- [Attack Surface](/docs/discovery/attack-surface)
- [Collectors](/docs/discovery/collectors)
- [Data Sources](/docs/discovery/data-sources)
