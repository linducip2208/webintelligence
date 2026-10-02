"""catalog routes (split from main.py; behavior unchanged)."""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import JSONResponse
from ..shared import (
    HTTPException,
    Header,
    ProjectIn,
    STORE,
    TargetIn,
    _audit,
    _check_url,
    _ctx,
    _porg,
    _sorted,
    _torg,
    _visible_by_org,
    inc,
    paginate,
)

router = APIRouter()

# ---- projects ----
@router.post("/api/v1/projects")
def create_project(p: ProjectIn, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _ctx(authorization, x_api_key)
    item = {"id": len(STORE["projects"]) + 1, "org": org, "name": p.name, "description": p.description}
    STORE["projects"].append(item)
    inc("projects_total")
    _audit(email, "project.create", item["name"])
    return item

@router.get("/api/v1/projects")
def list_projects(page: int = 1, size: int = 20, q: str = "", sort: str = "", order: str = "asc",
                  authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [x for x in STORE["projects"] if x.get("org", 1) == org]
    if q:
        items = [x for x in items if q.lower() in x["name"].lower()]
    return paginate(_sorted(items, sort, order), page, size)



# ---- targets ----
@router.post("/api/v1/targets")
def create_target(t: TargetIn, authorization: str = Header(""), x_api_key: str = Header("")):
    email, org, _ = _ctx(authorization, x_api_key)
    _check_url(t.url)
    item = t.model_dump() | {"id": len(STORE["targets"]) + 1, "org": org, "attempts": 0,
                             "successes": 0, "failures": 0}
    STORE["targets"].append(item)
    _audit(email, "target.create", t.url[:120])
    return item


@router.get("/api/v1/targets")
def list_targets(page: int = 1, size: int = 20, q: str = "", sort: str = "", order: str = "asc",
                 authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    items = [x for x in STORE["targets"] if x.get("org", 1) == org]
    if q:
        items = [x for x in items if q.lower() in (x["domain"] + x["url"]).lower()]
    return paginate(_sorted(items, sort, order), page, size)



# ---- connectors ----
@router.post("/api/v1/connectors", tags=["sources"])
def register_connector(spec: dict, authorization: str = Header(""), x_api_key: str = Header("")):
    from ...services import connectors as _c
    _, org, _ = _ctx(authorization, x_api_key)
    errs = _c.validate_manifest(spec.get("manifest", {}))
    if errs:
        raise HTTPException(400, "; ".join(errs))
    item = {"id": len(STORE["connectors"]) + 1, "org": org, "enabled": True, **spec}
    STORE["connectors"].append(item)
    return item


@router.get("/api/v1/connectors", tags=["sources"])
def list_connectors(authorization: str = Header(""), x_api_key: str = Header("")):
    _, org, _ = _ctx(authorization, x_api_key)
    return {"items": _visible_by_org(STORE["connectors"], org)}


@router.get("/api/v1/connectors/match", tags=["sources"])
def match_connector(capability: str = "", category: str = ""):
    from ...services import connectors as _c
    return {"items": _c.match(STORE["connectors"], capability, category)}


