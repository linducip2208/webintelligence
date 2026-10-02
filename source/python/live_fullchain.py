"""LIVE full chain (§63 with real processes, no mocks):
fakeredis TCP (real RESP) + uvicorn API + real Go collector binary + local page.

Run:  LIVE_FULLCHAIN=1 python tests/integration/test_live_fullchain.py
   or: python source/python/live_fullchain.py  (self-contained demo)

Requires: fakeredis, redis, uvicorn, Go-built collector binary.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while os.path.basename(ROOT) not in ("webintelligence", "") and len(ROOT) > 3:
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "source", "python"))

REDIS_PORT = 6399
API_PORT = 8001


class Page(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html><body>LiveChain Gadget Only $77.50 today</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def _page_server():
    s = HTTPServer(("127.0.0.1", 0), Page)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def run_chain(timeout_s=90):
    import urllib.request
    sys.path.insert(0, os.path.join(ROOT, "tests", "integration"))
    from resp_server import MiniRedis

    tmp = tempfile.mkdtemp(prefix="livechain_")
    dbfile = os.path.join(tmp, "live.db").replace(os.sep, "/")
    mini = MiniRedis(port=REDIS_PORT)
    threading.Thread(target=mini.serve_forever, daemon=True).start()
    time.sleep(0.3)
    shutdown_fake = mini.shutdown

    env = dict(os.environ,
               DATABASE_URL=f"sqlite:///{dbfile}",
               REDIS_URL=f"redis://127.0.0.1:{REDIS_PORT}/0",
               TRUSTED_EGRESS_CIDRS="127.0.0.1/32",
               REQUIRE_AUTH="0", DATA_DIR=tmp)
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("PYTEST_VERSION", None)
    api_log = open(os.path.join(tmp, "api.log"), "w")
    api = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(API_PORT)],
        cwd=os.path.join(ROOT, "source", "python"), env=env,
        stdout=api_log, stderr=subprocess.STDOUT)

    def call(method, path, payload=None):
        req = urllib.request.Request(
            f"http://127.0.0.1:{API_PORT}{path}",
            data=json.dumps(payload or {}).encode() if payload is not None or method == "POST" else None,
            headers={"Content-Type": "application/json"}, method=method)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode() or "{}")

    try:
        page = _page_server()
        page_url = f"http://127.0.0.1:{page.server_address[1]}/gadget"
        deadline = time.time() + 30
        while True:
            try:
                assert call("GET", "/healthz")["status"] == "ok"
                break
            except Exception:
                if time.time() > deadline:
                    raise RuntimeError("api never came up; see " + api_log.name)
                time.sleep(0.5)
        p = call("POST", "/api/v1/projects", {"name": "Live", "description": ""})
        t = call("POST", "/api/v1/targets", {"project_id": p["id"], "domain": "127.0.0.1",
                                             "url": page_url})
        job = call("POST", "/api/v1/jobs", {"project_id": p["id"], "target_id": t["id"],
                                            "url": page_url, "strategy": "AUTO"})
        assert job["plan"]["plan"][0] == "DIRECT_HTTP", job

        go_dir = os.path.join(ROOT, "source", "go", "collector")
        binary = os.path.join(tmp, "collector-live.exe")
        subprocess.run(["go", "build", "-o", binary, "./cmd/collector"],
                       cwd=go_dir, check=True, capture_output=True, timeout=180)
        coll_log = open(os.path.join(tmp, "collector.log"), "w")
        coll = subprocess.Popen(
            [binary], env=dict(env, REDIS_ADDR=f"127.0.0.1:{REDIS_PORT}",
                               API_BASE=f"http://127.0.0.1:{API_PORT}"),
            stdout=coll_log, stderr=subprocess.STDOUT)
        try:
            deadline = time.time() + timeout_s
            final = None
            while time.time() < deadline:
                js = call("GET", "/api/v1/jobs")
                match = [j for j in js["items"] if j["job_id"] == job["job_id"]]
                if match and match[0]["status"] in ("success", "failed"):
                    final = match[0]
                    break
                time.sleep(1.0)
            assert final and final["status"] == "success", f"collector did not succeed: {final}"
            prices = call("GET", "/api/v1/prices")["items"]
            assert any(x["price"] == 77.5 for x in prices), prices
            dash = call("GET", "/api/v1/dashboard")
            assert dash["jobs_success"] >= 1 and dash["price_points"] >= 1
            # RESTART RECOVERY: kill API, boot fresh on the same DB file
            api.terminate()
            api.wait(timeout=15)
            time.sleep(1)
            api2_log = open(os.path.join(tmp, "api2.log"), "w")
            api2 = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                 "--port", str(API_PORT)],
                cwd=os.path.join(ROOT, "source", "python"), env=env,
                stdout=api2_log, stderr=subprocess.STDOUT)
            try:
                deadline = time.time() + 30
                while True:
                    try:
                        assert call("GET", "/healthz")["status"] == "ok"
                        break
                    except Exception:
                        if time.time() > deadline:
                            raise RuntimeError("restarted api never came up")
                        time.sleep(0.5)
                dash2 = call("GET", "/api/v1/dashboard")
                assert dash2["jobs_success"] >= 1 and dash2["price_points"] >= 1, dash2
                assert os.path.exists(dbfile.replace("/", os.sep))
            finally:
                api2.terminate()
                api = None  # already dead; skip double-terminate below
            return {"job": final["job_id"], "price_points": dash["price_points"],
                    "db": dbfile, "tmp": tmp}
        finally:
            coll.terminate()
    finally:
        try:
            if api is not None:
                api.terminate()
        except Exception:
            pass
        page.shutdown()
        shutdown_fake()


if __name__ == "__main__":
    print(run_chain())
