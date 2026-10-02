"""Persistence tests: every mutation must survive a restart (new Repo on same file)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))

from sqlalchemy import create_engine  # noqa: E402
from app.db.repo import Repo  # noqa: E402


def _repo(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path}/t.db", future=True)
    return Repo(engine=eng)


def test_roundtrip_core(tmp_path):
    r = _repo(tmp_path)
    r.add("projects", {"id": 1, "name": "P", "description": "d"})
    r.add("targets", {"id": 1, "project_id": 1, "domain": "e.com",
                      "url": "https://e.com", "attempts": 0, "successes": 0, "failures": 0})
    r.add("jobs", {"job_id": "j1", "trace_id": "t", "project_id": 1, "target_id": 1,
                   "url": "https://e.com", "strategy": "AUTO",
                   "plan": {"plan": ["DIRECT_HTTP"]}, "status": "queued"})
    r.add("prices", {"product_id": 1, "price": 10.0, "currency": "USD",
                     "observed_at": 123.0, "job_id": "j1"})
    r.add("alerts", {"id": 1, "rule": "r", "message": "m", "channel": "inapp",
                     "project_id": 1, "is_read": False})
    # restart: brand-new Repo on the same file
    r2 = _repo(tmp_path)
    s = r2.load_all()
    assert s["projects"] == [{"id": 1, "name": "P", "description": "d"}]
    assert s["targets"][0]["domain"] == "e.com"
    assert s["jobs"][0]["job_id"] == "j1" and s["jobs"][0]["plan"] == {"plan": ["DIRECT_HTTP"]}
    assert s["prices"] == [{"product_id": 1, "price": 10.0, "currency": "USD",
                            "seller": "", "observed_at": 123.0, "job_id": "j1"}]
    assert s["alerts"][0]["rule"] == "r"


def test_sync_and_universal(tmp_path):
    r = _repo(tmp_path)
    r.add("jobs", {"job_id": "j9", "project_id": 1, "target_id": 1,
                   "url": "https://e.com", "strategy": "AUTO", "status": "queued"})
    r.sync("jobs", {"job_id": "j9", "project_id": 1, "target_id": 1,
                    "url": "https://e.com", "strategy": "AUTO", "status": "success",
                    "retries": 2})
    r.add("nodes", {"id": 1, "org": 1, "kind": "company", "key": "acme", "name": "Acme"})
    r.add("edges", {"id": 1, "org": 1, "src": 1, "dst": 1, "rel": "OWNS",
                    "confidence": 0.9, "evidence": [3], "valid_from": "2026-01-01",
                    "valid_to": None})
    r.add("history", {"key": "price:1", "state": {"price": 5}, "at": 7.0})
    r.add("entity_history", {"op": "MERGE", "keep": 1, "drop": 2, "actor": "t"})
    r.add("feed_subs", {"id": 1, "owner": "a@x", "kinds": ["ALERT"], "keywords": []})
    r.add("dsversions", {"id": 1, "dataset_id": 1, "version": 1, "row_count": 2,
                         "fingerprint": "f", "lineage": {}, "rows": [{"a": 1}, {"a": 2}]})
    r.add("events", {"id": 1, "org": 1, "type": "PRICE", "entity_key": "w",
                     "severity": "info", "confidence": 1.0, "evidence": []})
    r.add("documents", {"id": 1, "org": 1, "kind": "txt", "title": "t",
                        "source_url": "", "fingerprint": "f9", "doc_metadata": {},
                        "chunks": ["ab"], "extracted": True, "reason": ""})
    r.kv_set("alert_hist", {"r1": 123.0})
    r.set_budget(1, 9.5)
    r2 = _repo(tmp_path)
    s = r2.load_all()
    assert s["jobs"][0]["status"] == "success" and s["jobs"][0]["retries"] == 2
    assert s["nodes"][0]["key"] == "acme"
    assert s["edges"][0]["evidence"] == [3]
    assert s["history"] == [{"key": "price:1", "state": {"price": 5}, "at": 7.0}]
    assert s["entity_history"] == [{"op": "MERGE", "keep": 1, "drop": 2, "actor": "t"}]
    assert s["feed_subs"][0]["owner"] == "a@x"
    assert s["dsversions"][0]["rows"] == [{"a": 1}, {"a": 2}]
    assert s["events"][0]["type"] == "PRICE"
    assert s["documents"][0]["chunks"] == ["ab"]
    assert s["alert_hist"] == {"r1": 123.0}


def test_seed_and_login(tmp_path):
    r = _repo(tmp_path)
    assert r.verify_user("admin@local", "admin123")["role"] == "owner"
    assert r.verify_user("admin@local", "wrong") is None
    assert r.user_role("admin@local") == (1, "owner")
    s = r.load_all()
    assert {"id": 1, "name": "Default", "slug": "default"} in s["orgs"]
