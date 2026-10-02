"""UI gate: dashboard JS must parse (node --check when available) and the
index must reference only real API paths. Skips node check if absent."""
import io
import os
import re
import shutil
import subprocess

HTML = r"D:\project laravel\webintelligence\source\python\app\static\index.html"


def test_js_parses():
    s = io.open(HTML, encoding="utf-8").read()
    m = re.search(r"<script>(.*)</script>", s, re.S)
    assert m, "no script block"
    if not shutil.which("node"):
        return
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(m.group(1))
        path = f.name
    try:
        r = subprocess.run(["node", "--check", path], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stderr[:2000]
    finally:
        os.unlink(path)


def test_ui_calls_real_paths():
    import json as _j
    s = io.open(HTML, encoding="utf-8").read()
    used = set(re.findall(r"'(/api/v1/[a-z_/{}]+)", s))
    spec = _j.load(open(r"D:\project laravel\webintelligence\contracts\openapi\openapi.json"))
    documented = set()
    for p in spec["paths"]:
        documented.add(p.split("{")[0].rstrip("/"))
    for u in used:
        base = u.split("{")[0].rstrip("/")
        assert any(base == d or d.startswith(base) or base.startswith(d) for d in documented), u
