---
title: Common Errors
description: Symptoms, cause, solution and verification for the errors you will actually see.
category: Troubleshooting
order: 10
slug: troubleshooting/common-errors
language: en
shots: []
---

# Common Errors

> Symptoms, cause, solution and verification for the errors you will actually see.

Symptoms, cause, solution and verification for the errors you will actually see.

### 401 unauthorized on every API call

**Cause:** REQUIRE_AUTH=1 is active and no credentials were sent.

**Solution:** Sign in and use the Bearer token, or create a scoped key under External APIs.

**Verification:** A protected route returns 200 with credentials attached.

### 500 with request_id

**Cause:** Unhandled server error; the id correlates with server logs.

**Solution:** Retry once, then report the X-Request-ID and check the audit log.

**Verification:** The same request succeeds and the id disappears from new errors.

### 429 rate limited

**Cause:** Per-identity quota exceeded for the cost class.

**Solution:** Honor Retry-After, then reduce call rate or raise RATE_LIMIT_<CLASS>.

**Verification:** Calls return 200 with spacing between them.

### 413 payload too large

**Cause:** Body exceeded MAX_BODY_BYTES (default 10 MiB).

**Solution:** Chunk the import or raise the limit deliberately.

**Verification:** The chunked upload returns 200.

### Empty dashboard after setup

**Cause:** Fresh database: real-data-only means zeros until collection runs.

**Solution:** Create a project, add a target, run a job, refresh.

**Verification:** KPIs become non-zero.

## Related

- [Troubleshooting Index](/docs/troubleshooting)
- [Collection Issues](/docs/troubleshooting/collection)
- [Database Issues](/docs/troubleshooting/database)
- [Redis Issues](/docs/troubleshooting/redis)
- [Browser Issues](/docs/troubleshooting/browser)
