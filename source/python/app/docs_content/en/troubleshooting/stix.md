---
title: STIX / MISP Issues
description: Validation failures and import mismatches.
category: Troubleshooting
order: 70
slug: troubleshooting/stix
language: en
shots: []
---

# STIX / MISP Issues

> Validation failures and import mismatches.

Validation failures and import mismatches.

### STIX validation fails

**Cause:** Bundle uses constructs outside the supported subset.

**Solution:** Run /api/v1/stix/validate, read the reported path, simplify to the documented subset.

**Verification:** Validation returns ok before export is trusted downstream.

### MISP import maps nothing

**Cause:** Attributes outside the supported mapping.

**Solution:** Check the supported attribute list on the MISP page first.

**Verification:** Import returns entity counts greater than zero.

## Related

- [Troubleshooting Index](/docs/troubleshooting)
- [Common Errors](/docs/troubleshooting/common-errors)
- [Collection Issues](/docs/troubleshooting/collection)
- [Database Issues](/docs/troubleshooting/database)
- [Redis Issues](/docs/troubleshooting/redis)
