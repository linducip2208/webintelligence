---
title: Target Types
description: Domain, URL, IP, email, organization, identity or keyword — what each unlocks.
category: Investigations
order: 20
slug: investigations/target-types
language: en
shots: [04-target-type.png]
---

# Target Types

> Domain, URL, IP, email, organization, identity or keyword — what each unlocks.

Eight real target types: domain, URL, IP, organization, email, identity, keyword and custom. Each unlocks different collectors and carries its own real validation.

## Screenshots

![Target type selection inside the New Investigation wizard.](shot:04-target-type.png)

## Why it matters

This concept exists so analysts spend time on judgment, not plumbing. Understand it once and every related view reads naturally.

## Example

A domain investigation touches this concept within the first minutes: the wizard asks for it, collection produces it, and the graph, risk and findings views each show their side of it.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/investigations` | List Investigations |
| `POST` | `/api/v1/investigations` | Create Investigation |
| `GET` | `/api/v1/investigations/{iid}` | Get Investigation |
| `PUT` | `/api/v1/investigations/{iid}` | Update Investigation |
| `DELETE` | `/api/v1/investigations/{iid}` | Delete Investigation |
| `POST` | `/api/v1/investigations/{iid}/links` | Investigation Link |
| `POST` | `/api/v1/investigations/{iid}/members` | Investigation Member Add |
| `POST` | `/api/v1/investigations/{iid}/notes` | Investigation Note |
| `POST` | `/api/v1/investigations/{iid}/tasks` | Investigation Task Add |
| `POST` | `/api/v1/investigations/{iid}/tasks/{tid}/toggle` | Investigation Task Toggle |
| `POST` | `/api/v1/investigations/{iid}/views` | Investigation View Save |
| `DELETE` | `/api/v1/investigations/{iid}/views/{name}` | Investigation View Delete |
| `GET` | `/api/v1/search` | Search |
| `GET` | `/api/v1/search/semantic` | Search Semantic |


## Related

- [Create an Investigation](/docs/investigations/create-investigation)
- [Choosing Scope](/docs/investigations/scope)
- [Projects, Targets & Sources](/docs/investigations/sources)
- [Investigation Profiles: Quick, Standard, Deep](/docs/investigations/profiles)
- [Collection: Queued, Running, Success](/docs/investigations/collection)
