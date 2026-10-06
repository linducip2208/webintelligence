from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from ..db.base import Base
class Timestamp:
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
class User(Base, Timestamp):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True); email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255)); role = Column(String(32), default="admin"); is_active = Column(Boolean, default=True)
class Project(Base, Timestamp):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True); name = Column(String(255), index=True)
    description = Column(Text, default=""); config = Column(JSON, default=dict)
class Target(Base, Timestamp):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True); project_id = Column(Integer, ForeignKey("projects.id"))
    domain = Column(String(255), index=True); url = Column(Text); source_type = Column(String(64))
    country = Column(String(8), default=""); language = Column(String(8), default="")
    preferred_strategy = Column(String(32), default="DIRECT_HTTP")
    attempts = Column(Integer, default=0); successes = Column(Integer, default=0); failures = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0); avg_cost = Column(Float, default=0.0)
    parser_version = Column(String(32), default="v1"); schema_version = Column(String(32), default="1.0")
    data = Column(JSON, default=dict)
class CollectionJob(Base, Timestamp):
    __tablename__ = "collection_jobs"
    id = Column(Integer, primary_key=True); trace_id = Column(String(64), index=True)
    job_uid = Column(String(64), unique=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id")); target_id = Column(Integer, ForeignKey("targets.id"))
    url = Column(Text); strategy = Column(String(32), default="AUTO"); region = Column(String(8), default="")
    status = Column(String(32), default="queued", index=True); idempotency_key = Column(String(128), unique=True)
    plan = Column(JSON, default=dict); estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0); retries = Column(Integer, default=0)
    finished_at = Column(Float, default=0.0); org_id = Column(Integer, default=1, index=True)
    profile = Column(String(16), default="standard")
class CollectionAttempt(Base, Timestamp):
    __tablename__ = "collection_attempts"
    id = Column(Integer, primary_key=True); job_id = Column(Integer, ForeignKey("collection_jobs.id"), index=True, nullable=True)
    strategy = Column(String(32)); provider = Column(String(64)); http_status = Column(Integer)
    latency_ms = Column(Float); cost = Column(Float, default=0.0); ok = Column(Boolean); diagnostics = Column(JSON, default=dict)
class RawDocument(Base, Timestamp):
    __tablename__ = "raw_documents"
    id = Column(Integer, primary_key=True); source = Column(String(255)); url = Column(Text)
    retrieved_at = Column(DateTime, server_default=func.now()); strategy = Column(String(32)); provider = Column(String(64))
    collector_version = Column(String(32)); parser_version = Column(String(32))
    content_hash = Column(String(64), index=True); content_size = Column(Integer); status = Column(String(32))
    body_path = Column(String(512), default=""); data = Column(JSON, default=dict)
    __table_args__ = (Index("ix_raw_url_hash", "content_hash"),)
class NormalizedEntity(Base, Timestamp):
    __tablename__ = "normalized_entities"
    id = Column(Integer, primary_key=True); kind = Column(String(32), index=True); name = Column(String(512), index=True)
    domain = Column(String(255), default=""); data = Column(JSON, default=dict); raw_document_id = Column(Integer)
    parser_version = Column(String(32), default="v1"); confidence = Column(Float, default=1.0)
class Price(Base, Timestamp):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True); product_id = Column(Integer, index=True); price = Column(Float)
    currency = Column(String(8), default="USD"); seller = Column(String(255), default=""); availability = Column(String(32), default="")
    observed_at = Column(DateTime, server_default=func.now()); raw_document_id = Column(Integer)
    job_ref = Column(String(64), default="", index=True); observed_ts = Column(Float, default=0.0)
class Review(Base, Timestamp):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True); product_id = Column(Integer, index=True); rating = Column(Float)
    text = Column(Text); sentiment = Column(String(16), default=""); raw_document_id = Column(Integer)
class Article(Base, Timestamp):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True); publisher = Column(String(255), default=""); title = Column(Text)
    summary = Column(Text); url = Column(Text); raw_document_id = Column(Integer)
    data = Column(JSON, default=dict)
class Change(Base, Timestamp):
    __tablename__ = "changes"
    id = Column(Integer, primary_key=True); target_id = Column(Integer, index=True); kind = Column(String(16)); diff = Column(JSON, default=dict)
    at_ts = Column(Float, default=0.0)
class Alert(Base, Timestamp):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True); rule = Column(String(64)); message = Column(Text)
    channel = Column(String(16), default="inapp"); project_id = Column(Integer); is_read = Column(Boolean, default=False)
    severity = Column(String(16), default="info"); delivered = Column(Boolean, default=False)
    acked = Column(Boolean, default=False); resolved = Column(Boolean, default=False)
    resolution = Column(Text, default=""); sla_due = Column(Float, default=0.0)
class Report(Base, Timestamp):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True); kind = Column(String(64)); project_id = Column(Integer)
    payload = Column(JSON, default=dict); evidence = Column(JSON, default=list)
class AIProvider(Base, Timestamp):
    __tablename__ = "ai_providers"
    id = Column(Integer, primary_key=True); name = Column(String(64), unique=True); base_url = Column(String(512))
    api_key_enc = Column(String(1024), default=""); model = Column(String(128), default="muse-spark-1.3"); enabled = Column(Boolean, default=True)
    protocol = Column(String(16), default="chat")
    preset = Column(String(32), default="")
    last_tested_at = Column(Float, default=0.0); last_test_status = Column(String(16), default="untested")
    last_test_latency_ms = Column(Float, default=0.0); last_test_error = Column(String(128), default="")
class AIUsage(Base, Timestamp):
    __tablename__ = "ai_usage"
    id = Column(Integer, primary_key=True); provider = Column(String(64)); model = Column(String(128))
    input_tokens = Column(Integer, default=0); output_tokens = Column(Integer, default=0); cost = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0); org_id = Column(Integer, default=1, index=True)
class ProxyProviderRow(Base, Timestamp):
    __tablename__ = "proxy_providers"
    id = Column(Integer, primary_key=True); name = Column(String(64), unique=True); kind = Column(String(32))
    config_enc = Column(Text, default=""); healthy = Column(Boolean, default=True)
class Schedule(Base, Timestamp):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True); project_id = Column(Integer); kind = Column(String(32))
    cron = Column(String(128), default=""); status = Column(String(32), default="active")
    next_run = Column(DateTime); last_run = Column(DateTime)
    every_min = Column(Integer, default=60); url = Column(Text, default=""); data = Column(JSON, default=dict)
class SystemHealth(Base, Timestamp):
    __tablename__ = "system_health"
    id = Column(Integer, primary_key=True); service = Column(String(64)); status = Column(String(16)); detail = Column(Text, default="")
class AuditLog(Base, Timestamp):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True); actor = Column(String(255), default=""); action = Column(String(128)); ref = Column(String(255), default="")
    at_ts = Column(Float, default=0.0)
