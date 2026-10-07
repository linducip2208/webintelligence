---
title: Redis Issues
description: Queue stalls and rate-limit behavior with and without Redis.
category: Troubleshooting
order: 40
slug: troubleshooting/redis
language: en
shots: []
---

# Redis Issues

> Queue stalls and rate-limit behavior with and without Redis.

Queue stalls and rate-limit behavior with and without Redis.

### Queues feel stuck without Redis

**Cause:** Memory fallback works per-process only.

**Solution:** Run a single worker or install Redis for shared queues.

**Verification:** Scheduled runs execute on time.

### Rate limits behave per-process

**Cause:** Memory buckets cannot share across processes.

**Solution:** Point all processes at one Redis.

**Verification:** 429s become consistent across replicas.

## Related

- [Troubleshooting Index](/docs/troubleshooting)
- [Common Errors](/docs/troubleshooting/common-errors)
- [Collection Issues](/docs/troubleshooting/collection)
- [Database Issues](/docs/troubleshooting/database)
- [Browser Issues](/docs/troubleshooting/browser)
