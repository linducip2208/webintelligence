---
title: Search Console
description: One engine, four modes: keyword, exact, semantic and hybrid — with ranking, filters and honest empty states.
category: Investigations
order: 75
slug: search
language: en
shots: [31-search.png, 32-search-results.png]
---

# Search Console

> One engine, four modes: keyword, exact, semantic and hybrid — with ranking, filters and honest empty states.

One engine powers the search console, the dashboard hero search and Ctrl+K. Four modes, ranked results, filters, pagination and organization isolation — with no AI provider required for any mode.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![The Global Search console with mode and filter controls.](shot:31-search.png)

![Ranked search results with per-result actions.](shot:32-search-results.png)

## Steps

1. Open Global Search and type at least 2 characters.
2. Pick a mode: Hybrid (default), Keyword, Semantic or Exact.
3. Narrow with Type, Min risk and Source filters.
4. Read the result summary: total count, query and mode.
5. Act on cards: Open, Investigate, Add to Case, Watch, Create Finding or View Evidence.
6. Page with limit/offset for large result sets.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/search` | Search |
| `GET` | `/api/v1/search/semantic` | Search Semantic |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/search -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/search", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/search", {headers: {Authorization: "Bearer TOKEN"}});
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

> **Try it:** [Open in application](/#search) — opens the live view in the application.


## Modes

| Mode | Behavior |
|---|---|
| `hybrid` (default) | Keyword results first, then semantic extras not already present. |
| `keyword` | Exact, prefix and token matching with ranking. |
| `exact` | Field equality only (score 100). |
| `semantic` | Hashed lexical vectors over ingested documents — no neural model, no AI provider. |

## Ranking

Exact field match (100) beats prefix (50), which beats token hits (10 each), with small boosts for numeric risk and recency. Filters: `kind`, `risk_min`, `risk_max`, `source`, `date_from`, `date_to`, `investigation_id`. Pagination: `limit` (max 100) and `offset`; responses carry `total`, `mode` and `facets`. Every collection is filtered to your organization.

## Related

- [Create an Investigation](/docs/investigations/create-investigation)
- [Target Types](/docs/investigations/target-types)
- [Choosing Scope](/docs/investigations/scope)
- [Projects, Targets & Sources](/docs/investigations/sources)
- [Investigation Profiles: Quick, Standard, Deep](/docs/investigations/profiles)
