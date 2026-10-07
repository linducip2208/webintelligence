# Web Intelligence — AI Provider Audit

_Catalog vs configured vs tested. No keys, no secrets — only metadata._

## Catalog (backend presets, all adapter-backed)

| Preset | Protocol | Key | Local | Discovery | Default model | Capabilities |
|---|---|---|---|---|---|---|
| opencode-go | responses | required | no | yes | muse-spark-1.3-contributor | chat, reasoning, coding, research, summarization, classification, structured_output, tool_calling |
| opencode-zen | chat | required | no | yes | — | chat, coding, research, summarization, classification |
| claude | anthropic | required | no | yes | claude-3-5-haiku-latest | chat, reasoning, coding, research, summarization, classification, vision |
| openai | chat | required | no | yes | gpt-4o-mini | chat, reasoning, coding, research, summarization, classification, vision, structured_output, tool_calling |
| openrouter | chat | required | no | yes | openai/gpt-4o-mini | chat, reasoning, coding, research, summarization, classification |
| groq | chat | required | no | yes | llama-3.1-8b-instant | chat, coding, research, summarization, classification |
| deepseek | chat | required | no | yes | deepseek-chat | chat, reasoning, coding, research, summarization, classification |
| mistral | chat | required | no | yes | mistral-small-latest | chat, coding, research, summarization, classification |
| xai | chat | required | no | yes | grok-3-mini | chat, reasoning, research, summarization, classification |
| cohere | chat | required | no | yes | command-r | chat, research, summarization, classification |
| together | chat | required | no | yes | — | chat, coding, research, summarization, classification |
| fireworks | chat | required | no | yes | — | chat, coding, research, summarization, classification |
| perplexity | chat | required | no | yes | sonar | chat, research, summarization, classification |
| google | google | required | no | manual | gemini-2.0-flash | chat, reasoning, research, summarization, classification, vision |
| ollama | chat | optional | yes | yes | — | chat, coding, research, summarization, classification |
| openai-compatible | chat | required | no | yes | — | chat, research, summarization, classification |
| responses-compatible | responses | required | no | yes | — | chat, reasoning, research, summarization, classification |
| anthropic-compatible | anthropic | required | no | yes | — | chat, research, summarization, classification |
| google-compatible | google | required | no | manual | — | chat, research, summarization, classification |

## Configured providers (live shape, this environment)

Configured right now: **0** (fresh test database).


## Behaviors verified by tests (`test_ai_registry.py`)

- Listing/detail/test responses never contain `api_key_enc` or raw keys.
- Live test against an unreachable endpoint returns structured PROVIDER_UNAVAILABLE with latency, never a traceback or secret.
- Failed tests persist status/latency/error + discovered models only.
- Defaults cascade (user → org → system) validates providers and models.
- Empty chain answers `AI analysis is not configured` (HTTP 502).

## Production use
- Set defaults from any provider card (Set as default) or POST /api/v1/ai/default.
- Test All runs sequentially to respect vendor rate limits.
- Ollama models are discovered live from the local daemon.
- Research/ask accept explicit provider+model or use the cascade.
