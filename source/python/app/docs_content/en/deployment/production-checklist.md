---
title: Production Checklist
description: Twenty checks before you call it production — all verifiable.
category: Deployment
order: 100
slug: deployment/production-checklist
language: en
shots: []
---

# Production Checklist

> Twenty checks before you call it production — all verifiable.

- [ ] HTTPS terminated at Nginx with HSTS=1
- [ ] SECRET_KEY and CREDENTIALS_KEY set to random values
- [ ] REQUIRE_AUTH=1
- [ ] MySQL reachable (readyz shows backend=mysql)
- [ ] Redis reachable
- [ ] Worker tick running (systemd webintel-worker or TICK_SCHEDULES=1)
- [ ] Browser pool healthy (/api/v1/browser/health)
- [ ] Go collector built and running
- [ ] Backups scheduled and restore tested
- [ ] Rate limits tuned
- [ ] SSRF guard with TRUSTED_EGRESS_CIDRS
- [ ] Webhook ingest secret set
- [ ] Audit log reviewed
- [ ] System doctor green
- [ ] API keys scoped and expiring
- [ ] RBAC roles assigned; last-owner protection verified
- [ ] Organization isolation spot-checked
- [ ] Documentation reachable at /docs
- [ ] Screenshots regenerated after last UI change

## Related

- [Requirements](/docs/deployment/requirements)
- [Windows Development](/docs/deployment/windows)
- [Linux Production](/docs/deployment/linux)
- [aaPanel Guide](/docs/deployment/aapanel)
- [Nginx & Reverse Proxy](/docs/deployment/nginx)
