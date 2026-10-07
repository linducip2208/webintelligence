---
title: Secrets Management
description: Encrypted provider keys, masked connector secrets, redacted logs — and rotation.
category: Security
order: 60
slug: security/secrets
language: en
shots: []
---

# Secrets Management

> Encrypted provider keys, masked connector secrets, redacted logs — and rotation.

Provider keys are encrypted, connector secrets masked, logs redacted — and rotation is a first-class action.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## Verification

- The new or changed record is visible in the list view.
- `GET /api/v1/audit?size=20` shows the action with your identity.
- Related views (graph, timeline, feed) reflect the change.

## Troubleshooting

- Empty list: run collection first — the platform shows real data only.
- 401: sign in or supply a key; see [Authentication](/docs/security/authentication).
- 429: slow down; see [Rate Limits](/docs/api/rate-limits).

> **Try it:** [Open in application](/#settings) — opens the live view in the application.


## Related

- [Authentication](/docs/security/authentication)
- [RBAC & Organization Isolation](/docs/security/rbac)
- [SSRF Protection](/docs/security/ssrf)
- [API Security](/docs/security/api-security)
- [Webhook Security](/docs/security/webhooks)
