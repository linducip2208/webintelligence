---
title: Security Tools
description: Connect the tools you already run: configuration, health checks and expected output.
category: Integrations
order: 30
slug: integrations/security-tools
language: en
shots: [33-security-tools.png]
---

# Security Tools

> Connect the tools you already run: configuration, health checks and expected output.

Only real, adapter-backed tool integrations are documented here. Configuration, health checks and expected output per tool.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Collection and verification tooling with honest availability states.](shot:33-security-tools.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/healthz` | Healthz |
| `GET` | `/readyz` | Readyz |


## Examples

```bash
curl http://127.0.0.1:8000/healthz -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/healthz", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/healthz", {headers: {Authorization: "Bearer TOKEN"}});
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

> **Try it:** [Open in application](/#security-tools) — opens the live view in the application.


## Related

- [STIX 2.1](/docs/integrations/stix)
- [MISP](/docs/integrations/misp)
- [External APIs](/docs/integrations/external-apis)
- [AI Overview](/docs/integrations/ai)
