---
title: Create an Investigation
description: Use the 5-step wizard: type, target, depth, scope, review — then start.
category: Investigations
order: 10
slug: investigations/create-investigation
language: en
shots: [03-new-investigation.png, 08-review.png]
---

# Create an Investigation

> Use the 5-step wizard: type, target, depth, scope, review — then start.

The wizard has five steps — What, Target, Scope, Sources, Review — and one rule: the workspace project always resolves through the API, so results never land in the wrong place silently. The scan profile is derived from scope, not picked separately.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Web Intelligence New Investigation wizard showing target type selection.](shot:03-new-investigation.png)

![Reviewing the investigation before starting collection.](shot:08-review.png)

## Steps

1. Open **New Investigation** from the header.
2. Pick the target type (Website / Domain for websites).
3. Enter the target and confirm real validation passes.
4. Tick scope; read the auto-derived scan profile.
5. Check the sources screen for ready collectors.
6. Review type, target, scope and profile — then **Start** and watch Operations.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/investigations` | List Investigations |
| `POST` | `/api/v1/investigations` | Create Investigation |
| `GET` | `/api/v1/investigations/{iid}` | Get Investigation |
| `PUT` | `/api/v1/investigations/{iid}` | Update Investigation |
| `DELETE` | `/api/v1/investigations/{iid}` | Delete Investigation |
| `POST` | `/api/v1/investigations/{iid}/links` | Investigation Link |
| `POST` | `/api/v1/investigations/{iid}/members` | Investigation Member Add |
| `POST` | `/api/v1/investigations/{iid}/notes` | Investigation Note |
| `POST` | `/api/v1/investigations/{iid}/tasks` | Investigation Task Add |
| `POST` | `/api/v1/investigations/{iid}/tasks/{tid}/toggle` | Investigation Task Toggle |
| `POST` | `/api/v1/investigations/{iid}/views` | Investigation View Save |
| `DELETE` | `/api/v1/investigations/{iid}/views/{name}` | Investigation View Delete |
| `GET` | `/api/v1/schedules` | List Schedules |
| `POST` | `/api/v1/schedules` | Create Schedule |
| `GET` | `/api/v1/schedules/{sid}` | Get Schedule |
| `PUT` | `/api/v1/schedules/{sid}` | Update Schedule |
| `DELETE` | `/api/v1/schedules/{sid}` | Delete Schedule |
| `POST` | `/api/v1/schedules/{sid}/disable` | Disable Schedule |
| `POST` | `/api/v1/schedules/{sid}/enable` | Enable Schedule |
| `POST` | `/api/v1/schedules/{sid}/run` | Run Schedule Now |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/investigations -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/investigations", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/investigations", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/investigations -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Start New Investigation](/#new-investigation) — opens the live view in the application.


## Related

- [Target Types](/docs/investigations/target-types)
- [Choosing Scope](/docs/investigations/scope)
- [Projects, Targets & Sources](/docs/investigations/sources)
- [Investigation Profiles: Quick, Standard, Deep](/docs/investigations/profiles)
- [Collection: Queued, Running, Success](/docs/investigations/collection)
