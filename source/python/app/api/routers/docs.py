"""Docs portal routes (server-rendered, no frontend framework).

GET  /docs                    portal home (redirects to /docs/index)
GET  /docs/{path}             portal page; id/ and ar/ prefixes select language
GET  /api/v1/docs/search      local search (title, headings, body, keywords, API)
GET  /api/v1/docs/index       full search index (JSON)
GET  /api/v1/docs/sitemap     ordered sitemap (JSON)
GET  /api/v1/docs/help        contextual help: ?view=<hash> or ?view=all
GET  /api/v1/docs/coverage    per-page API coverage summary (JSON)

Subdirectory hosting: set DOCS_MOUNT=/intel (or send X-Forwarded-Prefix)
and every portal/chrome link is prefixed at render time. Content sources
stay root-relative; the engine rewrites them per request.
"""
from __future__ import annotations

import html as _html
import os as _os

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from ... import docs_data as D
from ... import docs_engine as E

router = APIRouter()

_CHROME = {
    "en": {"docs": "Documentation", "search_ph": "Search docs… (Ctrl+K)",
           "back": "Back to Application", "on_this_page": "On this page",
           "prev": "Previous", "next": "Next", "version": "version",
           "needs_translation": "Not yet translated — showing English.",
           "related_app": "Open in application", "try_it": "Try it",
           "home": "Docs home", "lang": "Language", "theme": "Theme",
           "toc_empty": "", "not_found": "Page not found",
           "not_found_body": "The documentation page you asked for does not exist.",
           "choose_path": "Choose your path", "search": "Search",
           "no_results": "No results. Try investigation, STIX, risk, graph, Redis or aaPanel."},
    "id": {"docs": "Dokumentasi", "search_ph": "Cari dokumentasi… (Ctrl+K)",
           "back": "Kembali ke Aplikasi", "on_this_page": "Di halaman ini",
           "prev": "Sebelumnya", "next": "Berikutnya", "version": "versi",
           "needs_translation": "Belum diterjemahkan — menampilkan Bahasa Inggris.",
           "related_app": "Buka di aplikasi", "try_it": "Coba",
           "home": "Beranda docs", "lang": "Bahasa", "theme": "Tema",
           "toc_empty": "", "not_found": "Halaman tidak ditemukan",
           "not_found_body": "Halaman dokumentasi yang diminta tidak ada.",
           "choose_path": "Pilih jalur Anda", "search": "Cari",
           "no_results": "Tidak ada hasil. Coba investigasi, STIX, risiko, graf, Redis atau aaPanel."},
    "ar": {"docs": "التوثيق", "search_ph": "ابحث في التوثيق… (Ctrl+K)",
           "back": "عودة إلى التطبيق", "on_this_page": "في هذه الصفحة",
           "prev": "السابق", "next": "التالي", "version": "الإصدار",
           "needs_translation": "غير مترجمة بعد — يتم عرض الإنجليزية.",
           "related_app": "افتح في التطبيق", "try_it": "جرّب",
           "home": "رئيسية التوثيق", "lang": "اللغة", "theme": "السمة",
           "toc_empty": "", "not_found": "الصفحة غير موجودة",
           "not_found_body": "صفحة التوثيق المطلوبة غير موجودة.",
           "choose_path": "اختر مسارك", "search": "بحث",
           "no_results": "لا نتائج. جرّب investigation أو STIX أو risk أو graph أو Redis أو aaPanel."},
}


def _mount(headers) -> str:
    fwd = (headers.get("x-forwarded-prefix", "") or "").rstrip("/")
    if fwd:
        return fwd
    return (_os.getenv("DOCS_MOUNT", "") or "").rstrip("/")


def _base_url(mount: str) -> str:
    dom = (_os.getenv("DOCS_BASE_URL", "") or "").rstrip("/")
    if dom:
        return dom + (mount or "")
    return (mount or "")


def _prefix_html(html_text: str, mount: str) -> str:
    if not mount:
        return html_text
    return (html_text
            .replace('href="/docs', f'href="{mount}/docs')
            .replace('src="/static', f'src="{mount}/static')
            .replace('href="/#', f'href="{mount}/#')
            .replace('href="/api-docs"', f'href="{mount}/api-docs"')
            .replace('href="/"', f'href="{mount}/"'))


