# Web Intelligence — API Coverage

_Application v2.14.0: 225 implemented paths, 225 documented, 0 missing documentation._

## Implemented but undocumented

(none — 100% of implemented paths are referenced by documentation)

## Documented endpoints per page

### index — 6 endpoint(s)

- `/api/v1/dashboard`
- `/api/v1/i18n`
- `/api/version`
- `/healthz`
- `/metrics`
- `/readyz`

### getting-started/overview — 3 endpoint(s)

- `/api/v1/dashboard`
- `/api/v1/i18n`
- `/api/version`

### getting-started/login — 1 endpoint(s)

- `/api/v1/auth/login`

### getting-started/dashboard — 4 endpoint(s)

- `/api/v1/dashboard`
- `/api/v1/feed`
- `/api/v1/feed/personalized`
- `/api/v1/feed/subscriptions`

### getting-started/first-investigation — 19 endpoint(s)

- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`
- `/api/v1/jobs`
- `/api/v1/jobs/{job_id}`
- `/api/v1/jobs/{job_id}/cancel`
- `/api/v1/jobs/{job_id}/retry`
- `/api/v1/jobs/{job_id}/run`
- `/api/v1/risk/target/{tid}`
- `/api/v1/targets`
- `/api/v1/targets/bulk-delete`
- `/api/v1/targets/{tid}`
- `/api/v1/targets/{tid}/test`

### getting-started/5-minute-investigation — 10 endpoint(s)

- `/api/v1/dashboard`
- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`

### investigations/create-investigation — 14 endpoint(s)

- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`
- `/api/v1/schedules`
- `/api/v1/schedules/{sid}`
- `/api/v1/schedules/{sid}/disable`
- `/api/v1/schedules/{sid}/enable`
- `/api/v1/schedules/{sid}/run`

### investigations/target-types — 11 endpoint(s)

- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`
- `/api/v1/search`
- `/api/v1/search/semantic`

### investigations/scope — 9 endpoint(s)

- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`

### investigations/sources — 13 endpoint(s)

- `/api/v1/connectors`
- `/api/v1/connectors/match`
- `/api/v1/connectors/{cid}`
- `/api/v1/connectors/{cid}/disable`
- `/api/v1/connectors/{cid}/enable`
- `/api/v1/connectors/{cid}/execute`
- `/api/v1/connectors/{cid}/test`
- `/api/v1/projects`
- `/api/v1/projects/{pid}`
- `/api/v1/targets`
- `/api/v1/targets/bulk-delete`
- `/api/v1/targets/{tid}`
- `/api/v1/targets/{tid}/test`

### investigations/profiles — 9 endpoint(s)

- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`

### investigations/collection — 14 endpoint(s)

- `/api/v1/dlq`
- `/api/v1/jobs`
- `/api/v1/jobs/{job_id}`
- `/api/v1/jobs/{job_id}/cancel`
- `/api/v1/jobs/{job_id}/retry`
- `/api/v1/jobs/{job_id}/run`
- `/api/v1/operations`
- `/api/v1/results`
- `/api/v1/schedules`
- `/api/v1/schedules/{sid}`
- `/api/v1/schedules/{sid}/disable`
- `/api/v1/schedules/{sid}/enable`
- `/api/v1/schedules/{sid}/run`
- `/api/v1/worker/tick`

### investigations/investigation-lifecycle — 15 endpoint(s)

