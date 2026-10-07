---
title: Authentication
description: Bearer login, OIDC, token expiry and when REQUIRE_AUTH=1 matters.
category: Security
order: 10
slug: security/authentication
language: en
shots: [01-login.png]
---

# Authentication

> Bearer login, OIDC, token expiry and when REQUIRE_AUTH=1 matters.

Login, bearer tokens, OIDC, API keys and why production sets REQUIRE_AUTH=1.

## Prerequisites

- A project exists and you can see it in Data Sources.
- You know which target you are authorized to investigate.

## Screenshots

![Web Intelligence sign-in view with token and API-key authentication.](shot:01-login.png)

## Steps

1. Open the view with the **Try it** link below.
2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.
3. Verify the result appears in the list and in the audit log.
4. Link the result into your investigation or case.

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Login |
| `POST` | `/api/v1/auth/logout` | Logout |
| `POST` | `/api/v1/auth/oidc/callback` | Oidc Callback |
| `POST` | `/api/v1/auth/oidc/login` | Oidc Login |
| `GET` | `/api/v1/auth/providers` | Auth Providers |


## Examples

```bash
curl http://127.0.0.1:8000/api/v1/dashboard -H "Authorization: Bearer TOKEN"
```

```python
import httpx
r = httpx.get("http://127.0.0.1:8000/api/v1/dashboard", headers={"Authorization": "Bearer TOKEN"})
print(r.json())
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/dashboard", {headers: {Authorization: "Bearer TOKEN"}});
console.log(await r.json());
```

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{}'
```

_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. Never commit real tokens to documentation._

## Verification

- The new or changed record is visible in the list view.
- `GET /api/v1/audit?size=20` shows the action with your identity.
- Related views (graph, timeline, feed) reflect the change.

## Troubleshooting

- Empty list: run collection first — the platform shows real data only.
- 401: sign in or supply a key; see [Authentication](/docs/security/authentication).
- 429: slow down; see [Rate Limits](/docs/api/rate-limits).

> **Try it:** [Open in application](/#login) — opens the live view in the application.


## Related

- [RBAC & Organization Isolation](/docs/security/rbac)
- [SSRF Protection](/docs/security/ssrf)
- [API Security](/docs/security/api-security)
- [Webhook Security](/docs/security/webhooks)
- [Secrets Management](/docs/security/secrets)