def _sidebar(mount: str, lang: str, active: str) -> str:
    parts = []
    for sec in sorted(D.SECTIONS, key=lambda s: s["order"]):
        pages = D.pages_in_section(sec["code"])
        if not pages:
            continue
        parts.append(f'<div class="docs-sec">{_html.escape(sec["name"].get(lang) or sec["name"]["en"])}</div>')
        for p in pages:
            cls = " active" if p[0] == active else ""
            cur = ' aria-current="page"' if p[0] == active else ""
            parts.append(
                f'<a class="docs-link{cls}" href="{mount}/docs/{lang}/{p[0]}"{cur}>'
                f'{_html.escape(D.title_of(p, lang))}</a>')
    return "".join(parts)


def _layout(mount: str, lang: str, meta: dict, body_html: str, toc: list,
            used_lang: str, fallback: bool, active: str) -> str:
    from ...main import app as _app
    t = _CHROME[lang]
    rtl = lang == "ar"
    prev, nxt = E.prev_next(active) if active else (None, None)

    def _plink(slug):
        p = D.page_by_slug(slug)
        return (f"{mount}/docs/{lang}/{slug}", D.title_of(p, lang)) if p else (None, None)

    toc_html = "".join(
        f'<a class="docs-toc{" sub" if h["level"] == 3 else ""}" href="#{_html.escape(h["id"])}">'
        f'{_html.escape(h["text"])}</a>' for h in toc)
    if not toc_html:
        toc_html = '<span class="text-muted small">—</span>'

    prev_html = nxt_html = ""
    if prev:
        u, lt = _plink(prev)
        prev_html = (f'<a class="btn" href="{u}"><span aria-hidden="true">←</span> '
                     f'{_html.escape(lt)}</a>')
    if nxt:
        u, lt = _plink(nxt)
        nxt_html = (f'<a class="btn ms-auto" href="{u}">{_html.escape(lt)} '
                    f'<span aria-hidden="true">→</span></a>')

    fb = (f'<div class="alert alert-warning" role="note">{t["needs_translation"]}</div>'
          if fallback else "")
    canon = _base_url(mount)
    canon_tag = (f'<link rel="canonical" href="{canon}/docs/{lang}/{active}">' if canon and active else "")
    robots = ('<meta name="robots" content="noindex">' 
              if _os.getenv("ENV", "dev") != "production" and _os.getenv("DOCS_INDEX", "") != "1" else "")
    desc = meta.get("description", "")
    title = meta.get("title", "Docs")
    og_title = f"Web Intelligence — {title}"
    search_idx = "en" if lang not in ("en", "id", "ar") else lang

    return f"""<!doctype html>
<html lang="{lang}" dir="{'rtl' if rtl else 'ltr'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(og_title)}</title>
<meta name="description" content="{_html.escape(desc)}">
{canon_tag}
{robots}
<meta property="og:title" content="{_html.escape(og_title)}">
<meta property="og:description" content="{_html.escape(desc)}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='13' fill='%23206bc4'/%3E%3Ccircle cx='16' cy='16' r='5' fill='white'/%3E%3C/svg%3E">
<script>
(function(){{try{{
var t=localStorage.getItem('wi-theme')||'light';
var eff=t==='system'?((window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light'):t;
document.documentElement.setAttribute('data-bs-theme',eff);
}}catch(e){{document.documentElement.setAttribute('data-bs-theme','light');}}}})();
</script>
<link href="{mount}/static/vendor/tabler/tabler.min.css" rel="stylesheet">
<style>
.skip-link{{position:absolute;inset-inline-start:-9999px;top:0;background:#fff;padding:.5rem 1rem;z-index:3000}}
.skip-link:focus{{inset-inline-start:0}}
.docs-wrap{{display:flex;min-height:100vh}}
.docs-side{{width:17rem;flex:none;border-inline-end:1px solid var(--tblr-border-color);padding:1rem .75rem;position:sticky;top:0;height:100vh;overflow:auto}}
.docs-main{{flex:1;min-width:0}}
.docs-body{{display:flex;gap:1.5rem;align-items:flex-start}}
.docs-content{{flex:1;min-width:0}}
.docs-tocwrap{{width:13rem;flex:none;position:sticky;top:1rem}}
.docs-sec{{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--tblr-muted);padding:.9rem .6rem .25rem}}
.docs-link{{display:block;padding:.3rem .6rem;border-radius:.4rem;color:var(--tblr-muted);text-decoration:none;font-size:.86rem}}
.docs-link:hover{{background:var(--tblr-border-color);color:inherit}}
.docs-link.active{{background:var(--tblr-primary-lt,var(--tblr-border-color));color:inherit;font-weight:600}}
.docs-toc{{display:block;padding:.2rem .5rem;font-size:.82rem;color:var(--tblr-muted);text-decoration:none}}
.docs-toc.sub{{padding-inline-start:1.2rem;font-size:.78rem}}
.docs-toc:hover{{color:inherit}}
pre{{background:#0d1117;color:#e6edf3;padding:.8rem 1rem;border-radius:.6rem;white-space:pre;overflow-x:auto;font-size:.82rem;position:relative}}
[data-bs-theme="light"] pre{{background:#0d1117;color:#e6edf3}}
.code-copy{{position:absolute;top:.4rem;inset-inline-end:.4rem}}
figure.shot{{margin:1rem 0;border:1px solid var(--tblr-border-color);border-radius:.6rem;overflow:hidden}}
figure.shot .shot-img{{background:var(--tblr-bg-surface-secondary);max-height:560px;overflow:auto}}
figure.shot img{{width:100%;height:auto;display:block}}
figure.shot figcaption{{padding:.5rem .8rem;font-size:.82rem;color:var(--tblr-muted);border-top:1px solid var(--tblr-border-color)}}
blockquote{{border-inline-start:3px solid var(--tblr-primary);padding:.4rem .8rem;background:var(--tblr-bg-surface-secondary);border-radius:.3rem}}
.breadcrumb{{background:none;padding:0;margin-bottom:.5rem}}
.search-results{{position:absolute;top:100%;inset-inline-start:0;inset-inline-end:0;z-index:1200;max-height:60vh;overflow:auto}}
@media(max-width:991px){{.docs-side{{display:none;position:fixed;inset-inline-start:0;top:0;bottom:0;z-index:1045;width:290px;background:var(--tblr-bg-surface);box-shadow:0 0 2rem rgba(0,0,0,.4)}}.docs-side.open{{display:block}}.docs-tocwrap{{display:none}}}}
:focus-visible{{outline:2px solid var(--tblr-primary);outline-offset:2px}}
</style>
</head>
<body>
<a class="skip-link" href="#docs-content">Skip to content</a>
<header class="navbar navbar-expand-md border-bottom sticky-top" style="background:var(--tblr-bg-surface)">
<div class="container-xl">
<button class="btn btn-icon d-lg-none" id="docs-navbtn" aria-label="Open navigation">☰</button>
<a class="navbar-brand mb-0" href="{mount}/docs/{lang}/index"><strong>WEB INTELLIGENCE</strong></a>
<span class="text-muted small d-none d-md-inline">{_html.escape(t["docs"])}</span>
<div class="ms-auto d-flex gap-2 align-items-center position-relative" role="search">
<div class="input-group input-group-sm" style="min-width:200px;max-width:320px">
<input id="docs-q" class="form-control" placeholder="{_html.escape(t["search_ph"])}" aria-label="Documentation search" autocomplete="off">
<span class="input-group-text d-none d-md-inline"><span class="kbd">Ctrl K</span></span>
</div>
<div id="docs-results" class="search-results card" style="display:none"><div class="card-body p-2" id="docs-results-body"></div></div>
<select id="docs-lang" class="form-select form-select-sm" style="width:auto" aria-label="{_html.escape(t["lang"])}">
<option value="en"{' selected' if lang=='en' else ''}>English</option>
<option value="id"{' selected' if lang=='id' else ''}>Indonesia</option>
<option value="ar"{' selected' if lang=='ar' else ''}>العربية</option>
</select>
<button class="btn btn-icon btn-sm" id="docs-theme" aria-label="{_html.escape(t["theme"])}">◐</button>
<a class="btn btn-sm btn-primary d-none d-md-inline-block" href="{mount}/">{_html.escape(t["back"])}</a>
</div>
</div>
</header>
<div class="container-xl py-3"><div class="docs-wrap" style="min-height:auto">
<aside class="docs-side" id="docs-side" aria-label="Documentation navigation">{_sidebar(mount, lang, active)}</aside>
<main class="docs-main px-lg-3" id="docs-content" tabindex="-1"><div class="docs-body">
<article class="docs-content">
<nav class="breadcrumb text-muted small" aria-label="Breadcrumb"><a href="{mount}/docs/{lang}/index">{_html.escape(t["home"])}</a> &rsaquo; {_html.escape(meta.get("category",""))} &rsaquo; <strong>{_html.escape(title)}</strong></nav>
<h1>{_html.escape(title)}</h1>
<p class="text-muted">{_html.escape(desc)}</p>
{fb}
{_prefix_html(body_html, mount)}
<hr>
<div class="d-flex gap-2 flex-wrap my-3" role="navigation" aria-label="Previous and next">{prev_html}{nxt_html}</div>
<div class="text-muted small">Web Intelligence v{_html.escape(_app.version)} · {_html.escape(t["version"])} · <a href="{mount}/">{_html.escape(t["back"])}</a> · <a href="{mount}/api-docs" target="_blank" rel="noopener">API</a></div>
</article>
<nav class="docs-tocwrap d-none d-lg-block" aria-label="{_html.escape(t["on_this_page"])}"><div class="text-muted small mb-1">{_html.escape(t["on_this_page"])}</div>{toc_html}</nav>
</div></main>
</div></div>
<script src="{mount}/static/docs.js" data-mount="{mount}" data-lang="{search_idx}" data-active="{_html.escape(active or 'index')}" data-empty="{_html.escape(t["no_results"])}"></script>
</body>
</html>"""