- `/api/v1/cases`
- `/api/v1/cases/{cid}`
- `/api/v1/cases/{cid}/links`
- `/api/v1/cases/{cid}/notes`
- `/api/v1/cases/{cid}/tasks`
- `/api/v1/cases/{cid}/tasks/{tid}/toggle`
- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`

### search — 2 endpoint(s)

- `/api/v1/search`
- `/api/v1/search/semantic`

### discovery/targets — 5 endpoint(s)

- `/api/v1/reliability/targets`
- `/api/v1/targets`
- `/api/v1/targets/bulk-delete`
- `/api/v1/targets/{tid}`
- `/api/v1/targets/{tid}/test`

### discovery/reconnaissance — 9 endpoint(s)

- `/api/v1/attack-surface`
- `/api/v1/changes`
- `/api/v1/changes/classify`
- `/api/v1/jobs`
- `/api/v1/jobs/{job_id}`
- `/api/v1/jobs/{job_id}/cancel`
- `/api/v1/jobs/{job_id}/retry`
- `/api/v1/jobs/{job_id}/run`
- `/api/v1/strategy/decide`

### discovery/attack-surface — 1 endpoint(s)

- `/api/v1/attack-surface`

### discovery/collectors — 5 endpoint(s)

- `/api/v1/brightdata/test`
- `/api/v1/browser/health`
- `/api/v1/collectors`
- `/api/v1/proxies/health`
- `/api/v1/strategy/decide`

### discovery/connectors — 7 endpoint(s)

- `/api/v1/connectors`
- `/api/v1/connectors/match`
- `/api/v1/connectors/{cid}`
- `/api/v1/connectors/{cid}/disable`
- `/api/v1/connectors/{cid}/enable`
- `/api/v1/connectors/{cid}/execute`
- `/api/v1/connectors/{cid}/test`

### discovery/data-sources — 15 endpoint(s)

- `/api/v1/connectors`
- `/api/v1/connectors/match`
- `/api/v1/connectors/{cid}`
- `/api/v1/connectors/{cid}/disable`
- `/api/v1/connectors/{cid}/enable`
- `/api/v1/connectors/{cid}/execute`
- `/api/v1/connectors/{cid}/test`
- `/api/v1/documents`
- `/api/v1/documents/{did}`
- `/api/v1/projects`
- `/api/v1/projects/{pid}`
- `/api/v1/targets`
- `/api/v1/targets/bulk-delete`
- `/api/v1/targets/{tid}`
- `/api/v1/targets/{tid}/test`

### intelligence/entities — 8 endpoint(s)

- `/api/v1/entities`
- `/api/v1/entities/history`
- `/api/v1/entities/merge`
- `/api/v1/entities/reject`
- `/api/v1/entities/resolve`
- `/api/v1/entities/split`
- `/api/v1/entities/{eid}`
- `/api/v1/entities/{eid}/aliases`

### intelligence/entity-resolution — 4 endpoint(s)

- `/api/v1/entities/merge`
- `/api/v1/entities/reject`
- `/api/v1/entities/resolve`
- `/api/v1/entities/split`

### intelligence/graph — 5 endpoint(s)

- `/api/v1/graph/edges`
- `/api/v1/graph/nodes`
- `/api/v1/graph/path`
- `/api/v1/graph/render`
- `/api/v1/graph/traverse`

### intelligence/pivoting — 3 endpoint(s)

- `/api/v1/graph/path`
- `/api/v1/transforms`
- `/api/v1/transforms/run`

### intelligence/findings — 3 endpoint(s)

- `/api/v1/findings`
- `/api/v1/findings/bulk`
- `/api/v1/findings/{fid}`

### intelligence/indicators — 3 endpoint(s)

- `/api/v1/findings`
- `/api/v1/findings/bulk`
- `/api/v1/findings/{fid}`

### intelligence/risk — 2 endpoint(s)

- `/api/v1/risk/entity/{eid}`
- `/api/v1/risk/target/{tid}`

### intelligence/timeline — 2 endpoint(s)

- `/api/v1/events`
- `/api/v1/timeline`

### intelligence/threat-intelligence — 20 endpoint(s)

- `/api/v1/analytics/prices`
- `/api/v1/analytics/quality`
- `/api/v1/analytics/trends`
- `/api/v1/articles`
- `/api/v1/articles/{aid}`
- `/api/v1/correlate/prices`
- `/api/v1/feed`
- `/api/v1/feed/personalized`
- `/api/v1/feed/subscriptions`
- `/api/v1/intel/competitors/compare`
- `/api/v1/intel/news/summarize`
- `/api/v1/intel/reviews`
- `/api/v1/opportunities`
- `/api/v1/prices`
- `/api/v1/quality/score`
- `/api/v1/reviews`
- `/api/v1/reviews/import`
- `/api/v1/reviews/queue`
- `/api/v1/reviews/summary`
- `/api/v1/stix/export`

### intelligence/feed — 3 endpoint(s)

- `/api/v1/feed`
- `/api/v1/feed/personalized`
- `/api/v1/feed/subscriptions`

### evidence/evidence — 2 endpoint(s)

- `/api/v1/evidence`
- `/api/v1/evidence/{eid}/verify`

### evidence/documents — 11 endpoint(s)

- `/api/v1/datasets`
- `/api/v1/datasets/{did}`
- `/api/v1/datasets/{did}/archive`
- `/api/v1/datasets/{did}/diff`
- `/api/v1/datasets/{did}/export`
- `/api/v1/datasets/{did}/import`
- `/api/v1/datasets/{did}/publish`
- `/api/v1/datasets/{did}/rollback`
- `/api/v1/datasets/{did}/versions`
- `/api/v1/documents`
- `/api/v1/documents/{did}`

### evidence/claims — 3 endpoint(s)

- `/api/v1/claims`
- `/api/v1/claims/verify`
- `/api/v1/contradictions/check`

### evidence/lineage — 1 endpoint(s)

- `/api/v1/lineage/{fid}`

### evidence/cases — 6 endpoint(s)

- `/api/v1/cases`
- `/api/v1/cases/{cid}`
- `/api/v1/cases/{cid}/links`
- `/api/v1/cases/{cid}/notes`
- `/api/v1/cases/{cid}/tasks`
- `/api/v1/cases/{cid}/tasks/{tid}/toggle`

### evidence/reports — 4 endpoint(s)

- `/api/v1/reports`
- `/api/v1/reports/{rep_id}`
- `/api/v1/reports/{rep_id}/export`
- `/api/v1/reports/{rep_id}/regenerate`

### monitoring/watchlists — 4 endpoint(s)

- `/api/v1/watchlists`
- `/api/v1/watchlists/check`
- `/api/v1/watchlists/{wid}`
- `/api/v1/watchlists/{wid}/evaluate`

### monitoring/alerts — 8 endpoint(s)

- `/api/v1/alerts`
- `/api/v1/alerts/bulk`
- `/api/v1/alerts/check`
- `/api/v1/alerts/incidents`
- `/api/v1/alerts/{alert_id}`
- `/api/v1/alerts/{alert_id}/ack`
- `/api/v1/alerts/{alert_id}/resolve`
- `/api/v1/alerts/{alert_id}/send`

### monitoring/workflows — 10 endpoint(s)

- `/api/v1/maintenance`
- `/api/v1/maintenance/{mid}/disable`
- `/api/v1/workflows`
- `/api/v1/workflows/{wid}`
- `/api/v1/workflows/{wid}/cancel`
- `/api/v1/workflows/{wid}/disable`
- `/api/v1/workflows/{wid}/enable`
- `/api/v1/workflows/{wid}/retry`
- `/api/v1/workflows/{wid}/run`
- `/api/v1/workflows/{wid}/runs`

### monitoring/webhooks — 7 endpoint(s)

- `/api/v1/webhooks`
- `/api/v1/webhooks/deliveries`
- `/api/v1/webhooks/deliveries/{did}/replay`
- `/api/v1/webhooks/{wid}`
- `/api/v1/webhooks/{wid}/disable`
- `/api/v1/webhooks/{wid}/enable`
- `/api/v1/webhooks/{wid}/test`

### integrations/stix — 3 endpoint(s)

- `/api/v1/stix/export`
- `/api/v1/stix/import`
- `/api/v1/stix/validate`

### integrations/misp — 2 endpoint(s)

- `/api/v1/misp/export`
- `/api/v1/misp/import`

### integrations/security-tools — 2 endpoint(s)

- `/healthz`
- `/readyz`

### integrations/external-apis — 3 endpoint(s)

- `/api/v1/apikeys`
- `/api/v1/apikeys/{kid}/revoke`
- `/api/v1/ingest/webhook`

### integrations/ai — 10 endpoint(s)

- `/api/v1/ai/providers`
- `/api/v1/ai/providers/db`
- `/api/v1/ai/providers/db/models`
- `/api/v1/ai/providers/db/test`
- `/api/v1/ai/providers/db/test-all`
- `/api/v1/ai/providers/db/{pid}`
- `/api/v1/ai/providers/db/{pid}/disable`
- `/api/v1/ai/providers/db/{pid}/enable`
- `/api/v1/ai/providers/db/{pid}/models`
- `/api/v1/ai/providers/db/{pid}/test`

### ai/providers — 14 endpoint(s)

- `/api/v1/ai/default`
- `/api/v1/ai/health`
- `/api/v1/ai/models`
- `/api/v1/ai/provider-presets`
- `/api/v1/ai/providers`
- `/api/v1/ai/providers/db`
- `/api/v1/ai/providers/db/models`
- `/api/v1/ai/providers/db/test`
- `/api/v1/ai/providers/db/test-all`
- `/api/v1/ai/providers/db/{pid}`
- `/api/v1/ai/providers/db/{pid}/disable`
- `/api/v1/ai/providers/db/{pid}/enable`
- `/api/v1/ai/providers/db/{pid}/models`
- `/api/v1/ai/providers/db/{pid}/test`

### ai/provider-configuration — 9 endpoint(s)

- `/api/v1/ai/providers/db`
- `/api/v1/ai/providers/db/models`
- `/api/v1/ai/providers/db/test`
- `/api/v1/ai/providers/db/test-all`
- `/api/v1/ai/providers/db/{pid}`
- `/api/v1/ai/providers/db/{pid}/disable`
- `/api/v1/ai/providers/db/{pid}/enable`
- `/api/v1/ai/providers/db/{pid}/models`
- `/api/v1/ai/providers/db/{pid}/test`

### ai/evidence-grounded-ai — 2 endpoint(s)

- `/api/v1/ai/chat`
- `/api/v1/ask`

### ai/research — 6 endpoint(s)

- `/api/v1/research/compare`
- `/api/v1/research/plan`
- `/api/v1/research/runs`
- `/api/v1/research/runs/{rid}/analyze`
- `/api/v1/research/runs/{rid}/export`
- `/api/v1/research/runs/{rid}/finish`

### ai/prompts — 1 endpoint(s)

- `/api/v1/ai/prompts`

### ai/privacy — 1 endpoint(s)

- `/api/v1/ai/usage`

### administration/users — 5 endpoint(s)

- `/api/v1/memberships`
- `/api/v1/memberships/{mid}`
- `/api/v1/users/{addr}/disable`
- `/api/v1/users/{addr}/enable`
- `/api/v1/users/{addr}/reset-password`

### administration/roles — 2 endpoint(s)

- `/api/v1/roles`
- `/api/v1/roles/{name}`

### administration/organizations — 2 endpoint(s)

- `/api/v1/orgs`
- `/api/v1/orgs/{oid}/branding`

### administration/api-keys — 2 endpoint(s)

- `/api/v1/apikeys`
- `/api/v1/apikeys/{kid}/revoke`

### administration/settings — 19 endpoint(s)

- `/api/v1/admin/backup`
- `/api/v1/admin/data-quality`
- `/api/v1/admin/data-quality/fix`
- `/api/v1/admin/demo/purge`
- `/api/v1/admin/demo/seed`
- `/api/v1/admin/first-run`
- `/api/v1/admin/retention/run`
- `/api/v1/billing/plan`
- `/api/v1/billing/plans`
- `/api/v1/billing/usage`
- `/api/v1/costs/budget`
- `/api/v1/costs/budget/check`
- `/api/v1/costs/summary`
- `/api/v1/flags`
- `/api/v1/settings/defaults`
- `/api/v1/settings/system`
- `/api/v1/verticals`
- `/api/v1/verticals/{name}`
- `/api/v1/verticals/{name}/apply`

### administration/audit-log — 1 endpoint(s)

- `/api/v1/audit`

### administration/system-health — 6 endpoint(s)

- `/api/v1/operations`
- `/api/v1/system/doctor`
- `/api/version`
- `/healthz`
- `/metrics`
- `/readyz`

### administration/backup — 1 endpoint(s)

- `/api/v1/admin/backup`

### security/authentication — 5 endpoint(s)

- `/api/v1/auth/login`
- `/api/v1/auth/logout`
- `/api/v1/auth/oidc/callback`
- `/api/v1/auth/oidc/login`
- `/api/v1/auth/providers`

### security/rbac — 4 endpoint(s)

- `/api/v1/memberships`
- `/api/v1/memberships/{mid}`
- `/api/v1/roles`
- `/api/v1/roles/{name}`

### security/ssrf — 4 endpoint(s)

- `/api/v1/targets`
- `/api/v1/targets/bulk-delete`
- `/api/v1/targets/{tid}`
- `/api/v1/targets/{tid}/test`

### security/api-security — 1 endpoint(s)

- `/api/v1/auth/login`

### security/webhooks — 1 endpoint(s)

- `/api/v1/ingest/webhook`

### deployment/playwright — 1 endpoint(s)

- `/api/v1/browser/health`

### api/overview — 6 endpoint(s)

- `/api/v1/docs/coverage`
- `/api/v1/docs/help`
- `/api/v1/docs/index`
- `/api/v1/docs/search`
- `/api/v1/docs/sitemap`
- `/api/version`

### api/authentication — 7 endpoint(s)

- `/api/v1/apikeys`
- `/api/v1/apikeys/{kid}/revoke`
- `/api/v1/auth/login`
- `/api/v1/auth/logout`
- `/api/v1/auth/oidc/callback`
- `/api/v1/auth/oidc/login`
- `/api/v1/auth/providers`

### api/projects — 2 endpoint(s)

- `/api/v1/projects`
- `/api/v1/projects/{pid}`

### api/investigations — 9 endpoint(s)

- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`

