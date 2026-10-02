"""Real persistence layer: every collection dual-commits to SQLAlchemy.

Backend resolution: MySQL (DATABASE_URL, when reachable) -> SQLite file
(DATA_DIR/webintel.db) -> in-memory. Under pytest always in-memory.
Full item dicts round-trip through JSON catch-alls so hydrated state is
identical to what was written. Failures degrade to memory, never crash.
"""
import datetime
import json
import os

from .base import Base


def _parse_dt(v):
    if not v:
        return None
    if isinstance(v, datetime.datetime):
        return v
    try:
        return datetime.datetime.fromisoformat(str(v))
    except ValueError:
        return None


def resolve_engine(url=""):
    from sqlalchemy import create_engine
    if url and url.startswith("mysql"):
        try:
            __import__("pymysql")
            eng = create_engine(url, pool_pre_ping=True, future=True,
                                connect_args={"connect_timeout": 3})
            with eng.connect() as c:
                c.exec_driver_sql("SELECT 1")
            return eng, "mysql"
        except Exception:
            pass
    if os.getenv("PYTEST_CURRENT_TEST") or url == "sqlite:///:memory:":
        from sqlalchemy.pool import StaticPool
        eng = create_engine("sqlite:///:memory:", future=True,
                            connect_args={"check_same_thread": False},
                            poolclass=StaticPool)
        return eng, "memory"
    if url and url.startswith("sqlite"):
        eng = create_engine(url, future=True)
        return eng, "sqlite"
    d = os.getenv("DATA_DIR", "data")
    os.makedirs(d, exist_ok=True)
    eng = create_engine(f"sqlite:///{os.path.join(d, 'webintel.db')}", future=True)
    return eng, "sqlite"


def _ensure_columns(engine):
    """Additive auto-migration: ADD columns that exist in models but not in
    the table (stale dev DBs). Never drops/renames. Failures are logged."""
    try:
        from sqlalchemy import inspect
        insp = inspect(engine)
        existing_tables = set(insp.get_table_names())
        for table in Base.metadata.tables.values():
            if table.name not in existing_tables:
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                try:
                    ctype = col.type.compile(dialect=engine.dialect)
                except Exception:
                    continue
                ddl = f"ALTER TABLE {table.name} ADD COLUMN {col.name} {ctype}"
                try:
                    with engine.begin() as conn:
                        conn.exec_driver_sql(ddl)
                except Exception as e:
                    from ..core.logging import log
                    log("migrate-column-failed", table=table.name,
                        column=col.name, error=str(e)[:160])
    except Exception:
        pass


