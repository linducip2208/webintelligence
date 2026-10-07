---
title: MISP API
description: MISP events: export and import.
category: API
order: 190
slug: api/misp
language: en
shots: []
---

# MISP API

> MISP events: export and import.

MISP events: export and import.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/misp/export` | Misp Export |
| `POST` | `/api/v1/misp/import` | Misp Import |

## Examples

```bash
curl http://127.0.0.1:8000/api/v1/misp/export -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/misp/export", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/misp/export", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/search -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#stix) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