### api/targets — 4 endpoint(s)

- `/api/v1/targets`
- `/api/v1/targets/bulk-delete`
- `/api/v1/targets/{tid}`
- `/api/v1/targets/{tid}/test`

### api/jobs — 7 endpoint(s)

- `/api/v1/dlq`
- `/api/v1/jobs`
- `/api/v1/jobs/{job_id}`
- `/api/v1/jobs/{job_id}/cancel`
- `/api/v1/jobs/{job_id}/retry`
- `/api/v1/jobs/{job_id}/run`
- `/api/v1/results`

### api/entities — 8 endpoint(s)

- `/api/v1/entities`
- `/api/v1/entities/history`
- `/api/v1/entities/merge`
- `/api/v1/entities/reject`
- `/api/v1/entities/resolve`
- `/api/v1/entities/split`
- `/api/v1/entities/{eid}`
- `/api/v1/entities/{eid}/aliases`

### api/graph — 5 endpoint(s)

- `/api/v1/graph/edges`
- `/api/v1/graph/nodes`
- `/api/v1/graph/path`
- `/api/v1/graph/render`
- `/api/v1/graph/traverse`

### api/findings — 4 endpoint(s)

- `/api/v1/findings`
- `/api/v1/findings/bulk`
- `/api/v1/findings/{fid}`
- `/api/v1/lineage/{fid}`

