---
title: Your First Investigation
description: A complete 20-step walkthrough: domain to report, with real screenshots at every step.
category: Getting Started
order: 20
slug: getting-started/first-investigation
language: en
shots: [03-new-investigation.png, 04-target-type.png, 05-target.png, 06-scope.png, 08-review.png, 09-queued.png, 10-running.png, 11-completed.png, 12-findings.png, 14-graph.png, 15-risk.png, 17-evidence.png, 18-case.png, 19-report.png, 20-watchlist.png, 21-alert.png, 22-workflow.png]
---

# Your First Investigation

> A complete 20-step walkthrough: domain to report, with real screenshots at every step.

Usable by a non-technical reader. Each step shows the real screen, what to do, what the platform does in response, what to verify, and the mistake everyone makes once.

> Safety: use `example.com` or your own authorized systems for these steps. Never scan targets you are not allowed to investigate.

### Step 1 — Open Web Intelligence

![Web Intelligence hero dashboard with KPIs, trends, risk and activity.](shot:02-dashboard.png)

**What to do:** Open the application in your browser and sign in if your server requires it.

**What happens:** You see the hero dashboard. On a fresh database it is mostly zeros — that is correct and honest.

**What to check:** Confirm the footer shows the application version and the timestamps read WIB.

**Common mistake:** Do not paste credentials or tokens into the global search box.

### Step 2 — Open New Investigation

![Web Intelligence New Investigation wizard showing target type selection.](shot:03-new-investigation.png)

**What to do:** Click **+ New Investigation** in the page header.

**What happens:** The 5-step wizard opens: What, Target, Scope, Sources, Review. The workspace project resolves through the API — never a silent project_id=1.

**What to check:** Confirm your project will be resolved (the wizard reuses the Investigations workspace or creates it via the API).

**Common mistake:** Starting without checking the project litters the wrong workspace.

### Step 3 — Choose Website / Domain

![Target type selection inside the New Investigation wizard.](shot:04-target-type.png)

**What to do:** Select the **Website / Domain** target type.

**What happens:** The wizard adapts: domain targets unlock DNS, subdomain and certificate scope options. Eight types exist: domain, URL, IP, organization, email, identity, keyword and custom.

**What to check:** Confirm the domain option is highlighted.

**Common mistake:** Picking keyword for a domain loses the DNS and TLS collectors.

### Step 4 — Enter your target

![Entering a domain target in the New Investigation wizard.](shot:05-target.png)

**What to do:** Type `example.com` — a safe, IANA-reserved demonstration domain. Never scan systems you are not authorized to investigate.

**What happens:** Real validation runs per type: domains must look like domains, URLs need a scheme, IPs must parse, emails must parse.

**What to check:** Confirm the target is accepted (validation errors appear inline instead).

**Common mistake:** Do not enter intranet hostnames, private IPs or customer data in a shared demo.

### Step 5 — Choose scope — profile follows automatically

![Scope selection: DNS, subdomains, TLS, technologies and more.](shot:06-scope.png)

**What to do:** Tick DNS, Subdomains, TLS / Certificates, Web Technologies, Web Content, Infrastructure, Related Entities, Documents, Threat Intelligence and Risk Analysis — or a subset you care about. There is no separate depth picker: infrastructure scope means a deep run, subdomains/TLS/tech/content means standard, anything smaller means quick.

**What happens:** Each scope maps to real collectors and analyzers; unselected scopes simply do not run. Only real, configured collectors are listed.

**What to check:** Confirm at least DNS and TLS are selected for a domain, and read the auto-derived scan profile.

**Common mistake:** Selecting everything on a first run makes results harder to read.

### Step 6 — Check sources

![Projects, targets and connectors as data sources.](shot:07-sources.png)

**What to do:** Read the sources screen: configured collectors and live system status, then Continue.

**What happens:** Anything not configured must be set up under Connectors — nothing here is faked.

**What to check:** Confirm the collectors you need show as ready.

**Common mistake:** Assuming an unconfigured collector will still run.

### Step 7 — Review

![Reviewing the investigation before starting collection.](shot:08-review.png)

**What to do:** Read the review screen: type, target, scope and profile. It lists exactly what Start will do: create the investigation, register the target, queue a collection job, run recon, link the target to the investigation.

**What happens:** This is your last cheap chance to fix a typo before collection starts.

**What to check:** Confirm the target and scope match your intent.

**Common mistake:** Skipping review is how investigations collect the wrong target.

### Step 8 — Start the investigation

![A newly created collection job on its scan page showing the queued state.](shot:09-queued.png)

**What to do:** Press **Start Investigation** and watch the Operations drawer.

**What happens:** The wizard works through five visible stages — creating the investigation, registering the target, queueing the collection job, running recon, linking results — then reports the outcome and opens the investigation. The scan page badge reads queued while the job waits.

**What to check:** Confirm each stage ticks over in Operations; on failure the error appears inline instead of a success toast.

**Common mistake:** Closing the tab mid-run is safe (collection continues server-side), but you will miss the failure message if one occurs.

### Step 9 — Watch it run

![The same collection job running, with attempts accumulating on the scan page.](shot:10-running.png)

