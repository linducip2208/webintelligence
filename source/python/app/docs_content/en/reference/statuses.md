---
title: Statuses
description: All async and lifecycle statuses and what each one promises.
category: Reference
order: 20
slug: reference/statuses
language: en
shots: []
---

# Statuses

> All async and lifecycle statuses and what each one promises.

Every asynchronous operation — collection, recon, research, report, export, import, STIX/MISP and workflows — reports one of these states. The UI badges each state with an icon dot plus text, never color alone.

| Status | Meaning | What to do |
|---|---|---|
| `queued` | Accepted and waiting for a worker. | Wait; check the worker tick for schedules. |
| `running` | Executing now; refresh the scan page to watch attempts. | Watch the attempts list; do not duplicate. |
| `success` | Finished with results attached (the UI toast calls this completed). | Review results; triage findings. |
| `failed` | Finished with an error and attempts logged. | Read the error; retry transient failures. |
| `cancelled` | Stopped by an operator. | Restart only if still needed. |
| `deferred` | Browser/proxy leg handed to a worker. | Ensure the worker or browser pool runs. |
| `open` / `investigating` / `pending` / `resolved` / `closed` | Investigation lifecycle (lowercase). | Advance deliberately; cases bundle the outcome. |
| `OPEN` / `INVESTIGATING` / `PENDING` / `RESOLVED` / `CLOSED` | Case lifecycle (uppercase). | Close only with a report attached. |
| `OPEN` / `CONFIRMED` / `FALSE_POSITIVE` / `RESOLVED` / `ACCEPTED` | Findings triage. | Confirm, accept, mark false positive, or resolve — with evidence attached. |
| new / acked / resolved | Alerts (acknowledge and resolve endpoints, plus bulk). | Acknowledge to claim, resolve to finish. |

## Related

- [Functional Status](/docs/functional-status)
- [Glossary](/docs/reference/glossary)
- [Risk Scoring](/docs/reference/risk-scoring)
- [Entity Types](/docs/reference/entity-types)
- [Collection Strategies](/docs/reference/collection-strategies)
