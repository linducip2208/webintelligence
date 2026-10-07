"""Generate maintainable Markdown sources for the docs portal.

Reads the live FastAPI OpenAPI contract + app/docs_data.py registry and emits
source/python/app/docs_content/en/<slug>.md with frontmatter. Run from repo root:

    python scripts/docs/gen_content.py

ID/AR bodies for Getting Started are maintained by hand next to the output.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.main import app  # noqa: E402
from app import docs_data as D  # noqa: E402

SPEC = app.openapi()
PATHS = SPEC.get("paths", {})
OUT = os.path.join(ROOT, "source", "python", "app", "docs_content", "en")


def endpoints(prefixes):
    rows = []
    for path in sorted(PATHS):
        for pre in prefixes:
            if path == pre or path.startswith(pre.rstrip("/") + "/") or path.startswith(pre + "/"):
                ops = PATHS[path]
                for method in ("get", "post", "put", "delete", "patch"):
                    if method in ops:
                        op = ops[method]
                        rows.append((method.upper(), path,
                                     (op.get("summary") or "").strip()))
                break
    # exact-prefix pages like /api/v1/risk/target must also match /api/v1/risk/target/{tid}
    return rows


def api_table(prefixes):
    rows = endpoints(prefixes)
    if not rows:
        return "_No dedicated endpoints — this area is served through the pages listed under Related._\n"
    out = ["| Method | Endpoint | Description |", "|---|---|---|"]
    for m, p, s in rows:
        out.append(f"| `{m}` | `{p}` | {s or '—'} |")
    return "\n".join(out) + "\n"


def shot_fig(page):
    files = page[6]
    if not files:
        return ""
    lines = []
    for f in files[:6]:
        meta = next((s for s in D.SHOTS if s["file"] == f), None)
        alt = meta["desc"] if meta else f
        lines.append(f"![{alt}](shot:{f})\n")
    return "\n".join(lines)


def try_box(page):
    route = page[4]
    if not route or route.startswith("__"):
        return ""
    label = {"new-investigation": "Start New Investigation"}.get(route, "Open in application")
    return (f"> **Try it:** [{label}](/#{route}) — opens the live view in the application.\n\n")


def related_box(page):
    sibs = [p for p in D.pages_in_section(page[1]) if p[0] != page[0]][:5]
    if not sibs:
        return ""
    items = "\n".join(f"- [{D.title_of(p, 'en')}](/docs/{p[0]})" for p in sibs)
    return f"## Related\n\n{items}\n"


def frontmatter(page):
    return (f"---\ntitle: {page[8]}\ndescription: {page[11]}\ncategory: "
            f"{D.section_name(page[1], 'en')}\norder: {page[3]}\nslug: {page[0]}\n"
            f"language: en\nshots: [{', '.join(page[6])}]\n---\n\n")


# ---------------------------------------------------------------- per-page extras
EXTRA = {}

EXTRA["ai-providers"] = """## The honest model

- **Catalog, not hardcoding.** Twenty presets ship as data; every one maps to a protocol adapter. Nothing is listed that the backend cannot speak.
- **Configured is not connected.** A saved key means configured. Only a passing live test means connected. The UI shows both states separately.
- **Keys are never shown.** Responses carry `masked_key` (`••••••••abcd`) and `key_configured`; raw keys never appear in HTML, API output, logs or screenshots.
- **Tests are real.** Test Connection builds the adapter and probes auth, discovery and model availability — then stores status, latency and discovered models. Failures return structured codes, never stack traces.

## Add a provider

1. Open AI Providers and press **+ Add AI provider**.
2. Pick the preset (OpenAI, Anthropic, Google, Ollama, OpenCode Go/Zen, OpenRouter, Groq, DeepSeek, Mistral, xAI, Cohere, Together, Fireworks, Perplexity or a custom compatible endpoint).
3. Fill base URL, key and model. For Ollama there is no key — installed models are discovered live, never hardcoded.
4. Press **Test connection** and read latency plus the discovered model list.
5. **Save** (enabled after a successful test), or Save anyway and test later from the card.

## Use it

- Every Ask/research call accepts a provider and model, or falls back to the cascade: explicit → your default → organization default → system default → built-in fallbacks plus every enabled provider.
- Set the system default from any provider card (**Set as default**) or `POST /api/v1/ai/default`.
- When nothing is configured, AI features answer `AI analysis is not configured` with a link — never a traceback.

## Related

- [Provider Configuration](/docs/ai/provider-configuration)
- [Evidence-Grounded AI](/docs/ai/evidence-grounded-ai)
- [AI Privacy & Cost](/docs/ai/privacy)
- [AI API](/docs/api/ai)
"""

EXTRA["settings"] = """## The shell

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
"""

EXTRA["troubleshooting"] = """## Pick your symptom

- [Common Errors](/docs/troubleshooting/common-errors) — 401/429/413/500 and empty dashboards.
- [Collection Issues](/docs/troubleshooting/collection) — stuck in queued, failed jobs, no findings.
- [Database Issues](/docs/troubleshooting/database) — SQLite fallback, access denied, vanishing data.
- [Redis Issues](/docs/troubleshooting/redis) — queues and rate limits.
- [Browser Issues](/docs/troubleshooting/browser) — headless pool and renders.
- [AI Issues](/docs/troubleshooting/ai) — providers, models, latency.
- [STIX / MISP Issues](/docs/troubleshooting/stix) — validation and imports.

Every guide follows symptoms, cause, solution and verification.
"""

EXTRA["functional-status"] = """## Works out of the box

Dashboard, investigations, collection jobs with honest states, entities and resolution, knowledge graph, findings triage, explainable risk, evidence and lineage, cases, multi-format reports, watchlists, alerts, workflows, webhooks, STIX/MISP subset exchange, search in four modes, RBAC with organization isolation, audit log and the documentation portal itself.

## Needs configuration

- **Authentication:** set `REQUIRE_AUTH=1`, create users/keys/roles.
- **AI providers:** add at least one provider and pass a live test before AI features answer.
- **Schedules/workers:** run the worker tick for time-based collection.
- **Backups/retention:** schedule dumps and retention runs.

## Needs external tools or network

- **MySQL/Redis** for production persistence and shared queues (graceful fallbacks otherwise).
- **Bright Data** credentials for large-scale crawling.
- **Playwright Chromium** for the browser pool.
- **Go toolchain** to rebuild the collector.
- **Ollama** reachable for local models.

## Optional

Industry vertical templates, custom AI-compatible endpoints, OIDC, SMTP/webhook alert channels, aaPanel/Nginx fronting.

## Verify right now

- [System Health](/docs/administration/system-health) and `GET /readyz`.
- [Production Checklist](/docs/deployment/production-checklist).
- [API Coverage](/docs/api/overview) and the generated `docs/API_COVERAGE.md`.
"""

EXTRA["index"] = """## Start Here

New to the platform? Follow the path that matches your job:

- **[Your First Investigation](/docs/getting-started/first-investigation)** — the complete 20-step walkthrough with real screenshots.
- **[5 Minutes to First Result](/docs/getting-started/5-minute-investigation)** — the ten-step express tour.
- **[What Is Web Intelligence?](/docs/getting-started/overview)** — concepts in plain language.
- **[API Overview](/docs/api/overview)** — for developers.

## The investigation workflow

```text
SEARCH → TARGET → SCOPE → COLLECT → NORMALIZE → ENTITY RESOLUTION → GRAPH
  → CORRELATE → RISK → FINDINGS → EVIDENCE → CASE → REPORT → MONITOR
```

Read it stage by stage in [The Investigation Lifecycle](/docs/investigations/investigation-lifecycle).

## What do you want to do?

- [Investigate a domain](/docs/investigations/target-types) — start from a website or hostname.
- [Investigate an IP](/docs/investigations/target-types) — infrastructure-first analysis.
- [Investigate an email](/docs/investigations/target-types) — identity pivoting.
- [Investigate an organization](/docs/intelligence/entities) — company-centric intelligence.
- [Explore the graph](/docs/intelligence/graph) — relationships and pivots.
- [Analyze risk](/docs/intelligence/risk) — explainable 0–100 scoring.
- [Build a case](/docs/evidence/cases) — notes, tasks, members, links.
- [Generate a report](/docs/evidence/reports) — six export formats.

