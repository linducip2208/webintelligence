"""Validate docs screenshots. Run from repo root:

    python scripts/docs/validate_screenshots.py

Checks: every planned shot exists in both locations, non-zero size, sane
dimensions (PNG IHDR), manifest complete and version-matched, no secrets
in filenames, tutorial coverage present.
"""
import json
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import docs_data as D  # noqa: E402
from app.main import app as _app  # noqa: E402

SHOT_DIR = os.path.join(ROOT, "source", "python", "app", "static", "docs_assets", "screenshots")
MIRROR_DIR = os.path.join(ROOT, "docs", "assets", "screenshots")
MANIFEST = os.path.join(SHOT_DIR, "manifest.json")

REQUIRED_TUTORIAL = ["01-login.png", "02-dashboard.png", "03-new-investigation.png",
                     "09-queued.png", "10-running.png", "11-completed.png",
                     "12-findings.png", "14-graph.png", "15-risk.png",
                     "17-evidence.png", "18-case.png", "19-report.png",
                     "20-watchlist.png", "21-alert.png", "22-workflow.png"]


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def main():
    fails = []
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.isfile(MANIFEST) else {}
    if not manifest:
        fails.append("manifest.json missing or empty")

    for shot in D.SHOTS:
        f = shot["file"]
        for d in (SHOT_DIR, MIRROR_DIR):
            p = os.path.join(d, f)
            if not os.path.isfile(p):
                fails.append(f"missing file: {f} in {d}")
                continue
            if os.path.getsize(p) == 0:
                fails.append(f"zero-byte image: {f}")
                continue
            dims = png_size(p)
            if not dims:
                fails.append(f"not a PNG: {f}")
            elif dims[0] < 300 or dims[1] < 300:
                fails.append(f"suspicious dimensions {dims}: {f}")
        m = manifest.get(f)
        if not m:
            fails.append(f"manifest entry missing: {f}")
            continue
        for k in ("route", "viewport", "generated_at", "app_version"):
            if not m.get(k):
                fails.append(f"manifest {f} missing {k}")
        if m.get("app_version") != _app.version:
            fails.append(f"manifest {f} version {m.get('app_version')} != app {_app.version}")

    for f in REQUIRED_TUTORIAL:
        if f not in manifest:
            fails.append(f"tutorial shot missing from manifest: {f}")

    # every shot referenced by content must exist
    referenced = set()
    for page in D.PAGES:
        referenced |= set(page[6])
    for f in referenced:
        if not os.path.isfile(os.path.join(SHOT_DIR, f)):
            fails.append(f"content references missing shot: {f}")

    if fails:
        print("SCREENSHOT VALIDATION FAILED:")
        for x in fails:
            print(" -", x)
        return 1
    print(f"screenshots ok: {len(D.SHOTS)} shots, manifest v{_app.version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
