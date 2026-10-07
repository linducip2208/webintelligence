"""Validate docs links, content quality and API consistency. Run from repo root:

    python scripts/docs/validate.py

- every /docs/<slug> link resolves to the registry
- every /#<view> app link is a real frontend view
- every (shot:<file>) exists in SHOTS and on disk
- no duplicate slugs, no banned content tokens, no secrets
- every OpenAPI path is covered by docs; every doc prefix matches something
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import docs_data as D  # noqa: E402
from app import docs_engine as E  # noqa: E402
from app.main import app as _app  # noqa: E402

CONTENT = os.path.join(ROOT, "source", "python", "app", "docs_content")
SHOT_DIR = os.path.join(ROOT, "source", "python", "app", "static", "docs_assets", "screenshots")

BANNED = ["TODO", "FIXME", "lorem ipsum", "coming soon", "TBD:", "password123",
          "secret123", "example-token", "changeme-token"]
SECRET_RES = [r"sk-[A-Za-z0-9]{8,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{8,}",
              r"xox[bap]-[A-Za-z0-9-]{8,}", r"wi_[A-Za-z0-9]{8,}"]

DOCS_LINK = re.compile(r"\]\(/docs/([a-z0-9\-/]+)\)")
APP_LINK = re.compile(r"\]\(/#([a-z0-9\-/]+)\)")
SHOT_LINK = re.compile(r"!\[.*?\]\(shot:([^)]+)\)")


def frontend_views():
    views = set(D.VIEW_DOCS)
    src = open(os.path.join(ROOT, "source", "python", "app", "static", "js", "views.js"),
               encoding="utf-8").read()
    for m in re.finditer(r"VIEW_TITLE=\{([^}]+)\}", src):
        for k in re.finditer(r"'([\w-]+)':", m.group(1)):
            views.add(k.group(1))
    return views


def main():
    fails = []
    slugs = [p[0] for p in D.PAGES]
    if len(slugs) != len(set(slugs)):
        fails.append("duplicate slugs in registry")
    by_slug = set(slugs)
    views = frontend_views()

    for bad_view, slug in D.VIEW_DOCS.items():
        if slug not in by_slug and slug != "index":
            fails.append(f"VIEW_DOCS {bad_view} -> unknown slug {slug}")

    md_files = []
    for root, _d, files in os.walk(CONTENT):
        for f in files:
            if f.endswith(".md"):
                md_files.append(os.path.join(root, f))
    if not md_files:
        fails.append("no markdown content found")

    for path in md_files:
        rel = os.path.relpath(path, CONTENT)
        text = open(path, encoding="utf-8").read()
        for token in BANNED:
            if token.lower() in text.lower():
                fails.append(f"{rel}: banned token {token!r}")
        for pat in SECRET_RES:
            if re.search(pat, text):
                fails.append(f"{rel}: possible secret matching {pat}")
        for slug in DOCS_LINK.findall(text):
            parts = slug.split("/")
            if parts and parts[0] in ("en", "id", "ar"):
                slug = "/".join(parts[1:])
            if slug in ("", "index"):
                continue
            if slug not in by_slug:
                fails.append(f"{rel}: dead docs link /docs/{slug}")
        for view in APP_LINK.findall(text):
            base = view.split("/")[0]
            if base not in views:
                fails.append(f"{rel}: dead app link /#{view}")
        for shot in SHOT_LINK.findall(text):
            if shot.strip() not in {s["file"] for s in D.SHOTS}:
                fails.append(f"{rel}: unknown shot {shot}")
            elif not os.path.isfile(os.path.join(SHOT_DIR, shot.strip())):
                fails.append(f"{rel}: shot file missing on disk: {shot}")

    # API consistency both directions
    spec_paths = set(_app.openapi().get("paths", {}))
    covered = set()
    for page in D.PAGES:
        matched = set()
        for pre in D.api_prefixes(page):
            for p in spec_paths:
                if p == pre or p.startswith(pre.rstrip("/") + "/") or p.startswith(pre + "/"):
                    matched.add(p)
        if D.api_prefixes(page) and not matched:
            fails.append(f"{page[0]}: api prefixes match nothing")
        covered |= matched
    for p in sorted(spec_paths - covered):
        fails.append(f"implemented but undocumented: {p}")

    if fails:
        print("DOCS VALIDATION FAILED:")
        for x in fails[:60]:
            print(" -", x)
        if len(fails) > 60:
            print(f" ... and {len(fails) - 60} more")
        return 1
    print(f"docs validation ok: {len(md_files)} md files, {len(spec_paths)} api paths covered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
