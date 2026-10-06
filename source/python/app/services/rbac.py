"""RBAC matrix + org isolation — stdlib."""
MATRIX = {
    "owner": {"*"},
    "admin": {"read", "collect", "research", "alert", "ai", "configure", "users"},
    "analyst": {"read", "collect", "research", "alert", "ai"},
    "viewer": {"read"},
}
# Actions assignable to custom roles (owner "*" stays unique to owner).
ACTIONS = ("read", "collect", "research", "alert", "ai", "configure", "users")


# Granular permission names accepted by _need(); each maps to one coarse
# action so every endpoint keeps a single enforcement point.
GRANULAR = {
    "dashboard.view": "read",
    "projects.view": "read", "projects.create": "collect",
    "projects.update": "collect", "projects.delete": "configure",
    "targets.view": "read", "targets.create": "collect",
    "targets.update": "collect", "targets.delete": "configure",
    "targets.scan": "collect",
    "scans.view": "read", "scans.create": "collect", "scans.run": "collect",
    "scans.cancel": "collect", "scans.delete": "configure",
    "findings.view": "read", "findings.manage": "research", "findings.delete": "configure",
    "entities.view": "read", "entities.manage": "configure",
    "graph.view": "read",
    "cases.view": "read", "cases.manage": "research",
    "evidence.view": "read", "evidence.manage": "collect",
    "collectors.view": "read", "collectors.manage": "configure",
    "connectors.view": "read", "connectors.manage": "configure",
    "workflows.view": "read", "workflows.manage": "collect",
    "reports.view": "read", "reports.create": "research",
    "alerts.view": "read", "alerts.manage": "alert",
    "watchlists.view": "read", "watchlists.manage": "collect",
    "schedules.view": "read", "schedules.manage": "collect",
    "datasets.view": "read", "datasets.manage": "collect",
    "documents.view": "read", "documents.manage": "collect",
    "ai.view": "read", "ai.use": "ai", "ai.manage": "configure",
    "search.use": "read",
    "users.view": "users", "users.manage": "configure",
    "roles.view": "users", "roles.manage": "configure",
    "settings.view": "read", "settings.manage": "configure",
    "audit.view": "read",
    "billing.view": "read", "billing.manage": "configure",
    "costs.view": "read", "costs.manage": "configure",
}


def can(role: str, action: str, custom: set = None) -> bool:
    if custom is not None:
        return action in custom
    perms = MATRIX.get(role or "", set())
    return "*" in perms or action in perms
def scope(items: list, org_id: int):
    return [x for x in items if x.get("org", x.get("org_id")) in (org_id, None)]
