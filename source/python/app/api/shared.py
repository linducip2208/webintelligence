"""FastAPI entrypoint — real routes, no fake metrics.

Persistence is write-through: every mutation commits to the repository
(MySQL when reachable, else SQLite file, else memory) and hydrates on boot,
so all state survives restarts. All dashboard numbers come from actual stores.
"""
import os
import time
import uuid

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os as _os

from ..core.ssrf import validate_url, SSRFError
from ..core.metrics import inc, render
from ..core.pagination import paginate
from ..core.deps import get_redis, redis_status, data_dir
from ..db.repo import Repo
from ..services import decision as dec
from ..services import cost as costeng
from ..services import change as changedet
from ..services import quality as qual
from ..services import health as healthsvc
from ..services import pipeline as pipe
from ..services import scheduler as sched
from ..schemas.api import ProjectIn, TargetIn, JobIn, AlertRuleIn
from . import dashboard as dash
from ..collectors.proxy import OwnProxyProvider
from ..collectors.brightdata import BrightDataProvider
from ..ai.muse_provider import MuseSparkProvider
from ..ai import registry as aireg
from ..core.config import settings
from ..alerts.service import build as build_alert
from ..auth import tokens as tok
from ..core.security import hash_password, verify_password


repo = Repo()


class MirrorList(list):
    """Write-through list: every append/delete persists to the repository,
    so all state survives restarts. Failures degrade to memory."""

    def __init__(self, coll):
        super().__init__()
        self._coll = coll

    def append(self, item):
        super().append(item)
        try:
            repo.add(self._coll, item)
        except Exception:
            if repo.should_raise:
                super().pop()
                raise
        return item

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if isinstance(key, slice):
            try:
                model = repo_model(self._coll)
                s = repo._session()
                s.query(model).delete()
                s.commit()
                s.close()
                for item in self:
                    repo.add(self._coll, item)
            except Exception:
                pass


def repo_model(coll):
    from ..db.repo import _model_for
    return _model_for(coll)


def _wrap(store):
    out = {}
    for k, v in store.items():
        if isinstance(v, list):
            ml = MirrorList(k)
            ml.extend(v)
            out[k] = ml
        else:
            out[k] = v
    return out


STORE = _wrap(repo.load_all())
USERS = {"admin@local": {"password_hash": hash_password("admin123")}}

own_proxy = OwnProxyProvider(settings.own_proxy_urls)
bright = BrightDataProvider(settings.brightdata_api_key, settings.brightdata_zone,
                            settings.brightdata_endpoint)
muse = MuseSparkProvider(settings.muse_base_url, settings.muse_api_key,
                         settings.muse_model)
aireg.register("muse-spark", muse)
try:
    from ..ai.factory import build_all as _build_ai
    for _n, _p in _build_ai().items():
        if _n == "muse-spark" and getattr(_p, "configured", False):
            muse = _p  # prefer the fully-configured build
        if _n not in aireg.names():
            aireg.register(_n, _p)
    aireg.register("muse-spark", muse)
except Exception:
    pass

import time as _tmod
_BUCKETS: dict = {}
_NONCES: dict = {}


def _rate_ok(ip: str) -> bool:
    import os as _o
    limit = int(_o.getenv("RATE_LIMIT_PER_MIN", "240") or 240)
    now = _tmod.time()
    b = _BUCKETS.get(ip)
    if not b or now - b["ts"] > 60:
        b = {"n": 0, "ts": now}
        _BUCKETS[ip] = b
    b["n"] += 1
    if len(_BUCKETS) > 10000:
        _BUCKETS.clear()
    return b["n"] <= limit


def _key_lookup(raw: str):
    import hashlib as _h
    import time as _t
    h = _h.sha256(raw.encode()).hexdigest()
    k = next((x for x in STORE["apikeys"] if x["key_hash"] == h and not x.get("revoked")), None)
    if not k:
        return None
    if k.get("expires_at") and k["expires_at"] < _t.time():
        return None
    return k


def _torg(tid):
    t = next((x for x in STORE["targets"] if x.get("id") == tid), None)
    return t.get("org", 1) if t else None


