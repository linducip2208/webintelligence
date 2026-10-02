import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from services import graph as G
from services import dedup as D
from services import temporal as T
from services import evidence as E
from services import research as R
from services import workflows as W
from services import datasets as DS
from services import connectors as C
from services import documents as DOC
from services import feed as F
from services import watchlists as WL
from services import opportunities as O
from services import alertguard as AG
from services import webhooks as WH
from services import rbac
from services import nlq
from i18n.lang import t


def test_graph_traverse_history():
    nodes, edges = [], []
    a = G.add_node(nodes, "company", "acme", "Acme")
    b = G.add_node(nodes, "product", "w1", "Widget")
    assert G.add_node(nodes, "company", "acme")["id"] == a["id"]
    G.add_edge(edges, a["id"], b["id"], "OWNS", 0.9, at="2024-01-01")
    G.add_edge(edges, a["id"], b["id"], "OWNS", 0.8, at="2026-01-01")
    assert edges[0]["valid_to"] == "2026-01-01"  # history preserved
    out = G.traverse(nodes, edges, a["id"])
    assert out and out[0]["node"]["id"] == b["id"]


def test_dedup():
    assert D.canonical_url("https://WWW.Example.com/p?utm_source=x&b=2") == "https://example.com/p?b=2"
    h1, h2 = D.fingerprint("Hello  World"), D.fingerprint("hello world")
    assert h1 == h2
    assert D.jaccard("apple banana cherry", "apple banana grape") > 0.3


def test_temporal():
    h = []
    assert T.record(h, "p1", {"price": 10}, "t1")[0] == "NEW"
    assert T.record(h, "p1", {"price": 10}, "t2")[0] == "UNCHANGED"
    assert T.record(h, "p1", {"price": 12}, "t3")[0] == "CHANGED"
    tl = T.timeline(h, "p1")
    assert tl["versions"] == 3 and tl["changes"] == 1 and tl["first_seen"] == "t1"


def test_evidence_verify():
    ev = [{"value": "100", "reliability": 0.9}, {"value": "100", "reliability": 0.7}]
    assert E.verify("100", ev)["status"] == "VERIFIED"
    assert E.verify("100", [])["status"] == "UNVERIFIED"
    assert E.verify("100", ev + [{"value": "120", "reliability": 0.8}])["status"] == "CONFLICTED"
    c = E.contradictions([{"value": "100", "reliability": 0.9}, {"value": "120", "reliability": 0.4}])
    assert c["conflict"] and c["preferred"] == "100"


def test_research_plan():
    p = R.plan("Which companies entered this market with lower pricing?")
    assert "competitor" in p["intents"] and len(p["steps"]) == 8
    b = R.bundle({"question": "q", "plan": p, "ai_model": "m", "config": {}})
    assert b["ai"]["model"] == "m"


def test_workflows_idempotent():
    store = {}
    k1 = W.key(1, "alert", {"x": 1})
    assert W.key(1, "alert", {"x": 1}) == k1
    assert W.check_condition({"type": "PRICE"}, {"type": "PRICE"})
    assert not W.check_condition({"type": "X"}, {"type": "PRICE"})
    r = W.run_step({"action": "create_alert", "params": {"rule": "t", "message": "m"}}, {}, store)
    assert r["ok"] and len(store["alerts"]) == 1
    assert W.run_step({"action": "nope"}, {}, {})["ok"] is False


def test_datasets_versions():
    vs = []
    v1 = DS.publish(vs, 1, [{"a": 1}], {"src": "s"})
    assert v1["version"] == 1
    assert DS.publish(vs, 1, [{"a": 1}], {})["version"] == 1  # no dup version
    assert DS.publish(vs, 1, [{"a": 2}], {})["version"] == 2
    assert "a" in DS.to_csv([{"a": 1}])


def test_connectors_registry():
    assert C.validate_manifest({})  # errors, not exception
    m = {"name": "n", "category": "WEB", "version": "1", "capabilities": ["collect"]}
    assert C.validate_manifest(m) == []
    cs = [{"category": "WEB", "manifest": m, "enabled": True}]
    assert C.match(cs, "collect") == cs and C.match(cs, "x") == []


def test_documents():
    r = DOC.extract("txt", b"hello world", "a.txt")
    assert r["extracted"] and "hello" in r["text"]
    h = DOC.extract("html", b"<p>Hi <b>there</b></p>")
    assert h["text"] == "Hi there"
    p = DOC.extract("pdf", b"%PDF fake")
    assert p["extracted"] is False and "reason" in p
    assert DOC.chunk("abcdefgh", size=4, overlap=1) == ["abcd", "defg", "gh"]
    assert len(DOC.fingerprint(b"x")) == 64


def test_feed_watchlist_opps_guard():
    items = F.build([{"id": 1, "type": "price", "entity_key": "p", "observed_at": "t2"}],
                    [{"id": 1, "title": "F", "created_at": "t1"}], [], [], limit=10)
    assert items[0]["title"].startswith("price")
    wl = [{"id": 1, "kind": "keyword", "value": "acme"}]
    assert WL.match(wl, {"text": "Acme launches X"}) == [1]
    assert WL.match(wl, {"text": "nothing"}) == []
    assert O.price_anomaly([10.0] * 20 + [50.0]) and not O.price_anomaly([1, 2])
    hist = {}
    assert AG.should_fire("k", hist, cooldown_s=60)
    assert not AG.should_fire("k", hist, cooldown_s=60)
    assert AG.group([{"rule": "a", "message": "m"}])[0]["count"] == 1


def test_webhook_sign():
    s1, s2 = WH.sign("s", b"body"), WH.sign("s", b"body!")
    assert s1 != s2 and len(s1) == 64


def test_rbac_nlq_i18n():
    assert rbac.can("viewer", "read") and not rbac.can("viewer", "configure")
    assert rbac.can("owner", "anything")
    assert rbac.scope([{"org": 1}, {"org": 2}], 1) == [{"org": 1}]
    assert nlq.to_plan("What products increased in price this month?")["intent"] == "price_increases"
    store = {"prices": [{"product_id": 1, "price": 10}, {"product_id": 1, "price": 12}]}
    assert nlq.answer(nlq.to_plan("What products increased in price?"), store)[0]["pct"] == 20.0
    assert t("id", "dashboard") == "Dasbor" and t("en", "dashboard") == "Dashboard"