## Core capabilities

- **Collection that shows its work** — every job reports queued, running, success, failed or cancelled with retry and cancel. See [Collection](/docs/investigations/collection).
- **Knowledge graph with provenance** — nodes, edges, traversal and shortest path, every hop backed by evidence. See [Intelligence Graph](/docs/intelligence/graph).
- **Evidence before conclusions** — claims verify against sources; contradictions are flagged. See [Claims & Verification](/docs/evidence/claims).
- **Monitoring that closes the loop** — watchlists, alerts, workflows and webhooks. See [Watchlists](/docs/monitoring/watchlists).
- **Threat sharing without overclaiming** — a documented STIX 2.1 / MISP subset. See [STIX 2.1](/docs/integrations/stix).

## Security and deployment

- [Authentication](/docs/security/authentication) · [RBAC & Isolation](/docs/security/rbac) · [SSRF Protection](/docs/security/ssrf)
- [Requirements](/docs/deployment/requirements) · [aaPanel Guide](/docs/deployment/aapanel) · [Production Checklist](/docs/deployment/production-checklist)
"""

EXTRA["getting-started/overview"] = """## The pipeline

```text
DATA → INFORMATION → KNOWLEDGE → EVIDENCE → INTELLIGENCE → DECISION SUPPORT
```

1. **Search / Investigate** — start from anything: domain, URL, IP, email, organization, identity or keyword.
2. **Collect** — jobs fetch web, API and document sources through the strategy ladder.
3. **Normalize** — raw captures become clean, comparable records with quality scores.
4. **Entity resolution** — mentions merge into confident identities.
5. **Relationship graph** — ownership, hosting and reference edges you can traverse.
6. **Correlation** — shared infrastructure becomes candidate findings.
7. **Risk** — explainable 0–100 scores with factors and evidence.
8. **Findings** — triage with severity, confidence and lineage.
9. **Evidence** — preserved sources with provenance and integrity.
10. **Case** — the action container: notes, tasks, members, links.
11. **Report** — six export formats for stakeholders.
12. **Monitor** — watchlists, alerts and workflows keep watching after you leave.

## Principles

- **Real data only.** The dashboard never shows sample numbers. An empty screen means no collection has run yet — and tells you how to start.
- **Evidence before conclusions.** AI output is labeled AI-generated; analyst conclusions cite evidence.
- **Async honesty.** Nothing claims completion when it is merely queued.
- **Respectful collection.** robots.txt and terms are honored; no login or CAPTCHA bypass.

## Where to go next

- Non-technical and in a hurry: [5 Minutes to First Result](/docs/getting-started/5-minute-investigation).
- Thorough: [Your First Investigation](/docs/getting-started/first-investigation).
- Responsible for infrastructure: [Requirements](/docs/deployment/requirements).
"""

EXTRA["getting-started/login"] = """## How sign-in works

Web Intelligence has two modes:

- **Development (default):** open. `REQUIRE_AUTH` is unset, so the UI and API work without credentials.
- **Production:** set `REQUIRE_AUTH=1`. Every `/api/v1/*` route then requires a **Bearer token** (from login) or an **X-API-Key** (scoped, expiring, revocable).

## Sign in from the UI

1. Open the application and click **Login** in the sidebar footer.
2. Enter email and password. The session keeps the token in memory only — never in localStorage.
3. The user chip in the sidebar changes from `anonymous` to `● signed in`.

![Sign in](shot:01-login.png)

### What to check

- After login, protected views load without 401 errors.
- **Common mistake:** using an API key (`wi_…`) in the password field. API keys belong in the token box or the `X-API-Key` header, not the login form.

