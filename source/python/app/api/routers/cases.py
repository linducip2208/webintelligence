"""investigation + case management (research action; org-scoped; audited)."""
from fastapi import APIRouter, HTTPException, Header
from ..shared import (
    HTTPException,
    Header,
    STORE,
    _audit,
    _ctx,
    _need,
    _sorted,
    _visible_by_org,
    paginate,
    repo,
    time,
)

router = APIRouter()

INV_STATUSES = ("open", "investigating", "pending", "resolved", "closed")
CASE_STATUSES = ("OPEN", "INVESTIGATING", "PENDING", "RESOLVED", "CLOSED")
PRIORITIES = ("low", "medium", "high", "critical")
INV_LINK_FIELDS = ("target_ids", "entity_ids", "finding_ids", "evidence_ids")
CASE_LINK_FIELDS = ("investigation_ids", "entity_ids", "finding_ids",
                    "evidence_ids", "alert_ids")


def _one(coll, iid, org):
    it = next((x for x in STORE[coll] if x.get("id") == iid and x.get("org", 1) == org), None)
    if not it:
        raise HTTPException(404, f"{coll[:-1] if coll.endswith('s') else coll} not found")
    return it


def _check_status(status, allowed, what):
    if status not in allowed:
        raise HTTPException(400, f"{what} status must be one of {list(allowed)}")
    return status


def _check_priority(p):
    p = (p or "medium").lower()
    if p not in PRIORITIES:
        raise HTTPException(400, f"priority must be one of {list(PRIORITIES)}")
    return p


