---
title: Connectors API
description: RSS, REST and CSV ingestion with test and execute.
category: API
order: 160
slug: api/connectors
language: en
shots: []
---

# Connectors API

> RSS, REST and CSV ingestion with test and execute.

RSS, REST and CSV ingestion with test and execute.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

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

## Examples

```bash
curl http://127.0.0.1:8000/api/v1/connectors -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/connectors", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/connectors", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/connectors -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#connectors) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
