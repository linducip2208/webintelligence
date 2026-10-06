# Intelligence Data Model (as implemented)

All tables InnoDB / utf8mb4 (MySQL) with `created_at/updated_at` UTC.
`source/python/app/models/entities.py` + `universal.py` are the source of
truth; `app/db/repo.py` mirrors dict-collections to tables (write-through:
MySQL → SQLite file → memory) and auto-adds missing columns.

## Identity & access
- `organizations` (plan, branding) → `memberships` (org, email, role) →
  `roles` (org-scoped custom roles: name unique per org, permissions JSON;
  builtins owner/admin/analyst/viewer live in `services/rbac.py MATRIX`)
- `api_keys` (org, name, key_hash SHA256, scopes, revoked, expires_at)
- `users` (email, password_hash bcrypt, role, is_active)
- `audit_logs` (actor, action, ref, at) — append-only trail of mutations

## Collection
- `projects` → `targets` (profile: attempts/successes/failures, EWMA
  latency/cost, preferred strategy, `recon` snapshot JSON, tags/notes in data)
- `collection_jobs` (job_uid unique, org_id, strategy, status, plan, costs)
- `collection_attempts`, `raw_documents` (content_hash dedupe)
- `schedules` (interval/hourly/daily/weekly/cron/event, next/last run)

## Normalization & entities
- `normalized_entities` (kind, name, domain, confidence, aliases, links)
- `entity_history` (via `snapshots` key=entity_op: merge/split/reject trail)
- `prices`, `reviews`, `articles`, `changes` (hash + field diffs)

## Knowledge & evidence (provenance-first)
- `graph_nodes` / `graph_edges` (rel, confidence, evidence refs)
- `events` (dedup_key 1h window), `evidence` (source/url/hash/snippet),
  `claims` (status UNVERIFIED→, confidence, evidence_ids)
- `findings` (kind/title/body, severity info→critical, status
  OPEN/CONFIRMED/FALSE_POSITIVE/RESOLVED/ACCEPTED, priority, resolved_at,
  entities, evidence_ids)
- Every finding/claim/edge cites evidence ids; `lineage/{fid}` walks
  finding → evidence → jobs.

## Investigations & cases
- `investigations` (status open→closed, priority, owner/members, tags,
  target/entity/finding/evidence links, notes[{by,at,text}], tasks[{done}])
- `cases` (UPPERCASE lifecycle, assignee, + investigation/alert links,
  audit trail assembled from `audit_logs` refs)

## Monitoring & automation
- `watchlists` (keyword/company/domain… + cooldown-guarded evaluation)
- `alerts` (rule/message/channel/severity, acked/resolved + resolution,
  sla_due), `maintenance_windows` (suppression), `workflows` (definition
  steps, enabled/paused, version) + `workflow_runs` (idempotent runs + log)
- `webhooks` (event_types, encrypted secret) + `webhook_deliveries`
  (status/attempts/response_status, replayable)

## Datasets, documents, reports, AI
- `datasets` + `dataset_versions` (fingerprint, lineage, diff/rollback)
- `documents` (fingerprint dedupe, chunks, semantic index)
- `reports` (kind/project/payload/evidence; export web/PDF/CSV/JSON/XLSX/md)
- `ai_providers` (encrypted key, protocol chat|responses|anthropic|google,
  test metadata), `ai_usage` (tokens/cost per call)

## Conventions
- Tenant isolation: `org_id` on every row; cross-org reads return 404.
- Ephemeral state (`budgets`, alert cooldowns, tags) lives in `kv_store`.
- JSON columns hold attributes/config; relations that matter (FKs, link id
  lists) stay queryable; `data`/`payload` catch-alls preserve full dicts.
