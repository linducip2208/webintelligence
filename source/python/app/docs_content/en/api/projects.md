---
title: Projects API
description: Create and manage investigation workspaces.
category: API
order: 20
slug: api/projects
language: en
shots: []
---

# Projects API

> Create and manage investigation workspaces.

Create and manage investigation workspaces.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/projects` | List Projects |
| `POST` | `/api/v1/projects` | Create Project |
| `GET` | `/api/v1/projects/{pid}` | Get Project |
| `PUT` | `/api/v1/projects/{pid}` | Update Project |
| `DELETE` | `/api/v1/projects/{pid}` | Delete Project |

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

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#data-sources) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
- [Jobs API](/docs/api/jobs)