def _serve(slug: str, lang: str, headers) -> HTMLResponse:
    lang = lang if lang in _CHROME else "en"
    mount = _mount(headers)
    try:
        meta, html_text, toc, used, fallback = E.load_page(slug, lang)
    except KeyError:
        t = _CHROME[lang]
        page = _layout(mount, lang,
                       {"title": t["not_found"], "description": "", "category": ""},
                       f"<p>{_html.escape(t['not_found_body'])}</p>", [], "en",
                       False, "")
        return HTMLResponse(page, status_code=404)
    page = _layout(mount, lang, meta, html_text, toc, used, fallback, slug)
    return HTMLResponse(page)


@router.get("/docs", include_in_schema=False)
def docs_root(request: Request):
    mount = _mount(request.headers)
    return RedirectResponse(f"{mount}/docs/en/index", status_code=302)


@router.get("/docs/index", include_in_schema=False)
def docs_index(request: Request):
    mount = _mount(request.headers)
    return RedirectResponse(f"{mount}/docs/en/index", status_code=302)


def _split(path: str):
    parts = (path or "").strip("/").split("/")
    if parts and parts[0] in ("en", "id", "ar"):
        lang = parts[0]
        slug = "/".join(parts[1:]) or "index"
    else:
        lang, slug = "en", "/".join(parts) or "index"
    return lang, slug


