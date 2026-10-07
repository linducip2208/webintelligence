---
title: Collectors
description: The Go collector engine, the strategy ladder DIRECT to BRIGHT_DATA, proxies and the browser pool.
category: Discovery
order: 40
slug: discovery/collectors
language: en
shots: []
---

# Collectors

> The Go collector engine, the strategy ladder DIRECT to BRIGHT_DATA, proxies and the browser pool.

Collectors fetch. The strategy decider picks the cheapest working ladder rung per target; the browser pool handles JavaScript-heavy pages.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/brightdata/test` | Bright Test |
| `GET` | `/api/v1/browser/health` | Browser Health |
| `GET` | `/api/v1/collectors` | Collector Registry |
| `GET` | `/api/v1/proxies/health` | Proxy Health |
| `POST` | `/api/v1/strategy/decide` | Decide Strategy |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/collectors -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/collectors", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/collectors", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/search -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Verification

- The new or changed record is visible in the list view.
- `GET /api/v1/audit?size=20` shows the action with your identity.
- Related views (graph, timeline, feed) reflect the change.

## Troubleshooting

- Empty list: run collection first — the platform shows real data only.
- 401: sign in or supply a key; see [Authentication](/docs/security/authentication).
- 429: slow down; see [Rate Limits](/docs/api/rate-limits).

> **Try it:** [Open in application](/#collectors) — opens the live view in the application.


## Related

- [Targets](/docs/discovery/targets)
- [Reconnaissance](/docs/discovery/reconnaissance)
- [Attack Surface](/docs/discovery/attack-surface)
- [Connectors](/docs/discovery/connectors)
- [Data Sources](/docs/discovery/data-sources)