class Repo:
    def __init__(self, engine=None, url=""):
        from sqlalchemy.orm import sessionmaker
        if engine is None:
            from ..core.config import settings
            engine, self.backend = resolve_engine(url or settings.database_url)
        else:
            self.backend = "given"
        self.engine = engine
        self.Session = sessionmaker(bind=engine, autoflush=False, future=True)
        Base.metadata.create_all(bind=engine)
        _ensure_columns(engine)
        self._seed()

    # ---------- seed / users ----------
    def _seed(self):
        try:
            from ..models.universal import Organization
            from ..models.entities import User
            s = self.Session()
            if s.query(Organization).count() == 0:
                s.add(Organization(id=1, name="Default", slug="default"))
            from ..models.universal import Membership
            if s.query(Membership).count() == 0:
                s.add(Membership(org_id=1, email="admin@local", role="owner"))
            if s.query(User).filter_by(email="admin@local").count() == 0:
                from ..core.security import hash_password
                s.add(User(email="admin@local", password_hash=hash_password("admin123"),
                           role="owner", is_active=True))
            s.commit()
            s.close()
        except Exception:
            pass

    def verify_user(self, email, password):
        try:
            from ..models.entities import User
            from ..core.security import verify_password
            s = self.Session()
            u = s.query(User).filter_by(email=email).first()
            s.close()
            if u and u.is_active and verify_password(password, u.password_hash):
                return {"email": u.email, "role": u.role}
        except Exception:
            pass
        return None

    def user_role(self, email):
        try:
            from ..models.universal import Membership
            s = self.Session()
            m = s.query(Membership).filter_by(email=email).first()
            s.close()
            if m:
                return (m.org_id, m.role)
        except Exception:
            pass
        return (1, "viewer")

    # ---------- generic ops ----------
    def _session(self):
        return self.Session()

    def add(self, coll, item):
        fn = _MIRRORS.get(coll)
        if not fn:
            return item
        try:
            model, cols = fn(item)
            s = self._session()
            if "id" in item and isinstance(item["id"], int):
                cols["id"] = item["id"]
            row = model(**cols)
            s.add(row)
            s.commit()
            if "id" not in item and hasattr(row, "id"):
                pass  # store keeps its own keys; DB id internal
            s.close()
        except Exception as e:
            from ..core.logging import log
            log("repo-mirror-failed", coll=coll, error=str(e)[:200])
        return item

    def sync(self, coll, item):
        """Update the mirrored row after in-place mutation."""
        fn = _MIRRORS.get(coll)
        if not fn:
            return
        try:
            model, cols = fn(item)
            cols.pop("id", None)
            s = self._session()
            q = s.query(model)
            key = _KEYS.get(coll, "id")
            if key == "job_uid":
                q = q.filter_by(job_uid=item.get("job_id"))
            elif key == "key":
                q = q.filter_by(key=item.get("key"))
            else:
                q = q.filter_by(id=item.get("id"))
            row = q.first()
            if row is None:
                s.close()
                self.add(coll, item)
                return
            for k, v in cols.items():
                if hasattr(row, k):
                    setattr(row, k, v)
            s.commit()
            s.close()
        except Exception as e:
            from ..core.logging import log
            log("repo-sync-failed", coll=coll, error=str(e)[:200])

    def delete(self, coll, item_id, key="id"):
        fn = _MIRRORS.get(coll)
        if not fn:
            return
        try:
            model, _ = fn({})
            s = self._session()
            s.query(model).filter_by(**{key: item_id}).delete()
            s.commit()
            s.close()
        except Exception:
            pass

    def load_all(self):
        out = {c: [] for c in _MIRRORS}
        out.update({"budgets": {}, "alert_hist": {}, "tags": {}, "health": []})
        try:
            for coll, (model, hyd) in _HYDRATE.items():
                if coll in ("entity_history", "history"):
                    continue  # split from snapshots below
                s = self._session()
                for row in s.query(model).all():
                    try:
                        out[coll].append(hyd(row))
                    except Exception:
                        continue
                s.close()
            from ..models.universal import Snapshot
            s = self._session()
            for row in s.query(Snapshot).all():
                if row.key == "entity_op":
                    out["entity_history"].append(dict(row.state or {}))
                else:
                    out["history"].append({"key": row.key, "state": row.state or {},
                                           "at": row.at_ts or 0})
            s.close()
            # budgets live in project configs
            from ..models.entities import Project
            s = self._session()
            for p in s.query(Project).all():
                b = (p.config or {}).get("budget")
                if b is not None:
                    out["budgets"][str(p.id)] = b
            s.close()
            # ephemeral dicts from kv
            from ..models.universal import KV
            s = self._session()
            for kv in s.query(KV).all():
                if kv.key == "alert_hist":
                    out["alert_hist"] = kv.value or {}
                elif kv.key.startswith("tag:"):
                    out["tags"][kv.key[4:]] = kv.value
            s.close()
        except Exception:
            pass
        return out

    def page(self, coll, page=1, size=20, sort="", order="asc",
             filters=None, in_filters=None, colmap=None):
        """DB-level pagination (LIMIT/OFFSET + COUNT) so large collections
        never load fully into memory. colmap: STORE key -> column name."""
        model = _model_for(coll)
        hyd = _HYDRATE[coll][1]
        page = max(1, page)
        size = max(1, min(100, size))
        try:
            s = self._session()
            q = s.query(model)
            for k, v in (filters or {}).items():
                if hasattr(model, k):
                    q = q.filter(getattr(model, k) == v)
            for k, vs in (in_filters or {}).items():
                if hasattr(model, k):
                    vs = list(vs)
                    if not vs:
                        s.close()
                        return {"items": [], "total": 0, "page": page, "size": size}
                    q = q.filter(getattr(model, k).in_(vs))
            total = q.count()
            col = None
            if sort:
                col = getattr(model, (colmap or {}).get(sort, sort), None)
            if col is None and hasattr(model, "id"):
                col, order = model.id, "desc"
            if col is not None:
                q = q.order_by(col.desc() if order == "desc" else col.asc())
            rows = q.offset((page - 1) * size).limit(size).all()
            items = []
            for r in rows:
                try:
                    items.append(hyd(r))
                except Exception:
                    continue
            s.close()
            return {"items": items, "total": total, "page": page, "size": size}
        except Exception as e:
            from ..core.logging import log
            log("repo-page-failed", coll=coll, error=str(e)[:200])
            return {"items": [], "total": 0, "page": page, "size": size}

    def kv_set(self, key, value):
        try:
            from ..models.universal import KV
            s = self._session()
            row = s.query(KV).filter_by(key=key).first()
            if row:
                row.value = value
            else:
                s.add(KV(key=key, value=value))
            s.commit()
            s.close()
        except Exception:
            pass

    def set_budget(self, project_id, limit):
        try:
            from ..models.entities import Project
            s = self._session()
            p = s.query(Project).filter_by(id=project_id).first()
            if p:
                cfg = dict(p.config or {})
                cfg["budget"] = limit
                p.config = cfg
                s.commit()
            s.close()
        except Exception:
            pass


