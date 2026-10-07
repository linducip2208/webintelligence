---
title: AI Overview
description: How AI plugs into investigations — start here, then read the AI section.
category: Integrations
order: 50
slug: integrations/ai
language: en
shots: [23-ai-provider.png]
---

# AI Overview

> How AI plugs into investigations — start here, then read the AI section.

AI Overview, explained in plain language.

## Screenshots

![AI provider configuration with live connection testing.](shot:23-ai-provider.png)

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/ai/providers` | Ai Providers |
| `GET` | `/api/v1/ai/providers/db` | Ai Provider List |
| `POST` | `/api/v1/ai/providers/db` | Ai Provider Create |
| `POST` | `/api/v1/ai/providers/db/models` | Ai Provider Discover Unsaved |
| `POST` | `/api/v1/ai/providers/db/test` | Ai Provider Test Unsaved |
| `POST` | `/api/v1/ai/providers/db/test-all` | Ai Provider Test All |
| `GET` | `/api/v1/ai/providers/db/{pid}` | Ai Provider Detail |
| `POST` | `/api/v1/ai/providers/db/{pid}` | Ai Provider Update |
| `PUT` | `/api/v1/ai/providers/db/{pid}` | Ai Provider Replace |
| `DELETE` | `/api/v1/ai/providers/db/{pid}` | Ai Provider Delete |
| `POST` | `/api/v1/ai/providers/db/{pid}/disable` | Ai Provider Disable |
| `POST` | `/api/v1/ai/providers/db/{pid}/enable` | Ai Provider Enable |
| `POST` | `/api/v1/ai/providers/db/{pid}/models` | Ai Provider Discover Saved |
| `POST` | `/api/v1/ai/providers/db/{pid}/test` | Ai Provider Test |


## Related

- [STIX 2.1](/docs/integrations/stix)
- [MISP](/docs/integrations/misp)
- [Security Tools](/docs/integrations/security-tools)
- [External APIs](/docs/integrations/external-apis)
