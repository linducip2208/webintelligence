"""RBAC matrix + org isolation — stdlib."""
MATRIX = {
    "owner": {"*"},
    "admin": {"read", "collect", "research", "alert", "ai", "configure", "users"},
    "analyst": {"read", "collect", "research", "alert", "ai"},
    "viewer": {"read"},
}
def can(role: str, action: str) -> bool:
    perms = MATRIX.get(role or "", set())
    return "*" in perms or action in perms
def scope(items: list, org_id: int):
    return [x for x in items if x.get("org", x.get("org_id")) in (org_id, None)]
