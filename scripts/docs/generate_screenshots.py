"""Documentation screenshot generator: real UI, real data, no secrets.

Starts the app with an isolated DATA_DIR, seeds the labeled DEMO workspace
(RFC-2606 .example domains only — never external targets), drives the actual
frontend with Playwright, captures docs/assets screenshots and writes
manifest.json. Redacts the dev-credential hint before capturing login.

Windows:  python scripts/docs/generate_screenshots.py
Linux:    python3 scripts/docs/generate_screenshots.py

Options: --port 8123 --update (re-capture all) --shots 01-login.png,02-dashboard.png
         --keep-data (do not purge demo data afterwards)
"""
import argparse
import base64
import copy
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

try:
    from app import docs_data as D
except Exception as e:
    print("cannot import app:", e)
    sys.exit(2)

APP_DIR = os.path.join(ROOT, "source", "python")
SHOT_DIR = os.path.join(APP_DIR, "app", "static", "docs_assets", "screenshots")
MIRROR_DIR = os.path.join(ROOT, "docs", "assets", "screenshots")


# ---------------------------------------------------------------- slow origin
class _Slow(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(6)
        body = (b"<html><head><title>Docs demo origin</title></head><body>"
                b"<h1>Docs demo product</h1><p>Price: $42.00</p></body></html>")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def log_message(self, *a):
        pass


def start_slow():
    srv = HTTPServer(("127.0.0.1", 0), _Slow)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv, port


def wait_http(base, path="/healthz", timeout=60):
    import urllib.request
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(base + path, timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    raise RuntimeError("server did not start: " + base)


def api(client, method, path, body=None):
    import urllib.request
    data = json.dumps(body or {}).encode() if body is not None or method in ("POST", "PUT") else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read().decode()
    return json.loads(raw) if raw else {}


def seed_demo():
    try:
        return api(None, "POST", "/api/v1/admin/demo/seed", {})
    except Exception as e:
        if "409" in str(e):
            return {"ok": True, "existing": True}
        raise


def ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        print("playwright not installed; installing browsers is skipped — install playwright first")
        sys.exit(2)


def launch(pw):
    try:
        return pw.chromium.launch(args=["--no-sandbox", "--force-device-scale-factor=1"])
    except Exception as e:
        print("chromium launch failed, trying install:", str(e)[:200])
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
        return pw.chromium.launch(args=["--no-sandbox", "--force-device-scale-factor=1"])


REDACT_JS = """() => {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const texts = [];
  while (walker.nextNode()) texts.push(walker.currentNode);
  for (const n of texts) {
    if (/admin@local\\s*\\/\\s*\\S+/.test(n.nodeValue || '')) {
      n.nodeValue = (n.nodeValue || '').replace(/admin@local\\s*\\/\\s*\\S+/, 'admin@local / [redacted in documentation]');
    }
  }
  const t = document.getElementById('toasts');
  if (t) t.style.display = 'none';
}"""

SECRET_SENTINELS = ["DOCS-SHOT-SECRET-1", "DOCS-SHOT-KEY-2"]


def check_no_secrets(page, shot):
    try:
        html = page.content()
    except Exception:
        return
    for pat in SECRET_SENTINELS:
        if pat in html:
            raise RuntimeError(f"secret sentinel present before shot {shot}")
    if "admin123" in html.lower():
        raise RuntimeError(f"dev credential leaked before shot {shot}")


def nav_target(shot, jobs, inv_id, case_id):
    view = shot["view"]
    if view == "__docs__":
        return BASE + "/docs/en/index", None
    if view.startswith("__docs__/"):
        return BASE + "/docs/en/" + view[len("__docs__/"):], None
    if view == "job":
        key = {"09-queued.png": "queued", "10-running.png": "running",
               "11-completed.png": "success"}[shot["file"]]
        jid = jobs[key]
        return BASE + "/#job/" + jid, "go('job','" + jid + "')"
    if view == "investigation" and inv_id:
        return BASE + f"/#investigation/{inv_id}", f"go('investigation',{inv_id})"
    if view == "cases" and case_id:
        return BASE + f"/#case/{case_id}", f"go('case',{case_id})"
    return BASE + "/#" + view, "go('" + view + "')"


def capture(page, base, shot, jobs, inv_id, case_id):
    url, go_expr = nav_target(shot, jobs, inv_id, case_id)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    if go_expr:
        page.evaluate(go_expr)
    ready_sel = "#docs-content" if go_expr is None else "#content"
    page.wait_for_selector(ready_sel, timeout=30000)
    if go_expr is not None:
        try:
            page.wait_for_function(
                "() => { const c = document.querySelector('#content'); "
                "return c && !c.querySelector('.placeholder-glow'); }",
                timeout=25000)
        except Exception:
            pass
    if shot["file"] == "32-search-results.png":
        try:
            page.fill("#sq", "acme")
            page.evaluate("document.querySelector('#content form').requestSubmit()")
            page.wait_for_function(
                "() => { const r = document.querySelector('#res'); "
                "return r && !/Searching/.test(r.textContent||''); }",
                timeout=30000)
        except Exception:
            pass
    page.wait_for_timeout(1200)
    page.evaluate(REDACT_JS)
    check_no_secrets(page, shot["file"])
    return url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8123)
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--shots", default="")
    ap.add_argument("--keep-data", action="store_true")
    args = ap.parse_args()
    global BASE
    BASE = f"http://127.0.0.1:{args.port}"

    only = {s.strip() for s in args.shots.split(",") if s.strip()}
    os.makedirs(SHOT_DIR, exist_ok=True)

    tmp = tempfile.mkdtemp(prefix="wi-docs-")
    env = dict(os.environ)
    env.pop("DATABASE_URL", None)
    env["DATA_DIR"] = tmp
    env["TRUSTED_EGRESS_CIDRS"] = "127.0.0.1/32"
    env["ENV"] = "dev"
    env["SECRET_KEY"] = "DOCS-SHOT-SECRET-1"
    env["CREDENTIALS_KEY"] = "DOCS-SHOT-KEY-2"

    log_path = os.path.join(tmp, "uvicorn.log")
    log_fh = open(log_path, "w", encoding="utf-8")
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                            "--port", str(args.port)],
                           cwd=APP_DIR, env=env,
                           stdout=log_fh, stderr=subprocess.STDOUT)
    manifest = {}
    man_path = os.path.join(SHOT_DIR, "manifest.json")
    if os.path.isfile(man_path):
        try:
            manifest = json.load(open(man_path, encoding="utf-8"))
        except Exception:
            manifest = {}
    try:
        wait_http(BASE)
        from app.main import app as _app
        version = _app.version

        seed = seed_demo()
        demo_pid = seed.get("project_id")

        slow, slow_port = start_slow()
        slow_url = f"http://127.0.0.1:{slow_port}/slow"
        # doc target + jobs for queued/running/success states
        projs = api(None, "GET", "/api/v1/projects?size=100")
        pid = demo_pid or (projs["items"] or [{}])[0].get("id")
        tgt = api(None, "POST", "/api/v1/targets",
                  {"project_id": pid, "domain": "docs-slow.example",
                   "url": slow_url, "source_type": "website", "tags": ["docs"]})
        tid = tgt["id"]
        q = api(None, "POST", "/api/v1/jobs",
                {"project_id": pid, "target_id": tid, "url": slow_url,
                 "strategy": "AUTO", "profile": "quick"})
        jobs = {"queued": q["job_id"]}

        run_box = {}
        def _bg():
            try:
                import urllib.request
                req = urllib.request.Request(
                    BASE + f"/api/v1/jobs/{q['job_id']}/run", data=b"{}",
                    method="POST", headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    run_box["res"] = json.loads(r.read().decode())
            except Exception as e:
                run_box["err"] = str(e)[:200]

        # demo investigation + case ids for detail shots
        invs = api(None, "GET", "/api/v1/investigations?size=100")
        inv_id = (invs.get("items") or [{}])[0].get("id")
        cases = api(None, "GET", "/api/v1/cases?size=100")
        case_id = (cases.get("items") or [{}])[0].get("id")

        sync_playwright = ensure_playwright()
        with sync_playwright() as pw:
            browser = launch(pw)
            try:
                desks = [s for s in D.SHOTS if s["kind"] == "desktop"]
                mobs = [s for s in D.SHOTS if s["kind"] == "mobile"]
                if only:
                    desks = [s for s in desks if s["file"] in only]
                    mobs = [s for s in mobs if s["file"] in only]

                ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                                          timezone_id="Asia/Jakarta",
                                          reduced_motion="reduce")
                page = ctx.new_page()
                bg = None
                for shot in desks:
                    if shot["file"] == "10-running.png" and bg is None:
                        bg = threading.Thread(target=_bg, daemon=True)
                        jobs["running"] = jobs["queued"]
                        bg.start()
                        # wait until the job really reports running
                        t0 = time.time()
                        while time.time() - t0 < 30:
                            try:
                                j = api(None, "GET", f"/api/v1/jobs/{q['job_id']}")
                            except Exception:
                                time.sleep(0.2)
                                continue
                            if j.get("status") == "running":
                                break
                            time.sleep(0.2)
                    if shot["file"] in ("10-running.png", "11-completed.png") and "success" not in jobs and bg is None:
                        # subset run without the running shot: execute synchronously first
                        _bg()
                        sj = api(None, "GET", f"/api/v1/jobs/{q['job_id']}")
                        if sj.get("status") != "success":
                            raise RuntimeError("run did not succeed: " + str(sj.get("status")))
                        jobs["success"] = q["job_id"]
                    url = capture(page, BASE, shot, jobs, inv_id, case_id)
                    if shot["file"] == "10-running.png" and bg is not None:
                        bg.join(timeout=120)
                        sj = api(None, "GET", f"/api/v1/jobs/{q['job_id']}")
                        if sj.get("status") != "success":
                            raise RuntimeError("run did not succeed: " + str(sj.get("status"))
                                               + " " + str(run_box.get("err", "")))
                        jobs["success"] = q["job_id"]
                    dest = os.path.join(SHOT_DIR, shot["file"])
                    if os.path.isfile(dest) and not args.update and shot["file"] not in only:
                        pass
                    else:
                        page.screenshot(path=dest)
                    manifest[shot["file"]] = {
                        "route": url.replace(BASE, ""), "view": shot["view"],
                        "viewport": "1440x900", "theme": "light", "lang": "en",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "app_version": version,
                        "redacted": shot["file"] == "01-login.png",
                        "demo_data": True}
                    print("shot", shot["file"], "->", url.replace(BASE, ""))
                ctx.close()

                if mobs:
                    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                                              timezone_id="Asia/Jakarta",
                                              reduced_motion="reduce",
                                              is_mobile=True, has_touch=True)
                    page = ctx.new_page()
                    for shot in mobs:
                        url = capture(page, BASE, shot, jobs, inv_id, case_id)
                        dest = os.path.join(SHOT_DIR, shot["file"])
                        if os.path.isfile(dest) and not args.update and shot["file"] not in only:
                            pass
                        else:
                            page.screenshot(path=dest)
                        manifest[shot["file"]] = {
                            "route": url.replace(BASE, ""), "view": shot["view"],
                            "viewport": "390x844", "theme": "light", "lang": "en",
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "app_version": version, "redacted": False,
                            "demo_data": True}
                        print("shot", shot["file"], "->", url.replace(BASE, ""))
                    ctx.close()
            finally:
                browser.close()
        slow.shutdown()

        with open(man_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=1)
        # mirror to docs/assets/screenshots for the repo-level contract
        os.makedirs(MIRROR_DIR, exist_ok=True)
        for f in os.listdir(SHOT_DIR):
            if f.endswith(".png") or f == "manifest.json":
                shutil.copy2(os.path.join(SHOT_DIR, f), os.path.join(MIRROR_DIR, f))
        print("manifest entries:", len(manifest))
        if not args.keep_data:
            print("demo data lives in isolated temp DATA_DIR only; nothing to purge from production")
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=10)
        except Exception:
            srv.kill()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
