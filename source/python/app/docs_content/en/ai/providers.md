---
title: AI Providers
description: Add a provider, test the live connection, discover models, then save.
category: AI
order: 10
slug: ai/providers
language: en
shots: [23-ai-provider.png]
---

# AI Providers

> Add a provider, test the live connection, discover models, then save.

Providers are added through the UI: choose, credential, test live, discover models, save. Keys are encrypted and never returned by the API.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![AI provider configuration with live connection testing.](shot:23-ai-provider.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/ai/credentials/inventory` | Ai Credentials Inventory |
| `GET` | `/api/v1/ai/default` | Ai Default View |
| `POST` | `/api/v1/ai/default` | Ai Default Set |
| `PATCH` | `/api/v1/ai/default` | Ai Default Set |
| `GET` | `/api/v1/ai/health` | Ai Health |
| `GET` | `/api/v1/ai/models` | Ai Models |
| `GET` | `/api/v1/ai/privacy` | Ai Privacy View |
| `POST` | `/api/v1/ai/privacy` | Ai Privacy Set |
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
| `GET` | `/api/v1/ai/providers/{name}/models` | Ai Provider Models By Name |
| `POST` | `/api/v1/ai/providers/{name}/models/sync` | Ai Provider Models Sync |
| `POST` | `/api/v1/ai/providers/{name}/test` | Ai Provider Test By Name |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/ai/providers -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/ai/providers", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/ai/providers", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ai/providers/db -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#ai-providers) — opens the live view in the application.


## Related

- [AI Providers Guide](/docs/ai-providers)
- [Provider Configuration](/docs/ai/provider-configuration)
- [Evidence-Grounded AI](/docs/ai/evidence-grounded-ai)
- [Research Runs](/docs/ai/research)
- [Prompt Registry](/docs/ai/prompts)
