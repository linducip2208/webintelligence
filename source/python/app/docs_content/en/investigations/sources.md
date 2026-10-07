---
title: Projects, Targets & Sources
description: Organize work in projects; register targets; test connections before collecting.
category: Investigations
order: 40
slug: investigations/sources
language: en
shots: [07-sources.png]
---

# Projects, Targets & Sources

> Organize work in projects; register targets; test connections before collecting.

Projects isolate work per organization. Targets register what to watch. Connectors bring outside feeds in.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Projects, targets and connectors as data sources.](shot:07-sources.png)

## Steps

1. Create a project first — everything else hangs off it.
2. Register each target with domain and URL.
3. Press **Test** to verify connectivity and get a strategy recommendation.
4. Add connectors for recurring outside feeds.

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

- [Create an Investigation](/docs/investigations/create-investigation)
- [Target Types](/docs/investigations/target-types)
- [Choosing Scope](/docs/investigations/scope)
- [Investigation Profiles: Quick, Standard, Deep](/docs/investigations/profiles)
- [Collection: Queued, Running, Success](/docs/investigations/collection)