@router.get("/docs/{doc_path:path}", include_in_schema=False)
def docs_page(doc_path: str, request: Request):
    lang, slug = _split(doc_path)
    return _serve(slug, lang, request.headers)


@router.get("/api/v1/docs/search")
def docs_search(q: str = Query(""), lang: str = Query("en")):
    lang = lang if lang in ("en", "id", "ar") else "en"
    t = _CHROME[lang]
    return {"query": q, "lang": lang, "results": E.search(q, lang),
            "empty": t["no_results"]}


@router.get("/api/v1/docs/index")
def docs_index_json(lang: str = Query("en")):
    lang = lang if lang in ("en", "id", "ar") else "en"
    return {"lang": lang, "pages": E.search_index(lang)}


@router.get("/api/v1/docs/sitemap")
def docs_sitemap():
    return {"pages": E.sitemap(), "sections": D.SECTIONS}


@router.get("/api/v1/docs/help")
def docs_help(view: str = Query("")):
    if view == "all":
        return {"map": D.VIEW_DOCS}
    slug = D.VIEW_DOCS.get(view or "")
    if not slug:
        return {"view": view, "slug": None, "url": None}
    p = D.page_by_slug(slug)
    return {"view": view, "slug": slug, "url": f"/docs/{slug}",
            "title": D.title_of(p, "en") if p else slug}


@router.get("/api/v1/docs/coverage")
def docs_coverage():
    from ...main import app as _app
    paths = _app.openapi().get("paths", {})
    rows = []
    for page in D.PAGES:
        matched = []
        for pre in D.api_prefixes(page):
            for p in paths:
                if p == pre or p.startswith(pre.rstrip("/") + "/") or p.startswith(pre + "/"):
                    matched.append(p)
        rows.append({"slug": page[0], "title": page[8], "endpoints": sorted(set(matched)),
                     "screenshots": page[6]})
    return {"paths": len(paths), "pages": rows}
