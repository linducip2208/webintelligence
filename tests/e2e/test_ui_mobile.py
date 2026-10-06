"""UI E2E: mobile viewport — no horizontal overflow, sidebar toggler works.

Gated: UI_E2E=1 (spawns uvicorn + Chromium).
"""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import pytest

playwright = pytest.importorskip("playwright")
pytestmark = pytest.mark.skipif(not os.getenv("UI_E2E"), reason="set UI_E2E=1 for browser UI E2E")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PORT = 8009


def test_ui_mobile_no_overflow():
    tmp = tempfile.mkdtemp(prefix="uimob_")
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{tmp}/ui.db".replace(os.sep, "/"),
               REQUIRE_AUTH="0", DATA_DIR=tmp, OLLAMA_BASE_URL="disabled")
    env.pop("PYTEST_CURRENT_TEST", None)
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                            "--host", "127.0.0.1", "--port", str(PORT)],
                           cwd=os.path.join(ROOT, "source", "python"), env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        deadline = time.time() + 30
        while True:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/healthz", timeout=5)
                break
            except Exception:
                assert time.time() < deadline, "api never came up"
                time.sleep(0.5)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{PORT}/", timeout=30000)
            pg.wait_for_selector("#mnav", timeout=15000)
            for v in ("dashboard", "targets", "alerts"):
                pg.evaluate(f"view='{v}'; load()")
                pg.wait_for_timeout(800)
                overflow = pg.evaluate(
                    "document.documentElement.scrollWidth - document.documentElement.clientWidth")
                assert overflow <= 1, (v, overflow)
            toggler = pg.locator("#mnav")
            assert toggler.is_visible(), "menu button must be visible on mobile"
            toggler.click()
            pg.wait_for_timeout(500)
            assert pg.locator(".navbar-vertical.open").is_visible()
            pg.locator("#nav a").first.click()
            pg.wait_for_timeout(500)
            assert pg.locator(".navbar-vertical.open").count() == 0
            assert errs == [], errs
            b.close()
    finally:
        api.terminate()
