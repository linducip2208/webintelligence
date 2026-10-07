"""Docs portal engine: Markdown loading, safe rendering, TOC, search index.

- Sources: app/docs_content/<lang>/<slug>.md with YAML-ish frontmatter.
  Falls back to English with a notice when a translation is missing.
- Rendering: `markdown` lib (fenced code, tables, toc) + allowlist sanitizer
  (stdlib html.parser — no extra dependencies, no script injection,
  no path traversal: only registry slugs resolve).
- Screenshot figures: `![alt](shot:<file>)` becomes a lazy <figure> with
  caption from docs_data.SHOTS and dimensions from the manifest when present.
- Internal links `/docs/<slug>` and `/#<view>` are validated by tests.
"""
from __future__ import annotations

import html as _html
import json as _json
import os as _os
import re as _re
from html.parser import HTMLParser

from . import docs_data as D

CONTENT_DIR = _os.path.join(_os.path.dirname(__file__), "docs_content")
SHOT_URL = "/static/docs_assets/screenshots"
LANGS = ("en", "id", "ar")
RTL = {"ar"}

ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "caption", "code", "col", "colgroup",
    "dd", "details", "div", "dl", "dt", "em", "figcaption", "figure",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "kbd", "li",
    "ol", "p", "pre", "small", "span", "strong", "sub", "summary", "sup",
    "table", "tbody", "td", "th", "thead", "tr", "ul",
}
ALLOWED_ATTRS = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "loading", "width", "height"},
    "code": {"class"},
    "pre": {"class"},
    "span": {"class", "id"},
    "div": {"class", "id"},
    "td": {"colspan", "rowspan"}, "th": {"colspan", "rowspan"},
    "ol": {"start"}, "ul": {"class"},
    "h1": {"id"}, "h2": {"id"}, "h3": {"id"}, "h4": {"id"},
    "details": {"open"}, "table": {"class"},
}
VOID = {"br", "hr", "img", "col"}


def _safe_href(v: str) -> str | None:
    v = (v or "").strip()
    if v.startswith(("https://", "http://", "mailto:")):
        return v
    if v.startswith(("/docs", "/static", "/api-docs", "/#", "#", "/")):
        return v
    return None


