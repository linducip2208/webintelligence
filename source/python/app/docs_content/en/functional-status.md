---
title: Functional Status
description: What works out of the box, what needs configuration, and what needs external tools.
category: Reference
order: 5
slug: functional-status
language: en
shots: [27-system-health.png]
---

# Functional Status

> What works out of the box, what needs configuration, and what needs external tools.

## Works out of the box

Dashboard, investigations, collection jobs with honest states, entities and resolution, knowledge graph, findings triage, explainable risk, evidence and lineage, cases, multi-format reports, watchlists, alerts, workflows, webhooks, STIX/MISP subset exchange, search in four modes, RBAC with organization isolation, audit log and the documentation portal itself.

## Needs configuration

- **Authentication:** set `REQUIRE_AUTH=1`, create users/keys/roles.
- **AI providers:** add at least one provider and pass a live test before AI features answer.
- **Schedules/workers:** run the worker tick for time-based collection.
- **Backups/retention:** schedule dumps and retention runs.

## Needs external tools or network

- **MySQL/Redis** for production persistence and shared queues (graceful fallbacks otherwise).
- **Bright Data** credentials for large-scale crawling.
- **Playwright Chromium** for the browser pool.
- **Go toolchain** to rebuild the collector.
- **Ollama** reachable for local models.

## Optional

Industry vertical templates, custom AI-compatible endpoints, OIDC, SMTP/webhook alert channels, aaPanel/Nginx fronting.

## Verify right now

- [System Health](/docs/administration/system-health) and `GET /readyz`.
- [Production Checklist](/docs/deployment/production-checklist).
- [API Coverage](/docs/api/overview) and the generated `docs/API_COVERAGE.md`.

## Related

- [Glossary](/docs/reference/glossary)
- [Statuses](/docs/reference/statuses)
- [Risk Scoring](/docs/reference/risk-scoring)
- [Entity Types](/docs/reference/entity-types)
- [Collection Strategies](/docs/reference/collection-strategies)
