"""Extended functionality audit: hardcoded IDs, fake-success candidates,
console-only actions, TODOs in product code, duplicate routes/presets,
stale hardcoded numbers in generated docs.

Run: python scripts/audit/functionality_audit.py
Exit 1 on hard failures; candidates are printed for review.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP = os.path.join(ROOT, "source", "python", "app")

HARD_ID = re.compile(r"\b(project_id|org_id|user_id|investigation_id|projectId|orgId|userId)\b\s*[:=]\s*1(?![0-9])")
HARD_ID_CMP = re.compile(r"\b(project_id|org_id)\b\s*==\s*1(?![0-9])")


def files(suffixes, skip=()):
    for root, dirs, fs in os.walk(APP):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in fs:
            if f.endswith(suffixes) and "vendor" not in root and "tabler" not in root:
                p = os.path.join(root, f)
                if any(s in p for s in skip):
                    continue
                yield p


def main():
    fails, notes = [], []

    # 1. hardcoded production IDs in product code
    for p in files((".py",)):
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        rel = os.path.relpath(p, ROOT)
        func = ""
        for i, line in enumerate(text.splitlines(), 1):
            m = re.match(r"\s*def (\w+)", line)
            if m:
                func = m.group(1)
            s = line.strip()
            if s.startswith(("#", '"""', "'''")) or "test" in rel.lower():
                continue
            if HARD_ID.search(line) or HARD_ID_CMP.search(line):
                # allowed: .get("org", 1) legacy-row defaults and function defaults
                if re.search(r"\.get\(\s*[\"'](org|project_id)[\"']\s*,\s*1\s*\)", line):
                    continue
                if re.search(r"def \w+\(.*=\s*1\b", line):
                    continue
                # allowed: prose documenting the no-magic-id rule, bootstrap seeds
                if re.search(r"[Nn]o .*fallback|never|bootstrap|seed", line + func):
                    continue
                if "seed" in func or "bootstrap" in func:
                    continue
                fails.append(f"{rel}:{i}: hardcoded id? {s[:100]}")

    # 2. console-only actions in shipped JS
    for p in files((".js",)):
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        rel = os.path.relpath(p, ROOT)
        for i, line in enumerate(text.splitlines(), 1):
            if "console.log" in line or "console.debug" in line:
                fails.append(f"{rel}:{i}: console-only action")

    # 3. TODO/FIXME in product code
    for p in files((".py", ".js")):
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        rel = os.path.relpath(p, ROOT)
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line):
                fails.append(f"{rel}:{i}: {line.strip()[:100]}")

    # 4. success-toast candidates for manual honesty review (reported, not failed)
    js = open(os.path.join(APP, "static", "js", "views.js"), encoding="utf-8").read()
    for m in re.finditer(r"toast\((`[^`]*`|'[^']*')\)", js):
        s = m.group(1)
        if re.search(r"success|complet|done", s, re.I):
            notes.append("toast: " + s[:110])

    # 5. duplicate preset ids / duplicate NAV views
    sys.path.insert(0, os.path.join(ROOT, "source", "python"))
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app.ai import presets as _pr
    ids = [p["id"] for p in _pr.list_presets()]
    if len(ids) != len(set(ids)):
        fails.append("duplicate preset ids")
    nav = re.findall(r"\[\['([^']+)','([\w-]+)','[\w]+'\]", js)
    seen = {}
    for label, view in nav:
        seen.setdefault(view, []).append(label)
    dupes = {v: l for v, l in seen.items() if len(set(l)) > 1}
    if dupes:
        fails.append(f"same view under different labels: {dupes}")

    # 6. stale hardcoded numbers in generated docs content
    sys.path.insert(0, os.path.join(ROOT, "source", "python"))
    from app.main import app as _app
    n_paths = len(_app.openapi()["paths"])
    content_dir = os.path.join(APP, "docs_content", "en")
    for root, _d, fs in os.walk(content_dir):
        for f in fs:
            if not f.endswith(".md"):
                continue
            text = open(os.path.join(root, f), encoding="utf-8").read()
            for m in re.finditer(r"(\d{3}) (?:versioned paths|paths? (?:under|reference|documented))", text):
                if int(m.group(1)) != n_paths:
                    fails.append(f"docs/{f}: stale count {m.group(1)} (live: {n_paths})")

    if fails:
        print("FUNCTIONALITY AUDIT FAILED:")
        for x in fails[:40]:
            print(" -", x)
        return 1
    print(f"functionality audit ok ({len(notes)} toast candidates reviewed separately)")
    for n in sorted(set(notes))[:20]:
        print("   candidate:", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
