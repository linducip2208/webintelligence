# API

Versioned under `/api/v1` (see `contracts/openapi/openapi.json`, regenerated
by `source/python/gen_openapi.py`; CI asserts sync via
`tests/integration/test_openapi_sync.py`).

- Auth: `POST /api/v1/auth/login` → Bearer, or `X-API-Key` (scoped, expiring).
- Errors: `{"error": {"code", "message", "request_id"}}` + `X-Request-ID`.
- Pagination: `?page=&size=` (max 100); prices/events use DB LIMIT/OFFSET.
- Sorting: `?sort=&order=asc|desc` where listed. Filtering per resource.
- Rate limits: per cost class + identity, `429` + `Retry-After`.
- Versioning: `/api/version` reports app/API/contracts; v1 stable, no
  deprecation scheduled. Breaking changes bump the path (`/api/v2`).
