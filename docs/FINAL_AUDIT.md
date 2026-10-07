# Web Intelligence — Final Audit (Documentation Portal + Functionality Audit)

## 1. Product status

Two tracks, both verified:

- **Documentation portal** at `/docs`, served by the application itself
  (no separate framework, no CDN, local Tabler only): 115 pages in English,
  Indonesian and Arabic; search, sitemap, contextual help and coverage APIs.
- **Functionality audit**: unified search engine, 19-vendor AI catalog with
  enriched listing/health/defaults, sectioned Settings with persisted
  defaults, static frontend audit gate, hermetic browser journey E2E.

## 2. Version

- Application: **v2.14.0** (single source: `FastAPI app.version`;
  `/api/version`, sidebar, footer and docs all read it).
- Fixed during this work: `/api/version` hardcoded `2.5.0` — now delegates
  to the app version; breadcrumb section for Settings; search view default
  mode preselected from saved defaults.

## 3. Git commit

`08057f3` (plus uncommitted working tree documented below).

## 4. Feature matrix (portal)

| Feature | Status | Evidence |
|---|---|---|
| `/docs` portal home + 110 pages | WORKING | `verify_portal.py` 31 checks pass; pytest 16/16 |
| Server-rendered shell (header/sidebar/TOC/footer) | WORKING | `app/api/routers/docs.py` |
| Local search + Ctrl+K (EN/ID/AR) | WORKING | `/api/v1/docs/search` tested for stix/Redis/risk/aaPanel/investigation |
| EN/ID/AR + RTL | WORKING | `dir="rtl"` asserted; 6 Getting Started pages fully translated, rest fall back with honest notice |
| Responsive + offcanvas sidebar | WORKING | mobile screenshots `m-dashboard.png`, `m-docs-home.png` |
| API docs from live OpenAPI | WORKING | endpoint tables generated from `app.openapi()` |
| Contextual in-app help + drawer | WORKING | `VIEW_DOCS` (68 views), `helpOpen()`, empty-state Learn-more links |
| Subdirectory/reverse-proxy | WORKING | `DOCS_MOUNT` / `X-Forwarded-Prefix` prefixing |
| SEO + robots | WORKING | canonical, OG/Twitter meta, dev `noindex` |

## 5. Documentation matrix

- Markdown sources: **127 files** (`app/docs_content/{en,id,ar}/`).
- Sitemap: `docs/SITEMAP.md` (generated, 115 pages).
- API coverage: `docs/API_COVERAGE.md` — **225/225 implemented paths documented**, 0 missing.
- Documentation coverage: `docs/DOCUMENTATION_COVERAGE.md` (feature × docs × screenshot × E2E).
- Functionality: `docs/FUNCTIONALITY_MATRIX.md`, `docs/ROUTE_AUDIT.md`,
  `docs/API_FUNCTIONALITY_AUDIT.md`, `docs/AI_PROVIDER_AUDIT.md`,
  `docs/FUNCTIONALITY_FINAL_REPORT.md` (all generated from live sources).

## 6. Screenshot matrix

34 shots, all from the real UI against isolated demo data (`.example`
domains, `TRUSTED_EGRESS_CIDRS=127.0.0.1/32` for the running-state capture),
Plus manifest with route/viewport/version per shot; dev credential redacted
on the login shot; sentinel secret scan before every capture.

| Shot | Route | State shown |
|---|---|---|
| 01-login … 08-review | wizard + sources | real views |
| 09-queued / 10-running / 11-completed | scan page | queued → running → **success** (real 6s collection, real $42 price extracted) |
| 12–28 | findings … external-apis | real demo-backed views |
| 29–30 | docs home + tutorial | real portal |
| 31-search / 32-search-results | search console | real unified-engine results (26 for "acme") |
| m-dashboard / m-docs-home | 390×844 | real mobile layout |

Regenerate: `python scripts/docs/generate_screenshots.py [--update]`.
Validate: `python scripts/docs/validate_screenshots.py`.
Full pipeline: `python scripts/docs/all.py [--skip-shots]`.

## 7. E2E matrix

| Suite | Result |
|---|---|
| `source/python/tests` + `tests/unit` (Makefile gate) | pass (incl. 12 docs, 10 search, 6 AI registry, 2 settings, 3 frontend-audit tests) |
| `tests/integration` + `tests/security` + `tests/load` | all pass (Redis-live verified against Memurai) |
| `tests/e2e` | pass (live-gated skips except hermetic journey) |
| Functional journey (`UI_E2E=1`) | **PASS** — 31 views, live collection, settings persistence, docs |
| Full combined run | **192 passed, 6 skipped (live-gated)** |
| `go test ./...` + `go vet` | pass |
| Playwright screenshot run | 34/34 captured, secrets clean |

## 8. API coverage

225 implemented paths → 225 referenced by documentation pages.
`test_openapi_sync` passes; contract regenerated (`contracts/openapi/openapi.json`).

## 9. Security checks

- Secret scan over all 127 markdown sources: no tokens/keys (patterns for
  sk-/AKIA/ghp-/X-API-Key formats); screenshot HTML scanned per capture.
- SSRF/RBAC/IDOR suites pass; search org isolation added and tested; Redis
  client no longer caches failure; STIX import no longer writes dangling
  graph edges.
- Login screenshot redacts the dev credential hint automatically.

## 10. Performance checks

- Docs pages lazy-load screenshots with width/height (no layout shift).
- Search index in-memory, substring-scored, no external service.
- Code copy buttons are the only docs JS; no client bundle.

## 11. Deployment checks

- Portal needs no extra services: same uvicorn process, same Tabler assets.
- `DOCS_BASE_URL` for canonical URLs; `DOCS_MOUNT` for subdirectory hosting.
- Deployment guides cover Windows/Linux/aaPanel/Nginx/MySQL/Redis/Playwright/Go.

## 12. Known limitations

1. ID/AR bodies exist for Getting Started only; other pages fall back to
   English with a notice (chrome, titles and search fully trilingual).
2. Screenshot timestamps reflect generation time (relative "ago" labels);
   structural — not pixel — comparison is used for regression.
3. Live-crawl (Bright Data), live AI chat (Muse Spark) and MySQL/Redis
   integration runs need external credentials/services (see README).
4. Installed `redis-py` is 4.6.0 while requirements allow ≥5.0; the app and
   tests now tolerate both.

## 13. External credentials required

- `BRIGHTDATA_API_KEY` / `BRIGHTDATA_ZONE` — large-scale crawling.
- `MUSE_SPARK_BASE_URL` / `MUSE_SPARK_API_KEY` — live AI chat.
- MySQL / Redis URLs — production persistence and shared queues.

## 14. Remaining risks

- Combined-suite STORE sharing: two fixtures hardened (unique names + real
  STIX node mapping); future tests must use unique fixture keys.
- `graph.add_edge` id scheme (`len()+1`) assumes append-only stores.
- Test runs write `data/vectors.json` (semantic index default DATA_DIR);
  cosmetic tracked-file churn, pre-existing.