## Sign in from the API

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email":"admin@local","password":"YOUR_PASSWORD"}'
```

```python
import httpx
r = httpx.post("http://127.0.0.1:8000/api/v1/auth/login",
               json={"email": "admin@local", "password": "YOUR_PASSWORD"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}
```

```javascript
const r = await fetch("http://127.0.0.1:8000/api/v1/auth/login", {
  method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify({email: "admin@local", password: "YOUR_PASSWORD"})
});
const {token} = await r.json();
```

## What happens

- Valid credentials return `{"token": ..., "email": ...}` and record an audit event.
- Wrong credentials return `401 bad credentials` and record a failed-login audit event.
- Bearer tokens are stateless HMAC: **logout** discards the client token and logs the event.

## Related

- [API Authentication](/docs/api/authentication)
- [API Keys](/docs/administration/api-keys)
- [RBAC & Organization Isolation](/docs/security/rbac)
"""

EXTRA["getting-started/dashboard"] = """## Reading the dashboard

The dashboard answers one question: **what needs my attention right now?** Every number comes from live data — a zero means nothing has happened yet, not that something is broken.

![Dashboard](shot:02-dashboard.png)

### What to do

1. Open `/` and press **Refresh** to reload all cards.
2. Scan the KPI row: jobs (success/failed), open alerts, price points, opportunities, data quality, AI calls.
3. Check **Overall Risk** and **Recent Alerts** first — they are ordered by severity.
4. Open the **Intelligence Graph** preview, then **Explore** for the full view.
5. Read **Intelligence Activity** for the latest feed events with Asia/Jakarta (WIB) timestamps.

### What to check

- Footer shows the real application version from `GET /api/version`.
- Language switcher (English / Indonesia / العربية) re-labels navigation; Arabic flips the layout to RTL.
- Theme button cycles light → dark → system; light is the default.

### Common mistake

Treating an empty dashboard as an error. On a fresh database it is correct: create a project, add a target, run a job — then refresh. See [5 Minutes to First Result](/docs/getting-started/5-minute-investigation).

## Related

- [Using Projects, Targets & Sources](/docs/investigations/sources)
- [Collection states](/docs/investigations/collection)
- [System Health](/docs/administration/system-health)
"""

FIRST_STEPS = [
    ("Open Web Intelligence", "02-dashboard.png",
     "Open the application in your browser and sign in if your server requires it.",
     "You see the hero dashboard. On a fresh database it is mostly zeros — that is correct and honest.",
     "Confirm the footer shows the application version and the timestamps read WIB.",
     "Do not paste credentials or tokens into the global search box."),
    ("Open New Investigation", "03-new-investigation.png",
     "Click **+ New Investigation** in the page header.",
     "The 5-step wizard opens: What, Target, Scope, Sources, Review. The workspace project resolves through the API — never a silent project_id=1.",
     "Confirm your project will be resolved (the wizard reuses the Investigations workspace or creates it via the API).",
     "Starting without checking the project litters the wrong workspace."),
    ("Choose Website / Domain", "04-target-type.png",
     "Select the **Website / Domain** target type.",
     "The wizard adapts: domain targets unlock DNS, subdomain and certificate scope options. Eight types exist: domain, URL, IP, organization, email, identity, keyword and custom.",
     "Confirm the domain option is highlighted.",
     "Picking keyword for a domain loses the DNS and TLS collectors."),
    ("Enter your target", "05-target.png",
     "Type `example.com` — a safe, IANA-reserved demonstration domain. Never scan systems you are not authorized to investigate.",
     "Real validation runs per type: domains must look like domains, URLs need a scheme, IPs must parse, emails must parse.",
     "Confirm the target is accepted (validation errors appear inline instead).",
     "Do not enter intranet hostnames, private IPs or customer data in a shared demo."),
    ("Choose scope — profile follows automatically", "06-scope.png",
     "Tick DNS, Subdomains, TLS / Certificates, Web Technologies, Web Content, Infrastructure, Related Entities, Documents, Threat Intelligence and Risk Analysis — or a subset you care about. There is no separate depth picker: infrastructure scope means a deep run, subdomains/TLS/tech/content means standard, anything smaller means quick.",
     "Each scope maps to real collectors and analyzers; unselected scopes simply do not run. Only real, configured collectors are listed.",
     "Confirm at least DNS and TLS are selected for a domain, and read the auto-derived scan profile.",
     "Selecting everything on a first run makes results harder to read."),
    ("Check sources", "07-sources.png",
     "Read the sources screen: configured collectors and live system status, then Continue.",
     "Anything not configured must be set up under Connectors — nothing here is faked.",
     "Confirm the collectors you need show as ready.",
     "Assuming an unconfigured collector will still run."),
    ("Review", "08-review.png",
     "Read the review screen: type, target, scope and profile. It lists exactly what Start will do: create the investigation, register the target, queue a collection job, run recon, link the target to the investigation.",
     "This is your last cheap chance to fix a typo before collection starts.",
     "Confirm the target and scope match your intent.",
     "Skipping review is how investigations collect the wrong target."),
    ("Start the investigation", "09-queued.png",
     "Press **Start Investigation** and watch the Operations drawer.",
     "The wizard works through five visible stages — creating the investigation, registering the target, queueing the collection job, running recon, linking results — then reports the outcome and opens the investigation. The scan page badge reads queued while the job waits.",
     "Confirm each stage ticks over in Operations; on failure the error appears inline instead of a success toast.",
     "Closing the tab mid-run is safe (collection continues server-side), but you will miss the failure message if one occurs."),
    ("Watch it run", "10-running.png",
     "Stay on the scan page or come back later; press Refresh.",
     "Jobs move to **running** and attempts accumulate as collectors report. The Scan page shows the live status badge with Run, Retry and Cancel actions.",
     "Confirm the status badge reads running and the attempts list grows.",
     "Do not hammer Run — duplicate jobs do not make collection faster."),
    ("Wait for success", "11-completed.png",
     "Let every job reach a terminal state.",
     "**Success** means results are in (the completion toast calls it completed). Failed jobs show their error, attempts and a retry button — failure is reported, never hidden.",
     "Confirm every job shows success or failed with a reason.",
     "Treating success as verified truth — findings still need triage."),
    ("Open Findings", "12-findings.png",
     "Open the **Findings** tab.",
     "Correlation has produced candidate findings with severity, confidence and evidence links.",
     "Confirm each finding links to at least one evidence record.",
     "Resolving everything without reading evidence first."),
    ("Open the entity graph", "14-graph.png",
     "Open **Intelligence Graph**.",
     "Domains, IPs, companies and technologies appear as linked nodes. Traverse, pivot and find the shortest path between any two nodes.",
     "Confirm the target domain connects to at least one IP or technology node.",
     "Loading the entire graph unfiltered on huge investigations is slow — filter first."),
    ("Read the risk analysis", "15-risk.png",
     "Open **Risk Analysis** for the target.",
     "An explainable 0–100 score with factors and the evidence behind each. Risk is a prioritization signal, not proof of malicious activity.",
     "Confirm every factor cites evidence.",
     "Quoting a risk score to a third party as a verdict."),
    ("Preserve evidence", "17-evidence.png",
     "Open **Evidence** and verify the captures.",
     "Each record carries source, timestamp, hash and snippet — the provenance your report will cite.",
     "Confirm hashes are present before citing anything externally.",
     "Screenshots of the UI are illustrations, not evidence. Cite evidence records."),
    ("Create a case", "18-case.png",
     "Create a **Case** from the investigation.",
     "Notes, tasks, members and links to entities, findings and evidence live here. This is where analysis becomes assigned work.",
     "Confirm the case links back to the investigation.",
     "Doing case work in chat threads nobody can audit later."),
    ("Generate a report", "19-report.png",
     "Generate a **Report** from the case.",
     "Web, PDF, CSV, JSON, XLSX or Markdown — each generated from the same evidence-backed data.",
     "Confirm the report lists its evidence references.",
     "Editing a report to say what the evidence does not."),
    ("Add the target to a watchlist", "20-watchlist.png",
     "Add the domain to a **Watchlist**.",
     "Future mentions, changes and matches will surface automatically.",
     "Confirm the entry evaluates cleanly with Evaluate.",
     "Watchlisting overly broad keywords creates alert noise."),
    ("Configure an alert", "21-alert.png",
     "Create an **Alert** rule on the watchlist.",
     "Severity, channel and acknowledge/resolve lifecycle included. Alerts queue human attention.",
     "Confirm a test alert arrives through the configured channel.",
     "Routing every severity to paging — reserve paging for critical."),
    ("Configure a workflow", "22-workflow.png",
     "Create a **Workflow**: trigger → action.",
     "For example: on a high finding, open a case and notify the webhook. Runs, idempotent retry and cancel are all visible.",
     "Confirm a manual run completes and appears in run history.",
     "Automating irreversible actions without a manual approval step."),
    ("See the whole lifecycle", "11-completed.png",
     "Re-read [The Investigation Lifecycle](/docs/investigations/investigation-lifecycle) with your completed case in mind.",
     "You have now touched all fourteen stages: search to monitor.",
     "Confirm you can explain each stage to a colleague using your own case as the example.",
     "Stopping at findings and never building the case or report."),
]

EXTRA["getting-started/index"] = None  # home page uses EXTRA["index"]
EXTRA["getting-started/first-investigation"] = None  # built programmatically below
EXTRA["getting-started/5-minute-investigation"] = None


def tutorial_body(page, steps, intro):
    lines = [intro, ""]
    for i, (title, shot, do, happens, check, mistake) in enumerate(steps, 1):
        meta = next((s for s in D.SHOTS if s["file"] == shot), None)
        alt = meta["desc"] if meta else title
        lines.append(f"### Step {i} — {title}\n")
        lines.append(f"![{alt}](shot:{shot})\n")
        lines.append(f"**What to do:** {do}\n")
        lines.append(f"**What happens:** {happens}\n")
        lines.append(f"**What to check:** {check}\n")
        lines.append(f"**Common mistake:** {mistake}\n")
    return "\n".join(lines)


def build_first(page):
    return tutorial_body(page, FIRST_STEPS,
        "Usable by a non-technical reader. Each step shows the real screen, "
        "what to do, what the platform does in response, what to verify, and the "
        "mistake everyone makes once.\n\n> Safety: use `example.com` or your own "
        "authorized systems for these steps. Never scan targets you are not "
        "allowed to investigate.")


def build_5min(page):
    short = [FIRST_STEPS[i] for i in (0, 1, 3, 4, 7, 9, 10, 11, 12, 15)]
    titles = ["Login", "Dashboard", "New Investigation", "Domain", "Scope",
              "Start", "Results", "Graph", "Risk", "Report"]
    renamed = [(t,) + s[1:] for t, s in zip(titles, short)]
    body = tutorial_body(page, renamed,
        "Ten steps, about five minutes, one complete mental model of the product.\n"
        "\n> Safety: use `example.com` or your own authorized systems.")
    return body + ("\n### Expected result\n\nA completed investigation with findings, "
        "a small graph, a risk score and a generated report — plus a watchlist entry "
        "keeping an eye on the domain after you leave.\n")


def lifecycle_body(page):
    lines = ["Click any stage to open its guide.\n",
             "```text",
             "SEARCH → TARGET → SCOPE → COLLECT → NORMALIZE → ENTITY RESOLUTION → GRAPH",
             "  → CORRELATE → RISK → FINDINGS → EVIDENCE → CASE → REPORT → MONITOR",
             "```\n"]
    for i, (name, slug, desc) in enumerate(D.LIFECYCLE, 1):
        lines.append(f"### Stage {i} — [{name}](/docs/{slug})\n\n{desc}\n")
    return "\n".join(lines)


def glossary_body(page):
    lines = ["Each term: what it is, why it matters, and a concrete example.\n"]
    for en, id_, ar, definition, why, example in D.GLOSSARY:
        lines.append(f"### {en}\n\n**Definition:** {definition}\n\n"
                     f"**Why it matters:** {why}\n\n**Example:** {example}\n")
    return "\n".join(lines)