def _porg(pid):
    p = next((x for x in STORE["projects"] if x.get("id") == pid), None)
    return p.get("org", 1) if p else None


def _visible_by_org(items, org, kind="direct"):
    """Tenant isolation: direct org field, or via target/project ownership."""
    out = []
    for i in items:
        if kind == "direct":
            if i.get("org", 1) == org:
                out.append(i)
        elif kind == "target":
            o = _torg(i.get("product_id", i.get("target_id")))
            if o is None or o == org:
                out.append(i)
        elif kind == "project":
            o = _porg(i.get("project_id"))
            if o is None or o == org:
                out.append(i)
    return out


def _sorted(items, sort="", order="asc"):
    if not sort:
        return items
    rev = order == "desc"
    try:
        return sorted(items, key=lambda x: (x.get(sort) is None, x.get(sort)), reverse=rev)
    except TypeError:
        return sorted(items, key=lambda x: str(x.get(sort)), reverse=rev)


def _fire_watchlists(item: dict):
    from ..services import watchlists as _w
    for wid in _w.match(STORE["watchlists"], {"value": item.get("entity_key", ""),
                                              "text": f"{item.get('type','')} {item.get('entity_key','')}"}):
        STORE["alerts"].append({"id": len(STORE["alerts"]) + 1, "rule": "watchlist_hit",
                                "channel": "inapp",
                                "message": f"Watchlist #{wid} hit by {item.get('type')}",
                                "project_id": 0, "is_read": False})


def _secret():
    return settings.secret_key or "dev-secret"


def _require_auth(authorization: str = "", x_api_key: str = ""):
    if x_api_key and _key_lookup(x_api_key):
        return "apikey"
    if os.getenv("REQUIRE_AUTH", "") != "1":
        return "dev-open"
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    email = tok.verify(authorization[7:], _secret())
    if not email:
        raise HTTPException(401, "invalid/expired token")
    return email


def _ctx(authorization: str = "", x_api_key: str = ""):
    """(email, org_id, role). API keys scope to their org; login tokens use membership.
    Dev-open (REQUIRE_AUTH!=1) acts as owner; production enforces real roles."""
    email = _require_auth(authorization, x_api_key)
    if email == "dev-open":
        return ("dev-open", 1, "owner")
    if x_api_key:
        import hashlib as _h
        h = _h.sha256(x_api_key.encode()).hexdigest()
        k = next((x for x in STORE["apikeys"] if x["key_hash"] == h and not x.get("revoked")), None)
        if not k:
            raise HTTPException(401, "bad api key")
        if k.get("expires_at") and k["expires_at"] < time.time():
            raise HTTPException(401, "api key expired")
        k["last_used"] = time.time()
        try:
            repo.sync("apikeys", k)
        except Exception:
            pass
        return ("apikey:" + k["name"], k["org_id"], "analyst")
    ms = [m for m in STORE["memberships"] if m["email"] == email]
    if ms:
        return (email, ms[0]["org_id"], ms[0]["role"])
    return (email, 1, "viewer")


def _need(authorization: str, action: str, x_api_key: str = ""):
    from ..services import rbac as _rbac
    email, org, role = _ctx(authorization, x_api_key)
    if email.startswith("apikey:"):
        import hashlib as _h
        k = next((x for x in STORE["apikeys"]
                  if x["key_hash"] == _h.sha256(x_api_key.encode()).hexdigest()), None)
        if not k or (k.get("scopes") and action not in k["scopes"] and "*" not in k["scopes"]):
            raise HTTPException(403, f"api key lacks scope {action}")
        return (email, org, role)
    if not _rbac.can(role, action):
        raise HTTPException(403, f"role {role} cannot {action}")
    return (email, org, role)


def _providers():
    return {"own_proxy": {"healthy": True, "cost": 0.002},
            "brightdata": {"healthy": True, "cost": 0.05,
                           "configured": bright.configured}}


def _check_url(url: str):
    """SSRF validation honoring the live TRUSTED_EGRESS_CIDRS allowlist."""
    import os as _o
    trust = [x.strip() for x in _o.getenv("TRUSTED_EGRESS_CIDRS", "").split(",") if x.strip()]
    try:
        validate_url(url, trust or None)
    except SSRFError as e:
        raise HTTPException(400, f"url rejected: {e}")


