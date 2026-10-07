---
title: Collection Strategies
description: The DIRECT to BRIGHT_DATA ladder and how the decider chooses.
category: Reference
order: 50
slug: reference/collection-strategies
language: en
shots: []
---

# Collection Strategies

> The DIRECT to BRIGHT_DATA ladder and how the decider chooses.

```text
DIRECT → API → BROWSER → OWN_PROXY → BRIGHT_DATA
```

| Strategy | When | Cost |
|---|---|---|
| DIRECT | Plain public pages | Cheapest |
| API | Structured endpoints | Cheap |
| BROWSER | JavaScript-heavy pages (Playwright pool) | Moderate |
| OWN_PROXY | Bot-sensitive hosts via your proxies | Moderate |
| BRIGHT_DATA | Large-scale crawling (needs `BRIGHTDATA_API_KEY`) | Metered |

Test the recommendation any time: `POST /api/v1/strategy/decide`.

## Related

- [Functional Status](/docs/functional-status)
- [Glossary](/docs/reference/glossary)
- [Statuses](/docs/reference/statuses)
- [Risk Scoring](/docs/reference/risk-scoring)
- [Entity Types](/docs/reference/entity-types)
