---
title: What Is Web Intelligence?
description: The Intelligence & Investigation Platform: from search to monitoring in one workspace.
category: Getting Started
order: 5
slug: getting-started/overview
language: en
shots: [02-dashboard.png]
---

# What Is Web Intelligence?

> The Intelligence & Investigation Platform: from search to monitoring in one workspace.

## The pipeline

```text
DATA → INFORMATION → KNOWLEDGE → EVIDENCE → INTELLIGENCE → DECISION SUPPORT
```

1. **Search / Investigate** — start from anything: domain, URL, IP, email, organization, identity or keyword.
2. **Collect** — jobs fetch web, API and document sources through the strategy ladder.
3. **Normalize** — raw captures become clean, comparable records with quality scores.
4. **Entity resolution** — mentions merge into confident identities.
5. **Relationship graph** — ownership, hosting and reference edges you can traverse.
6. **Correlation** — shared infrastructure becomes candidate findings.
7. **Risk** — explainable 0–100 scores with factors and evidence.
8. **Findings** — triage with severity, confidence and lineage.
9. **Evidence** — preserved sources with provenance and integrity.
10. **Case** — the action container: notes, tasks, members, links.
11. **Report** — six export formats for stakeholders.
12. **Monitor** — watchlists, alerts and workflows keep watching after you leave.

## Principles

- **Real data only.** The dashboard never shows sample numbers. An empty screen means no collection has run yet — and tells you how to start.
- **Evidence before conclusions.** AI output is labeled AI-generated; analyst conclusions cite evidence.
- **Async honesty.** Nothing claims completion when it is merely queued.
- **Respectful collection.** robots.txt and terms are honored; no login or CAPTCHA bypass.

## Where to go next

- Non-technical and in a hurry: [5 Minutes to First Result](/docs/getting-started/5-minute-investigation).
- Thorough: [Your First Investigation](/docs/getting-started/first-investigation).
- Responsible for infrastructure: [Requirements](/docs/deployment/requirements).


## Screenshots

![Web Intelligence hero dashboard with KPIs, trends, risk and activity.](shot:02-dashboard.png)

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/dashboard` | Dashboard |
| `GET` | `/api/v1/i18n` | Get Strings |
| `GET` | `/api/version` | Api Version |


## Related

- [Web Intelligence Documentation](/docs/index)
- [Sign In & Authentication](/docs/getting-started/login)
- [Using the Dashboard](/docs/getting-started/dashboard)
- [Your First Investigation](/docs/getting-started/first-investigation)
- [5 Minutes to First Result](/docs/getting-started/5-minute-investigation)