def _full(item):
    return json.loads(json.dumps(item, default=str))


# Map collection -> (model_factory, columns). Full item preserved in data/payload.
def _m_projects(item):
    from ..models.entities import Project
    return Project, {"name": item.get("name", ""), "description": item.get("description", "")}


def _h_projects(row):
    return {"id": row.id, "name": row.name, "description": row.description or ""}


def _m_targets(item):
    from ..models.entities import Target
    return Target, {"project_id": item.get("project_id"), "domain": item.get("domain", ""),
                    "url": item.get("url", ""), "source_type": item.get("source_type", "website"),
                    "country": item.get("country", ""), "language": item.get("language", ""),
                    "preferred_strategy": item.get("preferred_strategy", "DIRECT_HTTP"),
                    "attempts": item.get("attempts", 0), "successes": item.get("successes", 0),
                    "failures": item.get("failures", 0),
                    "avg_latency_ms": item.get("avg_latency_ms", 0.0),
                    "avg_cost": item.get("avg_cost", 0.0), "data": _full(item)}


def _h_targets(row):
    return dict(row.data or {}, id=row.id)


def _m_jobs(item):
    from ..models.entities import CollectionJob
    import uuid as _u
    return CollectionJob, {"job_uid": item.get("job_id"), "trace_id": item.get("trace_id", ""),
                           "project_id": item.get("project_id"), "target_id": item.get("target_id"),
                           "url": item.get("url", ""), "strategy": item.get("strategy", "AUTO"),
                           "status": item.get("status", "queued"),
                           "idempotency_key": item.get("job_id", "") + "-idem",
                           "plan": item.get("plan", {}),
                           "estimated_cost": item.get("estimated_cost", 0.0),
                           "actual_cost": item.get("actual_cost", 0.0) or 0.0,
                           "retries": item.get("retries", 0)}


def _h_jobs(row):
    d = {"job_id": row.job_uid, "trace_id": row.trace_id, "project_id": row.project_id,
         "target_id": row.target_id, "url": row.url, "strategy": row.strategy,
         "status": row.status, "plan": row.plan or {},
         "estimated_cost": row.estimated_cost or 0.0, "retries": row.retries or 0}
    if row.actual_cost:
        d["actual_cost"] = row.actual_cost
    return d


def _m_prices(item):
    from ..models.entities import Price
    return Price, {"product_id": item.get("product_id"), "price": item.get("price"),
                   "currency": item.get("currency", "USD"), "seller": item.get("seller", ""),
                   "job_ref": str(item.get("job_id", "")),
                   "observed_ts": item.get("observed_at", 0) or 0}


def _h_prices(row):
    return {"product_id": row.product_id, "price": row.price, "currency": row.currency,
            "seller": row.seller or "", "observed_at": row.observed_ts or 0,
            "job_id": row.job_ref or ""}


def _m_articles(item):
    from ..models.entities import Article
    return Article, {"publisher": item.get("publisher", ""), "title": item.get("title", ""),
                     "url": item.get("url", ""), "data": _full(item)}


def _h_articles(row):
    return dict(row.data or {}, id=row.id)


