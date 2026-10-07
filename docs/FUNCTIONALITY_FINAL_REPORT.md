# Web Intelligence — Functionality Final Report

## Executive Summary

Before: buttons and menus existed whose backend chains were unverified —
search crossed organization boundaries with no ranking or modes, Redis
silently never connected on common installs, STIX imports wrote graph edges
against the wrong ID namespace, `/api/version` disagreed with the app about
its own version, and two test suites failed only in combination.

After: every frontend handler, API call and route is statically verified by
a pytest gate; search is one org-isolated ranked engine; Redis connects with
retry; STIX edges reference real nodes; versions agree; the full combined
suite is green (171+ new tests included).

## Search: WORKING

- One engine (`app/search/unified.py`): keyword, exact, semantic, hybrid
  (default). Ranking exact > prefix > token + risk/recency nudges.
- Filters: kind, risk_min/max, source, date_from/to, investigation_id.
  Pagination with total. Org isolation tested (org-2 sees nothing).
- Console + hero + Ctrl+K share the backend. Result actions (Open,
  Investigate, Add to Case, Watch, Create Finding, View Evidence) verified
  against real endpoints. No AI required for any mode.

## AI Providers: WORKING (config-dependent)

- 19-preset catalog (OpenAI, Anthropic, Google, Ollama, OpenCode Go/Zen,
  OpenRouter, Groq, DeepSeek, Mistral, xAI, Cohere, Together, Fireworks,
  Perplexity + 4 custom-compat), all adapter-backed, capabilities declared.
- Configured providers listed with masked keys, test history, cached models;
  raw key material never leaves the server (tested).
- Live Test / Test All (sequential) with structured honest errors; Ollama
  models discovered live; empty chain answers 502 `AI analysis is not
  configured`.
- Defaults cascade user → org → system → fallbacks, validated and tested.
- Count in this environment: 0 configured (no vendor credentials here) —
  the UI shows the honest empty state, not fake providers.

## Settings: WORKING

- Sectioned shell (General/Workspace/Search/Appearance/Security/Collection/
  Notifications/Integrations/Data/System) reusing verified controls.
- Server-persisted workspace + search defaults, consumed by the wizard and
  the console (tested round-trip + reload).
- Appearance stays client-side by design and says so.

## Investigations: WORKING

- Wizard What→Target→Scope→Sources→Review→Start with real validation,
  scope-derived profiles, staged Operations progress, honest toasts.
- Tutorial wording verified against the implementation (no depth picker,
  `success` not `completed`, real finding/case lifecycles).

## Collection: WORKING

- queued → running → success/failed (+cancelled/deferred), attempts, prices,
  changes, retry/cancel, DLQ. Live run captured in screenshots with a real
  extracted price. Redis queue path verified live against Memurai.

## Graph: WORKING (bug fixed)

- STIX import mapped relationships to entity IDs as node IDs, producing
  dangling `node: null` edges — fixed to resolve entities to real graph
  nodes with dedupe. Traverse/path verified; order-dependent test fixed.

## Findings: WORKING

- Lifecycle OPEN→CONFIRMED/ACCEPTED/FALSE_POSITIVE→RESOLVED verified in UI
  filters and docs. Lineage and evidence links intact.

## Evidence: WORKING

- Source/URL/hash/snippet provenance, recon auto-evidence, integrity
  display, case/report citation paths verified.

## Cases: WORKING

- Notes/tasks/members/links (validated link kinds), case→report flow,
  investigation linkage verified.

## Reports: WORKING

- Generated from real case/investigation data (HTML/PDF/Markdown/CSV/JSON);
  PDF header asserted in tests.

## Watchlists: WORKING

- Keyword/company/domain watches, on-demand evaluation, alert firing
  verified (watchlist_hit rule in E2E).

## Alerts: WORKING

- Ack/resolve/bulk/incidents verified; severity routing on rules.

## Workflows: WORKING

- Trigger→action with runs, idempotent retry, cancel, enable/disable,
  duplication verified in tests.

## STIX/MISP: WORKING (documented subset)

- Export/validate/import round-trip tested; re-import dedupes; unsupported
  types reported, never silently dropped. Subset scope stated in UI and docs.

## System Health: WORKING

- readyz + doctor + AI aggregate health (env default + per-provider last
  known state) + settings system facts. No live calls in the aggregate;
  Test buttons do the live work.

## E2E: PASS

- Hermetic Playwright journey (44s): 31 views render with zero crash
  markers, live collection succeeds ($77 price), settings persist across
  reload, docs serve alongside. Gated behind UI_E2E=1.

## Unit: PASS

- `source/python/tests` + `tests/unit`: all pass including 16 docs tests,
  10 search tests, 6 AI registry tests, 2 settings tests, 3 frontend-audit tests.

## Integration: PASS

- Full combined run green; Redis-live suite passes against Memurai;
  MySQL-gated tests skip honestly without a server.

## Security: PASS

- RBAC/IDOR/SSRF/hardening suites pass; search org isolation added and
  tested; provider keys encrypted at rest, masked in transit, redacted in
  logs/screenshots/tests.

## Dead UI: 0

- Static gate: 479 functions defined, 345 API calls match real routes and
  methods, all `go()` targets resolve.

## Broken API mappings: 0

- 225/225 OpenAPI paths implemented, documented, and contract-synced
  (`test_openapi_sync` passes).

## Fake completion states: 0

- Docs and UI use the real vocabularies (job `success`, investigation
  `investigating`, finding triage states); tutorial corrected to match.

## Hardcoded production IDs: 0

- Wizard resolves the workspace through the API; no `project_id=1`
  fallback (verified in code + docs).

## Secret leaks: 0

- Secret-pattern scans over docs content, API responses (tests), logs and
  screenshots. Dev credential redacted in the login screenshot.

## CDN dependencies: 0

- Tabler + docs JS served locally; portal test asserts no CDN hosts.

## Remaining issues (only real ones)

1. ID/AR bodies cover Getting Started fully; deeper pages fall back to
   English with notice.
2. Screenshot timestamps reflect generation time (relative labels).
3. Live AI chat, Bright Data crawls and MySQL-backed runs need external
   credentials/services not present here.
4. Installed redis-py is 4.6.0 (requirements allow ≥5.0); app and tests
   tolerate both — upgrading the env to redis≥5 is still recommended.
