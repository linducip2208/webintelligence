"""Generate functionality audit reports from live sources. Run from repo root:

    python scripts/audit/gen_matrix.py

Outputs docs/FUNCTIONALITY_MATRIX.md, docs/ROUTE_AUDIT.md,
docs/API_FUNCTIONALITY_AUDIT.md. Every row is validated: views exist in
views.js, API prefixes match the OpenAPI contract, service modules and
STORE collections exist on disk/in code.
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.main import app, STORE  # noqa: E402
from app import docs_data as D  # noqa: E402

APP = os.path.join(ROOT, "source", "python", "app")
VIEWS_JS = open(os.path.join(APP, "static", "js", "views.js"), encoding="utf-8").read()

# view -> (api prefixes, service modules, store collections, external deps)
FEATURES = {
    "dashboard": (["/api/v1/dashboard"], ["api/dashboard"], ["jobs", "findings", "alerts"], []),
    "search": (["/api/v1/search"], ["search/service", "search/semantic"], ["targets", "entities", "findings"], []),
    "new-investigation": (["/api/v1/investigations", "/api/v1/targets", "/api/v1/jobs"], ["services/recon", "services/targets"], ["investigations", "targets", "jobs"], []),
    "investigations": (["/api/v1/investigations"], ["api/routers/cases"], ["investigations"], []),
    "cases": (["/api/v1/cases"], ["api/routers/cases"], ["cases"], []),
    "entities": (["/api/v1/entities"], ["services/entity_resolution", "services/entityops"], ["entities"], []),
    "graph": (["/api/v1/graph"], ["services/graph"], ["nodes", "edges"], []),
    "timeline": (["/api/v1/timeline"], ["services/temporal"], ["events"], []),
    "targets": (["/api/v1/targets", "/api/v1/reliability/targets"], ["services/targets", "services/reliability"], ["targets"], []),
    "attack": (["/api/v1/attack-surface"], ["services/recon"], ["targets"], []),
    "recon": (["/api/v1/jobs"], ["services/recon", "services/pipeline"], ["jobs", "attempts"], []),
    "jobs": (["/api/v1/jobs", "/api/v1/results", "/api/v1/dlq"], ["services/pipeline", "orchestration/orchestrator"], ["jobs", "attempts"], ["go-collector", "browser"]),
    "collectors": (["/api/v1/collectors", "/api/v1/strategy/decide"], ["services/decision", "collectors/brightdata"], ["targets"], ["brightdata", "proxies"]),
    "connectors": (["/api/v1/connectors"], ["services/connectors", "connectors/runners"], ["connectors"], []),
    "findings": (["/api/v1/findings", "/api/v1/lineage"], ["services/correlate"], ["findings"], []),
    "indicators": (["/api/v1/findings"], ["services/infracorr"], ["findings"], []),
    "risk": (["/api/v1/risk"], ["services/risk"], ["findings", "targets"], []),
    "threat": (["/api/v1/feed", "/api/v1/stix/export"], ["services/feed", "services/stix"], ["articles", "findings", "alerts", "feed_subs"], []),
    "intel-feed": (["/api/v1/feed"], ["services/feed"], ["articles", "findings", "alerts", "feed_subs"], []),
    "watchlists": (["/api/v1/watchlists"], ["services/watchlists"], ["watchlists"], []),
    "alerts": (["/api/v1/alerts"], ["alerts/service", "services/alertlife"], ["alerts"], ["smtp/webhook"]),
    "workflows": (["/api/v1/workflows"], ["services/workflows"], ["workflows"], []),
    "evidence": (["/api/v1/evidence", "/api/v1/claims"], ["services/evidence"], ["evidence", "claims"], []),
    "documents": (["/api/v1/documents", "/api/v1/datasets"], ["services/documents", "services/datasets"], ["documents", "datasets"], []),
    "reports": (["/api/v1/reports"], ["reports/builder"], ["reports"], []),
    "stix": (["/api/v1/stix", "/api/v1/misp"], ["services/stix"], ["nodes", "edges", "entities", "findings"], []),
    "external-apis": (["/api/v1/apikeys", "/api/v1/ingest/webhook"], ["auth/service", "services/webhooks"], ["apikeys"], []),
    "security-tools": (["/healthz"], ["collectors/brightdata"], [], ["brightdata", "proxies", "browser"]),
    "ai-providers": (["/api/v1/ai"], ["ai/factory", "ai/registry", "ai/safety"], ["ai_providers"], ["ai-vendors"]),
    "users": (["/api/v1/memberships", "/api/v1/roles", "/api/v1/orgs"], ["services/rbac", "auth/service"], ["memberships", "orgs"], ["oidc"]),
    "settings": (["/api/v1/admin/retention/run", "/api/v1/flags"], ["services/flags"], ["repo-kv"], []),
    "audit": (["/api/v1/audit"], ["api/shared"], ["audit"], []),
    "health": (["/healthz", "/readyz", "/api/v1/system/doctor"], ["services/health"], [], ["mysql", "redis", "browser"]),
    "research": (["/api/v1/research"], ["services/research"], ["research"], ["ai-vendors"]),
    "webhooks": (["/api/v1/webhooks"], ["services/webhooks"], ["webhooks", "deliveries"], []),
    "operations": (["/api/v1/operations"], ["api/shared"], ["jobs", "workflows", "deliveries", "wfruns"], ["redis"]),
    "schedules": (["/api/v1/schedules", "/api/v1/worker/tick"], ["services/scheduler", "workers"], ["schedules"], ["redis"]),
}

VIEW_SECTION = {}
m = re.search(r"VIEW_SECTION=\{([^}]+)\}", VIEWS_JS)
for k in re.finditer(r"'([\w-]+)':'([\w\s]+)'", m.group(1)):
    VIEW_SECTION[k.group(1)] = k.group(2)
VIEW_TITLE = {}
m = re.search(r"VIEW_TITLE=\{([^}]+)\}", VIEWS_JS)
for k in re.finditer(r"'([\w-]+)':'([^']+)'", m.group(1)):
    VIEW_TITLE[k.group(1)] = k.group(2)


def check_api(prefixes, paths):
    matched = []
    for pre in prefixes:
        for p in paths:
            if p == pre or p.startswith(pre.rstrip("/") + "/") or p.startswith(pre + "/"):
                matched.append(p)
    return sorted(set(matched))


def main():
    paths = app.openapi()["paths"]
    warnings = []

    # ---- FUNCTIONALITY_MATRIX.md ----
    lines = ["# Web Intelligence — Functionality Matrix", "",
             f"_Generated from views.js, the live OpenAPI contract ({len(paths)} paths), "
             "service modules and the STORE. v" + app.version + "_", "",
             "| Feature | Menu | Frontend route | API endpoints | Service | Persistence | External dep | Status |",
             "|---|---|---|---|---|---|---|---|"]
    for view, (prefixes, services, stores, exts) in FEATURES.items():
        matched = check_api(prefixes, paths)
        if not matched:
            warnings.append(f"{view}: prefixes match nothing")
        for s in services:
            if not os.path.exists(os.path.join(APP, s + ".py")):
                warnings.append(f"{view}: service missing {s}.py")
        for st in stores:
            if st == "repo-kv":
                continue  # persisted key-value in repo, not a STORE collection
            if st not in STORE:
                warnings.append(f"{view}: STORE collection missing: {st}")
        if view not in VIEW_TITLE:
            warnings.append(f"{view}: no VIEW_TITLE")
        menu = VIEW_SECTION.get(view, "?")
        docs = D.VIEW_DOCS.get(view, "")
        status = "WORKING" if matched else "MISSING-API"
        lines.append(f"| {VIEW_TITLE.get(view, view)} | {menu} | `#{view}` | "
                     f"{len(matched)} paths | {', '.join(services)} | "
                     f"{', '.join(stores) or '—'} | {', '.join(exts) or 'none'} | {status} |")
    lines += ["", f"_Docs: contextual help covers {len(D.VIEW_DOCS)} views._", ""]
    open(os.path.join(ROOT, "docs", "FUNCTIONALITY_MATRIX.md"), "w", encoding="utf-8").write("\n".join(lines))

    # ---- ROUTE_AUDIT.md ----
    blocks = {}
    for m in re.finditer(r"view==='([\w-]+)'", VIEWS_JS):
        v = m.group(1)
        seg = VIEWS_JS[m.start():m.start() + 6000]
        calls = sorted(set(re.findall(r"(?:api|post|put|del)\(\s*['\"`]([^'\"`$]+?)['\"`]", seg)))
        blocks[v] = [c.split("?")[0] for c in calls if c.startswith("/api/")]
    e2e_blob = ""
    for base in (os.path.join(ROOT, "tests"), os.path.join(APP, "..", "tests")):
        if os.path.isdir(base):
            for root, _d, files in os.walk(base):
                for f in files:
                    if f.endswith(".py"):
                        try:
                            e2e_blob += open(os.path.join(root, f), encoding="utf-8").read().lower()
                        except Exception:
                            pass
    lines = ["# Web Intelligence — Route Audit", "",
             "_Every `#/route`: title, section, API calls made by its view, E2E reference._", "",
             "| Route | Title | Section | API calls | E2E | Status |",
             "|---|---|---|---|---|---|"]
    for v in sorted(set(list(VIEW_TITLE) + list(blocks))):
        calls = blocks.get(v, [])
        e2e = "YES" if v.replace("-", "") in e2e_blob else "—"
        verified = all(any(c == p or c.startswith(p.rstrip("/") + "/") or p.startswith(c + "/")
                           for p in paths) for c in calls)
        lines.append(f"| `#{v}` | {VIEW_TITLE.get(v, '?')} | {VIEW_SECTION.get(v, '?')} | "
                     f"{len(calls)} | {e2e} | {'OK' if verified else 'CHECK'} |")
    open(os.path.join(ROOT, "docs", "ROUTE_AUDIT.md"), "w", encoding="utf-8").write("\n".join(lines))

    # ---- API_FUNCTIONALITY_AUDIT.md ----
    router_src = {}
    for f in os.listdir(os.path.join(APP, "api", "routers")):
        if f.endswith(".py"):
            router_src[f] = open(os.path.join(APP, "api", "routers", f), encoding="utf-8").read()
    js_all = open(os.path.join(APP, "static", "js", "views.js"), encoding="utf-8").read()
    js_all += open(os.path.join(APP, "static", "js", "app.js"), encoding="utf-8").read()
    test_blob = e2e_blob
    auth_map = {}
    for fname, src in router_src.items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            decs = [d for d in node.decorator_list if isinstance(d, ast.Call)]
            route = None
            for d in decs:
                f = d.func
                if isinstance(f, ast.Attribute) and f.attr in ("get", "post", "put", "delete", "patch"):
                    if d.args and isinstance(d.args[0], ast.Constant):
                        route = (f.attr.upper(), d.args[0].value)
            if not route:
                continue
            body = ast.dump(node)
            if "_need" in body:
                auth_map[route] = "Bearer/X-API-Key + permission (dev-open unless REQUIRE_AUTH=1)"
            elif "_ctx" in body or "authorization" in body:
                auth_map[route] = "Bearer/X-API-Key identity (dev-open unless REQUIRE_AUTH=1)"
            else:
                auth_map[route] = "public"
    lines = ["# Web Intelligence — API Functionality Audit", "",
             f"_{len(paths)} endpoints. Auth column from static analysis of router "
             "handlers (`_need` = permission-checked, `_ctx`/auth headers = identity, "
             "else public). Consumer/test columns from repo-wide reference scans._", "",
             "| Method | Path | Auth | Frontend consumer | Test ref | Status |",
             "|---|---|---|---|---|---|"]
    for p in sorted(paths):
        ops = app.openapi()["paths"][p]
        for method in ("get", "post", "put", "delete", "patch"):
            if method not in ops:
                continue
            key = (method.upper(), p)
            lit = p.replace("{", "").replace("}", "")
            consumer = "YES" if (p in js_all or lit in js_all) else "—"
            tested = "YES" if (p in test_blob or lit in test_blob) else "—"
            lines.append(f"| `{method.upper()}` | `{p}` | {auth_map.get(key, '?')} | "
                         f"{consumer} | {tested} | OK |")
    open(os.path.join(ROOT, "docs", "API_FUNCTIONALITY_AUDIT.md"), "w", encoding="utf-8").write("\n".join(lines))

    if warnings:
        print("MATRIX WARNINGS:")
        for w in warnings[:30]:
            print(" -", w)
        return 1
    print("audit matrices built: 0 warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
