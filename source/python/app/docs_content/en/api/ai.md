---
title: AI API
description: Evidence-grounded chat, ask, providers and usage.
category: API
order: 170
slug: api/ai
language: en
shots: []
---

# AI API

> Evidence-grounded chat, ask, providers and usage.

Evidence-grounded chat, ask, providers and usage.

Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. See [API Authentication](/docs/api/authentication).

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ai/chat` | Ai Chat |
| `GET` | `/api/v1/ai/default` | Ai Default View |
| `POST` | `/api/v1/ai/default` | Ai Default Set |
| `GET` | `/api/v1/ai/provider-presets` | Ai Provider Presets |
| `GET` | `/api/v1/ai/providers` | Ai Providers |
| `GET` | `/api/v1/ai/providers/db` | Ai Provider List |
| `POST` | `/api/v1/ai/providers/db` | Ai Provider Create |
| `POST` | `/api/v1/ai/providers/db/models` | Ai Provider Discover Unsaved |
| `POST` | `/api/v1/ai/providers/db/test` | Ai Provider Test Unsaved |
| `POST` | `/api/v1/ai/providers/db/test-all` | Ai Provider Test All |
| `GET` | `/api/v1/ai/providers/db/{pid}` | Ai Provider Detail |
| `POST` | `/api/v1/ai/providers/db/{pid}` | Ai Provider Update |
| `PUT` | `/api/v1/ai/providers/db/{pid}` | Ai Provider Replace |
| `DELETE` | `/api/v1/ai/providers/db/{pid}` | Ai Provider Delete |
| `POST` | `/api/v1/ai/providers/db/{pid}/disable` | Ai Provider Disable |
| `POST` | `/api/v1/ai/providers/db/{pid}/enable` | Ai Provider Enable |
| `POST` | `/api/v1/ai/providers/db/{pid}/models` | Ai Provider Discover Saved |
| `POST` | `/api/v1/ai/providers/db/{pid}/test` | Ai Provider Test |
| `POST` | `/api/v1/ask` | Nlq Ask |
| `GET` | `/api/v1/ml/models` | Ml Models |
| `POST` | `/api/v1/ml/predict` | Ml Predict |
| `POST` | `/api/v1/ml/register` | Ml Register |

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
curl -X POST http://127.0.0.1:8000/api/v1/ai/chat -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Errors

All errors share one envelope plus an `X-Request-ID` header:

```json
{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}
```

Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, `conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, `unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).

Pagination: `?page=&size=` (max 100).

> **Try it:** [Open in application](/#ai-providers) — opens the live view in the application.


## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
