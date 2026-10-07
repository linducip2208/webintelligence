"""Frontend<->backend static audit gate: no dead handlers, no dead API calls,
no dead routes. Fails the build on any break."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "..", "..", "scripts", "audit"))

import frontend_audit as FA


def test_handlers_defined():
    srcs = FA.js_sources()
    defined = set()
    for s in srcs.values():
        defined |= FA.defined_functions(s)
    defined |= FA.DEFINED_OK | FA.BUILTINS
    all_src = "\n".join(srcs.values())
    missing = set()
    for name, src in srcs.items():
        for attr, fn in FA.handler_refs(src):
            if fn not in defined and f"window.{fn}" not in all_src:
                import re
                if not re.search(rf"(this|window)\.{re.escape(fn)}\s*=", all_src):
                    missing.add(f"{name}: {attr} -> {fn}()")
    assert not missing, sorted(missing)[:10]


def test_api_calls_match_routes():
    from app.main import app
    srcs = FA.js_sources()
    spec = app.openapi()["paths"]
    opmap = {p: set(v) for p, v in ((k, set(v)) for k, v in spec.items())}
    bad = set()
    for name, src in srcs.items():
        for method, url in FA.api_calls(src):
            if "${" in url or url.startswith(("http", "/static", "/docs", "/api-docs")):
                continue
            ok, why = FA.match_path(method, url, opmap)
            if not ok:
                bad.add(f"{name}: {method} {url} -> {why}")
    assert not bad, sorted(bad)[:10]


def test_go_targets_are_views():
    import re
    srcs = FA.js_sources()
    views_js = srcs["js/views.js"]
    known = set(re.findall(r"'([\w-]+)':", re.search(r"VIEW_TITLE=\{([^}]+)\}", views_js).group(1)))
    known |= set(re.findall(r"'([\w-]+)':", re.search(r"VIEW_ALIAS=\{([^}]+)\}", views_js).group(1)))
    bad = set()
    for name, src in srcs.items():
        for v in FA.go_targets(src):
            if v not in known:
                bad.add(f"{name}: go('{v}')")
    assert not bad, sorted(bad)[:10]
