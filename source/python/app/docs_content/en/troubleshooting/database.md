---
title: Database Issues
description: SQLite fallback surprises, access denied and data that disappears on restart.
category: Troubleshooting
order: 30
slug: troubleshooting/database
language: en
shots: []
---

# Database Issues

> SQLite fallback surprises, access denied and data that disappears on restart.

SQLite fallback surprises, access denied and data that disappears on restart.

### readyz shows backend=sqlite despite MySQL

**Cause:** DATABASE_URL never reached the server process, or pymysql missing.

**Solution:** pip install -r requirements.txt; set DATABASE_URL in the server environment; restart.

**Verification:** readyz reports backend=mysql.

### Data vanishes on restart

**Cause:** Writes fell back to memory because the database was unreachable.

**Solution:** Fix connectivity, then verify organizations has rows before writing.

**Verification:** A restart preserves newly created projects.

### Access denied for user webintel

**Cause:** User or grant missing, or wrong password/host.

**Solution:** Recreate the user with host '%' as in the install guide.

**Verification:** Login to MySQL as webintel succeeds.

### bcrypt 72-byte crash

**Cause:** bcrypt 5.x incompatibility with passlib.

**Solution:** pip install "bcrypt==4.0.1".

**Verification:** Server boots without password errors.

## Related

- [Troubleshooting Index](/docs/troubleshooting)
- [Common Errors](/docs/troubleshooting/common-errors)
- [Collection Issues](/docs/troubleshooting/collection)
- [Redis Issues](/docs/troubleshooting/redis)
- [Browser Issues](/docs/troubleshooting/browser)