### api/risk — 2 endpoint(s)

- `/api/v1/risk/entity/{eid}`
- `/api/v1/risk/target/{tid}`

### api/evidence — 6 endpoint(s)

- `/api/v1/claims`
- `/api/v1/claims/verify`
- `/api/v1/documents`
- `/api/v1/documents/{did}`
- `/api/v1/evidence`
- `/api/v1/evidence/{eid}/verify`

### api/cases — 6 endpoint(s)

- `/api/v1/cases`
- `/api/v1/cases/{cid}`
- `/api/v1/cases/{cid}/links`
- `/api/v1/cases/{cid}/notes`
- `/api/v1/cases/{cid}/tasks`
- `/api/v1/cases/{cid}/tasks/{tid}/toggle`

### api/reports — 4 endpoint(s)

- `/api/v1/reports`
- `/api/v1/reports/{rep_id}`
- `/api/v1/reports/{rep_id}/export`
- `/api/v1/reports/{rep_id}/regenerate`

### api/watchlists — 4 endpoint(s)

- `/api/v1/watchlists`
- `/api/v1/watchlists/check`
- `/api/v1/watchlists/{wid}`
- `/api/v1/watchlists/{wid}/evaluate`

### api/alerts — 8 endpoint(s)

- `/api/v1/alerts`
- `/api/v1/alerts/bulk`
- `/api/v1/alerts/check`
- `/api/v1/alerts/incidents`
- `/api/v1/alerts/{alert_id}`
- `/api/v1/alerts/{alert_id}/ack`
- `/api/v1/alerts/{alert_id}/resolve`
- `/api/v1/alerts/{alert_id}/send`

