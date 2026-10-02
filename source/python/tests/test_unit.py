import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from core.ssrf import validate_url, SSRFError
from services import decision as dec
from services import cost as costeng
from services import change as ch
from services import quality as qual
from services import entity_resolution as er
from services import normalize as norm
from services import targets as tgt
from analytics import stats as st
from analytics import ml as ml
from collectors.proxy import OwnProxyProvider
from collectors.brightdata import BrightDataProvider
from ai.muse_provider import MuseSparkProvider
from search import service as searchsvc


def test_ssrf_blocks_private():
    for bad in ["http://localhost/x", "http://127.0.0.1/", "http://10.0.0.5/",
                "http://169.254.169.254/", "ftp://example.com/x", "http://192.168.1.1/"]:
        try:
            validate_url(bad)
            assert False, bad
        except SSRFError:
            pass
    assert validate_url("https://example.com/p?q=1") is True


def test_decision_escalation():
    e = dec.Engine()
    p = dec.Policy(allow_brightdata=True)
    r = e.decide({"last_signals": {"rate_limited": True}}, p,
                 {"own_proxy": {"healthy": True},
                  "brightdata": {"healthy": True, "configured": True}})
    assert r["plan"][0] == "DIRECT_HTTP"
    assert "OWN_PROXY" in r["plan"] and "BRIGHT_DATA" in r["plan"]
    ok, d = dec.validate_result(200, "text/html", 5000, ["price"], True, 0.9)
    assert ok
    ok2, _ = dec.validate_result(200, "text/html", 5000, ["price"], True, 0.1)
    assert not ok2  # 200 but incomplete


def test_cost():
    assert costeng.estimate("DIRECT_HTTP") < costeng.estimate("BRIGHT_DATA")
    assert costeng.per_1k(1.0, 100) == 10.0
    assert costeng.within_budget(0.5, 1.0)


def test_change_quality():
    assert ch.classify(None, "a", {}, {}) == "NEW"
    assert ch.classify("a", "a", {"p": 1}, {"p": 1}) == "UNCHANGED"
    assert ch.classify("a", "b", {"p": 1}, {"p": 2}) == "CHANGED"
    assert ch.field_diff({"p": 1}, {"p": 2}) == {"p": {"old": 1, "new": 2}}
    q = qual.score({"price": 10}, ["price"])
    assert q["overall"] > 0.8


def test_entity_normalize_targets():
    assert er.decide(er.score({"name": "Nike Air"}, {"name": "nike  air!"})) == "LINK"
    assert er.decide(er.score({"name": "abc"}, {"name": "xyz totally different thing"})) == "NEW"
    v, c = norm.parse_price("$ 1,299.99")
    assert v == 1299.99 and c == "USD"
    p = tgt.record_attempt({}, "DIRECT_HTTP", True, 100, 0.01)
    assert p["attempts"] == 1 and tgt.preferred_strategy(p) == "DIRECT_HTTP"


def test_analytics():
    assert st.mean([1, 2, 3]) == 2.0
    assert st.pct_change(100, 110) == 10.0
    assert st.pearson([1, 2, 3], [1, 2, 3]) == 1.0
    assert ml.forecast_ewma([1, 2, 3]) is not None
    assert ml.sentiment("I love it, excellent!") == "positive"


def test_proxy_brightdata():
    o = OwnProxyProvider(["http://a:1", "http://b:2"])
    assert o.get_proxy() in ("http://a:1", "http://b:2")
    b = BrightDataProvider("", "")
    assert b.configured is False
    assert b.health_check()["ok"] is False
    m = MuseSparkProvider("", "")
    assert m.health_check()["ok"] is False


def test_search_dashboard():
    from api.dashboard import build

    d = build([{"status": "success"}], [], [], [], {})
    assert d["jobs_success"] == 1
    r = searchsvc.search({"products": [{"name": "Nike Air"}]}, "nike", limit=5)
    assert len(r) == 1