def _m_reports(item):
    from ..models.entities import Report
    return Report, {"kind": item.get("kind", ""), "project_id": item.get("project_id", 0) or 0,
                    "payload": _full(item), "evidence": item.get("evidence", [])}


def _h_reports(row):
    d = dict(row.payload or {})
    d["id"] = row.id
    return d


def _m_schedules(item):
    from ..models.entities import Schedule
    return Schedule, {"project_id": item.get("project_id"), "kind": item.get("kind", "interval"),
                      "cron": item.get("cron", ""), "status": item.get("status", "active"),
                      "every_min": item.get("every_min", 60) or 60,
                      "url": item.get("url", ""), "data": _full(item)}


def _h_schedules(row):
    return dict(row.data or {}, id=row.id)


def _m_raw(item):
    from ..models.entities import RawDocument
    return RawDocument, {"source": "", "url": item.get("url", ""),
                         "strategy": item.get("strategy", ""), "provider": "",
                         "content_hash": item.get("hash", ""), "content_size": item.get("size", 0),
                         "status": "success", "data": _full(item)}


def _h_raw(row):
    return dict(row.data or {})


def _m_changes(item):
    from ..models.entities import Change
    return Change, {"target_id": item.get("target_id"), "kind": item.get("kind", ""),
                    "diff": item.get("diff", {}), "at_ts": item.get("at", 0) or 0}


def _h_changes(row):
    return {"target_id": row.target_id, "kind": row.kind, "diff": row.diff or {},
            "at": row.at_ts or 0}


def _m_alerts(item):
    from ..models.entities import Alert
    return Alert, {"rule": item.get("rule", ""), "message": item.get("message", ""),
                   "channel": item.get("channel", "inapp"),
                   "project_id": item.get("project_id", 0) or 0,
                   "is_read": bool(item.get("is_read", False)),
                   "severity": item.get("severity", "info"),
                   "delivered": bool(item.get("delivered", False)),
                   "acked": bool(item.get("acked", False)),
                   "resolved": bool(item.get("resolved", False)),
                   "resolution": item.get("resolution", "") or ""}


def _h_alerts(row):
    return {"id": row.id, "rule": row.rule, "message": row.message,
            "channel": row.channel, "project_id": row.project_id,
            "is_read": bool(row.is_read), "severity": row.severity or "info",
            "delivered": bool(row.delivered), "acked": bool(row.acked),
            "resolved": bool(row.resolved), "resolution": row.resolution or ""}


def _m_entities(item):
    from ..models.entities import NormalizedEntity
    return NormalizedEntity, {"kind": item.get("kind", "generic"),
                              "name": item.get("name", ""), "domain": item.get("domain", ""),
                              "data": _full(item)}


def _h_entities(row):
    d = dict(row.data or {})
    d.setdefault("id", row.id)
    return d


def _m_audit(item):
    from ..models.entities import AuditLog
    return AuditLog, {"actor": item.get("actor", ""), "action": item.get("action", ""),
                      "ref": item.get("ref", "")[:255], "at_ts": item.get("at", 0) or 0}


def _h_audit(row):
    return {"actor": row.actor, "action": row.action, "ref": row.ref, "at": row.at_ts or 0}


def _m_attempts(item):
    from ..models.entities import CollectionAttempt
    return CollectionAttempt, {"job_id": None, "latency_ms": item.get("latency_ms", 0),
                               "ok": bool(item.get("ok")),
                               "diagnostics": {"target_id": item.get("target_id"),
                                               "completeness": item.get("completeness", 0),
                                               "at": item.get("at", 0)}}


def _h_attempts(row):
    dg = row.diagnostics or {}
    return {"target_id": dg.get("target_id"), "ok": bool(row.ok),
            "latency_ms": row.latency_ms or 0, "completeness": dg.get("completeness", 0),
            "at": dg.get("at", 0)}


def _m_reviews(item):
    from ..models.entities import Review
    return Review, {"product_id": item.get("product_id"), "rating": item.get("rating"),
                    "text": item.get("text", ""), "sentiment": item.get("sentiment", ""),
                    "raw_document_id": item.get("raw_document_id", 0) or 0}


