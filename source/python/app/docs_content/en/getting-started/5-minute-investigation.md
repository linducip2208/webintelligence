---
title: 5 Minutes to First Result
description: Understand the entire product in five minutes: login to report in ten steps.
category: Getting Started
order: 25
slug: getting-started/5-minute-investigation
language: en
shots: [03-new-investigation.png, 11-completed.png, 14-graph.png, 15-risk.png, 19-report.png]
---

# 5 Minutes to First Result

> Understand the entire product in five minutes: login to report in ten steps.

Ten steps, about five minutes, one complete mental model of the product.

> Safety: use `example.com` or your own authorized systems.

### Step 1 — Login

![Web Intelligence hero dashboard with KPIs, trends, risk and activity.](shot:02-dashboard.png)

**What to do:** Open the application in your browser and sign in if your server requires it.

**What happens:** You see the hero dashboard. On a fresh database it is mostly zeros — that is correct and honest.

**What to check:** Confirm the footer shows the application version and the timestamps read WIB.

**Common mistake:** Do not paste credentials or tokens into the global search box.

### Step 2 — Dashboard

![Web Intelligence New Investigation wizard showing target type selection.](shot:03-new-investigation.png)

**What to do:** Click **+ New Investigation** in the page header.

**What happens:** The 5-step wizard opens: What, Target, Scope, Sources, Review. The workspace project resolves through the API — never a silent project_id=1.

**What to check:** Confirm your project will be resolved (the wizard reuses the Investigations workspace or creates it via the API).

**Common mistake:** Starting without checking the project litters the wrong workspace.

### Step 3 — New Investigation

![Entering a domain target in the New Investigation wizard.](shot:05-target.png)

**What to do:** Type `example.com` — a safe, IANA-reserved demonstration domain. Never scan systems you are not authorized to investigate.

**What happens:** Real validation runs per type: domains must look like domains, URLs need a scheme, IPs must parse, emails must parse.

**What to check:** Confirm the target is accepted (validation errors appear inline instead).

**Common mistake:** Do not enter intranet hostnames, private IPs or customer data in a shared demo.

### Step 4 — Domain

![Scope selection: DNS, subdomains, TLS, technologies and more.](shot:06-scope.png)

**What to do:** Tick DNS, Subdomains, TLS / Certificates, Web Technologies, Web Content, Infrastructure, Related Entities, Documents, Threat Intelligence and Risk Analysis — or a subset you care about. There is no separate depth picker: infrastructure scope means a deep run, subdomains/TLS/tech/content means standard, anything smaller means quick.

**What happens:** Each scope maps to real collectors and analyzers; unselected scopes simply do not run. Only real, configured collectors are listed.

**What to check:** Confirm at least DNS and TLS are selected for a domain, and read the auto-derived scan profile.

**Common mistake:** Selecting everything on a first run makes results harder to read.

### Step 5 — Scope

![A newly created collection job on its scan page showing the queued state.](shot:09-queued.png)

**What to do:** Press **Start Investigation** and watch the Operations drawer.

**What happens:** The wizard works through five visible stages — creating the investigation, registering the target, queueing the collection job, running recon, linking results — then reports the outcome and opens the investigation. The scan page badge reads queued while the job waits.

**What to check:** Confirm each stage ticks over in Operations; on failure the error appears inline instead of a success toast.

**Common mistake:** Closing the tab mid-run is safe (collection continues server-side), but you will miss the failure message if one occurs.

### Step 6 — Start

![The collection job finished with success, attempts, prices and changes attached.](shot:11-completed.png)

**What to do:** Let every job reach a terminal state.

**What happens:** **Success** means results are in (the completion toast calls it completed). Failed jobs show their error, attempts and a retry button — failure is reported, never hidden.

**What to check:** Confirm every job shows success or failed with a reason.

**Common mistake:** Treating success as verified truth — findings still need triage.

### Step 7 — Results

![Triaging correlated findings with severity and confidence.](shot:12-findings.png)

**What to do:** Open the **Findings** tab.

**What happens:** Correlation has produced candidate findings with severity, confidence and evidence links.

**What to check:** Confirm each finding links to at least one evidence record.

**Common mistake:** Resolving everything without reading evidence first.

### Step 8 — Graph

![The intelligence graph: companies, domains and infrastructure linked.](shot:14-graph.png)

**What to do:** Open **Intelligence Graph**.

**What happens:** Domains, IPs, companies and technologies appear as linked nodes. Traverse, pivot and find the shortest path between any two nodes.

**What to check:** Confirm the target domain connects to at least one IP or technology node.

**Common mistake:** Loading the entire graph unfiltered on huge investigations is slow — filter first.

### Step 9 — Risk

![Explainable 0-100 risk with factors and evidence.](shot:15-risk.png)

**What to do:** Open **Risk Analysis** for the target.

**What happens:** An explainable 0–100 score with factors and the evidence behind each. Risk is a prioritization signal, not proof of malicious activity.

**What to check:** Confirm every factor cites evidence.

**Common mistake:** Quoting a risk score to a third party as a verdict.

### Step 10 — Report

![Generated report with export formats.](shot:19-report.png)

**What to do:** Generate a **Report** from the case.

**What happens:** Web, PDF, CSV, JSON, XLSX or Markdown — each generated from the same evidence-backed data.

**What to check:** Confirm the report lists its evidence references.

**Common mistake:** Editing a report to say what the evidence does not.

### Expected result

A completed investigation with findings, a small graph, a risk score and a generated report — plus a watchlist entry keeping an eye on the domain after you leave.

## Related

- [Web Intelligence Documentation](/docs/index)
- [What Is Web Intelligence?](/docs/getting-started/overview)
- [Sign In & Authentication](/docs/getting-started/login)
- [Using the Dashboard](/docs/getting-started/dashboard)
- [Your First Investigation](/docs/getting-started/first-investigation)
