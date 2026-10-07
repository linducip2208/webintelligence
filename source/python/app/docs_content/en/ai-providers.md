---
title: AI Providers Guide
description: Configure providers, guard keys, test live, discover models and set defaults.
category: AI
order: 5
slug: ai-providers
language: en
shots: [23-ai-provider.png]
---

# AI Providers Guide

> Configure providers, guard keys, test live, discover models and set defaults.

## The honest model

- **Catalog, not hardcoding.** Twenty presets ship as data; every one maps to a protocol adapter. Nothing is listed that the backend cannot speak.
- **Configured is not connected.** A saved key means configured. Only a passing live test means connected. The UI shows both states separately.
- **Keys are never shown.** Responses carry `masked_key` (`••••••••abcd`) and `key_configured`; raw keys never appear in HTML, API output, logs or screenshots.
- **Tests are real.** Test Connection builds the adapter and probes auth, discovery and model availability — then stores status, latency and discovered models. Failures return structured codes, never stack traces.

## Add a provider

1. Open AI Providers and press **+ Add AI provider**.
2. Pick the preset (OpenAI, Anthropic, Google, Ollama, OpenCode Go/Zen, OpenRouter, Groq, DeepSeek, Mistral, xAI, Cohere, Together, Fireworks, Perplexity or a custom compatible endpoint).
3. Fill base URL, key and model. For Ollama there is no key — installed models are discovered live, never hardcoded.
4. Press **Test connection** and read latency plus the discovered model list.
5. **Save** (enabled after a successful test), or Save anyway and test later from the card.

## Use it

- Every Ask/research call accepts a provider and model, or falls back to the cascade: explicit → your default → organization default → system default → built-in fallbacks plus every enabled provider.
- Set the system default from any provider card (**Set as default**) or `POST /api/v1/ai/default`.
- When nothing is configured, AI features answer `AI analysis is not configured` with a link — never a traceback.

## Related

- [Provider Configuration](/docs/ai/provider-configuration)
- [Evidence-Grounded AI](/docs/ai/evidence-grounded-ai)
- [AI Privacy & Cost](/docs/ai/privacy)
- [AI API](/docs/api/ai)


## Screenshots

![AI provider configuration with live connection testing.](shot:23-ai-provider.png)

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/ai/default` | Ai Default View |
| `POST` | `/api/v1/ai/default` | Ai Default Set |
| `PATCH` | `/api/v1/ai/default` | Ai Default Set |
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

- [AI Providers](/docs/ai/providers)
- [Provider Configuration](/docs/ai/provider-configuration)
- [Evidence-Grounded AI](/docs/ai/evidence-grounded-ai)
- [Research Runs](/docs/ai/research)
- [Prompt Registry](/docs/ai/prompts)
