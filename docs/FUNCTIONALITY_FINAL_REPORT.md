# Web Intelligence — Functionality Final Report

## Executive Summary

Before: buttons and menus existed whose backend chains were unverified —
search crossed organization boundaries with no ranking or modes, Redis
silently never connected on common installs, STIX imports wrote graph edges
against the wrong ID namespace, `/api/version` disagreed with the app about
its own version, entity endpoints ignored organization isolation, and two
test suites failed only in combination.

After: every frontend handler, API call and route is statically verified by
pytest gates (including JS syntax); search is one org-isolated ranked engine
with 4 modes and 9 filters; Redis connects with retry; STIX edges reference
real nodes; versions agree from one constant; entities are org-scoped;
AI covers 19 vendors with inventory, health aggregate and defaults cascade;
Settings is sectioned with persisted defaults; the full combined suite is
green (199 passed).

## Search: WORKING

- One engine (`app/search/unified.py`): keyword, exact, semantic, hybrid
  (default). Ranking exact > prefix > token + risk/recency nudges.
- Filters: kind, risk_min/max, source, date_from/to, investigation_id,
  confidence_min/max, status. Pagination with total. Org isolation tested
  (org-2 sees nothing), including entity isolation.
- Console + hero + Ctrl+K share the backend. Result actions (Open,
  Investigate, Add to Case, Watch, Create Finding, View Evidence, View
  Graph, Export) verified against real endpoints. No AI required for any
  mode. Semantic index health shown in the console.

## AI Providers: WORKING (config-dependent)

- 19-preset catalog (OpenAI, Anthropic, Google, Ollama, OpenCode Go/Zen,
  OpenRouter, Groq, DeepSeek, Mistral, xAI, Cohere, Together, Fireworks,
  Perplexity + 4 custom-compat), all adapter-backed, capabilities declared.
- Environment discovery for every vendor key (OPENAI…PERPLEXITY, OPENCODE_*,
  GEMINI alias); database credentials override environment per documented
  precedence (explicit → user → org → system → env fallbacks → DB).
- Credentials inventory endpoint (source badges, masked keys, live status);
  raw key material never leaves the server (asserted, secret-scanned).
- Configured providers listed with masked keys, test history, cached models;
  live Test / sequential Test All with structured honest errors; Ollama
  models discovered live; empty chain answers 502 `AI analysis is not
  configured`; fallback usage reported (`fallbacks_tried`, `default_used`).
- Per-role routing (research/summarization/classification/risk/report);
  research analyze resolves explicit → role → cascade → fallbacks + DB.
- Defaults cascade user → org → system → fallbacks, validated and tested
  (POST and PATCH).
- Count in this environment: 0 configured (no vendor credentials here) —
  the UI shows the honest empty state plus the inventory table, not fake providers.

## Settings: WORKING

- Sectioned shell (General/Workspace/Search/Appearance/Security/Collection/
  Notifications/Integrations/Data/System) with section search, reusing
  verified controls — no alias pages.
- Server-persisted workspace + search + timezone defaults, consumed by the
  wizard, the console and timestamps (tested round-trip + reload + reset).
- Appearance (theme, density, layout, language, accent) applies instantly
  per browser and says so. Dirty tracking with beforeunload guard.
- Misleading aliases removed: Security Tools and External APIs are real
  views; `apikeys` remains a documented alias to the real page.

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

- `source/python/tests` + `tests/unit`: all pass including docs, search,
  AI registry, settings, frontend-audit (with JS syntax) and version tests.

## Integration: PASS

- Full combined run green; Redis-live suite passes against Memurai;
  MySQL-gated tests skip honestly without a server.

## Security: PASS

- RBAC/IDOR/SSRF/hardening suites pass; search org isolation added and
  tested; provider keys encrypted at rest, masked in transit, redacted in
  logs/screenshots/tests.

## Dead UI: 0

- Static gate: 505 functions defined, 365 API calls match real routes and
  methods, all `go()` targets resolve, JS syntax checked by node.

## Broken API mappings: 0

- 231/231 OpenAPI paths implemented, documented, and contract-synced
  (`test_openapi_sync` passes). Frontend-connected majority, documented
  API-only surface for the remainder, 0 broken.

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
