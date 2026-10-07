---
title: Errors
description: Every error envelope, code and what to do about it.
category: API
order: 200
slug: api/errors
language: en
shots: []
---

# Errors

> Every error envelope, code and what to do about it.

Envelope: `{"error": {"code", "message", "request_id"}}` plus `X-Request-ID` header.

| Code | HTTP | Meaning | Action |
|---|---|---|---|
| `bad_request` | 400 | Malformed input or illegal transition | Fix the request; read the message |
| `unauthorized` | 401 | Missing/invalid credentials | Sign in or supply a key |
| `forbidden` | 403 | Valid identity, insufficient permission | Ask for the role or scope |
| `not_found` | 404 | Unknown id or route | Check the id; never guess project_id |
| `conflict` | 409 | Duplicate or protected state | Use force/purge flows or rename |
| `too_large` | 413 | Body exceeded MAX_BODY_BYTES | Shrink or chunk the payload |
| `validation` | 422 | Schema failed | Align fields with the OpenAPI contract |
| `rate_limited` | 429 | Quota exceeded, Retry-After set | Back off; see Rate Limits |
| `unavailable` | 501/503 | Feature or database unavailable | Check health and doctor |
| `db_unavailable` | 503 | Production without database | Restore MySQL; SQLite fallback is dev-only |

## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
