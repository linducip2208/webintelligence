---
title: Investigation Profiles: Quick, Standard, Deep
description: What each depth collects, how long it takes, and when to use it.
category: Investigations
order: 50
slug: investigations/profiles
language: en
shots: []
---

# Investigation Profiles: Quick, Standard, Deep

> What each depth collects, how long it takes, and when to use it.

Quick, Standard and Deep are derived from scope automatically: infrastructure scope means deep (+RDAP/WHOIS), subdomains/TLS/tech/content means standard, anything smaller means quick. There is no separate depth picker to get wrong.

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


## Related

- [Create an Investigation](/docs/investigations/create-investigation)
- [Target Types](/docs/investigations/target-types)
- [Choosing Scope](/docs/investigations/scope)
- [Projects, Targets & Sources](/docs/investigations/sources)
- [Collection: Queued, Running, Success](/docs/investigations/collection)