**What to do:** Stay on the scan page or come back later; press Refresh.

**What happens:** Jobs move to **running** and attempts accumulate as collectors report. The Scan page shows the live status badge with Run, Retry and Cancel actions.

**What to check:** Confirm the status badge reads running and the attempts list grows.

**Common mistake:** Do not hammer Run — duplicate jobs do not make collection faster.

### Step 10 — Wait for success

![The collection job finished with success, attempts, prices and changes attached.](shot:11-completed.png)

**What to do:** Let every job reach a terminal state.

**What happens:** **Success** means results are in (the completion toast calls it completed). Failed jobs show their error, attempts and a retry button — failure is reported, never hidden.

**What to check:** Confirm every job shows success or failed with a reason.

**Common mistake:** Treating success as verified truth — findings still need triage.

### Step 11 — Open Findings

![Triaging correlated findings with severity and confidence.](shot:12-findings.png)

**What to do:** Open the **Findings** tab.

**What happens:** Correlation has produced candidate findings with severity, confidence and evidence links.

**What to check:** Confirm each finding links to at least one evidence record.

**Common mistake:** Resolving everything without reading evidence first.

### Step 12 — Open the entity graph

![The intelligence graph: companies, domains and infrastructure linked.](shot:14-graph.png)

**What to do:** Open **Intelligence Graph**.

**What happens:** Domains, IPs, companies and technologies appear as linked nodes. Traverse, pivot and find the shortest path between any two nodes.

**What to check:** Confirm the target domain connects to at least one IP or technology node.

**Common mistake:** Loading the entire graph unfiltered on huge investigations is slow — filter first.

### Step 13 — Read the risk analysis

![Explainable 0-100 risk with factors and evidence.](shot:15-risk.png)

**What to do:** Open **Risk Analysis** for the target.

**What happens:** An explainable 0–100 score with factors and the evidence behind each. Risk is a prioritization signal, not proof of malicious activity.

**What to check:** Confirm every factor cites evidence.

**Common mistake:** Quoting a risk score to a third party as a verdict.

### Step 14 — Preserve evidence

![Evidence records with source, timestamp and integrity.](shot:17-evidence.png)

**What to do:** Open **Evidence** and verify the captures.

**What happens:** Each record carries source, timestamp, hash and snippet — the provenance your report will cite.

**What to check:** Confirm hashes are present before citing anything externally.

**Common mistake:** Screenshots of the UI are illustrations, not evidence. Cite evidence records.

### Step 15 — Create a case

![Case workspace with notes, tasks and linked objects.](shot:18-case.png)

**What to do:** Create a **Case** from the investigation.

**What happens:** Notes, tasks, members and links to entities, findings and evidence live here. This is where analysis becomes assigned work.

**What to check:** Confirm the case links back to the investigation.

**Common mistake:** Doing case work in chat threads nobody can audit later.

### Step 16 — Generate a report

![Generated report with export formats.](shot:19-report.png)

**What to do:** Generate a **Report** from the case.

**What happens:** Web, PDF, CSV, JSON, XLSX or Markdown — each generated from the same evidence-backed data.

**What to check:** Confirm the report lists its evidence references.

**Common mistake:** Editing a report to say what the evidence does not.

### Step 17 — Add the target to a watchlist

![Watchlist entries evaluated against new intelligence.](shot:20-watchlist.png)

**What to do:** Add the domain to a **Watchlist**.

**What happens:** Future mentions, changes and matches will surface automatically.

**What to check:** Confirm the entry evaluates cleanly with Evaluate.

**Common mistake:** Watchlisting overly broad keywords creates alert noise.

### Step 18 — Configure an alert

![Alert queue with acknowledge and resolve actions.](shot:21-alert.png)

**What to do:** Create an **Alert** rule on the watchlist.

**What happens:** Severity, channel and acknowledge/resolve lifecycle included. Alerts queue human attention.

**What to check:** Confirm a test alert arrives through the configured channel.

**Common mistake:** Routing every severity to paging — reserve paging for critical.

### Step 19 — Configure a workflow

![Workflow automation with runs and retry.](shot:22-workflow.png)

**What to do:** Create a **Workflow**: trigger → action.

**What happens:** For example: on a high finding, open a case and notify the webhook. Runs, idempotent retry and cancel are all visible.

**What to check:** Confirm a manual run completes and appears in run history.

**Common mistake:** Automating irreversible actions without a manual approval step.

### Step 20 — See the whole lifecycle

![The collection job finished with success, attempts, prices and changes attached.](shot:11-completed.png)

**What to do:** Re-read [The Investigation Lifecycle](/docs/investigations/investigation-lifecycle) with your completed case in mind.

**What happens:** You have now touched all fourteen stages: search to monitor.

**What to check:** Confirm you can explain each stage to a colleague using your own case as the example.

**Common mistake:** Stopping at findings and never building the case or report.

## Related

- [Web Intelligence Documentation](/docs/index)
- [What Is Web Intelligence?](/docs/getting-started/overview)
- [Sign In & Authentication](/docs/getting-started/login)
- [Using the Dashboard](/docs/getting-started/dashboard)
- [5 Minutes to First Result](/docs/getting-started/5-minute-investigation)
