# Web Intelligence — Settings UX Final Report

_Sectioned shell, real persistence, verified saves._

## Information architecture

- General (org, plan, versions, timezone, templates)
- Workspace (investigation scope defaults, AI default pointer)
- Search (mode, limit)
- Appearance (theme, sidebar, navbar, language, accent, density, layout)
- Security (keys, users/roles, production requirements)
- Collection (connectors, Bright Data test, browser, scheduler)
- Notifications (webhooks, alerts, maintenance windows)
- Integrations (AI providers, feature flags)
- Data (backup with verification, retention, data quality)
- System (live facts, doctor, diagnostics export)

## Save-state honesty

- Server forms: UNCHANGED → EDITING (dirty badge + beforeunload guard) → SAVING → SAVED (reloaded + verified) or FAILED with the real reason.
- Reset restores factory defaults for workspace/search/timezone only, confirmed first.
- Appearance applies instantly per browser and says so.

## Verified

- Round-trip + validation + reload persistence (`test_settings_defaults.py`).
- Wizard prefills saved scope; console preselects saved mode.
- Section search filter, responsive shell, RTL-safe layout.