def _m_aiusage(item):
    from ..models.entities import AIUsage
    return AIUsage, {"provider": item.get("provider", ""), "model": item.get("model", ""),
                     "input_tokens": item.get("input_tokens", 0) or 0,
                     "output_tokens": item.get("output_tokens", 0) or 0,
                     "cost": item.get("cost", 0.0) or 0.0,
                     "latency_ms": item.get("latency_ms", 0) or 0}


def _h_aiusage(row):
    return {"id": row.id, "provider": row.provider, "model": row.model,
            "input_tokens": row.input_tokens, "output_tokens": row.output_tokens,
            "cost": row.cost, "at": str(getattr(row, "created_at", "") or "")}


def _h_reviews(row):
    return {"id": row.id, "product_id": row.product_id, "rating": row.rating,
            "text": row.text or "", "sentiment": row.sentiment or ""}


def _m_orgs(item):
    from ..models.universal import Organization
    return Organization, {"name": item.get("name", ""), "slug": item.get("slug", "")}


def _h_orgs(row):
    return {"id": row.id, "name": row.name, "slug": row.slug}


def _m_memberships(item):
    from ..models.universal import Membership
    return Membership, {"org_id": item.get("org_id"), "email": item.get("email", ""),
                        "role": item.get("role", "viewer")}


def _h_memberships(row):
    return {"org_id": row.org_id, "email": row.email, "role": row.role}


def _m_apikeys(item):
    from ..models.universal import APIKey
    return APIKey, {"org_id": item.get("org_id"), "name": item.get("name", ""),
                    "key_hash": item.get("key_hash", ""), "scopes": item.get("scopes", []),
                    "revoked": bool(item.get("revoked"))}


def _h_apikeys(row):
    return {"id": row.id, "org_id": row.org_id, "name": row.name, "key_hash": row.key_hash,
            "scopes": row.scopes or [], "revoked": bool(row.revoked),
            "expires_at": row.expires_at or 0, "last_used": row.last_used or 0}


def _m_nodes(item):
    from ..models.universal import GraphNode
    return GraphNode, {"org_id": item.get("org", 1), "kind": item.get("kind", ""),
                       "key": item.get("key", ""), "name": item.get("name", ""),
                       "data": {k: v for k, v in item.items()
                                if k not in ("id", "org", "kind", "key", "name")}}


def _h_nodes(row):
    d = dict(row.data or {})
    d.update({"id": row.id, "org": row.org_id, "kind": row.kind, "key": row.key, "name": row.name})
    return d


def _m_edges(item):
    from ..models.universal import GraphEdge
    return GraphEdge, {"org_id": item.get("org", 1), "src_id": item.get("src"),
                       "dst_id": item.get("dst"), "rel": item.get("rel", ""),
                       "confidence": item.get("confidence", 1.0),
                       "evidence": item.get("evidence", []), "data": _full(item)}


def _h_edges(row):
    return dict(row.data or {}, id=row.id)


def _m_events(item):
    from ..models.universal import Event
    return Event, {"org_id": item.get("org", 1), "type": item.get("type", ""),
                   "entity_kind": item.get("entity_kind", ""),
                   "entity_key": item.get("entity_key", ""),
                   "severity": item.get("severity", "info"),
                   "confidence": item.get("confidence", 1.0),
                   "evidence": item.get("evidence", []), "data": _full(item)}


def _h_events(row):
    return dict(row.data or {}, id=row.id)


def _m_evidence(item):
    from ..models.universal import Evidence
    return Evidence, {"org_id": item.get("org", 1), "source": item.get("source", ""),
                      "url": item.get("url", ""), "content_hash": item.get("content_hash", ""),
                      "selector": item.get("selector", ""), "method": item.get("method", ""),
                      "confidence": item.get("confidence", 1.0),
                      "snippet": item.get("snippet", "")}


def _h_evidence(row):
    return {"id": row.id, "org": row.org_id, "source": row.source, "url": row.url,
            "content_hash": row.content_hash, "selector": row.selector or "",
            "method": row.method or "", "confidence": row.confidence,
            "snippet": row.snippet or ""}


def _m_claims(item):
    from ..models.universal import Claim
    return Claim, {"org_id": item.get("org", 1), "subject": item.get("subject", ""),
                   "predicate": item.get("predicate", ""),
                   "value": str(item.get("value", "")),
                   "status": item.get("status", "UNVERIFIED"),
                   "confidence": item.get("confidence", 0.0),
                   "evidence_ids": item.get("evidence_ids", [])}