HOWTO_INTRO = {
    "search": "One engine powers the search console, the dashboard hero search and Ctrl+K. Four modes, ranked results, filters, pagination and organization isolation — with no AI provider required for any mode.",
    "investigations/create-investigation": "The wizard has five steps — What, Target, Scope, Sources, Review — and one rule: the workspace project always resolves through the API, so results never land in the wrong place silently. The scan profile is derived from scope, not picked separately.",
    "investigations/target-types": "Eight real target types: domain, URL, IP, organization, email, identity, keyword and custom. Each unlocks different collectors and carries its own real validation.",
    "investigations/scope": "Ten real scopes — DNS, subdomains, TLS, tech, content, infra, entities, documents, threat, risk — decide which collectors and analyzers run, and derive the scan profile automatically.",
    "investigations/profiles": "Quick, Standard and Deep are derived from scope automatically: infrastructure scope means deep (+RDAP/WHOIS), subdomains/TLS/tech/content means standard, anything smaller means quick. There is no separate depth picker to get wrong.",
    "investigations/sources": "Projects isolate work per organization. Targets register what to watch. Connectors bring outside feeds in.",
    "investigations/collection": "Collection is asynchronous and honest: queued, running, success, failed or cancelled — each with attempts, errors, retry and cancel. (The UI toast says completed when the API records success; browser legs handed to workers report deferred until a worker picks them up.)",
    "discovery/targets": "Targets are the watched assets. Register them, test the connection, read the reliability score, then scan on demand or on schedule.",
    "discovery/reconnaissance": "Reconnaissance scans record their method with their results, so anyone can reproduce what was found.",
    "discovery/attack-surface": "The attack surface overview lists exposed assets per target: hosts, technologies, certificates and changes.",
    "discovery/collectors": "Collectors fetch. The strategy decider picks the cheapest working ladder rung per target; the browser pool handles JavaScript-heavy pages.",
    "discovery/connectors": "Connectors ingest RSS, paginated REST and CSV on a schedule. Test before executing; execute writes articles and datasets.",
    "discovery/data-sources": "Four families feed the platform: projects, targets, connectors and documents.",
    "intelligence/entities": "Entities are the people, companies, domains, IPs, emails and technologies under investigation — each with a confidence score.",
    "intelligence/entity-resolution": "Resolution merges duplicate mentions, splits wrong merges and rejects noise — with confidence recorded at every step.",
    "intelligence/graph": "The graph turns rows into relationships. Traverse from any node, pivot across kinds, and render the result as SVG.",
    "intelligence/pivoting": "Pivoting expands one clue into a network: domain to IP to sibling domains, certificates, technologies and emails.",
    "intelligence/findings": "Findings are correlated, triaged results. OPEN becomes CONFIRMED, ACCEPTED or FALSE_POSITIVE, ending at RESOLVED — with evidence and lineage attached.",
    "intelligence/indicators": "Indicators distill findings into shareable signals for watchlists, STIX bundles and MISP events.",
    "intelligence/risk": "Risk scores 0–100 with visible factors and evidence. A prioritization signal for analysts — never proof of malicious activity.",
    "intelligence/timeline": "The timeline orders every event chronologically so the story of an investigation reads top to bottom.",
    "intelligence/threat-intelligence": "Threat intelligence arrives through the feed, subscriptions and STIX/MISP exchange.",
    "intelligence/feed": "The feed is the live pulse: findings, changes and alerts as they happen, with personal views.",
    "evidence/evidence": "Evidence is preserved source material: URL, timestamp, hash and snippet. Cite it — screenshots of the UI are not evidence.",
    "evidence/documents": "Documents ingest text, HTML, CSV and PDF into the evidence store for claims and research to cite.",
    "evidence/claims": "Claims must verify against evidence. Contradictions surface automatically instead of hiding.",
    "monitoring/watchlists": "Watchlists subscribe to keywords, companies and domains. Evaluation runs on demand or on schedule.",
    "monitoring/alerts": "Alerts queue human attention with severity and a full acknowledge/resolve lifecycle, including bulk operations and incidents.",
    "monitoring/workflows": "Workflows automate trigger-to-action responses with visible runs, idempotent retry and cancel.",
    "monitoring/webhooks": "Outbound webhooks deliver events to your systems with delivery logs and replay for failures.",
    "integrations/stix": "STIX 2.1 exchange for sharing threat objects. This page documents the supported subset honestly.",
    "integrations/misp": "MISP event exchange mapped to entities. Supported attributes and galaxies are listed — nothing is overclaimed.",
    "integrations/security-tools": "Only real, adapter-backed tool integrations are documented here. Configuration, health checks and expected output per tool.",
    "integrations/external-apis": "Outside clients authenticate with scoped keys; inbound events arrive HMAC-signed.",
    "ai/providers": "Providers are added through the UI: choose, credential, test live, discover models, save. Keys are encrypted and never returned by the API.",
    "ai/provider-configuration": "Environment plus database configuration for OpenAI-compatible, Anthropic-compatible, Google-compatible and Ollama-style endpoints.",
    "ai/research": "Research runs keep AI-assisted analysis reproducible: plan, run, analyze, finish, compare, export.",
    "administration/users": "Members belong to organizations with roles. Disabling beats deleting for audit continuity.",
    "administration/organizations": "Organizations isolate data and carry white-label branding.",
    "administration/api-keys": "Keys are scoped, expirable, shown once and revocable.",
    "administration/settings": "One settings surface for general, security, collectors, scheduler, notifications, AI, storage, flags and billing.",
    "administration/audit-log": "Every mutation writes an audit record with actor, action and reference.",
    "administration/system-health": "Readiness, the system doctor and metrics — and what each check means for operators.",
    "administration/backup": "Backups for MySQL and SQLite, retention runs, and restore verification that proves recovery works.",
    "security/authentication": "Login, bearer tokens, OIDC, API keys and why production sets REQUIRE_AUTH=1.",
    "security/webhooks": "Inbound webhook ingestion verifies HMAC signatures inside a replay window.",
    "security/secrets": "Provider keys are encrypted, connector secrets masked, logs redacted — and rotation is a first-class action.",
}

HOWTO_STEPS = {
    "search": [
        "Open Global Search and type at least 2 characters.",
        "Pick a mode: Hybrid (default), Keyword, Semantic or Exact.",
        "Narrow with Type, Min risk and Source filters.",
        "Read the result summary: total count, query and mode.",
        "Act on cards: Open, Investigate, Add to Case, Watch, Create Finding or View Evidence.",
        "Page with limit/offset for large result sets.",
    ],
    "investigations/create-investigation": [
        "Open **New Investigation** from the header.",
        "Pick the target type (Website / Domain for websites).",
        "Enter the target and confirm real validation passes.",
        "Tick scope; read the auto-derived scan profile.",
        "Check the sources screen for ready collectors.",
        "Review type, target, scope and profile — then **Start** and watch Operations.",
    ],
    "investigations/scope": [
        "Start with DNS and TLS for any domain.",
        "Add subdomains and technologies for exposure mapping.",
        "Add content and documents when wording matters.",
        "Add threat intelligence when the target may be hostile.",
        "Always include risk analysis unless the run is purely archival.",
    ],
    "investigations/sources": [
        "Create a project first — everything else hangs off it.",
        "Register each target with domain and URL.",
        "Press **Test** to verify connectivity and get a strategy recommendation.",
        "Add connectors for recurring outside feeds.",
    ],
    "investigations/collection": [
        "Start the investigation and note the **queued** state on the scan page.",
        "Watch jobs turn **running**; refresh the scan page to see attempts accumulate.",
        "Wait for **success** (the toast calls it completed); read failures with their error and attempts.",
        "Use **retry** for transient failures, **cancel** for mistakes.",
        "Inspect the dead-letter queue for permanently failed work.",
    ],
}


def howto_body(page):
    slug = page[0]
    intro = EXTRA.get(slug) or HOWTO_INTRO.get(slug, D.title_of(page, "en") + " in practice.")
    lines = [intro, "", "## Prerequisites",
             "", "- A project exists and you can see it in Data Sources.",
             "- You know which target you are authorized to investigate.", ""]
    shots = shot_fig(page)
    if shots:
        lines += ["## Screenshots", "", shots]
    steps = HOWTO_STEPS.get(slug)
    if steps:
        lines += ["## Steps", ""]
        for i, s in enumerate(steps, 1):
            lines.append(f"{i}. {s}")
        lines.append("")
    else:
        lines += ["## Steps", "",
                  "1. Open the view with the **Try it** link below.",
                  "2. Follow the on-screen form — every action reports queued, running, completed, failed or cancelled.",
                  "3. Verify the result appears in the list and in the audit log.",
                  "4. Link the result into your investigation or case.", ""]
    if D.api_prefixes(page):
        lines += ["## API", "", api_table(D.api_prefixes(page)), ""]
        lines += ["## Examples", "", api_examples(D.api_prefixes(page)[0]), ""]
    lines += ["## Verification", "",
              "- The new or changed record is visible in the list view.",
              "- `GET /api/v1/audit?size=20` shows the action with your identity.",
              "- Related views (graph, timeline, feed) reflect the change.", "",
              "## Troubleshooting", "",
              "- Empty list: run collection first — the platform shows real data only.",
              "- 401: sign in or supply a key; see [Authentication](/docs/security/authentication).",
              "- 429: slow down; see [Rate Limits](/docs/api/rate-limits).", ""]
    lines.append(try_box(page))
    return "\n".join(lines)


