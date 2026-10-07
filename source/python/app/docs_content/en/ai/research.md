---
title: Research Runs
description: Plan, run, analyze, finish, compare and export research as Markdown.
category: AI
order: 40
slug: ai/research
language: en
shots: []
---

# Research Runs

> Plan, run, analyze, finish, compare and export research as Markdown.

Research runs keep AI-assisted analysis reproducible: plan, run, analyze, finish, compare, export.

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
| `GET` | `/api/v1/research/compare` | Research Compare |
| `POST` | `/api/v1/research/plan` | Research Plan |
| `GET` | `/api/v1/research/runs` | Research Runs |
| `POST` | `/api/v1/research/runs` | Research Run |
| `POST` | `/api/v1/research/runs/{rid}/analyze` | Research Analyze |
| `GET` | `/api/v1/research/runs/{rid}/export` | Research Export |
| `POST` | `/api/v1/research/runs/{rid}/finish` | Research Finish |


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
curl -X POST http://127.0.0.1:8000/api/v1/research/plan -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#research) — opens the live view in the application.


## Related

- [AI Providers Guide](/docs/ai-providers)
- [AI Providers](/docs/ai/providers)
- [Provider Configuration](/docs/ai/provider-configuration)
- [Evidence-Grounded AI](/docs/ai/evidence-grounded-ai)
- [Prompt Registry](/docs/ai/prompts)
