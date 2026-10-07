---
title: AI Issues
description: Provider down, model discovery empty and slow answers.
category: Troubleshooting
order: 60
slug: troubleshooting/ai
language: en
shots: []
---

# AI Issues

> Provider down, model discovery empty and slow answers.

Provider down, model discovery empty and slow answers.

### Provider shows down

**Cause:** No credentials configured or endpoint unreachable.

**Solution:** Add the provider, press Test connection, read latency and discovered models.

**Verification:** Health flips to up and models list populates.

### Model list empty after save

**Cause:** Discovery failed silently on an incompatible endpoint.

**Solution:** Re-test the connection and pick a preset matching the vendor protocol.

**Verification:** Save succeeds only after a successful test.

### Core features ask for AI

**Cause:** Misconfiguration: core flows must work without AI.

**Solution:** Report it as a bug; collection, graph, risk and reports never require AI.

**Verification:** Disabling all providers leaves collection green.

## Related

- [Troubleshooting Index](/docs/troubleshooting)
- [Common Errors](/docs/troubleshooting/common-errors)
- [Collection Issues](/docs/troubleshooting/collection)
- [Database Issues](/docs/troubleshooting/database)
- [Redis Issues](/docs/troubleshooting/redis)
