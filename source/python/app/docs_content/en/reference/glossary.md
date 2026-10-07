---
title: Glossary
description: Every term that matters: entity to collection strategy, with examples.
category: Reference
order: 10
slug: reference/glossary
language: en
shots: []
---

# Glossary

> Every term that matters: entity to collection strategy, with examples.

Each term: what it is, why it matters, and a concrete example.

### Entity

**Definition:** A distinct real-world thing the platform tracks: person, company, domain, IP, email, technology.

**Why it matters:** Resolution turns noisy mentions into one confident identity; everything else hangs off entities.

**Example:** Acme Corporation resolved from three different spellings across two sources.

### Indicator

**Definition:** A distilled signal of interest, often an IOC: a malicious IP, a phishing domain, a bad hash.

**Why it matters:** Indicators feed STIX/MISP exchange and watchlist matching.

**Example:** 203.0.113.10 flagged after resolving three phishing domains in one hour.

### Finding

**Definition:** A correlated, analyst-triaged result with severity, confidence, evidence and lineage.

**Why it matters:** Findings are the unit of triage: OPEN to CONFIRMED, ACCEPTED or FALSE_POSITIVE, ending at RESOLVED — never silently dropped.

**Example:** Exposed admin panel on acme.example, severity high, confidence 0.8.

### Evidence

**Definition:** A preserved source record: URL, timestamp, hash and snippet proving what was seen.

**Why it matters:** No claim or finding ships without evidence_ids pointing here.

**Example:** HTTP capture of https://acme.example with content hash at collection time.

### Claim

**Definition:** An assertion that must be verified against evidence before anyone trusts it.

**Why it matters:** Verification marks claims confirmed or contradicted; contradictions raise flags.

**Example:** Claim: acme.example runs nginx — verified against two captures.

### Investigation

**Definition:** A scoped work unit with target, depth, scope, lifecycle status and linked entities.

**Why it matters:** Investigations move open to investigating to completed; cases bundle them for action.

**Example:** Acme exposure review: domain target, standard profile, completed.

### Case

**Definition:** The action container: notes, tasks, members, links to entities, findings and evidence.

**Why it matters:** Cases turn analysis into assigned, trackable work ending in a report.

**Example:** Acme case: two findings, one evidence record, three tasks.

### Target

**Definition:** A monitored site or identifier inside a project, with a learning profile.

**Why it matters:** Targets carry reliability scores from real collection history.

**Example:** https://acme.example watched for TLS and technology changes.

### Collector

**Definition:** An engine that fetches data: the Go collector, the browser pool, or an API adapter.

**Why it matters:** Collectors escalate along the strategy ladder when the simple path fails.

**Example:** Go collector fetched acme.example directly in 1.2s.

### Connector

**Definition:** A configured RSS, paginated REST or CSV source that can be tested and executed.

**Why it matters:** Connectors turn outside feeds into articles and datasets on a schedule.

**Example:** Sector-news RSS executed nightly into the articles store.

### Intelligence Graph

**Definition:** Nodes and edges with confidence: companies own domains, domains resolve to IPs.

**Why it matters:** Traversal and shortest path reveal relationships no single record shows.

**Example:** Acme OWNS acme.example RESOLVES_TO 203.0.113.10.

### Pivot

**Definition:** A transform that expands one entity into related ones: domain to IP to domain.

**Why it matters:** Pivoting is how one clue becomes a network.

**Example:** From acme.example to its IP to three sibling domains on the same host.

### Risk

**Definition:** An explainable 0-100 score built from factors, each backed by evidence.

**Why it matters:** Risk is an analytical signal for prioritization — not proof of malicious activity.

**Example:** acme.example scores 72: exposed panel (+30), outdated library (+25), new cert (+17).

### Watchlist

**Definition:** A keyword, company or domain subscription evaluated against new intelligence.

**Why it matters:** Matches raise alerts; evaluation can run on demand or on schedule.

**Example:** Watch acme so every new mention raises an alert.

