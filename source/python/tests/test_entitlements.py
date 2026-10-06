import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from services import entitlements as E  # noqa: E402


def _store(org_plan="starter"):
    return {"orgs": [{"id": 1, "plan": org_plan}], "projects": [], "targets": [],
            "jobs": [], "ai_usage": [], "connectors": []}


def test_starter_quotas():
    s = _store()
    s["projects"] = [{"org": 1}, {"org": 1}, {"org": 1}]
    ok, why = E.check(s, 1, "projects")
    assert not ok and "max_projects=3" in why
    ok, _ = E.check(s, 1, "browser")
    assert not ok
    ok, _ = E.check(s, 1, "targets")
    assert ok


def test_pro_and_enterprise():
    s = _store("pro")
    assert E.check(s, 1, "browser")[0] is True
    assert E.check(s, 1, "projects")[0] is True
    s2 = _store("enterprise")
    for _ in range(5):
        s2["projects"].append({"org": 1})
    assert E.check(s2, 1, "projects")[0] is True


def test_ai_quota_and_usage():
    s = _store()
    s["ai_usage"] = [{"org": 1, "input_tokens": 99900, "output_tokens": 0}]
    ok, why = E.check(s, 1, "ai_tokens", 200)
    assert not ok and "max_ai_tokens" in why
    u = E.usage(s, 1)
    assert u["plan"] == "starter" and u["used"]["ai_tokens"] == 99900
    assert u["limits"]["max_projects"] == 3


def test_jobs_quota_mixed_timestamp_shapes():
    import time
    import datetime as _dt
    s = _store()
    s["jobs"] = [{"org": 1, "created_at": time.time()},
                 {"org": 1, "created_at": _dt.datetime.now().isoformat()},
                 {"org": 1},
                 {"org": 1, "created_at": "garbage"}]
    assert E.check(s, 1, "jobs")[0] is True
    assert E.usage(s, 1)["used"]["jobs_today"] == 2
    assert E._day_of(None) == "" and E._day_of("garbage") == ""
