---
title: Findings API
description: Correlated findings with evidence lineage.
category: API
order: 80
slug: api/findings
language: en
shots: []
---

# Findings API

> Correlated findings with evidence lineage.

Correlated findings with evidence lineage.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/findings` | List Findings |
| `POST` | `/api/v1/findings` | Create Finding |
| `POST` | `/api/v1/findings/bulk` | Findings Bulk |
| `GET` | `/api/v1/findings/{fid}` | Finding Detail |
| `PUT` | `/api/v1/findings/{fid}` | Update Finding |
| `DELETE` | `/api/v1/findings/{fid}` | Delete Finding |
| `GET` | `/api/v1/lineage/{fid}` | Lineage |

## Examples

```bash
curl http://127.0.0.1:8000/api/v1/findings -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/findings", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/findings", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/findings -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#findings) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
