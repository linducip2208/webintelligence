"""Docs screenshot manifest tests (no browser needed).

Validates the committed manifest + PNG files produced by
scripts/docs/generate_screenshots.py.
"""
import json
import os
import struct

import app as _app_pkg
from app import docs_data as D
from app.main import app

APP_DIR = os.path.dirname(os.path.abspath(_app_pkg.__file__))
SHOT_DIR = os.path.join(APP_DIR, "static", "docs_assets", "screenshots")


def _png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(26)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", f"not a PNG: {path}"
    return struct.unpack(">II", head[16:24])


def _manifest():
    with open(os.path.join(SHOT_DIR, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)


def test_manifest_covers_plan():
    manifest = _manifest()
    planned = {s["file"] for s in D.SHOTS}
    assert planned <= set(manifest), f"missing: {sorted(planned - set(manifest))[:5]}"


def test_shot_files_sane():
    for shot in D.SHOTS:
        p = os.path.join(SHOT_DIR, shot["file"])
        assert os.path.isfile(p), f"missing {shot['file']}"
        assert os.path.getsize(p) > 0, f"empty {shot['file']}"
        w, h = _png_size(p)
        assert w >= 300 and h >= 300, f"tiny {shot['file']}: {w}x{h}"


def test_manifest_entries_honest():
    manifest = _manifest()
    for shot in D.SHOTS:
        m = manifest[shot["file"]]
        for k in ("route", "viewport", "generated_at", "app_version"):
            assert m.get(k), f"{shot['file']} missing {k}"
        assert m["app_version"] == app.version
        assert m["route"], f"{shot['file']} has no route"


def test_tutorial_shots_present():
    manifest = _manifest()
    required = ["01-login.png", "02-dashboard.png", "03-new-investigation.png",
                "09-queued.png", "10-running.png", "11-completed.png",
                "12-findings.png", "14-graph.png", "15-risk.png",
                "17-evidence.png", "18-case.png", "19-report.png",
                "20-watchlist.png", "21-alert.png", "22-workflow.png"]
    for f in required:
        assert f in manifest, f"tutorial shot missing: {f}"
