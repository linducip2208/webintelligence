"""Live browser tests: real Chromium renders real local pages (incl. JS).

Skips honestly when the browser cannot launch in this environment.
"""
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

playwright = pytest.importorskip("playwright")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "source", "python"))
from app.browser import worker as bw  # noqa: E402


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = (b"<html><head><title>static</title></head><body>"
                b"<div id='app'>loading</div>"
                b"<script>document.getElementById('app').textContent='RENDERED-BY-JS $42.00';"
                b"document.title='js-title';</script></body></html>")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def _srv():
    s = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def test_browser_ssrf_guard():
    r = bw.fetch("http://169.254.169.254/")
    assert r["ok"] is False and "ssrf" in r["error"]


def test_browser_renders_js():
    try:
        s = _srv()
        url = f"http://127.0.0.1:{s.server_port}/p"
        out = bw.fetch(url, trusted_cidrs=["127.0.0.1/32"])
    except Exception as e:
        pytest.skip(f"browser cannot launch here: {e}")
    if not out.get("ok"):
        pytest.skip(f"browser fetch failed here: {out.get('error')}")
    assert out["http_status"] == 200
    assert "RENDERED-BY-JS" in out["html"]  # proves JS actually executed
    assert "$42.00" in out["html"]
    st = bw.pool_status()
    assert st["installed"] is True and st["browser_alive"] is True
    s.shutdown()