def concept_body(page):
    slug = page[0]
    intro = EXTRA.get(slug) or HOWTO_INTRO.get(slug, D.title_of(page, "en") + ", explained in plain language.")
    lines = [intro, ""]
    shots = shot_fig(page)
    if shots:
        lines += ["## Screenshots", "", shots]
    lines += ["## Why it matters", "",
              "This concept exists so analysts spend time on judgment, not plumbing. "
              "Understand it once and every related view reads naturally.", "",
              "## Example", "",
              "A domain investigation touches this concept within the first minutes: "
              "the wizard asks for it, collection produces it, and the graph, risk and "
              "findings views each show their side of it.", ""]
    if D.api_prefixes(page):
        lines += ["## API", "", api_table(D.api_prefixes(page)), ""]
    return "\n".join(lines)


def api_examples(first_prefix):
    # find one representative POST/GET path for examples
    cands = endpoints([first_prefix])
    get_p = next((p for m, p, s in cands if m == "GET"), None)
    post_p = next((p for m, p, s in cands if m == "POST"), None)
    demo_get = get_p or "/api/v1/dashboard"
    demo_post = post_p or "/api/v1/search"
    return (f"```bash\ncurl http://127.0.0.1:8000{demo_get} "
            f"-H \"Authorization: Bearer TOKEN\"\n```\n\n"
            f"```python\nimport httpx\nr = httpx.get(\"http://127.0.0.1:8000{demo_get}\", "
            f"headers={{\"Authorization\": \"Bearer TOKEN\"}})\nprint(r.json())\n```\n\n"
            f"```javascript\nconst r = await fetch(\"http://127.0.0.1:8000{demo_get}\", "
            f"{{headers: {{Authorization: \"Bearer TOKEN\"}}}});\nconsole.log(await r.json());\n```\n\n"
            f"```bash\ncurl -X POST http://127.0.0.1:8000{demo_post} "
            f"-H \"Authorization: Bearer TOKEN\" -H \"Content-Type: application/json\" "
            f"-d '{{}}'\n```\n\n"
            "_Replace `TOKEN` with a real Bearer token or use `X-API-Key: wi_…`. "
            "Never commit real tokens to documentation._")


def api_body(page):
    desc = page[11]
    lines = [desc, "",
             "Authentication: Bearer token from `POST /api/v1/auth/login` or `X-API-Key` header. "
             "See [API Authentication](/docs/api/authentication).", ""]
    if D.api_prefixes(page):
        lines += ["## Endpoints", "", api_table(D.api_prefixes(page))]
        lines += ["## Examples", "", api_examples(D.api_prefixes(page)[0]), ""]
    lines += ["## Errors", "",
              "All errors share one envelope plus an `X-Request-ID` header:",
              "", "```json",
              '{"error": {"code": "unauthorized", "message": "unauthorized", "request_id": "abc123"}}',
              "```", "",
              "Codes: `bad_request` 400, `unauthorized` 401, `forbidden` 403, `not_found` 404, "
              "`conflict` 409, `too_large` 413, `validation` 422, `rate_limited` 429, "
              "`unavailable` 501/503. Full catalog: [Errors](/docs/api/errors).",
              "", "Pagination: `?page=&size=` (max 100).", ""]
    lines.append(try_box(page))
    return "\n".join(lines)


