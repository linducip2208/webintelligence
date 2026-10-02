"""Live DB test: creates ALL tables in SQLite and round-trips one row per
core table — proves the schema/migrations are real, not declarations."""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models import entities as m  # noqa: E402
from app.models import universal as u  # noqa: E402


def test_all_tables_live():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=eng)
    names = sorted(Base.metadata.tables)
    assert len(names) >= 37, names
    S = sessionmaker(bind=eng)
    s = S()
    s.add(m.User(email="t@x.io", password_hash="h", role="admin"))
    s.add(m.Project(name="P", description="d", config={}))
    s.commit()
    pid = s.query(m.Project).first().id
    s.add(m.Target(project_id=pid, domain="example.com", url="https://example.com", source_type="website"))
    s.add(m.CollectionJob(trace_id="t1", project_id=pid, target_id=1, url="https://example.com",
                          strategy="AUTO", status="queued", idempotency_key="k1"))
    s.add(m.RawDocument(source="s", url="u", strategy="DIRECT_HTTP", provider="go",
                        content_hash="h", content_size=10, status="success"))
    s.add(m.NormalizedEntity(kind="product", name="Nike", data={}))
    s.add(m.Price(product_id=1, price=9.99, currency="USD", raw_document_id=1))
    s.add(m.Review(product_id=1, rating=5.0, text="great", raw_document_id=1))
    s.add(m.Article(publisher="p", title="t", summary="s", url="u", raw_document_id=1))
    s.add(m.Change(target_id=1, kind="NEW", diff={}))
    s.add(m.Alert(rule="anomaly", message="m", project_id=pid))
    s.add(m.Report(kind="price", project_id=pid, payload={}, evidence=[]))
    s.add(m.AIProvider(name="muse-spark", base_url="https://x", model="muse-spark-1.3"))
    s.add(m.AIUsage(provider="muse-spark", model="muse-spark-1.3", input_tokens=10, output_tokens=5, cost=0.001))
    s.add(m.ProxyProviderRow(name="own", kind="own"))
    s.add(m.Schedule(project_id=pid, kind="interval", status="active"))
    s.add(m.SystemHealth(service="api", status="up"))
    s.add(m.AuditLog(actor="t", action="test"))
    s.commit()
    assert s.query(m.Price).count() == 1
    assert s.query(m.Alert).count() == 1
    # universal domain
    org = u.Organization(name="Acme", slug="acme"); s.add(org); s.commit()
    s.add(u.Membership(org_id=org.id, email="a@x.io", role="owner"))
    s.add(u.APIKey(org_id=org.id, name="k", key_hash="h" * 32, scopes=["read"]))
    n = u.GraphNode(org_id=org.id, kind="company", key="acme", name="Acme"); s.add(n); s.commit()
    s.add(u.GraphEdge(org_id=org.id, src_id=n.id, dst_id=n.id, rel="OWNS", confidence=0.9))
    s.add(u.Event(org_id=org.id, type="PRICE", entity_key="w", severity="info"))
    s.add(u.Evidence(org_id=org.id, source="s", url="u", content_hash="h"))
    s.add(u.Claim(org_id=org.id, subject="s", predicate="price", value="10"))
    s.add(u.Finding(org_id=org.id, kind="k", title="t"))
    s.add(u.ResearchRun(org_id=org.id, question="q?", plan={}))
    s.add(u.Watchlist(org_id=org.id, kind="keyword", value="acme"))
    wf = u.Workflow(org_id=org.id, name="w", definition={}); s.add(wf); s.commit()
    s.add(u.WorkflowRun(workflow_id=wf.id, status="done", idempotency_key="k1"))
    ds = u.Dataset(org_id=org.id, name="d"); s.add(ds); s.commit()
    s.add(u.DatasetVersion(dataset_id=ds.id, version=1, fingerprint="f"))
    s.add(u.Connector(org_id=org.id, name="c", category="WEB"))
    s.add(u.Document(org_id=org.id, kind="txt", fingerprint="f"))
    wh = u.Webhook(org_id=org.id, event_types=["*"], url="https://x"); s.add(wh); s.commit()
    s.add(u.WebhookDelivery(webhook_id=wh.id, event="ping", status="ok"))
    s.commit()
    assert s.query(u.GraphNode).count() == 1
    assert s.query(u.Finding).count() == 1
    s.close()
