---
title: Sign In & Authentication
description: Sign in with a Bearer token or API key, or run open in local development.
category: Getting Started
order: 10
slug: getting-started/login
language: en
shots: [01-login.png]
---

# Sign In & Authentication

> Sign in with a Bearer token or API key, or run open in local development.

## How sign-in works

Web Intelligence has two modes:

- **Development (default):** open. `REQUIRE_AUTH` is unset, so the UI and API work without credentials.
- **Production:** set `REQUIRE_AUTH=1`. Every `/api/v1/*` route then requires a **Bearer token** (from login) or an **X-API-Key** (scoped, expiring, revocable).

## Sign in from the UI

1. Open the application and click **Login** in the sidebar footer.
2. Enter email and password. The session keeps the token in memory only — never in localStorage.
3. The user chip in the sidebar changes from `anonymous` to `● signed in`.

![Sign in](shot:01-login.png)

### What to check

- After login, protected views load without 401 errors.
- **Common mistake:** using an API key (`wi_…`) in the password field. API keys belong in the token box or the `X-API-Key` header, not the login form.

## Sign in from the API

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@local","password":"YOUR_PASSWORD"}'
```

```python
import httpx
r = httpx.post("http://127.0.0.1:8000/api/v1/auth/login",
               json={"email": "admin@local", "password": "YOUR_PASSWORD"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/auth/login", {
  method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify({email: "admin@local", password: "YOUR_PASSWORD"})
});
const {token} = await r.json();
```

## What happens

- Valid credentials return `{"token": ..., "email": ...}` and record an audit event.
- Wrong credentials return `401 bad credentials` and record a failed-login audit event.
- Bearer tokens are stateless HMAC: **logout** discards the client token and logs the event.

## Related

- [API Authentication](/docs/api/authentication)
- [API Keys](/docs/administration/api-keys)
- [RBAC & Organization Isolation](/docs/security/rbac)


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

- [Web Intelligence Documentation](/docs/index)
- [What Is Web Intelligence?](/docs/getting-started/overview)
- [Using the Dashboard](/docs/getting-started/dashboard)
- [Your First Investigation](/docs/getting-started/first-investigation)
- [5 Minutes to First Result](/docs/getting-started/5-minute-investigation)
