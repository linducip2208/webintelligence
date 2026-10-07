# Web Intelligence — Production Readiness

_Generated checks + honest manual items (app v2.14.0)._

| Check | State | Evidence |
|---|---|---|
| Test suites | PASS | combined run + gates above |
| Version single source | PASS | test_version_consistency |
| OpenAPI sync | PASS | test_openapi_sync |
| Docs match implementation | PASS | validate.py: 127 md, 225+ paths covered, links resolve |
| Screenshots real | PASS | manifest with routes; redaction verified |
| Secrets | PASS | secret_scan.py |
| REQUIRE_AUTH in production | CONFIGURE | set REQUIRE_AUTH=1 + SECRET_KEY/CREDENTIALS_KEY (see deployment guide) |
| MySQL/Redis | CONFIGURE | UNVERIFIED live here; fallbacks exercised |
| HTTPS/TLS termination | CONFIGURE | Nginx guide + HSTS=1 flag; UNVERIFIED live here |
| Backups | READY | one-click .sql download with table-count verification toast |
| Workers/schedules | READY | worker tick + manual tick endpoint |

Ship only when every CONFIGURE row above is done in the target environment.
