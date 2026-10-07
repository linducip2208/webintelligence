---
title: Intelligence Graph
description: Nodes, edges, traversal, shortest path and SVG rendering — investigate a domain through the graph.
category: Intelligence
order: 30
slug: intelligence/graph
language: en
shots: [14-graph.png]
---

# Intelligence Graph

> Nodes, edges, traversal, shortest path and SVG rendering — investigate a domain through the graph.

The graph turns rows into relationships. Traverse from any node, pivot across kinds, and render the result as SVG.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![The intelligence graph: companies, domains and infrastructure linked.](shot:14-graph.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/graph/edges` | Graph Edges |
| `POST` | `/api/v1/graph/edges` | Graph Edge |
| `GET` | `/api/v1/graph/nodes` | Graph Nodes |
| `POST` | `/api/v1/graph/nodes` | Graph Node |
| `GET` | `/api/v1/graph/path` | Graph Path |
| `GET` | `/api/v1/graph/render` | Graph Svg |
| `GET` | `/api/v1/graph/traverse` | Graph Traverse |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/graph/nodes -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/graph/nodes", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/graph/nodes", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/graph/nodes -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
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

> **Try it:** [Open in application](/#graph) — opens the live view in the application.


## Related

- [Entities](/docs/intelligence/entities)
- [Entity Resolution](/docs/intelligence/entity-resolution)
- [Pivoting & Transforms](/docs/intelligence/pivoting)
- [Findings](/docs/intelligence/findings)
- [Indicators](/docs/intelligence/indicators)
