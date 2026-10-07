---
title: Investigations API
description: Full lifecycle plus notes, tasks, members, links and saved views.
category: API
order: 30
slug: api/investigations
language: en
shots: []
---

# Investigations API

> Full lifecycle plus notes, tasks, members, links and saved views.

Full lifecycle plus notes, tasks, members, links and saved views.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

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

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#investigations) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Targets API](/docs/api/targets)
- [Jobs API](/docs/api/jobs)
