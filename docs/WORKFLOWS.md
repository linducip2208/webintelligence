# Workflows, Correlation & Risk (as implemented)

## Workflow engine (`services/workflows.py` + `ops.py` routes)
- **Definition**: `{steps: [{condition, action, params}]}` with versioning
  (every definition edit bumps `version`; runs record `workflow_version`).
- **Conditions**: `check_condition` equality matching against the event.
- **Actions** (real, executed server-side):
  - `create_alert` → persisted alert (cooldown-guarded)
  - `tag` → `kv_store` tag (ephemeral-but-persistent)
  - `run_collection` → queued collection job reference
  - `webhook` → outbound HMAC delivery record
  - `run_analysis` → analysis artifact reference
- **Execution**: manual Run, idempotent Retry (same event replays to the
  same idempotency keys and returns the ORIGINAL run), Cancel (running
  runs only), pause via `paused` flag (409 on run), enable/disable.
- **History**: every run persisted to `workflow_runs` with context + step
  log; UI detail page lists runs with cancel for live ones.

## Correlation (`services/infracorr.py`)
- Signals: **SHARES_IP**, **SHARES_CERTIFICATE**, **SHARES_TECHNOLOGY**
  (2+), **SHARES_CONTENT** — computed from recon snapshots across an
  org's targets after every successful ingest.
- Output is **candidate findings** (`kind=infra-correlation`, status OPEN,
  confidence 0.6–0.8, reason + evidence): never silent merges. Analysts
  CONFIRM or mark FALSE_POSITIVE through the findings workflow.
- Idempotent: identical open candidates are never duplicated
  (title-keyed dedupe).

## Risk engine (`services/risk.py`)
Deterministic 0–100 score, fully explainable — every point cites a factor:
- open findings by severity (critical +25 cap 50, high +15 cap 30, …)
- unresolved alerts (critical +15 cap 30, others +8 cap 24)
- recent hostile site changes (+10 cap 20, 30-day window)
- linked infrastructure peers (+12 base cap 24)
- credential/leak evidence (+20 cap 20)
- collection blind spots (+5 when failing with zero success)
- Levels: none/low/medium/high/critical (0/1/25/50/75 cutoffs).
- Endpoints: `GET /api/v1/risk/target/{id}`, `/risk/entity/{id}`;
  UI panels on target/entity pages render factors + evidence.

## Alerts lifecycle
Rules (`alerts/service.py` whitelist) → threshold/cooldown evaluation →
in-app/email/HMAC-webhook delivery with attempts + errors → ack → resolve
(with note) → incidents grouping (`alerts/incidents`) → SLA dues →
maintenance-window suppression. Bulk ack/resolve for triage.