# ---- investigations ----
@router.post("/api/v1/investigations")
def create_investigation(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    if not (spec.get("title") or "").strip():
        raise HTTPException(400, "title required")
    item = {"id": max([x.get("id", 0) for x in STORE["investigations"]] + [0]) + 1,
            "org": org, "title": spec["title"].strip()[:200],
            "description": (spec.get("description") or "")[:5000],
            "status": _check_status((spec.get("status") or "open").lower(), INV_STATUSES, "investigation"),
            "priority": _check_priority(spec.get("priority")),
            "owner_email": spec.get("owner_email", email),
            "member_emails": list(spec.get("member_emails", []) or [])[:50],
            "tags": [str(t)[:80] for t in (spec.get("tags", []) or [])][:20],
            "target_ids": [], "entity_ids": [], "finding_ids": [],
            "evidence_ids": [], "notes": [], "tasks": []}
    STORE["investigations"].append(item)
    _audit(email, "investigation.create", f"{item['id']}:{item['title'][:80]}")
    return item


@router.get("/api/v1/investigations")
def list_investigations(page: int = 1, size: int = 20, q: str = "", status: str = "",
                        authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [x for x in STORE["investigations"] if x.get("org", 1) == org]
    if status:
        items = [x for x in items if x.get("status") == status.lower()]
    if q:
        ql = q.lower()
        items = [x for x in items if ql in (x.get("title", "") + x.get("description", "")).lower()]
    return paginate(items, page, size)


@router.get("/api/v1/investigations/{iid}")
def get_investigation(iid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    inv = _one("investigations", iid, org)
    targets = [t for t in STORE["targets"] if t.get("id") in (inv.get("target_ids") or [])]
    entities = [e for e in STORE["entities"] if e.get("id") in (inv.get("entity_ids") or [])]
    findings = [f for f in STORE["findings"] if f.get("id") in (inv.get("finding_ids") or [])]
    evidence = [e for e in STORE["evidence"] if e.get("id") in (inv.get("evidence_ids") or [])]
    return {**inv, "linked": {"targets": targets, "entities": entities,
                              "findings": findings, "evidence": evidence}}


@router.put("/api/v1/investigations/{iid}")
def update_investigation(iid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    inv = _one("investigations", iid, org)
    if "title" in spec and spec["title"]:
        inv["title"] = str(spec["title"])[:200]
    if "description" in spec:
        inv["description"] = str(spec["description"] or "")[:5000]
    if "status" in spec:
        inv["status"] = _check_status(str(spec["status"]).lower(), INV_STATUSES, "investigation")
    if "priority" in spec:
        inv["priority"] = _check_priority(spec["priority"])
    for f in ("owner_email",):
        if f in spec:
            inv[f] = str(spec[f] or "")[:255]
    for f in ("member_emails", "tags"):
        if f in spec and isinstance(spec[f], list):
            inv[f] = [str(x)[:120] for x in spec[f]][:50]
    repo.sync("investigations", inv)
    _audit(email, "investigation.update", str(iid))
    return inv


@router.delete("/api/v1/investigations/{iid}")
def delete_investigation(iid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    _one("investigations", iid, org)
    STORE["investigations"][:] = [x for x in STORE["investigations"] if x.get("id") != iid]
    _audit(email, "investigation.delete", str(iid))
    return {"ok": True}


@router.post("/api/v1/investigations/{iid}/notes")
def investigation_note(iid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    inv = _one("investigations", iid, org)
    text = (spec.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text required")
    inv.setdefault("notes", []).append({"by": email, "at": time.time(), "text": text[:5000]})
    repo.sync("investigations", inv)
    _audit(email, "investigation.note", str(iid))
    return {"ok": True, "notes": inv["notes"]}


@router.post("/api/v1/investigations/{iid}/tasks")
def investigation_task_add(iid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    inv = _one("investigations", iid, org)
    title = (spec.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "title required")
    tasks = inv.setdefault("tasks", [])
    task = {"id": max([t.get("id", 0) for t in tasks] + [0]) + 1,
            "title": title[:200], "done": False, "by": spec.get("by", email)}
    tasks.append(task)
    repo.sync("investigations", inv)
    _audit(email, "investigation.task.add", f"{iid}:{task['id']}")
    return task


@router.post("/api/v1/investigations/{iid}/tasks/{tid}/toggle")
def investigation_task_toggle(iid: int, tid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    inv = _one("investigations", iid, org)
    t = next((x for x in inv.get("tasks", []) if x.get("id") == tid), None)
    if not t:
        raise HTTPException(404, "task not found")
    t["done"] = not t.get("done")
    repo.sync("investigations", inv)
    return {"ok": True, "done": t["done"]}


@router.post("/api/v1/investigations/{iid}/links")
def investigation_link(iid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    inv = _one("investigations", iid, org)
    kind = spec.get("kind", "")
    if kind not in INV_LINK_FIELDS:
        raise HTTPException(400, f"kind must be one of {list(INV_LINK_FIELDS)}")
    try:
        ids = [int(x) for x in (spec.get("ids") or [])][:500]
    except (TypeError, ValueError):
        raise HTTPException(400, "ids must be integers")
    cur = inv.setdefault(kind, [])
    added = []
    for i in ids:
        if i not in cur and i not in added:
            added.append(i)
    cur.extend(added)
    repo.sync("investigations", inv)
    _audit(email, "investigation.link", f"{iid}:{kind}:{len(added)}")
    return {"ok": True, "added": added, kind: cur}


@router.post("/api/v1/investigations/{iid}/members")
def investigation_member_add(iid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    inv = _one("investigations", iid, org)
    addr = (spec.get("email") or "").strip()
    if not addr or "@" not in addr:
        raise HTTPException(400, "valid email required")
    members = inv.setdefault("member_emails", [])
    if addr not in members:
        members.append(addr[:255])
    repo.sync("investigations", inv)
    _audit(email, "investigation.member.add", f"{iid}:{addr}"[:160])
    return {"ok": True, "member_emails": members}


@router.post("/api/v1/investigations/{iid}/views")
def investigation_view_save(iid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    """Save a named graph view (node id set) on the investigation."""
    email, org, _ = _need(authorization, "research", x_api_key)
    inv = _one("investigations", iid, org)
    name = (spec.get("name") or "").strip()[:120]
    if not name:
        raise HTTPException(400, "name required")
    try:
        nodes = [int(x) for x in (spec.get("node_ids") or [])][:200]
    except (TypeError, ValueError):
        raise HTTPException(400, "node_ids must be integers")
    data = inv.setdefault("data", {})
    views = data.setdefault("views", {})
    views[name] = {"node_ids": nodes, "by": email, "at": time.time()}
    repo.sync("investigations", inv)
    _audit(email, "investigation.view.save", f"{iid}:{name}"[:160])
    return {"ok": True, "views": views}


@router.delete("/api/v1/investigations/{iid}/views/{name}")
def investigation_view_delete(iid: int, name: str, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    inv = _one("investigations", iid, org)
    views = (inv.get("data") or {}).get("views", {})
    if name not in views:
        raise HTTPException(404, "view not found")
    del views[name]
    repo.sync("investigations", inv)
    _audit(email, "investigation.view.delete", f"{iid}:{name}"[:160])
    return {"ok": True}


# ---- cases ----
@router.post("/api/v1/cases")
def create_case(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    if not (spec.get("title") or "").strip():
        raise HTTPException(400, "title required")
    item = {"id": max([x.get("id", 0) for x in STORE["cases"]] + [0]) + 1,
            "org": org, "title": spec["title"].strip()[:200],
            "description": (spec.get("description") or "")[:5000],
            "status": _check_status((spec.get("status") or "OPEN").upper(), CASE_STATUSES, "case"),
            "priority": _check_priority(spec.get("priority")),
            "assignee": str(spec.get("assignee") or "")[:255],
            "member_emails": list(spec.get("member_emails", []) or [])[:50],
            "tags": [str(t)[:80] for t in (spec.get("tags", []) or [])][:20],
            "investigation_ids": [], "entity_ids": [], "finding_ids": [],
            "evidence_ids": [], "alert_ids": [], "notes": [], "tasks": []}
    STORE["cases"].append(item)
    _audit(email, "case.create", f"{item['id']}:{item['title'][:80]}")
    return item


@router.get("/api/v1/cases")
def list_cases(page: int = 1, size: int = 20, q: str = "", status: str = "",
               authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [x for x in STORE["cases"] if x.get("org", 1) == org]
    if status:
        items = [x for x in items if x.get("status") == status.upper()]
    if q:
        ql = q.lower()
        items = [x for x in items if ql in (x.get("title", "") + x.get("description", "")).lower()]
    return paginate(items, page, size)


@router.get("/api/v1/cases/{cid}")
def get_case(cid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    c = _one("cases", cid, org)
    invs = [x for x in STORE["investigations"] if x.get("id") in (c.get("investigation_ids") or [])]
    entities = [x for x in STORE["entities"] if x.get("id") in (c.get("entity_ids") or [])]
    findings = [x for x in STORE["findings"] if x.get("id") in (c.get("finding_ids") or [])]
    evidence = [x for x in STORE["evidence"] if x.get("id") in (c.get("evidence_ids") or [])]
    alerts = [x for x in STORE["alerts"] if x.get("id") in (c.get("alert_ids") or [])]
    trail = [a for a in STORE["audit"] if str(cid) in str(a.get("ref", ""))][-50:]
    return {**c, "linked": {"investigations": invs, "entities": entities,
                            "findings": findings, "evidence": evidence,
                            "alerts": alerts},
            "audit_trail": trail}


@router.put("/api/v1/cases/{cid}")
def update_case(cid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    c = _one("cases", cid, org)
    if "title" in spec and spec["title"]:
        c["title"] = str(spec["title"])[:200]
    if "description" in spec:
        c["description"] = str(spec["description"] or "")[:5000]
    if "status" in spec:
        c["status"] = _check_status(str(spec["status"]).upper(), CASE_STATUSES, "case")
    if "priority" in spec:
        c["priority"] = _check_priority(spec["priority"])
    for f in ("assignee",):
        if f in spec:
            c[f] = str(spec[f] or "")[:255]
    for f in ("member_emails", "tags"):
        if f in spec and isinstance(spec[f], list):
            c[f] = [str(x)[:120] for x in spec[f]][:50]
    repo.sync("cases", c)
    _audit(email, "case.update", str(cid))
    return c


@router.delete("/api/v1/cases/{cid}")
def delete_case(cid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "configure", x_api_key)
    _one("cases", cid, org)
    STORE["cases"][:] = [x for x in STORE["cases"] if x.get("id") != cid]
    _audit(email, "case.delete", str(cid))
    return {"ok": True}


@router.post("/api/v1/cases/{cid}/notes")
def case_note(cid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    c = _one("cases", cid, org)
    text = (spec.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text required")
    c.setdefault("notes", []).append({"by": email, "at": time.time(), "text": text[:5000]})
    repo.sync("cases", c)
    _audit(email, "case.note", str(cid))
    return {"ok": True, "notes": c["notes"]}


@router.post("/api/v1/cases/{cid}/tasks")
def case_task_add(cid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    c = _one("cases", cid, org)
    title = (spec.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "title required")
    tasks = c.setdefault("tasks", [])
    task = {"id": max([t.get("id", 0) for t in tasks] + [0]) + 1,
            "title": title[:200], "done": False, "by": spec.get("by", email)}
    tasks.append(task)
    repo.sync("cases", c)
    _audit(email, "case.task.add", f"{cid}:{task['id']}")
    return task


@router.post("/api/v1/cases/{cid}/tasks/{tid}/toggle")
def case_task_toggle(cid: int, tid: int, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    c = _one("cases", cid, org)
    t = next((x for x in c.get("tasks", []) if x.get("id") == tid), None)
    if not t:
        raise HTTPException(404, "task not found")
    t["done"] = not t.get("done")
    repo.sync("cases", c)
    return {"ok": True, "done": t["done"]}


@router.post("/api/v1/cases/{cid}/links")
def case_link(cid: int, spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _need(authorization, "research", x_api_key)
    c = _one("cases", cid, org)
    kind = spec.get("kind", "")
    if kind not in CASE_LINK_FIELDS:
        raise HTTPException(400, f"kind must be one of {list(CASE_LINK_FIELDS)}")
    try:
        ids = [int(x) for x in (spec.get("ids") or [])][:500]
    except (TypeError, ValueError):
        raise HTTPException(400, "ids must be integers")
    cur = c.setdefault(kind, [])
    added = []
    for i in ids:
        if i not in cur and i not in added:
            added.append(i)
    cur.extend(added)
    repo.sync("cases", c)
    _audit(email, "case.link", f"{cid}:{kind}:{len(added)}")
    return {"ok": True, "added": added, kind: cur}