### api/workflows — 8 endpoint(s)

- `/api/v1/workflows`
- `/api/v1/workflows/{wid}`
- `/api/v1/workflows/{wid}/cancel`
- `/api/v1/workflows/{wid}/disable`
- `/api/v1/workflows/{wid}/enable`
- `/api/v1/workflows/{wid}/retry`
- `/api/v1/workflows/{wid}/run`
- `/api/v1/workflows/{wid}/runs`

### api/connectors — 7 endpoint(s)

- `/api/v1/connectors`
- `/api/v1/connectors/match`
- `/api/v1/connectors/{cid}`
- `/api/v1/connectors/{cid}/disable`
- `/api/v1/connectors/{cid}/enable`
- `/api/v1/connectors/{cid}/execute`
- `/api/v1/connectors/{cid}/test`

### api/ai — 17 endpoint(s)

- `/api/v1/ai/chat`
- `/api/v1/ai/default`
- `/api/v1/ai/provider-presets`
- `/api/v1/ai/providers`
- `/api/v1/ai/providers/db`
- `/api/v1/ai/providers/db/models`
- `/api/v1/ai/providers/db/test`
- `/api/v1/ai/providers/db/test-all`
- `/api/v1/ai/providers/db/{pid}`
- `/api/v1/ai/providers/db/{pid}/disable`
- `/api/v1/ai/providers/db/{pid}/enable`
- `/api/v1/ai/providers/db/{pid}/models`
- `/api/v1/ai/providers/db/{pid}/test`
- `/api/v1/ask`
- `/api/v1/ml/models`
- `/api/v1/ml/predict`
- `/api/v1/ml/register`

