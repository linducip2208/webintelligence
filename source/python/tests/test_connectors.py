import sys, os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from connectors.runners import execute  # noqa: E402


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/feed":
            body = (b'<?xml version="1.0"?><rss version="2.0"><channel>'
                    b"<title>T</title>"
                    b"<item><title>Item One</title><link>https://x.test/1</link>"
                    b"<pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>"
                    b"<description>First</description></item>"
                    b"<item><title>Item Two</title><link>https://x.test/2</link></item>"
                    b"</channel></rss>")
            ctype = "application/rss+xml"
        elif self.path == "/api":
            import json as _j
            body = _j.dumps({"items": [{"a": 1}, {"a": 2}],
                             "next": f"http://127.0.0.1:{self.server.server_port}/api?page=2"}).encode()
            ctype = "application/json"
        else:
            body, ctype = b"{}", "application/json"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def _srv():
    s = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def test_rss_real():
    s = _srv()
    url = f"http://127.0.0.1:{s.server_port}/feed"
    import app.services.decision  # noqa  (ensure ssrf trust path used below)
    os.environ["TRUSTED_EGRESS_CIDRS"] = "127.0.0.1/32"
    out = execute({"category": "NEWS", "config": {"url": url}})
    assert out["ok"] and len(out["items"]) == 2
    assert out["items"][0]["title"] == "Item One"
    assert out["items"][1]["url"] == "https://x.test/2"
    bad = execute({"category": "NEWS", "config": {"url": "http://169.254.169.254/"}})
    assert not bad["ok"] and "ssrf" in bad["error"]
    assert execute({"category": "NOPE", "config": {}})["ok"] is False
    s.shutdown()


def test_rest_pagination_real():
    s = _srv()
    url = f"http://127.0.0.1:{s.server_port}/api"
    os.environ["TRUSTED_EGRESS_CIDRS"] = "127.0.0.1/32"
    out = execute({"category": "API", "config": {"url": url, "data_path": "items",
                                                 "next_path": "next", "max_pages": 3}})
    assert out["ok"] and len(out["items"]) >= 2 and out["pages"] >= 1
    s.shutdown()


def test_csv_inline():
    out = execute({"category": "DOCUMENT",
                   "config": {"kind": "csv", "text": "a;b\n1;2\n3;4"}})
    assert out["ok"] and out["items"] == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
    assert execute({"category": "DOCUMENT", "config": {"kind": "csv", "text": ""}})["ok"] is False
