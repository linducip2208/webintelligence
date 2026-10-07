---
title: RBAC & Organization Isolation
description: Every collection is org-scoped and IDOR-tested. No magic project_id=1 fallback.
category: Security
order: 20
slug: security/rbac
language: en
shots: []
---

# RBAC & Organization Isolation

> Every collection is org-scoped and IDOR-tested. No magic project_id=1 fallback.

RBAC & Organization Isolation, explained in plain language.

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/memberships` | List Members |
| `POST` | `/api/v1/memberships` | Add Member |
| `PUT` | `/api/v1/memberships/{mid}` | Update Member |
| `DELETE` | `/api/v1/memberships/{mid}` | Remove Member |
| `GET` | `/api/v1/roles` | Roles Matrix |
| `POST` | `/api/v1/roles` | Create Role |
| `PUT` | `/api/v1/roles/{name}` | Update Role |
| `DELETE` | `/api/v1/roles/{name}` | Delete Role |


## Related

- [Authentication](/docs/security/authentication)
- [SSRF Protection](/docs/security/ssrf)
- [API Security](/docs/security/api-security)
- [Webhook Security](/docs/security/webhooks)
- [Secrets Management](/docs/security/secrets)