### api/stix — 3 endpoint(s)

- `/api/v1/stix/export`
- `/api/v1/stix/import`
- `/api/v1/stix/validate`

### api/misp — 2 endpoint(s)

- `/api/v1/misp/export`
- `/api/v1/misp/import`

### troubleshooting/collection — 6 endpoint(s)

- `/api/v1/dlq`
- `/api/v1/jobs`
- `/api/v1/jobs/{job_id}`
- `/api/v1/jobs/{job_id}/cancel`
- `/api/v1/jobs/{job_id}/retry`
- `/api/v1/jobs/{job_id}/run`

### troubleshooting/browser — 1 endpoint(s)

- `/api/v1/browser/health`

### troubleshooting/ai — 1 endpoint(s)

- `/api/v1/ai/health`

### troubleshooting/stix — 2 endpoint(s)

- `/api/v1/misp/import`
- `/api/v1/stix/validate`

### reference/statuses — 9 endpoint(s)

- `/api/v1/investigations`
- `/api/v1/investigations/{iid}`
- `/api/v1/investigations/{iid}/links`
- `/api/v1/investigations/{iid}/members`
- `/api/v1/investigations/{iid}/notes`
- `/api/v1/investigations/{iid}/tasks`
- `/api/v1/investigations/{iid}/tasks/{tid}/toggle`
- `/api/v1/investigations/{iid}/views`
- `/api/v1/investigations/{iid}/views/{name}`

### reference/risk-scoring — 1 endpoint(s)

- `/api/v1/risk/target/{tid}`

### reference/entity-types — 8 endpoint(s)

- `/api/v1/entities`
- `/api/v1/entities/history`
- `/api/v1/entities/merge`
- `/api/v1/entities/reject`
- `/api/v1/entities/resolve`
- `/api/v1/entities/split`
- `/api/v1/entities/{eid}`
- `/api/v1/entities/{eid}/aliases`

### reference/collection-strategies — 1 endpoint(s)

- `/api/v1/strategy/decide`

### ai-providers — 11 endpoint(s)

- `/api/v1/ai/default`
- `/api/v1/ai/providers`
- `/api/v1/ai/providers/db`
- `/api/v1/ai/providers/db/models`
- `/api/v1/ai/providers/db/test`
- `/api/v1/ai/providers/db/test-all`
- `/api/v1/ai/providers/db/{pid}`
- `/api/v1/ai/providers/db/{pid}/disable`
- `/api/v1/ai/providers/db/{pid}/enable`
- `/api/v1/ai/providers/db/{pid}/models`
- `/api/v1/ai/providers/db/{pid}/test`

### settings — 3 endpoint(s)

- `/api/v1/flags`
- `/api/v1/settings/defaults`
- `/api/v1/settings/system`

### functional-status — 3 endpoint(s)

- `/api/version`
- `/healthz`
- `/readyz`

### changelog — 1 endpoint(s)

- `/api/version`
