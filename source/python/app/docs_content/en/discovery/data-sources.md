---
title: Data Sources
description: Projects, targets, connectors and documents as the four source families.
category: Discovery
order: 60
slug: discovery/data-sources
language: en
shots: [07-sources.png]
---

# Data Sources

> Projects, targets, connectors and documents as the four source families.

Four families feed the platform: projects, targets, connectors and documents.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Projects, targets and connectors as data sources.](shot:07-sources.png)

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
| `GET` | `/api/v1/documents` | List Documents |
| `POST` | `/api/v1/documents` | Ingest Document |
| `DELETE` | `/api/v1/documents/{did}` | Delete Document |
| `GET` | `/api/v1/projects` | List Projects |
| `POST` | `/api/v1/projects` | Create Project |
| `GET` | `/api/v1/projects/{pid}` | Get Project |
| `PUT` | `/api/v1/projects/{pid}` | Update Project |
| `DELETE` | `/api/v1/projects/{pid}` | Delete Project |
| `GET` | `/api/v1/targets` | List Targets |
| `POST` | `/api/v1/targets` | Create Target |
| `POST` | `/api/v1/targets/bulk-delete` | Bulk Delete Targets |
| `GET` | `/api/v1/targets/{tid}` | Get Target |
| `PUT` | `/api/v1/targets/{tid}` | Update Target |
| `DELETE` | `/api/v1/targets/{tid}` | Delete Target |
| `POST` | `/api/v1/targets/{tid}/test` | Target Test |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/projects -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/projects", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/projects", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/projects -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#data-sources) — opens the live view in the application.


## Related

- [Targets](/docs/discovery/targets)
- [Reconnaissance](/docs/discovery/reconnaissance)
- [Attack Surface](/docs/discovery/attack-surface)
- [Collectors](/docs/discovery/collectors)
- [Connectors](/docs/discovery/connectors)
