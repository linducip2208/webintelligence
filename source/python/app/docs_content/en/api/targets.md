---
title: Targets API
description: Register targets and test connections with strategy advice.
category: API
order: 40
slug: api/targets
language: en
shots: []
---

# Targets API

> Register targets and test connections with strategy advice.

Register targets and test connections with strategy advice.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/targets` | List Targets |
| `POST` | `/api/v1/targets` | Create Target |
| `POST` | `/api/v1/targets/bulk-delete` | Bulk Delete Targets |
| `GET` | `/api/v1/targets/{tid}` | Get Target |
| `PUT` | `/api/v1/targets/{tid}` | Update Target |
| `DELETE` | `/api/v1/targets/{tid}` | Delete Target |
| `POST` | `/api/v1/targets/{tid}/test` | Target Test |

## Examples

```bash
curl http://127.0.0.1:8000/api/v1/targets -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/targets", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/targets", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/targets -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#targets) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Jobs API](/docs/api/jobs)
