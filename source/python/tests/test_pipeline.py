import sys, os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from services import pipeline as pipe
from services import decision as dec
from auth.tokens import issue, verify


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><body>Only $29.99 today! Was $49.99</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def _server():
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_pipeline_end_to_end_local():
    srv = _server()
    url = f"http://127.0.0.1:{srv.server_port}/p"
    trust = ["127.0.0.1/32"]
    f = pipe.fetch_direct(url, trusted_cidrs=trust)
    assert f["ok"] and f["http_status"] == 200 and f["body"]
    res = pipe.run_job({"job_id": "j1", "url": url}, {"url": url}, [],
                       dec.Policy(), {"own_proxy": {"healthy": True},
                                      "brightdata": {"healthy": False,
                                                     "configured": False}},
                       trusted_cidrs=trust)
    assert res["status"] == "success"
    assert res["prices"] and res["prices"][0]["price"] == 29.99
    assert res["change"] == "NEW"
    # second run with previous price -> CHANGED + alert
    res2 = pipe.run_job({"job_id": "j2", "url": url}, {"url": url},
                        [{"price": 99.0}], dec.Policy(),
                        {"own_proxy": {"healthy": True},
                         "brightdata": {"healthy": False, "configured": False}},
                        trusted_cidrs=["127.0.0.1/32"])
    assert res2["change"] == "CHANGED"
    assert any(a["rule"] == "price_changed" for a in res2["alerts"])
    srv.shutdown()


def test_pipeline_ssrf_blocked():
    try:
        pipe.run_job({"job_id": "x", "url": "http://localhost/secret"},
                     {"url": "http://localhost/secret"}, [], dec.Policy(), {})
        assert False, "SSRF url must not be fetched"
    except Exception:
        pass


def test_fetch_ssrf_raises():
    try:
        pipe.fetch_direct("http://169.254.169.254/")
        assert False
    except Exception:
        pass


def test_tokens():
    t = issue("a@b.c", "secret123")
    assert verify(t, "secret123") == "a@b.c"
    assert verify(t, "wrong") is None
    assert verify("garbage", "secret123") is None
