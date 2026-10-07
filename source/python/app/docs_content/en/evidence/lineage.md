---
title: Data Lineage
description: Trace any finding back to the raw collection that produced it.
category: Evidence
order: 40
slug: evidence/lineage
language: en
shots: []
---

# Data Lineage

> Trace any finding back to the raw collection that produced it.

Data Lineage, explained in plain language.

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/lineage/{fid}` | Lineage |


## Related

- [Evidence](/docs/evidence/evidence)
- [Documents](/docs/evidence/documents)
- [Claims & Verification](/docs/evidence/claims)
- [Cases](/docs/evidence/cases)
- [Reports](/docs/evidence/reports)