def _safe_src(v: str) -> str | None:
    v = (v or "").strip()
    if v.startswith(SHOT_URL + "/") or v.startswith("/static/"):
        return v
    return None


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "script" or tag == "style" or tag not in ALLOWED_TAGS:
            self.out.append("")
            return
        kept = []
        allowed = ALLOWED_ATTRS.get(tag, set())
        for k, v in attrs:
            k = k.lower()
            if k not in allowed:
                continue
            if k == "href":
                v2 = _safe_href(v)
                if v2 is None:
                    continue
                v = v2
            elif k == "src":
                v2 = _safe_src(v)
                if v2 is None:
                    continue
                v = v2
            elif k == "target" and v != "_blank":
                continue
            kept.append(f'{k}="{_html.escape(v, quote=True)}"')
        extra = ""
        if tag == "a" and any(k == 'target="_blank"' for k in kept):
            extra = ' rel="noopener"'
        if tag in VOID:
            self.out.append(f"<{tag}{' ' + ' '.join(kept) if kept else ''}>")
        else:
            self.out.append(f"<{tag}{' ' + ' '.join(kept) if kept else ''}{extra}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ALLOWED_TAGS and tag not in VOID and tag not in ("script", "style"):
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        self.out.append(_html.escape(data))

    def result(self):
        return "".join(self.out)


def sanitize(html_text: str) -> str:
    p = _Sanitizer()
    p.feed(html_text or "")
    return p.result()


def parse_frontmatter(text: str):
    meta: dict = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            raw = text[3:end].strip()
            body = text[end + 4:].lstrip("\n")
            for line in raw.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
    return meta, body


def _manifest():
    path = _os.path.join(_os.path.dirname(__file__), "static",
                         "docs_assets", "screenshots", "manifest.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return _json.load(fh)
    except Exception:
        return {}


def _shot_figure(match, counter):
    alt, fname = match.group(1), match.group(2).strip()
    if "/" in fname or ".." in fname:
        return _html.escape(match.group(0))
    meta = next((s for s in D.SHOTS if s["file"] == fname), None)
    title = meta["title"] if meta else fname
    caption = meta["desc"] if meta and meta.get("desc") else alt
    counter[0] += 1
    dims = ""
    man = _manifest().get(fname)
    if isinstance(man, dict) and man.get("width") and man.get("height"):
        dims = f' width="{int(man["width"])}" height="{int(man["height"])}"'
    img = (f'<img src="{SHOT_URL}/{_html.escape(fname)}" '
           f'alt="{_html.escape(caption)}" loading="lazy"{dims}>')
    return (f"<figure class=\"shot\"><div class=\"shot-img\">{img}</div>"
            f"<figcaption>Figure {counter[0]} — {_html.escape(title)}. "
            f"{_html.escape(caption)}</figcaption></figure>")


SHOT_RE = _re.compile(r"!\[([^\]]*)\]\(shot:([^)]+)\)")


def render_markdown(md_text: str) -> tuple[str, list[dict]]:
    """Returns (safe_html, toc[{level,id,text}])."""
    import markdown as _md
    counter = [0]

    def _rep(m):
        return _shot_figure(m, counter)

    pre = SHOT_RE.sub(_rep, md_text)
    html_text = _md.markdown(pre, extensions=["fenced_code", "tables", "toc",
                                             "sane_lists"])
    safe = sanitize(html_text)
    toc = [{"level": int(m.group(1)), "id": m.group(2), "text": _html.unescape(m.group(3))}
           for m in _re.finditer(r"<h([23]) id=\"([^\"]+)\">(.+?)</h\1>", safe)]
    # strip any nested tags inside toc text
    for t in toc:
        t["text"] = _re.sub(r"<[^>]+>", "", t["text"])
    return safe, toc


def load_page(slug: str, lang: str = "en"):
    """(meta, html, toc, used_lang, fallback). Raises KeyError for unknown slug."""
    page = D.page_by_slug(slug)
    if page is None:
        raise KeyError(slug)
    lang = lang if lang in LANGS else "en"
    path = _os.path.join(CONTENT_DIR, lang, slug + ".md")
    used = lang
    fallback = False
    if not _os.path.isfile(path):
        path = _os.path.join(CONTENT_DIR, "en", slug + ".md")
        used = "en"
        fallback = lang != "en"
    with open(path, encoding="utf-8") as fh:
        meta, body = parse_frontmatter(fh.read())
    # The portal layout renders the title + description itself; drop the
    # leading "# Title" and "> description" duplicates from the body so
    # pages (and their TOCs) do not repeat the heading.
    body = _re.sub(r"^#[^\n]*\n(?:\s*\n)?", "", body, count=1)
    body = _re.sub(r"^>[^\n]*\n(?:\s*\n)?", "", body, count=1)
    html_text, toc = render_markdown(body)
    return {"slug": slug, "title": D.title_of(page, used),
            "description": meta.get("description") or D.desc_of(page, used),
            "section": page[1], "category": D.section_name(page[1], used),
            "order": page[3], "shots": page[6]}, html_text, toc, used, fallback


def _strip(html_text: str) -> str:
    t = _re.sub(r"<[^>]+>", " ", html_text or "")
    return _re.sub(r"\s+", " ", _html.unescape(t)).strip()


_search_cache: dict = {}


def search_index(lang: str = "en"):
    if lang in _search_cache:
        return _search_cache[lang]
    items = []
    for page in D.PAGES:
        try:
            meta, html_text, _toc, used, _fb = load_page(page[0], lang)
        except Exception:
            continue
        items.append({
            "slug": page[0],
            "title": D.title_of(page, lang),
            "section": D.section_name(page[1], lang),
            "description": meta.get("description") or "",
            "keywords": " ".join(page[7] or []),
            "api": " ".join(D.api_prefixes(page)),
            "body": _strip(html_text)[:6000],
            "fallback": used != lang,
        })
    _search_cache[lang] = items
    return items


def search(query: str, lang: str = "en", limit: int = 12):
    q = (query or "").strip().lower()
    if not q:
        return []
    terms = [t for t in _re.split(r"\s+", q) if t]
    scored = []
    for it in search_index(lang if lang in LANGS else "en"):
        score = 0
        hay_title = it["title"].lower()
        hay_sec = it["section"].lower()
        hay_kw = it["keywords"].lower()
        hay_api = it["api"].lower()
        hay_body = it["body"].lower()
        for t in terms:
            if t in hay_title:
                score += 10
            if t in hay_sec:
                score += 4
            if t in hay_kw:
                score += 6
            if t in hay_api:
                score += 5
            if t in hay_body:
                score += 1
        if score:
            idx = hay_body.find(terms[0])
            excerpt = it["body"][max(0, idx - 60):idx + 160] if idx >= 0 else it["body"][:180]
            scored.append((score, it, excerpt))
    scored.sort(key=lambda x: -x[0])
    return [{"slug": it["slug"], "title": it["title"], "section": it["section"],
             "excerpt": ex.strip(), "category": it["section"]}
            for score, it, ex in scored[:limit]]


def sitemap():
    out = []
    for sec in sorted(D.SECTIONS, key=lambda s: s["order"]):
        for page in D.pages_in_section(sec["code"]):
            out.append({"slug": page[0], "section": sec["code"],
                        "section_title": sec["name"]["en"],
                        "title": D.title_of(page, "en"),
                        "order": page[3]})
    return out


def prev_next(slug: str):
    flat = [e["slug"] for e in sitemap()]
    if slug not in flat:
        return None, None
    i = flat.index(slug)
    prev = flat[i - 1] if i > 0 else None
    nxt = flat[i + 1] if i < len(flat) - 1 else None
    return prev, nxt