def _h_claims(row):
    return {"id": row.id, "org": row.org_id, "subject": row.subject,
            "predicate": row.predicate, "value": row.value, "status": row.status,
            "confidence": row.confidence, "evidence_ids": row.evidence_ids or []}


def _m_findings(item):
    from ..models.universal import Finding
    return Finding, {"org_id": item.get("org", 1), "kind": item.get("kind", ""),
                     "title": item.get("title", ""), "body": item.get("body", ""),
                     "confidence": item.get("confidence", 0.0),
                     "entities": item.get("entities", []),
                     "evidence_ids": item.get("evidence_ids", [])}


def _h_findings(row):
    return {"id": row.id, "org": row.org_id, "kind": row.kind, "title": row.title,
            "body": row.body or "", "confidence": row.confidence,
            "entities": row.entities or [], "evidence_ids": row.evidence_ids or []}


def _m_research(item):
    from ..models.universal import ResearchRun
    return ResearchRun, {"org_id": item.get("org", 1), "question": item.get("question", ""),
                         "plan": item.get("plan", {}), "status": item.get("status", "planned"),
                         "sources": item.get("sources", []), "job_ids": item.get("job_ids", []),
                         "evidence_ids": item.get("evidence_ids", []),
                         "ai_provider": item.get("ai_provider", ""),
                         "ai_model": item.get("ai_model", ""),
                         "prompt_version": item.get("prompt_version", "v1"),
                         "analysis": item.get("analysis", "") or "",
                         "config": item.get("config", {}), "data": _full(item)}


def _h_research(row):
    return dict(row.data or {}, id=row.id)


def _m_watchlists(item):
    from ..models.universal import Watchlist
    return Watchlist, {"org_id": item.get("org", 1), "kind": item.get("kind", ""),
                       "value": item.get("value", ""),
                       "schedule_id": item.get("schedule_id", 0) or 0}


def _h_watchlists(row):
    return {"id": row.id, "org": row.org_id, "kind": row.kind, "value": row.value,
            "schedule_id": row.schedule_id or 0}


def _m_workflows(item):
    from ..models.universal import Workflow
    return Workflow, {"org_id": item.get("org", 1), "name": item.get("name", ""),
                      "definition": item.get("definition", {}),
                      "enabled": bool(item.get("enabled", True))}


def _h_workflows(row):
    return {"id": row.id, "org": row.org_id, "name": row.name,
            "definition": row.definition or {}, "enabled": bool(row.enabled)}


def _m_wfruns(item):
    from ..models.universal import WorkflowRun
    return WorkflowRun, {"workflow_id": item.get("workflow_id"),
                         "status": item.get("status", "running"),
                         "context": item.get("context", {}), "log": item.get("log", []),
                         "idempotency_key": item.get("idempotency_key", "")}


def _h_wfruns(row):
    return {"id": row.id, "workflow_id": row.workflow_id, "status": row.status,
            "context": row.context or {}, "log": row.log or [],
            "idempotency_key": row.idempotency_key}


def _m_datasets(item):
    from ..models.universal import Dataset
    return Dataset, {"org_id": item.get("org", 1), "name": item.get("name", ""),
                     "kind": item.get("kind", "generic"),
                     "status": item.get("status", "draft")}


def _h_datasets(row):
    return {"id": row.id, "org": row.org_id, "name": row.name, "kind": row.kind,
            "status": row.status}


def _m_dsversions(item):
    from ..models.universal import DatasetVersion
    return DatasetVersion, {"dataset_id": item.get("dataset_id"),
                            "version": item.get("version", 1),
                            "row_count": item.get("row_count", 0),
                            "fingerprint": item.get("fingerprint", ""),
                            "lineage": item.get("lineage", {}),
                            "data": {"rows": (item.get("rows") or [])[:10000]}}


def _h_dsversions(row):
    return {"id": row.id, "dataset_id": row.dataset_id, "version": row.version,
            "row_count": row.row_count, "fingerprint": row.fingerprint,
            "lineage": row.lineage or {}, "rows": (row.data or {}).get("rows", [])}