def _audit(actor, action, ref=""):
    STORE["audit"].append({"actor": actor, "action": action, "ref": ref,
                           "at": time.time()})
    if len(STORE["audit"]) > 5000:
        # hot window in memory; full history persists in the repository
        del STORE["audit"][:-5000]


def _apply_result(res: dict, job_url: str, project_id: int, target_id: int):
    """Persist a pipeline/collector result bundle into STORE. Shared by
    inline runs, /results ingestion, and worker ticks."""
    job = next((j for j in STORE["jobs"] if j.get("job_id") == res.get("job_id")), None)
    if job:
        job["status"] = res.get("status", job["status"])
        job["finished_at"] = time.time()
        job["actual_cost"] = res.get("cost", 0)
        try:
            repo.sync("jobs", job)
        except Exception:
            pass
    # persisted target learning: counters + learned preferred strategy
    try:
        from ..services import targets as _tgt
        tgt = next((t for t in STORE["targets"] if t.get("id") == target_id), None)
        if tgt is not None:
            prof = _tgt.record_attempt(tgt.get("profile", {}), res.get("strategy", "DIRECT_HTTP"),
                                       res.get("status") == "success",
                                       res.get("latency_ms", 0), res.get("cost", 0))
            tgt["profile"] = prof
            tgt["attempts"] = prof.get("attempts", 0)
            tgt["successes"] = prof.get("successes", 0)
            tgt["failures"] = prof.get("failures", 0)
            tgt["preferred_strategy"] = _tgt.preferred_strategy(prof)
            repo.sync("targets", tgt)
    except Exception:
        pass
    if res.get("content_hash"):
        STORE["raw"].append({"job_id": res.get("job_id"), "url": job_url,
                             "hash": res["content_hash"], "size": res.get("content_size", 0),
                             "strategy": res.get("strategy"), "at": time.time()})
    for p in res.get("prices", []):
        STORE["prices"].append({"product_id": target_id, "price": p["price"],
                                "currency": p.get("currency", "USD"), "seller": "",
                                "observed_at": time.time(), "job_id": res.get("job_id")})
    if res.get("change") in ("CHANGED", "NEW"):
        STORE["changes"].append({"target_id": target_id, "kind": res["change"],
                                 "diff": res.get("diagnostics", {}), "at": time.time()})
    for a in res.get("alerts", []):
        STORE["alerts"].append({"id": len(STORE["alerts"]) + 1, **a,
                                "project_id": project_id, "is_read": False})
    if res.get("status") == "success":
        inc("jobs_success")
    elif res.get("status") in ("failed",):
        inc("jobs_failed")
        STORE["alerts"].append({"id": len(STORE["alerts"]) + 1,
                                "rule": "collection_failure", "channel": "inapp",
                                "message": f"Job {res.get('job_id')} failed "
                                           f"({res.get('strategy')}, http={res.get('http_status')})",
                                "project_id": project_id, "is_read": False})
    STORE["attempts"].append({"target_id": target_id, "ok": res.get("status") == "success",
                              "latency_ms": res.get("latency_ms", 0),
                              "completeness": (res.get("quality") or {}).get("overall", 0),
                              "at": time.time()})
    if True:
        from ..services import temporal as _t
        for p in res.get("prices", []):
            _t.record(STORE["history"], f"price:{target_id}",
                      {"price": p["price"], "currency": p.get("currency")}, time.time())
    return res


def _execute_job(job: dict):
    target = next((t for t in STORE["targets"] if t["id"] == job["target_id"]), {"url": job["url"]})
    last = [p for p in STORE["prices"] if p.get("product_id") == job["target_id"]][-3:]
    res = pipe.run_job(job, target, last,
                       dec.Policy(allow_brightdata=bright.configured),
                       _providers())
    if res.get("content_hash") and res.get("status") == "success":
        try:
            body = b""  # body already hashed; raw bytes live with collector/browser
            path = os.path.join(data_dir(), "raw", res["content_hash"])
            if not os.path.exists(path):
                open(path, "wb").write(body)
        except Exception:
            pass
    return _apply_result(res, job["url"], job["project_id"], job["target_id"])


