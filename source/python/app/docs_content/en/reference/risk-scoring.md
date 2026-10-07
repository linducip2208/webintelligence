---
title: Risk Scoring
description: How 0-100 scores, factors, evidence and confidence combine.
category: Reference
order: 30
slug: reference/risk-scoring
language: en
shots: []
---

# Risk Scoring

> How 0-100 scores, factors, evidence and confidence combine.

Scores run 0–100. Each factor adds weight and cites evidence; confidence reflects corroboration.

| Band | Range | Meaning |
|---|---|---|
| Critical | 80–100 | Immediate analyst attention; verify before acting. |
| High | 60–79 | Prioritize this week; check exposures. |
| Medium | 40–59 | Track; re-evaluate on change. |
| Low | 0–39 | Routine; monitor via watchlists. |

Severity colors follow the same scale across findings, alerts and risk. Risk is an analytical signal — [never proof of malicious activity](/docs/intelligence/risk).

Endpoints: `GET /api/v1/risk/target/{tid}`, `GET /api/v1/risk/entity/{eid}`.

## Related

- [Functional Status](/docs/functional-status)
- [Glossary](/docs/reference/glossary)
- [Statuses](/docs/reference/statuses)
- [Entity Types](/docs/reference/entity-types)
- [Collection Strategies](/docs/reference/collection-strategies)
