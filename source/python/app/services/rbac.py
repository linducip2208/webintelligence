"""RBAC matrix + org isolation — stdlib."""
MATRIX = {
    "owner": {"*"},
    "admin": {"read", "collect", "research", "alert", "ai", "configure", "users"},
    "analyst": {"read", "collect", "research", "alert", "ai"},
    "viewer": {"read"},
}
# Actions assignable to custom roles (owner "*" stays unique to owner).
ACTIONS = ("read", "collect", "research", "alert", "ai", "configure", "users")


def can(role: str, action: str, custom: set = None) -> bool:
    if custom is not None:
        return action in custom
    perms = MATRIX.get(role or "", set())
    return "*" in perms or action in perms
def scope(items: list, org_id: int):
    return [x for x in items if x.get("org", x.get("org_id")) in (org_id, None)]
