import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from services import flags as FL  # noqa: E402
from services import pii as PII  # noqa: E402
from services import graph as G  # noqa: E402


class FakeRepo:
    def __init__(self):
        self.kv = {}

    def kv_set(self, k, v):
        self.kv[k] = v

    def kv_get(self, k, default=None):
        return self.kv.get(k, default)


def test_flags_scoped():
    r = FakeRepo()
    assert FL.is_enabled(r, "ai") is True
    FL.set_flag(r, "ai", False)
    assert FL.is_enabled(r, "ai") is False
    FL.set_flag(r, "ai", True, scope="org", ref="9")
    assert FL.is_enabled(r, "ai", org=9) is True
    assert FL.key("x", "org", "1") == "flag:org:1:x"


def test_pii():
    found = PII.detect("mail me at joe@x.io or +62 812-3456-7890, NIK 1234567890123456")
    assert found["email"] == ["joe@x.io"] and found["nik_like"] == ["1234567890123456"]
    masked = PII.mask("joe@x.io called")
    assert "joe@x.io" not in masked and "[REDACTED]" in masked
    assert PII.detect("") == {}


def test_graph_path():
    nodes = [{"id": 1}, {"id": 2}, {"id": 3}]
    edges = [{"src": 1, "dst": 2, "rel": "OWNS"}, {"src": 2, "dst": 3, "rel": "SELLS"}]
    hops = G.path(nodes, edges, 1, 3)
    assert [h["via"] for h in hops] == [None, "OWNS", "SELLS"]
    assert G.path(nodes, edges, 1, 9) == []
    assert G.path(nodes, edges, 2, 2)[0]["node"] == {"id": 2}
