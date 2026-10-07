---
title: API Overview
description: Every versioned path under /api/v1, generated from the live OpenAPI contract.
category: API
order: 5
slug: api/overview
language: en
shots: [28-api.png]
---

# API Overview

> Every versioned path under /api/v1, generated from the live OpenAPI contract.

231 versioned paths under /api/v1, generated from the live OpenAPI contract (this number is computed at build time, never hardcoded).

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/docs/coverage` | Docs Coverage |
| `GET` | `/api/v1/docs/help` | Docs Help |
| `GET` | `/api/v1/docs/index` | Docs Index Json |
| `GET` | `/api/v1/docs/search` | Docs Search |
| `GET` | `/api/v1/docs/sitemap` | Docs Sitemap |
| `GET` | `/api/version` | Api Version |

## Examples

```bash
curl http://127.0.0.1:8000/api/version -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/version", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/version", {headers: {Authorization: "Bearer TOKEN"}});
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

> **Try it:** [Open in application](/#external-apis) — opens the live view in the application.


## Related

- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
- [Jobs API](/docs/api/jobs)
