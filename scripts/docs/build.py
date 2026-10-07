"""Build docs reports + mirrors. Run from repo root:

    python scripts/docs/build.py

Outputs:
  docs/SITEMAP.md                every documentation page (generated)
  docs/API_COVERAGE.md           documented / implemented / missing (generated)
  docs/DOCUMENTATION_COVERAGE.md feature x docs x screenshot x E2E (generated)
  docs/assets/screenshots/       mirror of served screenshots
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import docs_data as D  # noqa: E402
from app.main import app as _app  # noqa: E402

SHOT_DIR = os.path.join(ROOT, "source", "python", "app", "static", "docs_assets", "screenshots")
MIRROR_DIR = os.path.join(ROOT, "docs", "assets", "screenshots")


def e2e_hits():
    """Map view keyword -> True when any root e2e test references it."""
    e2e_dir = os.path.join(ROOT, "tests", "e2e")
    blob = ""
    if os.path.isdir(e2e_dir):
        for f in os.listdir(e2e_dir):
            if f.endswith(".py"):
                try:
                    blob += open(os.path.join(e2e_dir, f), encoding="utf-8").read().lower()
                except Exception:
                    pass
    return blob


def build_sitemap():
    lines = ["# Web Intelligence — Documentation Sitemap", "",
             f"_Generated from the application registry (v{_app.version}). "
             "Every row is a live `/docs` page._", ""]
    for sec in sorted(D.SECTIONS, key=lambda s: s["order"]):
        pages = D.pages_in_section(sec["code"])
        if not pages:
            continue
        lines.append(f"## {sec['name']['en']}")
        lines.append("")
        for p in pages:
            lines.append(f"- [{D.title_of(p, 'en')}](/docs/{p[0]}) — {p[11]}")
        lines.append("")
    return "\n".join(lines)


def coverage_rows():
    spec_paths = _app.openapi().get("paths", {})
    rows = []
    for page in D.PAGES:
        matched = set()
        for pre in D.api_prefixes(page):
            for p in spec_paths:
                if p == pre or p.startswith(pre.rstrip("/") + "/") or p.startswith(pre + "/"):
                    matched.add(p)
        rows.append((page, sorted(matched)))
    return spec_paths, rows


def build_api_coverage():
    spec_paths, rows = coverage_rows()
    covered = set()
    for _p, m in rows:
        covered |= set(m)
    missing = sorted(set(spec_paths) - covered)
    lines = ["# Web Intelligence — API Coverage", "",
             f"_Application v{_app.version}: {len(spec_paths)} implemented paths, "
             f"{len(covered)} documented, {len(missing)} missing documentation._", "",
             "## Implemented but undocumented", ""]
    lines.append("(none — 100% of implemented paths are referenced by documentation)"
                 if not missing else "\n".join(f"- `{p}`" for p in missing))
    lines += ["", "## Documented endpoints per page", ""]
    for page, matched in rows:
        if not matched:
            continue
        lines.append(f"### {page[0]} — {len(matched)} endpoint(s)")
        lines.append("")
        for p in matched:
            lines.append(f"- `{p}`")
        lines.append("")
    return "\n".join(lines)


def build_doc_coverage():
    _spec, rows = coverage_rows()
    blob = e2e_hits()
    manifest = {}
    man_path = os.path.join(SHOT_DIR, "manifest.json")
    if os.path.isfile(man_path):
        try:
            manifest = json.load(open(man_path, encoding="utf-8"))
        except Exception:
            manifest = {}
    lines = ["# Web Intelligence — Documentation Coverage", "",
             "_Feature matrix: documentation page, real screenshot, E2E reference._", "",
             "| Feature | Docs | Screenshot | E2E |",
             "|---|---|---|---|"]
    for page, matched in rows:
        slug = page[0]
        docs = f"YES `/docs/{slug}`"
        shots = ", ".join(f"`{s}`" for s in page[6]) if page[6] else "—"
        if page[6] and not all(s in manifest for s in page[6]):
            shots += " (PENDING regeneration)"
        keys = {slug.split("/")[-1].replace("-", ""), (page[4] or "").replace("-", "")}
        e2e = "YES" if any(k and k in blob for k in keys) else "NO"
        lines.append(f"| {D.title_of(page, 'en')} | {docs} | {shots} | {e2e} |")
    return "\n".join(lines)


def main():
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    with open(os.path.join(ROOT, "docs", "SITEMAP.md"), "w", encoding="utf-8") as fh:
        fh.write(build_sitemap())
    with open(os.path.join(ROOT, "docs", "API_COVERAGE.md"), "w", encoding="utf-8") as fh:
        fh.write(build_api_coverage())
    with open(os.path.join(ROOT, "docs", "DOCUMENTATION_COVERAGE.md"), "w", encoding="utf-8") as fh:
        fh.write(build_doc_coverage())
    os.makedirs(MIRROR_DIR, exist_ok=True)
    if os.path.isdir(SHOT_DIR):
        for f in os.listdir(SHOT_DIR):
            if f.endswith(".png") or f == "manifest.json":
                shutil.copy2(os.path.join(SHOT_DIR, f), os.path.join(MIRROR_DIR, f))
    print("built docs/SITEMAP.md, docs/API_COVERAGE.md, docs/DOCUMENTATION_COVERAGE.md")


if __name__ == "__main__":
    main()
