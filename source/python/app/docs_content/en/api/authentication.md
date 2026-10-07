---
title: API Authentication
description: Bearer tokens and scoped API keys with curl, Python and JavaScript examples.
category: API
order: 10
slug: api/authentication
language: en
shots: []
---

# API Authentication

> Bearer tokens and scoped API keys with curl, Python and JavaScript examples.

Bearer tokens and scoped API keys with curl, Python and JavaScript examples.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/apikeys` | List Apikeys |
| `POST` | `/api/v1/apikeys` | Create Apikey |
| `POST` | `/api/v1/apikeys/{kid}/revoke` | Revoke Apikey |
| `POST` | `/api/v1/auth/login` | Login |
| `POST` | `/api/v1/auth/logout` | Logout |
| `POST` | `/api/v1/auth/oidc/callback` | Oidc Callback |
| `POST` | `/api/v1/auth/oidc/login` | Oidc Login |
| `GET` | `/api/v1/auth/providers` | Auth Providers |

## Examples

```bash
curl http://127.0.0.1:8000/api/v1/dashboard -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/dashboard", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/dashboard", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#login) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
- [Jobs API](/docs/api/jobs)
