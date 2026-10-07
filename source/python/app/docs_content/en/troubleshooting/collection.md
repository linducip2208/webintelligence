---
title: Collection Issues
description: Investigations stuck in queued, failed jobs and empty results.
category: Troubleshooting
order: 20
slug: troubleshooting/collection
language: en
shots: []
---

# Collection Issues

> Investigations stuck in queued, failed jobs and empty results.

Investigations stuck in queued, failed jobs and empty results.

### Investigation stuck in queued

**Cause:** Worker tick not running (schedules) or executor busy.

**Solution:** Press Run now on the job; start the worker (TICK_SCHEDULES=1) for schedules.

**Verification:** Job reaches running, then completed or failed with a reason.

### Job failed immediately

**Cause:** Unreachable URL, blocked host, or SSRF/allowlist denial.

**Solution:** Open the job detail: read attempts and error; test the target connection.

**Verification:** Retry returns running; DLQ shows only permanently failed work.

### No findings after completed jobs

**Cause:** Correlation found nothing above thresholds on this scope.

**Solution:** Widen scope, check entities and graph for partial results first.

**Verification:** Entities or graph nodes exist even when findings are empty.

### Collector unavailable

**Cause:** Go collector or browser pool down.

**Solution:** Check /api/v1/browser/health and collector service logs.

**Verification:** Health reads up.

## Related

- [Troubleshooting Index](/docs/troubleshooting)
- [Common Errors](/docs/troubleshooting/common-errors)
- [Database Issues](/docs/troubleshooting/database)
- [Redis Issues](/docs/troubleshooting/redis)
- [Browser Issues](/docs/troubleshooting/browser)
