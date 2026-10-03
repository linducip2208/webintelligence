"""Universal Intelligence domain: orgs, RBAC keys, graph, events, evidence,
claims, findings, research, watchlists, workflows, datasets, connectors,
documents, webhooks. Separate from entities.py (untouched, working)."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from ..db.base import Base


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, index=True)
    slug = Column(String(128), unique=True, index=True)
    plan = Column(String(32), default="starter")
    branding = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Membership(Base):
    __tablename__ = "memberships"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    email = Column(String(255), index=True)
    role = Column(String(32), default="viewer")  # owner/admin/analyst/viewer
    created_at = Column(DateTime, server_default=func.now())


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    name = Column(String(128))
    key_hash = Column(String(128), unique=True, index=True)
    scopes = Column(JSON, default=list)
    revoked = Column(Boolean, default=False)
    expires_at = Column(Float, default=0.0)
    last_used = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())


class GraphNode(Base):
    __tablename__ = "graph_nodes"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    kind = Column(String(32), index=True)  # company/product/person/brand/domain/location/document/event/topic
    key = Column(String(512), index=True)  # canonical identity
    name = Column(String(512))
    data = Column(JSON, default=dict)
    first_seen = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    __table_args__ = (Index("ix_node_org_kind_key", "org_id", "kind", "key"),)


class GraphEdge(Base):
    __tablename__ = "graph_edges"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    src_id = Column(Integer, ForeignKey("graph_nodes.id"), index=True)
    dst_id = Column(Integer, ForeignKey("graph_nodes.id"), index=True)
    rel = Column(String(64), index=True)  # OWNS/COMPETES_WITH/HAS_PRICE/MENTIONS/WORKS_FOR/...
    confidence = Column(Float, default=1.0)
    evidence = Column(JSON, default=list)
    valid_from = Column(DateTime, server_default=func.now())
    valid_to = Column(DateTime, nullable=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    type = Column(String(64), index=True)
    entity_kind = Column(String(32), default="")
    entity_key = Column(String(512), default="")
    severity = Column(String(16), default="info")
    confidence = Column(Float, default=1.0)
    evidence = Column(JSON, default=list)
    data = Column(JSON, default=dict)
    observed_at = Column(DateTime, server_default=func.now(), index=True)


class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    source = Column(String(255))
    url = Column(Text)
    retrieved_at = Column(DateTime, server_default=func.now())
    content_hash = Column(String(64), index=True)
    selector = Column(String(512), default="")
    method = Column(String(64), default="")
    confidence = Column(Float, default=1.0)
    snippet = Column(Text, default="")


class Claim(Base):
    __tablename__ = "claims"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    subject = Column(String(512))
    predicate = Column(String(128))
    value = Column(Text)
    status = Column(String(16), default="UNVERIFIED", index=True)
    confidence = Column(Float, default=0.0)
    evidence_ids = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())


class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    kind = Column(String(64), index=True)
    title = Column(Text)
    body = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    entities = Column(JSON, default=list)
    evidence_ids = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now(), index=True)


class ResearchRun(Base):
    __tablename__ = "research_runs"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    question = Column(Text)
    plan = Column(JSON, default=dict)
    status = Column(String(32), default="planned", index=True)
    sources = Column(JSON, default=list)
    job_ids = Column(JSON, default=list)
    evidence_ids = Column(JSON, default=list)
    ai_provider = Column(String(64), default="")
    ai_model = Column(String(128), default="")
    prompt_version = Column(String(32), default="v1")
    analysis = Column(Text, default="")
    config = Column(JSON, default=dict)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)


class Watchlist(Base):
    __tablename__ = "watchlists"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    kind = Column(String(32))  # company/product/brand/domain/keyword/topic
    value = Column(String(512), index=True)
    schedule_id = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    name = Column(String(255))
    definition = Column(JSON, default=dict)  # steps: trigger/condition/action
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    id = Column(Integer, primary_key=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), index=True)
    status = Column(String(32), default="running", index=True)
    context = Column(JSON, default=dict)
    log = Column(JSON, default=list)
    idempotency_key = Column(String(128), unique=True)
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    name = Column(String(255), index=True)
    kind = Column(String(64), default="generic")
    status = Column(String(32), default="draft")
    created_at = Column(DateTime, server_default=func.now())


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), index=True)
    version = Column(Integer)
    row_count = Column(Integer, default=0)
    fingerprint = Column(String(64), index=True)
    lineage = Column(JSON, default=dict)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (Index("ix_ds_ver", "dataset_id", "version"),)


class Connector(Base):
    __tablename__ = "connectors"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    name = Column(String(128), index=True)
    category = Column(String(32))  # WEB/API/DOCUMENT/NEWS/ECOMMERCE/...
    version = Column(String(32), default="1.0")
    manifest = Column(JSON, default=dict)
    config = Column(JSON, default=dict)
    enabled = Column(Boolean, default=True)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    kind = Column(String(16))  # pdf/docx/xlsx/csv/json/xml/txt/html
    title = Column(String(512), default="")
    source_url = Column(Text, default="")
    fingerprint = Column(String(64), index=True)
    doc_metadata = Column(JSON, default=dict)
    text_ref = Column(String(512), default="")
    chunks = Column(JSON, default=list)
    version = Column(Integer, default=1)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())


class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    event_types = Column(JSON, default=list)
    url = Column(Text)
    secret = Column(String(256), default="")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), index=True)
    event = Column(String(64))
    status = Column(String(32), default="pending", index=True)
    attempts = Column(Integer, default=0)
    last_error = Column(Text, default="")
    response_status = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Snapshot(Base):
    """Temporal snapshots: full state history per key (price:1, page:2, ...)."""
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True)
    key = Column(String(512), index=True)
    state = Column(JSON, default=dict)
    at_ts = Column(Float, default=0.0, index=True)
    created_at = Column(DateTime, server_default=func.now())


class FeedSub(Base):
    __tablename__ = "feed_subs"
    id = Column(Integer, primary_key=True)
    owner = Column(String(255), index=True)
    kinds = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())


class KV(Base):
    """Ephemeral-but-persistent small state: cooldowns, tags, budgets overflow."""
    __tablename__ = "kv_store"
    key = Column(String(255), primary_key=True)
    value = Column(JSON, default=dict)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    name = Column(String(255))
    starts_at = Column(Float, default=0.0)
    ends_at = Column(Float, default=0.0)
    suppress_rules = Column(JSON, default=list)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
