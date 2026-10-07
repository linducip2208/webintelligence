---
title: Risk Analysis
description: Explainable 0-100 risk: factors plus evidence. A signal for analysts — never proof of malice.
category: Intelligence
order: 70
slug: intelligence/risk
language: en
shots: [15-risk.png]
---

# Risk Analysis

> Explainable 0-100 risk: factors plus evidence. A signal for analysts — never proof of malice.

Risk scores 0–100 with visible factors and evidence. A prioritization signal for analysts — never proof of malicious activity.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Explainable 0-100 risk with factors and evidence.](shot:15-risk.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/risk/entity/{eid}` | Risk Entity |
| `GET` | `/api/v1/risk/target/{tid}` | Risk Target |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/risk/target/{tid} -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/risk/target/{tid}", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/risk/target/{tid}", {headers: {Authorization: "Bearer TOKEN"}});
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

> **Try it:** [Open in application](/#risk) — opens the live view in the application.


## Related

- [Entities](/docs/intelligence/entities)
- [Entity Resolution](/docs/intelligence/entity-resolution)
- [Intelligence Graph](/docs/intelligence/graph)
- [Pivoting & Transforms](/docs/intelligence/pivoting)
- [Findings](/docs/intelligence/findings)
