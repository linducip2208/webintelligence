---
title: Reconnaissance
description: DNS, TLS, technologies, robots and deep RDAP/WHOIS scans — and infra-correlation findings.
category: Discovery
order: 20
slug: discovery/reconnaissance
language: en
shots: []
---

# Reconnaissance

> DNS, TLS, technologies, robots and deep RDAP/WHOIS scans — and infra-correlation findings.

Reconnaissance scans record their method with their results, so anyone can reproduce what was found.

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
| `GET` | `/api/v1/attack-surface` | Attack Surface |
| `GET` | `/api/v1/changes` | List Changes |
| `POST` | `/api/v1/changes/classify` | Classify Change |
| `GET` | `/api/v1/jobs` | List Jobs |
| `POST` | `/api/v1/jobs` | Create Job |
| `GET` | `/api/v1/jobs/{job_id}` | Get Job |
| `DELETE` | `/api/v1/jobs/{job_id}` | Delete Job |
| `POST` | `/api/v1/jobs/{job_id}/cancel` | Cancel Job |
| `POST` | `/api/v1/jobs/{job_id}/retry` | Retry Job |
| `POST` | `/api/v1/jobs/{job_id}/run` | Run Job Now |
| `POST` | `/api/v1/strategy/decide` | Decide Strategy |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/jobs -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/jobs", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/jobs", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#recon) — opens the live view in the application.


## Related

- [Targets](/docs/discovery/targets)
- [Attack Surface](/docs/discovery/attack-surface)
- [Collectors](/docs/discovery/collectors)
- [Connectors](/docs/discovery/connectors)
- [Data Sources](/docs/discovery/data-sources)
