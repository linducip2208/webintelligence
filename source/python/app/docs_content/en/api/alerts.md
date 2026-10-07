---
title: Alerts API
description: Alert lifecycle, bulk operations and incidents.
category: API
order: 140
slug: api/alerts
language: en
shots: []
---

# Alerts API

> Alert lifecycle, bulk operations and incidents.

Alert lifecycle, bulk operations and incidents.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/alerts` | List Alerts |
| `POST` | `/api/v1/alerts` | Create Alert |
| `POST` | `/api/v1/alerts/bulk` | Alerts Bulk |
| `POST` | `/api/v1/alerts/check` | Alert Check |
| `GET` | `/api/v1/alerts/incidents` | Alert Incidents |
| `GET` | `/api/v1/alerts/{alert_id}` | Get Alert |
| `POST` | `/api/v1/alerts/{alert_id}/ack` | Alert Ack |
| `POST` | `/api/v1/alerts/{alert_id}/resolve` | Alert Resolve |
| `POST` | `/api/v1/alerts/{alert_id}/send` | Alert Send |

## Examples

```bash
curl http://127.0.0.1:8000/api/v1/alerts -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/alerts", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/alerts", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/alerts -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#alerts) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
