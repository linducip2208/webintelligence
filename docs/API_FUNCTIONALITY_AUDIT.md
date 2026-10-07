# Web Intelligence — API Functionality Audit

_225 endpoints. Auth column from static analysis of router handlers (`_need` = permission-checked, `_ctx`/auth headers = identity, else public). Consumer/test columns from repo-wide reference scans._

| Method | Path | Auth | Frontend consumer | Test ref | Status |
|---|---|---|---|---|---|
| `POST` | `/api/v1/admin/backup` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/admin/data-quality` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/admin/data-quality/fix` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/admin/demo/purge` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/admin/demo/seed` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/admin/first-run` | public | YES | YES | OK |
| `POST` | `/api/v1/admin/retention/run` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/ai/chat` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/ai/default` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/ai/default` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/ai/health` | public | YES | YES | OK |
| `GET` | `/api/v1/ai/models` | public | — | — | OK |
| `GET` | `/api/v1/ai/prompts` | public | — | — | OK |
| `GET` | `/api/v1/ai/provider-presets` | public | YES | YES | OK |
| `GET` | `/api/v1/ai/providers` | public | YES | YES | OK |
| `GET` | `/api/v1/ai/providers/db` | public | YES | YES | OK |
| `POST` | `/api/v1/ai/providers/db` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/ai/providers/db/models` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/ai/providers/db/test` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/ai/providers/db/test-all` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/ai/providers/db/{pid}` | public | — | YES | OK |
| `POST` | `/api/v1/ai/providers/db/{pid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/ai/providers/db/{pid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/ai/providers/db/{pid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/ai/providers/db/{pid}/disable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/ai/providers/db/{pid}/enable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/ai/providers/db/{pid}/models` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/ai/providers/db/{pid}/test` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/ai/usage` | public | — | — | OK |
| `GET` | `/api/v1/alerts` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/alerts` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/alerts/bulk` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/alerts/check` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/alerts/incidents` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/alerts/{alert_id}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/alerts/{alert_id}/ack` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/alerts/{alert_id}/resolve` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/alerts/{alert_id}/send` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/analytics/prices` | public | YES | YES | OK |
| `GET` | `/api/v1/analytics/quality` | public | YES | — | OK |
| `GET` | `/api/v1/analytics/trends` | public | YES | — | OK |
| `GET` | `/api/v1/apikeys` | public | YES | YES | OK |
| `POST` | `/api/v1/apikeys` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/apikeys/{kid}/revoke` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/articles` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/articles` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `DELETE` | `/api/v1/articles/{aid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/ask` | public | — | YES | OK |
| `GET` | `/api/v1/attack-surface` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/audit` | public | YES | YES | OK |
| `POST` | `/api/v1/auth/login` | public | YES | YES | OK |
| `POST` | `/api/v1/auth/logout` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/auth/oidc/callback` | public | — | YES | OK |
| `POST` | `/api/v1/auth/oidc/login` | public | — | YES | OK |
| `GET` | `/api/v1/auth/providers` | public | — | YES | OK |
| `POST` | `/api/v1/billing/plan` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/billing/plans` | public | — | YES | OK |
| `GET` | `/api/v1/billing/usage` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/brightdata/test` | public | YES | — | OK |
| `GET` | `/api/v1/browser/health` | public | — | YES | OK |
| `GET` | `/api/v1/cases` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/cases` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/cases/{cid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/cases/{cid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/cases/{cid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/cases/{cid}/links` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/cases/{cid}/notes` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/cases/{cid}/tasks` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/cases/{cid}/tasks/{tid}/toggle` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/changes` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `POST` | `/api/v1/changes/classify` | public | — | — | OK |
| `POST` | `/api/v1/claims` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/claims/verify` | public | YES | YES | OK |
| `GET` | `/api/v1/collectors` | public | — | YES | OK |
| `GET` | `/api/v1/connectors` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/connectors` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/connectors/match` | public | — | — | OK |
| `GET` | `/api/v1/connectors/{cid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/connectors/{cid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/connectors/{cid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/connectors/{cid}/disable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/connectors/{cid}/enable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/connectors/{cid}/execute` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/connectors/{cid}/test` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/contradictions/check` | public | YES | YES | OK |
| `POST` | `/api/v1/correlate/prices` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/costs/budget` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `GET` | `/api/v1/costs/budget/check` | public | YES | — | OK |
| `GET` | `/api/v1/costs/summary` | public | YES | YES | OK |
| `GET` | `/api/v1/dashboard` | public | YES | YES | OK |
| `GET` | `/api/v1/datasets` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/datasets` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/datasets/{did}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `PUT` | `/api/v1/datasets/{did}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `DELETE` | `/api/v1/datasets/{did}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/datasets/{did}/archive` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/datasets/{did}/diff` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/datasets/{did}/export` | public | — | — | OK |
| `POST` | `/api/v1/datasets/{did}/import` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/datasets/{did}/publish` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/datasets/{did}/rollback` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/datasets/{did}/versions` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/dlq` | public | YES | — | OK |
| `GET` | `/api/v1/docs/coverage` | public | — | YES | OK |
| `GET` | `/api/v1/docs/help` | public | — | YES | OK |
| `GET` | `/api/v1/docs/index` | public | — | — | OK |
| `GET` | `/api/v1/docs/search` | public | — | YES | OK |
| `GET` | `/api/v1/docs/sitemap` | public | — | YES | OK |
| `GET` | `/api/v1/documents` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/documents` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `DELETE` | `/api/v1/documents/{did}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/entities` | public | YES | YES | OK |
| `GET` | `/api/v1/entities/history` | public | — | — | OK |
| `POST` | `/api/v1/entities/merge` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/entities/reject` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `POST` | `/api/v1/entities/resolve` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/entities/split` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `GET` | `/api/v1/entities/{eid}` | public | — | YES | OK |
| `POST` | `/api/v1/entities/{eid}/aliases` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/events` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/events` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/evidence` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/evidence` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/evidence/{eid}/verify` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/feed` | public | YES | YES | OK |
| `GET` | `/api/v1/feed/personalized` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `POST` | `/api/v1/feed/subscriptions` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `GET` | `/api/v1/findings` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/findings` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/findings/bulk` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/findings/{fid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/findings/{fid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/findings/{fid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/flags` | public | YES | YES | OK |
| `POST` | `/api/v1/flags` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/graph/edges` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/graph/edges` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/graph/nodes` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/graph/nodes` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/graph/path` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/graph/render` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `GET` | `/api/v1/graph/traverse` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/i18n` | public | YES | YES | OK |
| `POST` | `/api/v1/ingest/webhook` | public | — | YES | OK |
| `POST` | `/api/v1/intel/competitors/compare` | public | — | — | OK |
| `POST` | `/api/v1/intel/news/summarize` | public | — | — | OK |
| `POST` | `/api/v1/intel/reviews` | public | — | — | OK |
| `GET` | `/api/v1/investigations` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/investigations` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/investigations/{iid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/investigations/{iid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/investigations/{iid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/investigations/{iid}/links` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/investigations/{iid}/members` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/investigations/{iid}/notes` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/investigations/{iid}/tasks` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/investigations/{iid}/tasks/{tid}/toggle` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/investigations/{iid}/views` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `DELETE` | `/api/v1/investigations/{iid}/views/{name}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/jobs` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/jobs` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/jobs/{job_id}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `DELETE` | `/api/v1/jobs/{job_id}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/jobs/{job_id}/cancel` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/jobs/{job_id}/retry` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/jobs/{job_id}/run` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/lineage/{fid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/maintenance` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/maintenance` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/maintenance/{mid}/disable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/memberships` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/memberships` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `PUT` | `/api/v1/memberships/{mid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `DELETE` | `/api/v1/memberships/{mid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/misp/export` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/misp/import` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/ml/models` | public | — | — | OK |
| `POST` | `/api/v1/ml/predict` | public | — | — | OK |
| `POST` | `/api/v1/ml/register` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/operations` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/opportunities` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `GET` | `/api/v1/orgs` | public | YES | YES | OK |
| `POST` | `/api/v1/orgs` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/orgs/{oid}/branding` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `PUT` | `/api/v1/orgs/{oid}/branding` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/prices` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/projects` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/projects` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/projects/{pid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/projects/{pid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/projects/{pid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/proxies/health` | public | — | — | OK |
| `POST` | `/api/v1/quality/score` | public | — | — | OK |
| `GET` | `/api/v1/reliability/targets` | public | YES | — | OK |
| `GET` | `/api/v1/reports` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/reports` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/reports/{rep_id}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `DELETE` | `/api/v1/reports/{rep_id}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/reports/{rep_id}/export` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/reports/{rep_id}/regenerate` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/research/compare` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/research/plan` | public | YES | YES | OK |
| `GET` | `/api/v1/research/runs` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/research/runs` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/research/runs/{rid}/analyze` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/research/runs/{rid}/export` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/research/runs/{rid}/finish` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/results` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/reviews` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/reviews/import` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/reviews/queue` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | — | OK |
| `GET` | `/api/v1/reviews/summary` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/risk/entity/{eid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/risk/target/{tid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/roles` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/roles` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `PUT` | `/api/v1/roles/{name}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `DELETE` | `/api/v1/roles/{name}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/schedules` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/schedules` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/schedules/{sid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/schedules/{sid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/schedules/{sid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/schedules/{sid}/disable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/schedules/{sid}/enable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/schedules/{sid}/run` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/search` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/search/semantic` | public | — | YES | OK |
| `GET` | `/api/v1/settings/defaults` | public | YES | YES | OK |
| `PATCH` | `/api/v1/settings/defaults` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/settings/system` | public | YES | YES | OK |
| `POST` | `/api/v1/stix/export` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/stix/import` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/stix/validate` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/strategy/decide` | public | — | — | OK |
| `GET` | `/api/v1/system/doctor` | public | YES | — | OK |
| `GET` | `/api/v1/targets` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/targets` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/targets/bulk-delete` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/targets/{tid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `PUT` | `/api/v1/targets/{tid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `DELETE` | `/api/v1/targets/{tid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/targets/{tid}/test` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/timeline` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/transforms` | public | YES | YES | OK |
| `POST` | `/api/v1/transforms/run` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/users/{addr}/disable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/users/{addr}/enable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/users/{addr}/reset-password` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/verticals` | public | YES | YES | OK |
| `GET` | `/api/v1/verticals/{name}` | public | — | — | OK |
| `POST` | `/api/v1/verticals/{name}/apply` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/watchlists` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/watchlists` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/watchlists/check` | public | — | — | OK |
| `PUT` | `/api/v1/watchlists/{wid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `DELETE` | `/api/v1/watchlists/{wid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/watchlists/{wid}/evaluate` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/webhooks` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/webhooks` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/webhooks/deliveries` | public | YES | YES | OK |
| `POST` | `/api/v1/webhooks/deliveries/{did}/replay` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `GET` | `/api/v1/webhooks/{wid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/webhooks/{wid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/webhooks/{wid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/webhooks/{wid}/disable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/webhooks/{wid}/enable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/webhooks/{wid}/test` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/worker/tick` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/workflows` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `POST` | `/api/v1/workflows` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | YES | YES | OK |
| `GET` | `/api/v1/workflows/{wid}` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `PUT` | `/api/v1/workflows/{wid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `DELETE` | `/api/v1/workflows/{wid}` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/workflows/{wid}/cancel` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/workflows/{wid}/disable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/workflows/{wid}/enable` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `POST` | `/api/v1/workflows/{wid}/retry` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | — | OK |
| `POST` | `/api/v1/workflows/{wid}/run` | Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/v1/workflows/{wid}/runs` | Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1) | — | YES | OK |
| `GET` | `/api/version` | public | YES | — | OK |
| `GET` | `/healthz` | public | YES | YES | OK |
| `GET` | `/metrics` | public | — | — | OK |
| `GET` | `/readyz` | public | YES | YES | OK |