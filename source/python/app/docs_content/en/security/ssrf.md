---
title: SSRF Protection
description: Guard plus trusted-egress allowlist: what admins must configure.
category: Security
order: 30
slug: security/ssrf
language: en
shots: []
---

# SSRF Protection

> Guard plus trusted-egress allowlist: what admins must configure.

SSRF Protection, explained in plain language.

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/targets` | List Targets |
| `POST` | `/api/v1/targets` | Create Target |
| `POST` | `/api/v1/targets/bulk-delete` | Bulk Delete Targets |
| `GET` | `/api/v1/targets/{tid}` | Get Target |
| `PUT` | `/api/v1/targets/{tid}` | Update Target |
| `DELETE` | `/api/v1/targets/{tid}` | Delete Target |
| `POST` | `/api/v1/targets/{tid}/test` | Target Test |


## Related

- [Authentication](/docs/security/authentication)
- [RBAC & Organization Isolation](/docs/security/rbac)
- [API Security](/docs/security/api-security)
- [Webhook Security](/docs/security/webhooks)
- [Secrets Management](/docs/security/secrets)