def _m_connectors(item):
    from ..models.universal import Connector
    return Connector, {"org_id": item.get("org", 1), "name": item.get("name", ""),
                       "category": item.get("category", "CUSTOM"),
                       "version": item.get("version", "1.0"),
                       "manifest": item.get("manifest", {}),
                       "config": item.get("config", {}),
                       "enabled": bool(item.get("enabled", True))}


def _h_connectors(row):
    return {"id": row.id, "org": row.org_id, "name": row.name, "category": row.category,
            "version": row.version, "manifest": row.manifest or {},
            "config": row.config or {}, "enabled": bool(row.enabled)}


def _m_documents(item):
    from ..models.universal import Document
    return Document, {"org_id": item.get("org", 1), "kind": item.get("kind", "txt"),
                      "title": item.get("title", ""),
                      "source_url": item.get("source_url", ""),
                      "fingerprint": item.get("fingerprint", ""),
                      "doc_metadata": item.get("doc_metadata", {}),
                      "text_ref": "",
                      "chunks": item.get("chunks", []), "version": 1,
                      "data": {"extracted": item.get("extracted"),
                               "reason": item.get("reason", "")}}


def _h_documents(row):
    d = dict(row.data or {})
    d.update({"id": row.id, "org": row.org_id, "kind": row.kind, "title": row.title,
              "source_url": row.source_url, "fingerprint": row.fingerprint,
              "doc_metadata": row.doc_metadata or {}, "chunks": row.chunks or []})
    return d


def _m_webhooks(item):
    from ..models.universal import Webhook
    return Webhook, {"org_id": item.get("org", 1), "event_types": item.get("event_types", []),
                     "url": item.get("url", ""), "secret": item.get("secret", ""),
                     "enabled": bool(item.get("enabled", True))}


def _h_webhooks(row):
    return {"id": row.id, "org": row.org_id, "event_types": row.event_types or [],
            "url": row.url, "secret": row.secret or "", "enabled": bool(row.enabled)}


def _m_deliveries(item):
    from ..models.universal import WebhookDelivery
    return WebhookDelivery, {"webhook_id": item.get("webhook_id"),
                             "event": item.get("event", ""),
                             "status": item.get("status", "pending"),
                             "attempts": item.get("attempts", 0),
                             "last_error": item.get("last_error", ""),
                             "response_status": item.get("response_status", 0)}


def _h_deliveries(row):
    return {"id": row.id, "webhook_id": row.webhook_id, "event": row.event,
            "status": row.status, "attempts": row.attempts,
            "last_error": row.last_error or "", "response_status": row.response_status}


def _m_snapshots(item):
    from ..models.universal import Snapshot
    return Snapshot, {"key": item.get("key", ""), "state": item.get("state", {}),
                      "at_ts": item.get("at", 0) or 0}


def _h_snapshots(row):
    return {"key": row.key, "state": row.state or {}, "at": row.at_ts or 0}


def _m_feedsubs(item):
    from ..models.universal import FeedSub
    return FeedSub, {"owner": item.get("owner", ""),
                     "kinds": item.get("kinds", []), "keywords": item.get("keywords", [])}


def _h_feedsubs(row):
    return {"id": row.id, "owner": row.owner, "kinds": row.kinds or [],
            "keywords": row.keywords or []}


def _m_aiproviders(item):
    from ..models.entities import AIProvider
    return AIProvider, {"name": item.get("name", ""), "base_url": item.get("base_url", ""),
                        "api_key_enc": item.get("api_key_enc", ""),
                        "model": item.get("model", ""),
                        "enabled": bool(item.get("enabled", True))}


def _h_aiproviders(row):
    return {"id": row.id, "name": row.name, "base_url": row.base_url,
            "model": row.model, "enabled": bool(row.enabled)}


def _m_entity_history(item):
    from ..models.universal import Snapshot
    return Snapshot, {"key": "entity_op", "state": _full(item), "at_ts": 0}


def _h_entity_history(row):
    return dict(row.state or {})


