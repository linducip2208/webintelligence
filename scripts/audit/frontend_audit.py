"""Frontend<->backend static audit (also runnable as pytest).

Extracts from app/static:
  - onclick/onsubmit/oninput/onchange="fn(" handler references
  - api('p') / post/put/del('p') + fetch("p") API calls (+ method)
  - go('view'[, id]) navigation targets
and verifies:
  - every handler is defined (function decl or window assignment)
  - every API call matches an OpenAPI path+method (query stripped, {params} ok)
  - every go() target is a real view (VIEW_TITLE or alias)

Run: python scripts/audit/frontend_audit.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.main import app  # noqa: E402

STATIC = os.path.join(ROOT, "source", "python", "app", "static")
HANDLER_ATTRS = ("onclick", "onsubmit", "oninput", "onchange", "onkeydown", "onkeyup")

# identifiers that are not JS functions (object paths handled separately)
DEFINED_OK = {"event"}
BUILTINS = {"String", "Number", "Boolean", "Array", "Object", "JSON", "Math",
            "Date", "Promise", "confirm", "prompt", "alert", "setTimeout",
            "setInterval", "clearTimeout", "clearInterval", "fetch",
            "encodeURIComponent", "decodeURIComponent", "parseInt",
            "parseFloat", "isNaN", "URL", "Blob", "FormData", "console"}


def js_sources():
    out = {}
    for name in ("js/app.js", "js/views.js", "js/viewdocs.js", "index.html", "docs.js"):
        p = os.path.join(STATIC, name)
        if os.path.isfile(p):
            out[name] = open(p, encoding="utf-8").read()
    return out


def defined_functions(src):
    fns = set(re.findall(r"(?:^|[;\s{}])function\s+([A-Za-z_$][\w$]*)", src))
    fns |= set(re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=", src))
    fns |= set(re.findall(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(", src))
    fns |= set(re.findall(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", src))
    return fns


def handler_refs(src):
    refs = []
    for attr in HANDLER_ATTRS:
        for m in re.finditer(attr + r"\s*=\s*\"([^\"]+)\"", src):
            code = m.group(1)
            for fn in re.finditer(r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(", code):
                if fn.group(1) in ("if", "for", "while", "switch", "catch", "function"):
                    continue
                refs.append((attr, fn.group(1)))
    return refs


def api_calls(src):
    calls = []
    for m in re.finditer(r"\b(api|post|put|del)\(\s*['\"`]([^'\"`]+)['\"`]", src):
        method = {"api": "GET", "post": "POST", "put": "PUT", "del": "DELETE"}[m.group(1)]
        calls.append((method, m.group(2)))
    for m in re.finditer(r"\bapi\(\s*`([^`]+)`", src):
        calls.append(("GET", m.group(1)))
    for m in re.finditer(r"\bfetch\(\s*['\"`]([^'\"`]+)['\"`]", src):
        u = m.group(1)
        if u.startswith("/api/"):
            tail = src[m.end():m.end() + 80]
            mm = re.search(r"""method\s*:\s*['"]([A-Z]+)['"]""", tail)
            calls.append((mm.group(1) if mm else "GET?", u))
    return calls


def go_targets(src):
    return re.findall(r"\bgo\(\s*['\"]([\w-]+)['\"]", src)


def match_path(method, raw, paths):
    url = raw.split("?")[0].split("#")[0]
    if "${" in url or "`" in url or "+" in url:
        return True, "dynamic"  # built at runtime; checked by E2E instead
    if url.endswith("/") and len(url) > 1:
        return True, "dynamic-prefix"  # string prefix before a concatenated id
    if not url.startswith("/api/"):
        return True, "non-api"
    if url in paths:
        ops = paths[url]
        if method == "GET?":
            return ("get" in ops, "ok(fetch)" if "get" in ops else f"GET not allowed on {url}")
        return (method.lower() in ops,
                "ok" if method.lower() in ops else f"method {method} not allowed on {url}")
    cands = []
    for pattern, ops in paths.items():
        if "{" not in pattern:
            continue
        rx = "^" + re.sub(r"\{[^}]+\}", r"[^/]+", pattern) + "$"
        if re.match(rx, url):
            cands.append((pattern.count("{"), pattern, ops))
    cands.sort()
    if cands:
        _n, pattern, ops = cands[0]
        if method == "GET?":
            return True, "ok(fetch)"
        if method.lower() in ops:
            return True, "ok"
        return False, f"method {method} not allowed on {pattern}"
    return False, f"no route {url}"


def main():
    srcs = js_sources()
    all_src = "\n".join(srcs.values())
    defined = set()
    for s in srcs.values():
        defined |= defined_functions(s)
    defined |= DEFINED_OK | BUILTINS

    spec = app.openapi()["paths"]
    opmap = {p: set(v) for p, v in ((k, set(v)) for k, v in spec.items())}

    fails = []

    for name, src in srcs.items():
        for attr, fn in handler_refs(src):
            base = fn
            if base not in defined and f"window.{base}" not in all_src:
                # allow method-style this.x / object handlers resolved at runtime
                if not re.search(rf"(this|window)\.{re.escape(base)}\s*=", all_src):
                    fails.append(f"{name}: {attr} calls undefined {fn}()")

    for name, src in srcs.items():
        for method, url in api_calls(src):
            if "${" in url or url.startswith(("http", "/static", "/docs", "/api-docs")):
                continue
            ok, why = match_path(method, url, opmap)
            if not ok:
                fails.append(f"{name}: {method} {url} -> {why}")

    views_js = srcs.get("js/views.js", "")
    known = set(re.findall(r"'([\w-]+)':", re.search(r"VIEW_TITLE=\{([^}]+)\}", views_js).group(1)))
    known |= set(re.findall(r"'([\w-]+)':", re.search(r"VIEW_ALIAS=\{([^}]+)\}", views_js).group(1)))
    for name, src in srcs.items():
        for v in go_targets(src):
            if v not in known:
                fails.append(f"{name}: go('{v}') unknown view")

    if fails:
        print("FRONTEND AUDIT FAILED:")
        for x in sorted(set(fails))[:50]:
            print(" -", x)
        return 1
    print(f"frontend audit ok: {len(defined)} functions, "
          f"{sum(len(api_calls(s)) for s in srcs.values())} api calls checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
