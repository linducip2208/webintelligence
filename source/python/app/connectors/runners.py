"""Real connector executors: RSS / REST (paginated) / CSV.
Each execution returns normalized items + provenance, never invented data.
stdlib only (urllib + xml + csv)."""
import csv as _csv
import io as _io
import json as _j
import os as _o
import time as _t
import urllib.request as _u
import xml.etree.ElementTree as _ET


def _trust():
    return [x.strip() for x in _o.getenv("TRUSTED_EGRESS_CIDRS", "").split(",") if x.strip()]


try:  # package context: app.connectors.runners
    from ..core.ssrf import validate_url as _validate_url
except ImportError:  # flat test context: connectors on sys.path
    from core.ssrf import validate_url as _validate_url


def _guard(url):
    _validate_url(url, _trust() or None)


def _fetch(url, timeout=20, headers=None):
    req = _u.Request(url, headers={"User-Agent": "Mozilla/5.0 WebIntel/1.0",
                                   **(headers or {})})
    with _u.urlopen(req, timeout=timeout) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read(5_000_000)


def rss_collect(config: dict):
    """Fetch RSS/ATOM feed -> items with title/link/published/summary."""
    url = config.get("url", "")
    if not url:
        return {"ok": False, "error": "missing url"}
    try:
        _guard(url)
    except Exception as e:
        return {"ok": False, "error": f"ssrf-blocked: {e}"}
    try:
        status, ctype, body = _fetch(url)
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    try:
        root = _ET.fromstring(body)
    except Exception as e:
        return {"ok": False, "error": f"xml parse: {e}"[:200]}
    items = []
    for it in list(root.iter("item"))[:100] + list(root.iter("{http://www.w3.org/2005/Atom}entry"))[:100]:
        def txt(names):
            for n in names:
                el = it.find(n)
                if el is None:
                    el = it.find("{http://www.w3.org/2005/Atom}" + n.strip("{}"))
                if el is not None and el.text:
                    return el.text.strip()
            return ""
        link = txt(["link"])
        if not link:
            le = it.find("link")
            if le is not None:
                link = (le.get("href") or "").strip()
        items.append({"title": txt(["title"]), "url": link,
                      "published": txt(["pubDate", "published", "updated"]),
                      "summary": txt(["description", "summary"])[:1000]})
    return {"ok": True, "http_status": status, "items": items,
            "retrieved_at": _t.time()}


def rest_collect(config: dict):
    """Paginated REST JSON: follows next-page links or ?page=N up to max_pages."""
    url = config.get("url", "")
    if not url:
        return {"ok": False, "error": "missing url"}
    try:
        _guard(url)
    except Exception as e:
        return {"ok": False, "error": f"ssrf-blocked: {e}"}
    data_path = config.get("data_path", "")
    next_path = config.get("next_path", "")
    max_pages = min(int(config.get("max_pages", 3) or 3), 20)
    items, seen_pages, next_url = [], 0, url
    try:
        while next_url and seen_pages < max_pages:
            _, _, body = _fetch(next_url)
            try:
                doc = _j.loads(body.decode("utf-8", "ignore"))
            except Exception as e:
                return {"ok": False, "error": f"json parse: {e}"[:200], "items": items}
            node = doc
            for part in (data_path.split(".") if data_path else []):
                node = node.get(part, {}) if isinstance(node, dict) else {}
            page_items = node if isinstance(node, list) else node.get("items", [])
            items += page_items[:500]
            seen_pages += 1
            next_url = None
            if next_path:
                n = doc
                for part in next_path.split("."):
                    n = n.get(part, {}) if isinstance(n, dict) else {}
                next_url = n if isinstance(n, str) else None
            elif seen_pages < max_pages and "page=" in url:
                import re as _re
                next_url = _re.sub(r"page=\d+", f"page={seen_pages + 1}", url)
        return {"ok": True, "items": items[:2000], "pages": seen_pages,
                "retrieved_at": _t.time()}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200], "items": items}


def csv_collect(config: dict):
    """Parse inline CSV text (or URL) -> rows with detected delimiter."""
    text = config.get("text", "")
    if config.get("url") and not text:
        try:
            _guard(config["url"])
            _, _, body = _fetch(config["url"])
            text = body.decode("utf-8", "ignore")
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
    if not text:
        return {"ok": False, "error": "missing text/url"}
    try:
        dialect = _csv.Sniffer().sniff(text[:5000], delimiters=[",", ";", "\t", "|"])
    except Exception:
        dialect = _csv.excel
    try:
        rows = list(_csv.DictReader(_io.StringIO(text), dialect=dialect))[:10000]
    except Exception as e:
        return {"ok": False, "error": f"csv parse: {e}"[:200]}
    return {"ok": True, "items": rows, "columns": list(rows[0].keys()) if rows else [],
            "retrieved_at": _t.time()}


EXECUTORS = {"rss": rss_collect, "rest": rest_collect, "csv": csv_collect}


CATEGORY_EXECUTOR = {"NEWS": "rss", "API": "rest", "DOCUMENT": "csv",
                     "WEB": "rss", "CUSTOM": ""}


def execute(connector: dict):
    cfg = connector.get("config", {}) or {}
    manifest = connector.get("manifest", {}) or {}
    kind = (cfg.get("kind") or manifest.get("executor") or
            CATEGORY_EXECUTOR.get(connector.get("category", ""), ""))
    fn = EXECUTORS.get((kind or "").lower())
    if not fn:
        return {"ok": False,
                "error": f"no executor (set config.kind=rss|rest|csv for category {connector.get('category')})"}
    return fn(cfg)
