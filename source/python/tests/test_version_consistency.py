"""Version single source of truth: every declaration must agree."""
import os
import re

import app as _pkg
from app.main import app
from app.version import APP_VERSION, API_VERSION, BUILD_ID, APP_NAME

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_version_consistency():
    assert app.version == APP_VERSION
    assert _pkg.__version__ == APP_VERSION
    assert APP_NAME == "webintel" and API_VERSION == "v1" and BUILD_ID
    import tomllib
    with open(os.path.join(ROOT, "source", "python", "pyproject.toml"), "rb") as fh:
        assert tomllib.load(fh)["project"]["version"] == APP_VERSION
    y = open(os.path.join(ROOT, "contracts", "openapi", "openapi.yaml"), encoding="utf-8").read()
    assert re.search(r"version:\s*" + re.escape(APP_VERSION), y)
    assert app.openapi()["info"]["version"] == APP_VERSION
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    assert f"v{APP_VERSION}" in readme.splitlines()[0]
    from fastapi.testclient import TestClient
    c = TestClient(app)
    hz = c.get("/healthz").json()
    assert hz["status"] == "ok" and hz["version"] == APP_VERSION
    assert hz["api_version"] == API_VERSION and hz["build"] == BUILD_ID
    ver = c.get("/api/version").json()
    assert ver["version"] == APP_VERSION and ver["api_version"] == API_VERSION


def test_no_stale_version_literals():
    stale = []
    for base in (os.path.join(ROOT, "source", "python", "app"),
                 os.path.join(ROOT, "source", "go")):
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in ("__pycache__",)]
            for f in files:
                if not f.endswith((".py", ".html", ".js", ".go", ".mod")):
                    continue
                if "vendor" in root or f.endswith(".min.js"):
                    continue
                p = os.path.join(root, f)
                try:
                    text = open(p, encoding="utf-8").read()
                except Exception:
                    continue
                for lit in ("1.0.0", "2.5.0", "2.11", "2.12", "2.13"):
                    if lit == APP_VERSION:
                        continue
                    for m in re.finditer(r"[\"'}\s>=:(]" + re.escape(lit) + r"(?=[\"'\s<.,)])", text):
                        stale.append(f"{os.path.relpath(p, ROOT)}: {lit}")
    assert not stale, stale[:10]
