# API (as implemented)

Versioned under `/api/v1` (see `contracts/openapi/openapi.json`, regenerated
by `source/python/gen_openapi.py`; sync asserted by
`tests/integration/test_openapi_sync.py`).

- Auth: `POST /api/v1/auth/login` → Bearer, or `X-API-Key` (scoped, expiring,
  revocable). Dev-open unless `REQUIRE_AUTH=1`.
- Errors: `{"error": {"code", "message", "request_id"}}` + `X-Request-ID`
  header. Human messages in UI; request IDs for diagnostics.
- Pagination: `?page=&size=` (max 100); prices/events use DB LIMIT/OFFSET.
- Search: `GET /api/v1/search` — one engine, modes keyword/exact/semantic/
  hybrid, 10 filters, ranking, org isolation, no AI required.
- AI: providers catalog, encrypted DB credentials (masked), live test,
  model discovery + sync, system/org/user defaults, per-role routing,
  privacy policy, inventory, usage. See `docs/AI_PROVIDER_AUDIT.md`.
- Settings: `GET/PATCH /api/v1/settings/defaults`, `POST /api/v1/settings/reset`,
  `GET /api/v1/settings/system`.
- Version: `/api/version` + `/healthz` report the single `APP_VERSION`.
- Live surface: `docs/API_COVERAGE.md` (generated per-endpoint table);
  consumer/test mapping: `docs/API_IMPLEMENTATION_MATRIX.md`;
  auth/consumer analysis: `docs/API_FUNCTIONALITY_AUDIT.md`.
- Interactive reference: `/api-docs`. Product guide: `/docs/api/overview`.
