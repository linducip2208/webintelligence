"""Docs portal tests: routing, rendering, i18n/RTL, search, help, coverage.

Uses the hermetic in-memory backend from conftest. No network, no browser.
"""
import os
import re

from fastapi.testclient import TestClient

import app as _app_pkg
from app import docs_data as D
from app.main import app

APP_DIR = os.path.dirname(os.path.abspath(_app_pkg.__file__))

c = TestClient(app, follow_redirects=False)


def test_docs_root_redirects():
    r = c.get("/docs")
    assert r.status_code == 302
    assert r.headers["location"].endswith("/docs/en/index")


def test_docs_home():
    r = c.get("/docs/en/index")
    assert r.status_code == 200
    t = r.text
    assert "first-investigation" in t
    assert "2.14.0" in t
    assert "/static/vendor/tabler/tabler.min.css" in t
    assert "/static/docs.js" in t
    for cdn in ("cdn.jsdelivr", "unpkg", "googleapis"):
        assert cdn not in t


def test_docs_ar_rtl_and_fallback():
    r = c.get("/docs/ar/security/ssrf")
    assert r.status_code == 200
    assert 'dir="rtl"' in r.text
    # untranslated page falls back with an honest notice
    assert "غير مترجمة" in r.text or "translated" in r.text


def test_docs_translated_pages_have_no_fallback():
    r = c.get("/docs/id/getting-started/first-investigation")
    assert r.status_code == 200
    assert "Langkah 1" in r.text
    assert "alert-warning" not in r.text
    r = c.get("/docs/ar/getting-started/first-investigation")
    assert r.status_code == 200
    assert "الخطوة 1" in r.text


def test_docs_missing_is_404():
    assert c.get("/docs/en/no-such-page").status_code == 404


def test_docs_search_shape_and_queries():
    r = c.get("/api/v1/docs/search", params={"q": "stix", "lang": "en"})
    d = r.json()
    assert d["results"], "expected stix results"
    for item in d["results"]:
        assert set(item) >= {"slug", "title", "section", "excerpt", "category"}
    for lang, q in (("id", "Redis"), ("ar", "risk"), ("en", "aaPanel"),
                    ("en", "investigation")):
        r = c.get("/api/v1/docs/search", params={"q": q, "lang": lang})
        assert r.json()["results"], f"no results for {q} ({lang})"
    r = c.get("/api/v1/docs/search", params={"q": "xyznonexistent", "lang": "en"})
    assert r.json()["results"] == []


def test_docs_help_map():
    r = c.get("/api/v1/docs/help", params={"view": "graph"})
    assert r.json()["slug"] == "intelligence/graph"
    r = c.get("/api/v1/docs/help", params={"view": "all"})
    assert len(r.json()["map"]) > 40
    # every mapped view resolves to a real page
    slugs = {p[0] for p in D.PAGES} | {"index"}
    for view, slug in r.json()["map"].items():
        assert slug in slugs, f"VIEW_DOCS {view} -> {slug}"


def test_docs_sitemap_count():
    r = c.get("/api/v1/docs/sitemap")
    assert len(r.json()["pages"]) == len(D.PAGES)


def test_docs_api_coverage_full():
    cov = c.get("/api/v1/docs/coverage").json()
    allp = set()
    for row in cov["pages"]:
        allp |= set(row["endpoints"])
    missing = [p for p in app.openapi()["paths"] if p not in allp]
    assert not missing, f"undocumented: {missing[:5]}"


def test_all_pages_render_all_langs():
    bad = []
    for p in D.PAGES:
        for lang in ("en", "id", "ar"):
            rr = c.get(f"/docs/{lang}/{p[0]}")
            if rr.status_code != 200:
                bad.append(f"{lang}/{p[0]}:{rr.status_code}")
    assert not bad, str(bad[:5])


def test_no_dead_docs_links_in_rendered_html():
    slugs = {p[0] for p in D.PAGES}
    views = set(D.VIEW_DOCS)
    src = open(os.path.join(APP_DIR, "static", "js", "views.js"), encoding="utf-8").read()
    m = re.search(r"VIEW_TITLE=\{([^}]+)\}", src)
    if m:
        views |= set(re.findall(r"'([\w-]+)':", m.group(1)))
    dead = []
    for p in D.PAGES:
        html = c.get(f"/docs/en/{p[0]}").text
        for slug in re.findall(r'href="/docs/([a-z0-9\-/]+)"', html):
            parts = slug.split("/")
            if parts and parts[0] in ("en", "id", "ar"):
                slug = "/".join(parts[1:])
            if slug in ("", "index"):
                continue
            if slug not in slugs:
                dead.append(f"{p[0]} -> /docs/{slug}")
        for view in re.findall(r'href="/#([a-z0-9\-/]+)"', html):
            if view.split("/")[0] not in views:
                dead.append(f"{p[0]} -> /#{view}")
    assert not dead, str(dead[:5])


def test_screenshots_referenced_exist():
    d = os.path.join(APP_DIR, "static", "docs_assets", "screenshots")
    missing = [f for p in D.PAGES for f in p[6]
               if not os.path.isfile(os.path.join(d, f))]
    assert not missing, str(missing[:5])
    assert os.path.isfile(os.path.join(d, "manifest.json"))
