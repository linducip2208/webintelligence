---
title: API Security
description: Per-identity rate limits, body-size guards, request IDs and error envelopes.
category: Security
order: 40
slug: security/api-security
language: en
shots: []
---

# API Security

> Per-identity rate limits, body-size guards, request IDs and error envelopes.

API Security, explained in plain language.

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Login |


## Related

- [Authentication](/docs/security/authentication)
- [RBAC & Organization Isolation](/docs/security/rbac)
- [SSRF Protection](/docs/security/ssrf)
- [Webhook Security](/docs/security/webhooks)
- [Secrets Management](/docs/security/secrets)