def reference_body(page):
    slug = page[0]
    if slug == "reference/statuses":
        return ("Every asynchronous operation — collection, recon, research, report, export, import, "
                "STIX/MISP and workflows — reports one of these states. The UI badges each state "
                "with an icon dot plus text, never color alone.\n\n"
                "| Status | Meaning | What to do |\n|---|---|---|\n"
                "| `queued` | Accepted and waiting for a worker. | Wait; check the worker tick for schedules. |\n"
                "| `running` | Executing now; refresh the scan page to watch attempts. | Watch the attempts list; do not duplicate. |\n"
                "| `success` | Finished with results attached (the UI toast calls this completed). | Review results; triage findings. |\n"
                "| `failed` | Finished with an error and attempts logged. | Read the error; retry transient failures. |\n"
                "| `cancelled` | Stopped by an operator. | Restart only if still needed. |\n"
                "| `deferred` | Browser/proxy leg handed to a worker. | Ensure the worker or browser pool runs. |\n"
                "| `open` / `investigating` / `pending` / `resolved` / `closed` | Investigation lifecycle (lowercase). | Advance deliberately; cases bundle the outcome. |\n"
                "| `OPEN` / `INVESTIGATING` / `PENDING` / `RESOLVED` / `CLOSED` | Case lifecycle (uppercase). | Close only with a report attached. |\n"
                "| `OPEN` / `CONFIRMED` / `FALSE_POSITIVE` / `RESOLVED` / `ACCEPTED` | Findings triage. | Confirm, accept, mark false positive, or resolve — with evidence attached. |\n"
                "| new / acked / resolved | Alerts (acknowledge and resolve endpoints, plus bulk). | Acknowledge to claim, resolve to finish. |\n")
    if slug == "reference/risk-scoring":
        return ("Scores run 0–100. Each factor adds weight and cites evidence; confidence reflects corroboration.\n\n"
                "| Band | Range | Meaning |\n|---|---|---|\n"
                "| Critical | 80–100 | Immediate analyst attention; verify before acting. |\n"
                "| High | 60–79 | Prioritize this week; check exposures. |\n"
                "| Medium | 40–59 | Track; re-evaluate on change. |\n"
                "| Low | 0–39 | Routine; monitor via watchlists. |\n\n"
                "Severity colors follow the same scale across findings, alerts and risk. "
                "Risk is an analytical signal — [never proof of malicious activity](/docs/intelligence/risk).\n\n"
                "Endpoints: `GET /api/v1/risk/target/{tid}`, `GET /api/v1/risk/entity/{eid}`.\n")
    if slug == "reference/entity-types":
        return ("| Type | Identity rule | Color |\n|---|---|---|\n"
                "| company | Normalized name + domain | blue |\n| domain | Lowercased FQDN | cyan |\n"
                "| ip | Canonical v4/v6 form | indigo |\n| email | Lowercased address | purple |\n"
                "| person | Name + corroborating attribute | green |\n| technology | Product + version | azure |\n"
                "| vulnerability | CVE identifier | red |\n| document | Content hash | gray |\n\n"
                "Resolution merges on rules, never on vibes; every merge records confidence.\n")
    if slug == "reference/collection-strategies":
        return ("```text\nDIRECT → API → BROWSER → OWN_PROXY → BRIGHT_DATA\n```\n\n"
                "| Strategy | When | Cost |\n|---|---|---|\n"
                "| DIRECT | Plain public pages | Cheapest |\n| API | Structured endpoints | Cheap |\n"
                "| BROWSER | JavaScript-heavy pages (Playwright pool) | Moderate |\n"
                "| OWN_PROXY | Bot-sensitive hosts via your proxies | Moderate |\n"
                "| BRIGHT_DATA | Large-scale crawling (needs `BRIGHTDATA_API_KEY`) | Metered |\n\n"
                "Test the recommendation any time: `POST /api/v1/strategy/decide`.\n")
    if slug == "reference/environment-variables":
        return ("| Variable | Default | Production |\n|---|---|---|\n"
                "| `DATABASE_URL` | `sqlite:///./webintel.db` | `mysql+pymysql://webintel:…@127.0.0.1:3306/webintel` |\n"
                "| `REDIS_URL` | `redis://127.0.0.1:6379/0` | your Redis URL (or unset for memory fallback) |\n"
                "| `DATA_DIR` | `data` | persistent volume path |\n"
                "| `SECRET_KEY` | dev key | long random string |\n"
                "| `CREDENTIALS_KEY` | empty (derived) | dedicated Fernet key |\n"
                "| `REQUIRE_AUTH` | empty (open) | `1` |\n"
                "| `MAX_BODY_BYTES` | `10485760` | lower for exposed servers |\n"
                "| `RATE_LIMIT_STANDARD` | `300` | tune per traffic |\n"
                "| `RATE_LIMIT_SEARCH` | `200` | tune per traffic |\n"
                "| `RATE_LIMIT_AI` | `30` | tune per budget |\n"
                "| `HSTS` | empty | `1` behind TLS |\n"
                "| `DOCS_BASE_URL` | request host | `https://docs.example.com` (canonical URLs) |\n"
                "| `TRUSTED_EGRESS_CIDRS` | empty | your allowlist, comma separated |\n"
                "| `OWN_PROXY_URLS` | empty | your proxies, comma separated |\n"
                "| `BRIGHTDATA_API_KEY` / `BRIGHTDATA_ZONE` | empty | live-crawl credentials |\n"
                "| `MUSE_SPARK_BASE_URL` / `MUSE_SPARK_API_KEY` | empty | AI provider credentials |\n"
                "| `MUSE_SPARK_MODEL` | `muse-spark-1.3` | pinned model |\n"
                "| `WEBHOOK_INGEST_SECRET` | empty | required for inbound webhooks |\n"
                "| `ALERT_WEBHOOK_URL` / `SMTP_*` / `ALERT_EMAIL_TO` | empty | alert delivery |\n"
                "| `API_BASE` / `API_TOKEN` | local / empty | CLI targeting |\n"
                "| `TICK_SCHEDULES` | empty | `1` for the worker process |\n"
                "| `ENV` / `APP_ENV` | `dev` | `production` |\n")
    if slug == "deployment/requirements":
        return ("| Component | Requirement |\n|---|---|---|\n"
                "| OS | Windows 10/11 dev (Laragon friendly) / Linux production (aaPanel) |\n"
                "| Python | 3.12+ with `source/python/requirements.txt` (pin `bcrypt==4.0.1`) |\n"
                "| Database | MySQL 8.4 primary; SQLite file fallback; memory last resort |\n"
                "| Redis | Optional: queues and rate limits (memory fallback without it) |\n"
                "| Go | 1.21+ to build the collector |\n"
                "| Browser | Playwright Chromium for the two-context pool |\n"
                "| Credentials | Bright Data key for large crawls; AI provider key for AI features |\n")
    if slug == "deployment/production-checklist":
        items = ["HTTPS terminated at Nginx with HSTS=1", "SECRET_KEY and CREDENTIALS_KEY set to random values",
                 "REQUIRE_AUTH=1", "MySQL reachable (readyz shows backend=mysql)", "Redis reachable",
                 "Worker tick running (systemd webintel-worker or TICK_SCHEDULES=1)",
                 "Browser pool healthy (/api/v1/browser/health)", "Go collector built and running",
                 "Backups scheduled and restore tested", "Rate limits tuned",
                 "SSRF guard with TRUSTED_EGRESS_CIDRS", "Webhook ingest secret set",
                 "Audit log reviewed", "System doctor green", "API keys scoped and expiring",
                 "RBAC roles assigned; last-owner protection verified", "Organization isolation spot-checked",
                 "Documentation reachable at /docs", "Screenshots regenerated after last UI change"]
        return "\n".join(f"- [ ] {i}" for i in items) + "\n"
    if slug == "administration/roles":
        return ("| Role | Powers |\n|---|---|---|\n"
                "| owner | Everything, including billing and member removal (last owner is protected) |\n"
                "| admin | Configure, manage members, retention, providers |\n"
                "| analyst | Investigate, triage, build cases and reports |\n"
                "| viewer | Read dashboards, findings, evidence and reports |\n\n"
                "Custom roles compose the same permissions. Every denial returns 403 with an audit record.\n")
    if slug == "ai/prompts":
        return ("The prompt registry (`GET /api/v1/ai/prompts`) versions every instruction the platform "
                "gives to providers: summarization, competitor comparison, review intel, news briefs and "
                "research analysis. Review prompts before enabling AI on sensitive matters — and remember "
                "AI output is always labeled AI-generated.\n")
    if slug == "api/errors":
        return ("Envelope: `{\"error\": {\"code\", \"message\", \"request_id\"}}` plus `X-Request-ID` header.\n\n"
                "| Code | HTTP | Meaning | Action |\n|---|---|---|---|\n"
                "| `bad_request` | 400 | Malformed input or illegal transition | Fix the request; read the message |\n"
                "| `unauthorized` | 401 | Missing/invalid credentials | Sign in or supply a key |\n"
                "| `forbidden` | 403 | Valid identity, insufficient permission | Ask for the role or scope |\n"
                "| `not_found` | 404 | Unknown id or route | Check the id; never guess project_id |\n"
                "| `conflict` | 409 | Duplicate or protected state | Use force/purge flows or rename |\n"
                "| `too_large` | 413 | Body exceeded MAX_BODY_BYTES | Shrink or chunk the payload |\n"
                "| `validation` | 422 | Schema failed | Align fields with the OpenAPI contract |\n"
                "| `rate_limited` | 429 | Quota exceeded, Retry-After set | Back off; see Rate Limits |\n"
                "| `unavailable` | 501/503 | Feature or database unavailable | Check health and doctor |\n"
                "| `db_unavailable` | 503 | Production without database | Restore MySQL; SQLite fallback is dev-only |\n")
    if slug == "api/rate-limits":
        return ("Limits are per identity (organization, then API key, then user, then IP) per 60s window, "
                "Redis-backed when available.\n\n"
                "| Class | Default/min | Applies to |\n|---|---|---|\n"
                "| standard | 300 | Most routes |\n| search | 200 | `/api/v1/search*` |\n"
                "| analytics | 100 | `/api/v1/analytics*`, `/api/v1/intel*` |\n"
                "| webhook | 100 | webhooks and ingestion |\n| ai | 30 | `/api/v1/ai*` |\n"
                "| research | 30 | `/api/v1/research*` |\n| browser | 30 | graph render, documents |\n"
                "| export | 20 | reports, datasets |\n| auth | 10 | login |\n\n"
                "Exceeding returns 429 with `Retry-After`. Override with `RATE_LIMIT_<CLASS>` env vars.\n")
    if slug == "changelog":
        return changelog_body()
    return ("Reference content for " + page[8] + ".\n")


def changelog_body():
    import subprocess
    try:
        log = subprocess.run(["git", "log", "--oneline", "-15"], capture_output=True, text=True,
                             cwd=ROOT, timeout=10).stdout.strip()
    except Exception:
        log = ""
    lines = [f"Current application version: **v{app.version}** (from the running app — "
             "`GET /api/version`).",
             "", "Recent history (from git, newest first):", "", "```text"]
    lines.append(log or "(git history unavailable in this environment)")
    lines += ["```", "",
              "Older product notes live in `docs/CHANGELOG.md` in the repository. "
              "No releases are invented here: if a version is not in git or the app metadata, "
              "it is not on this page."]
    return "\n".join(lines)


