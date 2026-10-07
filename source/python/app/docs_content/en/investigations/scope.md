---
title: Choosing Scope
description: DNS, subdomains, TLS, technologies, content, infrastructure, documents, threat intel and risk.
category: Investigations
order: 30
slug: investigations/scope
language: en
shots: [06-scope.png]
---

# Choosing Scope

> DNS, subdomains, TLS, technologies, content, infrastructure, documents, threat intel and risk.

Ten real scopes — DNS, subdomains, TLS, tech, content, infra, entities, documents, threat, risk — decide which collectors and analyzers run, and derive the scan profile automatically.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Scope selection: DNS, subdomains, TLS, technologies and more.](shot:06-scope.png)

## Steps

1. Start with DNS and TLS for any domain.
2. Add subdomains and technologies for exposure mapping.
3. Add content and documents when wording matters.
4. Add threat intelligence when the target may be hostile.
5. Always include risk analysis unless the run is purely archival.

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

- [Create an Investigation](/docs/investigations/create-investigation)
- [Target Types](/docs/investigations/target-types)
- [Projects, Targets & Sources](/docs/investigations/sources)
- [Investigation Profiles: Quick, Standard, Deep](/docs/investigations/profiles)
- [Collection: Queued, Running, Success](/docs/investigations/collection)
