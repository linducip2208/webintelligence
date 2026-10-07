"""Portal verification via TestClient (no external server needed)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app, follow_redirects=False)
fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name, extra)
    if not cond:
        fails.append(name)


r = c.get("/docs")
check("docs root redirects", r.status_code == 302 and r.headers["location"].endswith("/docs/en/index"), str(r.status_code))

r = c.get("/docs/en/index")
check("docs home 200", r.status_code == 200, str(r.status_code))
t = r.text
check("home hero", "Start Your First Investigation" in t or "first-investigation" in t)
check("home version", "2.14.0" in t)
check("tabler local", "/static/vendor/tabler/tabler.min.css" in t)
check("no cdn", "cdn.jsdelivr" not in t and "unpkg" not in t and "googleapis" not in t)
check("docs.js local", "/static/docs.js" in t)

r = c.get("/docs/ar/security/ssrf")
check("ar page 200", r.status_code == 200, str(r.status_code))
check("ar rtl", 'dir="rtl"' in r.text)
check("ar fallback notice", "غير مترجمة" in r.text or "translated" in r.text)

r = c.get("/docs/id/getting-started/first-investigation")
check("id tutorial translated", "Langkah 1" in r.text and "alert-warning" not in r.text)
r = c.get("/docs/ar/getting-started/first-investigation")
check("ar tutorial translated", "الخطوة 1" in r.text and "alert-warning" not in r.text)
r = c.get("/docs/id/intelligence/risk")
check("id untranslated falls back", "Belum diterjemahkan" in r.text)

r = c.get("/docs/en/nope")
check("missing page 404", r.status_code == 404, str(r.status_code))

r = c.get("/api/v1/docs/search", params={"q": "stix", "lang": "en"})
d = r.json()
check("search stix", len(d["results"]) > 0, str([x["slug"] for x in d["results"][:3]]))
check("search shape", all(set(x) >= {"slug", "title", "section", "excerpt", "category"} for x in d["results"]))

for lang, q in (("id", "Redis"), ("ar", "risk"), ("en", "aaPanel"), ("en", "investigation")):
    r = c.get("/api/v1/docs/search", params={"q": q, "lang": lang})
    check(f"search {q} ({lang})", len(r.json()["results"]) > 0)

r = c.get("/api/v1/docs/search", params={"q": "xyznonexistent", "lang": "en"})
check("search empty", r.json()["results"] == [])

r = c.get("/api/v1/docs/help", params={"view": "graph"})
check("help graph", r.json().get("slug") == "intelligence/graph", r.text[:120])
r = c.get("/api/v1/docs/help", params={"view": "all"})
check("help all", len(r.json().get("map", {})) > 40)

r = c.get("/api/v1/docs/sitemap")
pages = r.json()["pages"]
from app import docs_data as D
check("sitemap count", len(pages) == len(D.PAGES), f"{len(pages)}/{len(D.PAGES)}")

r = c.get("/api/v1/docs/coverage")
cov = r.json()
allp = set()
for row in cov["pages"]:
    allp |= set(row["endpoints"])
spec = app.openapi()["paths"]
missing = [p for p in spec if p not in allp]
check("api coverage full", not missing, str(missing[:5]))

r = c.get("/api/v1/docs/index", params={"lang": "ar"})
check("index ar", len(r.json()["pages"]) == len(D.PAGES))

# every docs page renders 200 in all three langs
bad = []
for p in D.PAGES:
    for lang in ("en", "id", "ar"):
        rr = c.get(f"/docs/{lang}/{p[0]}")
        if rr.status_code != 200:
            bad.append(f"{lang}/{p[0]}:{rr.status_code}")
check("all pages render x3", not bad, str(bad[:5]) + (f" (+{len(bad)-5})" if len(bad) > 5 else ""))

print()
print("FAILURES:", fails if fails else "none")
sys.exit(1 if fails else 0)