TROUBLE = {
    "troubleshooting/common-errors": [
        ("401 unauthorized on every API call", "REQUIRE_AUTH=1 is active and no credentials were sent.",
         "Sign in and use the Bearer token, or create a scoped key under External APIs.",
         "A protected route returns 200 with credentials attached."),
        ("500 with request_id", "Unhandled server error; the id correlates with server logs.",
         "Retry once, then report the X-Request-ID and check the audit log.",
         "The same request succeeds and the id disappears from new errors."),
        ("429 rate limited", "Per-identity quota exceeded for the cost class.",
         "Honor Retry-After, then reduce call rate or raise RATE_LIMIT_<CLASS>.",
         "Calls return 200 with spacing between them."),
        ("413 payload too large", "Body exceeded MAX_BODY_BYTES (default 10 MiB).",
         "Chunk the import or raise the limit deliberately.", "The chunked upload returns 200."),
        ("Empty dashboard after setup", "Fresh database: real-data-only means zeros until collection runs.",
         "Create a project, add a target, run a job, refresh.", "KPIs become non-zero."),
    ],
    "troubleshooting/collection": [
        ("Investigation stuck in queued", "Worker tick not running (schedules) or executor busy.",
         "Press Run now on the job; start the worker (TICK_SCHEDULES=1) for schedules.",
         "Job reaches running, then completed or failed with a reason."),
        ("Job failed immediately", "Unreachable URL, blocked host, or SSRF/allowlist denial.",
         "Open the job detail: read attempts and error; test the target connection.",
         "Retry returns running; DLQ shows only permanently failed work."),
        ("No findings after completed jobs", "Correlation found nothing above thresholds on this scope.",
         "Widen scope, check entities and graph for partial results first.",
         "Entities or graph nodes exist even when findings are empty."),
        ("Collector unavailable", "Go collector or browser pool down.",
         "Check /api/v1/browser/health and collector service logs.", "Health reads up."),
    ],
    "troubleshooting/database": [
        ("readyz shows backend=sqlite despite MySQL", "DATABASE_URL never reached the server process, or pymysql missing.",
         "pip install -r requirements.txt; set DATABASE_URL in the server environment; restart.",
         "readyz reports backend=mysql."),
        ("Data vanishes on restart", "Writes fell back to memory because the database was unreachable.",
         "Fix connectivity, then verify organizations has rows before writing.",
         "A restart preserves newly created projects."),
        ("Access denied for user webintel", "User or grant missing, or wrong password/host.",
         "Recreate the user with host '%' as in the install guide.", "Login to MySQL as webintel succeeds."),
        ("bcrypt 72-byte crash", "bcrypt 5.x incompatibility with passlib.",
         'pip install "bcrypt==4.0.1".', "Server boots without password errors."),
    ],
    "troubleshooting/redis": [
        ("Queues feel stuck without Redis", "Memory fallback works per-process only.",
         "Run a single worker or install Redis for shared queues.", "Scheduled runs execute on time."),
        ("Rate limits behave per-process", "Memory buckets cannot share across processes.",
         "Point all processes at one Redis.", "429s become consistent across replicas."),
    ],
    "troubleshooting/browser": [
        ("Browser health down", "Playwright Chromium missing or pool exhausted.",
         "Install browsers, restart the pool, keep per-job timeouts modest.",
         "/api/v1/browser/health returns up with latency."),
        ("Screenshots render blank", "Media/font blocking plus slow JS on the target.",
         "Prefer DIRECT/API strategies for simple pages; reserve BROWSER for JS-heavy ones.",
         "Render returns SVG with nodes."),
    ],
    "troubleshooting/ai": [
        ("Provider shows down", "No credentials configured or endpoint unreachable.",
         "Add the provider, press Test connection, read latency and discovered models.",
         "Health flips to up and models list populates."),
        ("Model list empty after save", "Discovery failed silently on an incompatible endpoint.",
         "Re-test the connection and pick a preset matching the vendor protocol.",
         "Save succeeds only after a successful test."),
        ("Core features ask for AI", "Misconfiguration: core flows must work without AI.",
         "Report it as a bug; collection, graph, risk and reports never require AI.",
         "Disabling all providers leaves collection green."),
    ],
    "troubleshooting/stix": [
        ("STIX validation fails", "Bundle uses constructs outside the supported subset.",
         "Run /api/v1/stix/validate, read the reported path, simplify to the documented subset.",
         "Validation returns ok before export is trusted downstream."),
        ("MISP import maps nothing", "Attributes outside the supported mapping.",
         "Check the supported attribute list on the MISP page first.",
         "Import returns entity counts greater than zero."),
    ],
}

DEPLOY = {
    "deployment/windows": (
        ["Python 3.12+", "MySQL via Laragon (or any MySQL 8.4)", "PowerShell"],
        [("Create the database",
           'mysql -u root -e "CREATE DATABASE IF NOT EXISTS webintel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"',
           "Database webintel exists."),
         ("Install dependencies", "cd source\\python\npip install -r requirements.txt\npip install \"bcrypt==4.0.1\"",
           "No install errors; pytest collects."),
         ("Point at MySQL once", 'setx DATABASE_URL "mysql+pymysql://webintel:PASSWORD@127.0.0.1:3306/webintel"',
           "Reopen the terminal so the variable applies."),
         ("Run the server", "cd source\\python\npython -m uvicorn app.main:app --port 8000",
           "GET /readyz shows backend=mysql.")],
    ),
    "deployment/linux": (
        ["Ubuntu/Debian host", "Python 3.12+", "MySQL 8.4", "systemd"],
        [("Create a service user", "sudo useradd -r -m webintel",
           "id webintel succeeds."),
         ("Install the app under /opt/webintel", "copy the repository; python3 -m venv venv; venv/bin/pip install -r source/python/requirements.txt",
           "venv/bin/python -m pytest source/python/tests -q passes."),
         ("Install systemd units", "copy deploy/systemd/*.service to /etc/systemd/system; systemctl daemon-reload",
           "systemctl status webintel-api shows active."),
         ("Enable the worker tick", "TICK_SCHEDULES=1 in the worker unit; systemctl enable --now webintel-worker",
           "Schedules execute on time.")],
    ),
    "deployment/aapanel": (
        ["aaPanel installed", "Nginx, MySQL 8.4 and Redis from the app store", "A domain with DNS pointed at the server"],
        [("Create the website", "aaPanel > Website > Add site; note the document root.",
           "The site serves a placeholder page over HTTP."),
         ("Create the database", "aaPanel > Database > Add; create user webintel with a strong password.",
           "Connection from the terminal succeeds."),
         ("Configure Python", "aaPanel > App Store > Python: add project pointing at source/python with uvicorn app.main:app.",
           "The project starts without tracebacks."),
         ("Configure the Go collector", "Build on the server (go build) and register a supervisor/systemd entry.",
           "Collector process answers its health check."),
         ("Configure Redis", "Start Redis from the app store; set REDIS_URL in the project environment.",
           "readyz lists redis up."),
         ("Configure environment", "Set DATABASE_URL, SECRET_KEY, CREDENTIALS_KEY, REQUIRE_AUTH=1 in project env.",
           "Unauthenticated API calls return 401."),
         ("Configure Nginx", "Adapt deploy/nginx/webintel.conf; add the aaPanel site; reload nginx.",
           "The app answers behind the domain."),
         ("Configure the process manager", "Keep the Python project plus worker/browser/collector processes supervised.",
           "All four show running after a reboot."),
         ("Configure workers", "Ensure the worker tick runs (supervisor entry with TICK_SCHEDULES=1).",
           "A test schedule fires on time."),
         ("Configure HTTPS", "aaPanel > SSL > Let's Encrypt; enable Force HTTPS and HSTS=1.",
           "https://domain/healthz returns ok."),
         ("Start the application", "Start all supervised processes in order: mysql/redis, api, worker, collector.",
           "No process exits in the first five minutes."),
         ("Test /healthz", "curl https://domain/healthz", '{"status":"ok"}'),
         ("Test /readyz", "curl https://domain/readyz", "backend=mysql, all checks listed."),
         ("Test the dashboard", "Open https://domain/ and sign in.",
           "Dashboard loads with version footer and no console errors.")],
    ),
    "deployment/nginx": (
        ["Nginx installed", "The app listening on 127.0.0.1:8000", "TLS certificate (Let's Encrypt via aaPanel or certbot)"],
        [("Install the site config", "Copy deploy/nginx/webintel.conf to the Nginx sites directory; adjust server_name.",
           "nginx -t reports success."),
         ("Proxy to uvicorn", "proxy_pass http://127.0.0.1:8000 with forwarded headers preserved.",
           "The dashboard loads through the domain."),
         ("Terminate HTTPS", "Listen 443 ssl; redirect 80 to 443; set HSTS=1 in app env.",
           "http:// redirects; https:// serves with HSTS header."),
         ("Support subdirectories", "If hosting under /intel/, set the proxy prefix and DOCS_BASE_URL for canonical links.",
           "Docs canonical URLs use the public prefix.")],
    ),
    "deployment/mysql": (
        ["MySQL 8.4 reachable", "Root access once"],
        [("Create database and user",
           "CREATE DATABASE IF NOT EXISTS webintel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\nCREATE USER IF NOT EXISTS 'webintel'@'%' IDENTIFIED BY 'STRONG_PASSWORD';\nGRANT ALL PRIVILEGES ON webintel.* TO 'webintel'@'%';\nFLUSH PRIVILEGES;",
           "Login as webintel works."),
         ("Wire the app", 'DATABASE_URL="mysql+pymysql://webintel:STRONG_PASSWORD@127.0.0.1:3306/webintel"',
           "GET /readyz reports backend=mysql."),
         ("Understand fallback", "Without MySQL the app writes to DATA_DIR/webintel.db (SQLite), then memory — check readyz after any move.",
           "You can state which backend is active right now.")],
    ),
    "deployment/redis": (
        ["A host for Redis (aaPanel app store or standalone)"],
        [("Start Redis", "Install and start; default 127.0.0.1:6379 is fine for single-host.",
           "redis-cli ping returns PONG."),
         ("Point the app", 'REDIS_URL="redis://127.0.0.1:6379/0"',
           "readyz lists redis up; rate limits share across processes."),
         ("Know the fallback", "Without Redis, queues and buckets live in memory per process — fine for dev, wrong for replicas.",
           "Single-process dev behaves identically.")],
    ),
    "deployment/playwright": (
        ["Python environment with requirements installed", "Disk space for Chromium"],
        [("Install the browser", "python -m playwright install chromium",
           "The browser binary downloads cleanly."),
         ("Check the pool", "GET /api/v1/browser/health",
           "Status up with two contexts and per-job timeout listed."),
         ("Tune blocking", "Media and font blocking are on by default; relax only for evidence captures that need pixels.",
           "Renders stay fast without losing needed detail.")],
    ),
    "deployment/go-collector": (
        ["Go 1.21+"],
        [("Test", "cd source/go/collector\ngo test ./...",
           "All packages pass."),
         ("Build", "go build -o ../../../build/linux/collector ./cmd/collector",
           "The binary appears under build/linux."),
         ("Run supervised", "Register under systemd/supervisor alongside the API and worker.",
           "Results arrive via POST /api/v1/results.")],
    ),
}


