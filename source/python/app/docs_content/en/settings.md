---
title: Settings Guide
description: The sectioned settings shell: what is stored where, and what each save does.
category: Administration
order: 45
slug: settings
language: en
shots: [26-settings.png]
---

# Settings Guide

> The sectioned settings shell: what is stored where, and what each save does.

## The shell

Settings is a sectioned workspace, not a database table:

- **General** — organization, plan, versions, industry templates.
- **Workspace** — investigation scope defaults (prefill the wizard) and the AI default pointer. Saved server-side and reloaded to verify.
- **Search** — default mode and result count for the console. Saved server-side.
- **Appearance** — theme, sidebar, navbar, language, accent. Stored in this browser by design.
- **Security** — API keys, users and roles, production auth requirements.
- **Collection** — connectors, Bright Data test, browser pool, scheduler.
- **Notifications** — webhooks, alerts, maintenance windows.
- **Integrations** — AI providers page plus feature flags.
- **Data** — backup download, retention runs, data-quality checks.
- **System** — live facts (versions, backends, counts) plus the system doctor.

## Save behavior

Every server-side form loads actual values, validates, persists, reloads and verifies — showing `Settings saved` or the real reason it failed. Browser-side appearance controls apply instantly. Nothing silently swallows errors.

## Related

- [API Keys](/docs/administration/api-keys)
- [System Health](/docs/administration/system-health)
- [Backup & Restore](/docs/administration/backup)


## Screenshots

![Administration settings: security, collectors, scheduler and storage.](shot:26-settings.png)

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/flags` | Flags List |
| `POST` | `/api/v1/flags` | Flags Set |
| `GET` | `/api/v1/settings/defaults` | Settings Defaults Get |
| `PATCH` | `/api/v1/settings/defaults` | Settings Defaults Patch |
| `GET` | `/api/v1/settings/system` | Settings System |


## Related

- [Users & Roles](/docs/administration/users)
- [Roles & Permissions](/docs/administration/roles)
- [Organizations & Branding](/docs/administration/organizations)
- [API Keys](/docs/administration/api-keys)
- [Settings](/docs/administration/settings)
