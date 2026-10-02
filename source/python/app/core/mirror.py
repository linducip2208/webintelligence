"""Best-effort MySQL mirror: every mutation is dual-written here when the DB
is reachable. Never raises; failures are returned as detail strings."""
import datetime


def _session():
    from ..db.session import SessionLocal
    return SessionLocal()


def mirror_project(name, description=""):
    try:
        from ..models.entities import Project
        s = _session()
        row = Project(name=name, description=description, config={})
        s.add(row)
        s.commit()
        rid = row.id
        s.close()
        return rid
    except Exception as e:
        return f"mirror-skip: {e}"[:200]


def mirror_target(project_id, domain, url, source_type="website"):
    try:
        from ..models.entities import Target
        s = _session()
        row = Target(project_id=project_id, domain=domain, url=url,
                     source_type=source_type)
        s.add(row)
        s.commit()
        rid = row.id
        s.close()
        return rid
    except Exception as e:
        return f"mirror-skip: {e}"[:200]


def mirror_job(trace_id, project_id, target_id, url, strategy, status):
    try:
        from ..models.entities import CollectionJob
        import uuid as _u
        s = _session()
        row = CollectionJob(trace_id=trace_id, project_id=project_id,
                            target_id=target_id, url=url, strategy=strategy,
                            status=status,
                            idempotency_key=_u.uuid4().hex)
        s.add(row)
        s.commit()
        rid = row.id
        s.close()
        return rid
    except Exception as e:
        return f"mirror-skip: {e}"[:200]


def mirror_price(product_id, price, currency, job_id=""):
    try:
        from ..models.entities import Price
        s = _session()
        row = Price(product_id=product_id, price=price, currency=currency,
                    seller="", availability="", raw_document_id=0)
        s.add(row)
        s.commit()
        rid = row.id
        s.close()
        return rid
    except Exception as e:
        return f"mirror-skip: {e}"[:200]


def mirror_alert(rule, message, project_id=0):
    try:
        from ..models.entities import Alert
        s = _session()
        row = Alert(rule=rule, message=message, channel="inapp",
                    project_id=project_id, is_read=False)
        s.add(row)
        s.commit()
        rid = row.id
        s.close()
        return rid
    except Exception as e:
        return f"mirror-skip: {e}"[:200]


def mirror_health(service, status, detail=""):
    try:
        from ..models.entities import SystemHealth
        s = _session()
        s.add(SystemHealth(service=service, status=status, detail=detail[:500]))
        s.commit()
        s.close()
        return True
    except Exception:
        return False


def mirror_audit(actor, action, ref=""):
    try:
        from ..models.entities import AuditLog
        s = _session()
        s.add(AuditLog(actor=actor, action=action, ref=ref[:255]))
        s.commit()
        s.close()
        return True
    except Exception:
        return False


def ts():
    return datetime.datetime.utcnow().isoformat() + "Z"