### Alert

**Definition:** A fired notification with severity, status and acknowledge/resolve lifecycle.

**Why it matters:** Alerts queue human attention; bulk operations keep the queue manageable.

**Example:** New asset alert for api.acme.example, severity info.

### Workflow

**Definition:** Trigger-to-action automation with visible runs, idempotent retry and cancel.

**Why it matters:** Workflows connect detection to response without hiding state.

**Example:** On high finding: open a case and notify the webhook.

### STIX

**Definition:** Structured Threat Information Expression 2.1: bundles of typed threat objects.

**Why it matters:** The platform exports a documented subset, validates it, and imports with dedupe.

**Example:** Acme indicators exported as a STIX 2.1 bundle for sharing.

### MISP

**Definition:** Malware Information Sharing Platform events with attributes and galaxies.

**Why it matters:** Export events with attributes and tags; import maps them back to entities.

**Example:** Acme event with three attributes pushed to the sharing community.

### IOC

**Definition:** Indicator of Compromise: an artifact observed in malicious activity.

**Why it matters:** IOCs are indicators with teeth — handle them as response triggers.

**Example:** Phishing URL first seen in the feed, now on the domain watchlist.

### OSINT

**Definition:** Open-source intelligence: insight from publicly available data.

**Why it matters:** The platform only collects public data and respects robots.txt and terms.

**Example:** Certificate transparency logs revealing a new subdomain.

### Attack Surface

**Definition:** The sum of exposed assets: subdomains, IPs, ports, technologies, certificates.

**Why it matters:** You cannot defend what you cannot see; the overview lists it all.

**Example:** Fourteen hosts, two outdated libraries, one expiring certificate.

### Reconnaissance

**Definition:** Active information gathering: DNS, TLS, technology and WHOIS/RDAP scans.

**Why it matters:** Each scan is recorded with its method so results stay reproducible.

**Example:** Deep scan of acme.example captured DNS, TLS and RDAP in one pass.

### Data Source

**Definition:** Any origin of records: projects, targets, connectors or documents.

**Why it matters:** Source health and reliability decide how much to trust what arrives.

**Example:** The sector RSS connector, healthy for 30 consecutive runs.

### Research Run

**Definition:** A planned, analyzed and finished AI-assisted research session with exports.

**Why it matters:** Runs keep AI work reproducible instead of chat-shaped and forgettable.

**Example:** Competitor pricing research finished with a Markdown export.

### Entity Resolution

**Definition:** Matching, merging and splitting mentions into canonical entities.

**Why it matters:** Confidence scores record how sure the match is — and what would change it.

**Example:** Three admin@ variants merged into one email entity at 0.92.

### Data Lineage

**Definition:** The chain from raw collection to finding: every hop recorded.

**Why it matters:** Lineage makes findings auditable and retractions possible.

**Example:** Finding 7 traces to job 3, document 5 and evidence 9.

### Confidence

**Definition:** A 0-1 or percentage estimate of how sure a record, match or score is.

**Why it matters:** Confidence separates strong leads from noise without hiding either.

**Example:** Entity match at 0.92 confidence after three corroborating sources.

### Severity

**Definition:** Critical, high, medium, low or info: how urgently a finding or alert needs humans.

**Why it matters:** Severity drives triage order and workflow triggers.

**Example:** Exposed admin panel: high severity, open status.

### Collection Strategy

**Definition:** The escalation ladder DIRECT, API, BROWSER, OWN_PROXY, BRIGHT_DATA.

**Why it matters:** The decider picks the cheapest strategy that can succeed for each target.

**Example:** acme.example collected DIRECT; the JS-heavy portal needed BROWSER.

## Related

- [Functional Status](/docs/functional-status)
- [Statuses](/docs/reference/statuses)
- [Risk Scoring](/docs/reference/risk-scoring)
- [Entity Types](/docs/reference/entity-types)
- [Collection Strategies](/docs/reference/collection-strategies)
