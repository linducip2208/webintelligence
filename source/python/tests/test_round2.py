import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from services import reliability as REL
from services import correlate as COR
from services import entityops as OPS
from services import predict as PR
from services import feed as F
from services import alertguard as AG


def test_reliability_honest():
    assert REL.score([]) == {"score": None, "reason": "no history"}
    atts = [{"ok": True, "latency_ms": 200, "completeness": 1.0}] * 8 + [
        {"ok": False, "latency_ms": 5000, "completeness": 0.2}]
    s = REL.score(atts)
    assert 0.5 < s["score"] < 1.0 and s["attempts"] == 9
    assert s["success_rate"] == round(8 / 9, 3)


def test_correlate():
    assert COR.shared_entities([{"entities": ["a", "b"]}], [{"entities": ["b", "c"]}]) == ["b"]
    out = COR.correlate_price_sources({"s1": [10.0], "s2": [10.0], "s3": [12.0]})
    kinds = sorted(x["type"] for x in out)
    assert kinds == ["AGREEMENT", "CONFLICT", "CONFLICT"]
    f = COR.to_finding(out[0], [7])
    assert f["evidence_ids"] == [7] and f["confidence"] == 0.7


def test_entity_ops_history():
    ents = [{"id": 1, "name": "A"}, {"id": 2, "name": "a"}]
    hist = []
    assert OPS.merge(ents, hist, 1, 2, actor="t")["ok"]
    assert ents[1]["merged_into"] == 1 and hist[0]["op"] == "MERGE"
    assert OPS.merge(ents, hist, 1, 99)["ok"] is False
    r = OPS.split(ents, hist, 1, [{"name": "A1"}, {"name": "A2"}])
    assert r["ok"] and len(r["entities"]) == 2
    assert OPS.reject(hist, 2, "dup")["ok"] and hist[-1]["op"] == "REJECT"


def test_predict_metadata():
    assert PR.predict([1.0, 2.0])["ok"] is False
    p = PR.predict([10.0, 11.0, 12.0, 13.0], model="linear")
    assert p["ok"] and p["model"] == "price-linear-v1"
    assert "not a fact" in p["note"] and p["features"]["n"] == 4


def test_feed_subs_threshold():
    items = [{"kind": "PRICE_CHANGE", "title": "Acme price up"},
             {"kind": "ALERT", "title": "other"}]
    assert len(F.subscribed(items, [{"kinds": ["PRICE_CHANGE"]}])) == 1
    assert len(F.subscribed(items, [{"keywords": ["acme"]}])) == 1
    assert F.subscribed(items, [{"kinds": ["X"]}]) == []
    assert AG.check_threshold(10, "gt", 5)["fired"] is True
    assert AG.check_threshold(10, "lt", 5)["fired"] is False
    assert AG.check_threshold(1, "bad", 1)["ok"] is False