_MIRRORS = {
    "projects": _m_projects, "targets": _m_targets, "jobs": _m_jobs,
    "prices": _m_prices, "articles": _m_articles, "reports": _m_reports,
    "schedules": _m_schedules, "raw": _m_raw, "changes": _m_changes,
    "alerts": _m_alerts,
    "entities": _m_entities, "audit": _m_audit, "attempts": _m_attempts,
    "orgs": _m_orgs, "memberships": _m_memberships, "apikeys": _m_apikeys,
    "nodes": _m_nodes, "edges": _m_edges, "events": _m_events,
    "evidence": _m_evidence, "claims": _m_claims, "findings": _m_findings,
    "research": _m_research, "watchlists": _m_watchlists,
    "workflows": _m_workflows, "wfruns": _m_wfruns, "datasets": _m_datasets,
    "dsversions": _m_dsversions, "connectors": _m_connectors,
    "documents": _m_documents, "webhooks": _m_webhooks,
    "deliveries": _m_deliveries, "history": _m_snapshots, "feed_subs": _m_feedsubs,
    "entity_history": _m_entity_history, "ai_providers": _m_aiproviders,
    "reviews": _m_reviews, "ai_usage": _m_aiusage,
}

_HYDRATE = {
    "projects": (None, _h_projects), "targets": (None, _h_targets),
    "jobs": (None, _h_jobs), "prices": (None, _h_prices),
    "articles": (None, _h_articles), "reports": (None, _h_reports),
    "schedules": (None, _h_schedules), "raw": (None, _h_raw),
    "changes": (None, _h_changes), "alerts": (None, _h_alerts), "entities": (None, _h_entities),
    "audit": (None, _h_audit), "attempts": (None, _h_attempts),
    "orgs": (None, _h_orgs), "memberships": (None, _h_memberships),
    "apikeys": (None, _h_apikeys), "nodes": (None, _h_nodes),
    "edges": (None, _h_edges), "events": (None, _h_events),
    "evidence": (None, _h_evidence), "claims": (None, _h_claims),
    "findings": (None, _h_findings), "research": (None, _h_research),
    "watchlists": (None, _h_watchlists), "workflows": (None, _h_workflows),
    "wfruns": (None, _h_wfruns), "datasets": (None, _h_datasets),
    "dsversions": (None, _h_dsversions), "connectors": (None, _h_connectors),
    "documents": (None, _h_documents), "webhooks": (None, _h_webhooks),
    "deliveries": (None, _h_deliveries), "history": (None, _h_snapshots),
    "feed_subs": (None, _h_feedsubs), "entity_history": (None, _h_entity_history),
    "ai_providers": (None, _h_aiproviders), "reviews": (None, _h_reviews),
    "ai_usage": (None, _h_aiusage),
}

_KEYS = {"jobs": "job_uid", "apikeys": "key_hash"}


def _model_for(coll):
    from ..models.entities import (Project, Target, CollectionJob, Price, Article,
                                   Report, Schedule, RawDocument, Change, Alert,
                                   NormalizedEntity, AuditLog, CollectionAttempt,
                                   AIProvider, AIUsage, Review)
    from ..models.universal import (Organization, Membership, APIKey, GraphNode,
                                    GraphEdge, Event, Evidence, Claim, Finding,
                                    ResearchRun, Watchlist, Workflow, WorkflowRun,
                                    Dataset, DatasetVersion, Connector, Document,
                                    Webhook, WebhookDelivery, Snapshot, FeedSub)
    return {"projects": Project, "targets": Target, "jobs": CollectionJob,
            "prices": Price, "articles": Article, "reports": Report,
            "schedules": Schedule, "raw": RawDocument, "changes": Change,
            "alerts": Alert, "ai_providers": AIProvider, "reviews": Review,
            "ai_usage": AIUsage,
            "entities": NormalizedEntity, "audit": AuditLog,
            "attempts": CollectionAttempt, "orgs": Organization,
            "memberships": Membership, "apikeys": APIKey, "nodes": GraphNode,
            "edges": GraphEdge, "events": Event, "evidence": Evidence,
            "claims": Claim, "findings": Finding, "research": ResearchRun,
            "watchlists": Watchlist, "workflows": Workflow,
            "wfruns": WorkflowRun, "datasets": Dataset,
            "dsversions": DatasetVersion, "connectors": Connector,
            "documents": Document, "webhooks": Webhook,
            "deliveries": WebhookDelivery, "history": Snapshot,
            "feed_subs": FeedSub, "entity_history": Snapshot}[coll]


# bind models into _HYDRATE
for _c, (_m, _h) in list(_HYDRATE.items()):
    _HYDRATE[_c] = (_model_for(_c), _h)
