---
title: Entity Types
description: Every entity kind, its identity rules and its color.
category: Reference
order: 40
slug: reference/entity-types
language: en
shots: []
---

# Entity Types

> Every entity kind, its identity rules and its color.

| Type | Identity rule | Color |
|---|---|---|
| company | Normalized name + domain | blue |
| domain | Lowercased FQDN | cyan |
| ip | Canonical v4/v6 form | indigo |
| email | Lowercased address | purple |
| person | Name + corroborating attribute | green |
| technology | Product + version | azure |
| vulnerability | CVE identifier | red |
| document | Content hash | gray |

Resolution merges on rules, never on vibes; every merge records confidence.

## Related

- [Functional Status](/docs/functional-status)
- [Glossary](/docs/reference/glossary)
- [Statuses](/docs/reference/statuses)
- [Risk Scoring](/docs/reference/risk-scoring)
- [Collection Strategies](/docs/reference/collection-strategies)
