---
title: Environment Variables
description: Every variable the platform reads, with defaults and production values.
category: Reference
order: 60
slug: reference/environment-variables
language: en
shots: []
---

# Environment Variables

> Every variable the platform reads, with defaults and production values.

| Variable | Default | Production |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./webintel.db` | `mysql+pymysql://webintel:…@127.0.0.1:3306/webintel` |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | your Redis URL (or unset for memory fallback) |
| `DATA_DIR` | `data` | persistent volume path |
| `SECRET_KEY` | dev key | long random string |
| `CREDENTIALS_KEY` | empty (derived) | dedicated Fernet key |
| `REQUIRE_AUTH` | empty (open) | `1` |
| `MAX_BODY_BYTES` | `10485760` | lower for exposed servers |
| `RATE_LIMIT_STANDARD` | `300` | tune per traffic |
| `RATE_LIMIT_SEARCH` | `200` | tune per traffic |
| `RATE_LIMIT_AI` | `30` | tune per budget |
| `HSTS` | empty | `1` behind TLS |
| `DOCS_BASE_URL` | request host | `https://docs.example.com` (canonical URLs) |
| `TRUSTED_EGRESS_CIDRS` | empty | your allowlist, comma separated |
| `OWN_PROXY_URLS` | empty | your proxies, comma separated |
| `BRIGHTDATA_API_KEY` / `BRIGHTDATA_ZONE` | empty | live-crawl credentials |
| `MUSE_SPARK_BASE_URL` / `MUSE_SPARK_API_KEY` | empty | AI provider credentials |
| `MUSE_SPARK_MODEL` | `muse-spark-1.3` | pinned model |
| `WEBHOOK_INGEST_SECRET` | empty | required for inbound webhooks |
| `ALERT_WEBHOOK_URL` / `SMTP_*` / `ALERT_EMAIL_TO` | empty | alert delivery |
| `API_BASE` / `API_TOKEN` | local / empty | CLI targeting |
| `TICK_SCHEDULES` | empty | `1` for the worker process |
| `ENV` / `APP_ENV` | `dev` | `production` |

## Related

- [Functional Status](/docs/functional-status)
- [Glossary](/docs/reference/glossary)
- [Statuses](/docs/reference/statuses)
- [Risk Scoring](/docs/reference/risk-scoring)
- [Entity Types](/docs/reference/entity-types)
