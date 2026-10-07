---
title: Browser Issues
description: Headless pool failures, timeouts and blocked media.
category: Troubleshooting
order: 50
slug: troubleshooting/browser
language: en
shots: []
---

# Browser Issues

> Headless pool failures, timeouts and blocked media.

Headless pool failures, timeouts and blocked media.

### Browser health down

**Cause:** Playwright Chromium missing or pool exhausted.

**Solution:** Install browsers, restart the pool, keep per-job timeouts modest.

**Verification:** /api/v1/browser/health returns up with latency.

### Screenshots render blank

**Cause:** Media/font blocking plus slow JS on the target.

**Solution:** Prefer DIRECT/API strategies for simple pages; reserve BROWSER for JS-heavy ones.

**Verification:** Render returns SVG with nodes.

## Related

- [Troubleshooting Index](/docs/troubleshooting)
- [Common Errors](/docs/troubleshooting/common-errors)
- [Collection Issues](/docs/troubleshooting/collection)
- [Database Issues](/docs/troubleshooting/database)
- [Redis Issues](/docs/troubleshooting/redis)
