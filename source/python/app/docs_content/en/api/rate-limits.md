---
title: Rate Limits
description: Per-identity cost classes, limits and Retry-After handling.
category: API
order: 210
slug: api/rate-limits
language: en
shots: []
---

# Rate Limits

> Per-identity cost classes, limits and Retry-After handling.

Limits are per identity (organization, then API key, then user, then IP) per 60s window, Redis-backed when available.

| Class | Default/min | Applies to |
|---|---|---|
| standard | 300 | Most routes |
| search | 200 | `/api/v1/search*` |
| analytics | 100 | `/api/v1/analytics*`, `/api/v1/intel*` |
| webhook | 100 | webhooks and ingestion |
| ai | 30 | `/api/v1/ai*` |
| research | 30 | `/api/v1/research*` |
| browser | 30 | graph render, documents |
| export | 20 | reports, datasets |
| auth | 10 | login |

Exceeding returns 429 with `Retry-After`. Override with `RATE_LIMIT_<CLASS>` env vars.

## Related

- [API Overview](/docs/api/overview)
- [API Authentication](/docs/api/authentication)
- [Projects API](/docs/api/projects)
- [Investigations API](/docs/api/investigations)
- [Targets API](/docs/api/targets)
