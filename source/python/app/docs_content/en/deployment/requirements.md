---
title: Requirements
description: Exact versions for Python, MySQL, Redis, Go and browsers.
category: Deployment
order: 10
slug: deployment/requirements
language: en
shots: []
---

# Requirements

> Exact versions for Python, MySQL, Redis, Go and browsers.

| Component | Requirement |
|---|---|---|
| OS | Windows 10/11 dev (Laragon friendly) / Linux production (aaPanel) |
| Python | 3.12+ with `source/python/requirements.txt` (pin `bcrypt==4.0.1`) |
| Database | MySQL 8.4 primary; SQLite file fallback; memory last resort |
| Redis | Optional: queues and rate limits (memory fallback without it) |
| Go | 1.21+ to build the collector |
| Browser | Playwright Chromium for the two-context pool |
| Credentials | Bright Data key for large crawls; AI provider key for AI features |

## Related

- [Windows Development](/docs/deployment/windows)
- [Linux Production](/docs/deployment/linux)
- [aaPanel Guide](/docs/deployment/aapanel)
- [Nginx & Reverse Proxy](/docs/deployment/nginx)
- [MySQL](/docs/deployment/mysql)