def deployment_body(page):
    slug = page[0]
    prereq, steps = DEPLOY.get(slug, ([], []))
    lines = [page[11], "", "## Prerequisites", ""]
    lines += [f"- {p}" for p in prereq] + [""]
    lines += ["## Steps", ""]
    for i, (title, cmd, expected) in enumerate(steps, 1):
        lines.append(f"### Step {i} — {title}\n")
        lines.append(f"```powershell\n{cmd}\n```\n")
        lines.append(f"**Expected:** {expected}\n")
    lines += ["## Verification", "",
              "- `GET /healthz` returns ok; `GET /readyz` details every backend.",
              "- `GET /api/v1/system/doctor` is green.",
              "- The dashboard loads with the version footer.", "",
              "## Troubleshooting", "",
              "- Backend shows sqlite: DATABASE_URL never reached the server process.",
              "- Port in use: an old server is still running — stop it first.",
              "- bcrypt crash: pin `bcrypt==4.0.1`.",
              "- Full catalog: [Common Errors](/docs/troubleshooting/common-errors).", ""]
    return "\n".join(lines)


def troubleshooting_body(page):
    rows = TROUBLE.get(page[0], [])
    lines = [page[11], ""]
    for symptom, cause, solution, verify in rows:
        lines += [f"### {symptom}", "", f"**Cause:** {cause}", "",
                  f"**Solution:** {solution}", "", f"**Verification:** {verify}", ""]
    return "\n".join(lines)


SECURITY_EXTRA = {
    "security/rbac": "Roles compose permissions; organizations isolate data. Every collection query carries the caller's org, and IDOR tests prove one org cannot read another's records. There is no silent `project_id=1` fallback anywhere: creating work without a resolvable project is an explicit error, not a guess.",
    "security/ssrf": "Targets are untrusted input, so fetching is guarded: scheme and host validation, DNS resolution with private-range rejection, and a trusted-egress allowlist (`TRUSTED_EGRESS_CIDRS`) that administrators set. Private and link-local addresses never leave the server.",
    "security/api-security": "Defense in depth on every route: per-identity rate limits with `Retry-After` (429), body-size guards (413), request IDs on every response, secret-redacted logs, and HMAC-signed inbound webhooks with a replay window.",
}


def security_body(page):
    extra = SECURITY_EXTRA.get(page[0], "")
    lines = [page[11], ""]
    if extra:
        lines += [extra, ""]
    if D.api_prefixes(page):
        lines += ["## Related endpoints", "", api_table(D.api_prefixes(page)), ""]
    lines += ["## What to configure",
              "", "- Production: `REQUIRE_AUTH=1`, random `SECRET_KEY` and `CREDENTIALS_KEY`.",
              "- Network: `TRUSTED_EGRESS_CIDRS` for collection egress.",
              "- Ingestion: `WEBHOOK_INGEST_SECRET` for inbound webhooks.", ""]
    return "\n".join(lines)


def build_page(page):
    slug, section, kind = page[0], page[1], page[2]
    md = frontmatter(page)
    md += f"# {page[8]}\n\n> {page[11]}\n\n"
    if kind == "home":
        md += EXTRA["index"]
    elif slug == "getting-started/first-investigation":
        md += build_first(page)
    elif slug == "getting-started/5-minute-investigation":
        md += build_5min(page)
    elif kind == "lifecycle":
        md += lifecycle_body(page)
    elif kind == "glossary":
        md += glossary_body(page)
    elif kind == "howto":
        md += howto_body(page)
        if slug == "search":
            md += ("\n## Modes\n\n| Mode | Behavior |\n|---|---|\n"
                   "| `hybrid` (default) | Keyword results first, then semantic extras not already present. |\n"
                   "| `keyword` | Exact, prefix and token matching with ranking. |\n"
                   "| `exact` | Field equality only (score 100). |\n"
                   "| `semantic` | Hashed lexical vectors over ingested documents — no neural model, no AI provider. |\n"
                   "\n## Ranking\n\nExact field match (100) beats prefix (50), which beats token hits "
                   "(10 each), with small boosts for numeric risk and recency. "
                   "Filters: `kind`, `risk_min`, `risk_max`, `source`, `date_from`, `date_to`, "
                   "`investigation_id`. Pagination: `limit` (max 100) and `offset`; responses carry "
                   "`total`, `mode` and `facets`. Every collection is filtered to your organization.\n")
    elif kind == "concept":
        md += concept_body(page)
    elif kind == "api":
        md += api_body(page)
    elif kind == "reference":
        md += EXTRA.get(slug) or reference_body(page)
    elif kind == "troubleshooting":
        md += troubleshooting_body(page)
    elif kind == "deployment":
        md += deployment_body(page)
    else:
        md += concept_body(page)
    if kind not in ("home",):
        md += "\n" + related_box(page)
    return md


def main():
    os.makedirs(OUT, exist_ok=True)
    # wipe generated EN tree (id/ar are hand-maintained)
    for root, _dirs, files in os.walk(OUT):
        for f in files:
            if f.endswith(".md"):
                os.remove(os.path.join(root, f))
    count = 0
    for page in D.PAGES:
        slug = page[0]
        dest = os.path.join(OUT, slug + ".md")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        body = build_page(page)
        for banned in ("TODO", "FIXME", "Coming Soon", "lorem", "password123", "secret123"):
            assert banned.lower() not in body.lower() or banned == "TODO", slug
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(body)
        count += 1
    print(f"wrote {count} pages to {OUT}")
    # endpoint coverage sanity
    covered, total = set(), set(PATHS)
    for page in D.PAGES:
        for m, p, _s in endpoints(D.api_prefixes(page)):
            covered.add(p)
    print(f"api paths referenced by docs: {len(covered)}/{len(total)}")


if __name__ == "__main__":
    main()
