"""Seed DEMO environment (dev only). All records prefixed 'demo-'.

Usage: cd source/python && python seed_demo.py
Never run against production; production code never depends on this data.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
p = c.post("/api/v1/projects", json={"name": "demo-market", "description": "DEMO DATA"}).json()
t = c.post("/api/v1/targets", json={"project_id": p["id"], "domain": "demo.example.com",
    "url": "https://demo.example.com/p", "source_type": "website"}).json()
c.post("/api/v1/articles", json={"publisher": "demo-wire", "title": "demo: market note",
    "url": "https://demo.example.com/note"})
n = c.post("/api/v1/graph/nodes", json={"kind": "company", "key": "demo-acme", "name": "demo-Acme"}).json()
m = c.post("/api/v1/graph/nodes", json={"kind": "product", "key": "demo-widget", "name": "demo-Widget"}).json()
c.post("/api/v1/graph/edges", json={"src": n["id"], "dst": m["id"], "rel": "OWNS", "at": "2026-01-01"})
c.post("/api/v1/watchlists", json={"kind": "keyword", "value": "demo-acme"})
c.post("/api/v1/workflows", json={"name": "demo-alert", "definition": {"steps": [
    {"condition": {"type": "PRICE"}, "action": "create_alert",
     "params": {"rule": "demo", "message": "demo workflow fired"}}]}})
c.post("/api/v1/connectors", json={"name": "demo-web", "category": "WEB",
    "manifest": {"name": "demo-web", "category": "WEB", "version": "1",
                 "capabilities": ["collect"]}})
print("seeded demo-market: project=%s target=%s" % (p["id"], t["id"]))
