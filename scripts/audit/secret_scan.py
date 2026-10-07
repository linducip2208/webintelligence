"""Secret scanner: fail on real-secret patterns, allow documented placeholders.

Run: python scripts/audit/secret_scan.py [--strict]
- Scans tracked source (app, scripts, tests, docs content, contracts).
- Placeholders (YOUR_API_KEY, <API_KEY>, ${...}, example.com values,
  sk-test-*, *abcd-style masked tails) never fail the build.
- --strict also scans git history (slow); default scans the working tree.
Exit 1 on any probable real secret.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PATTERNS = [
    (r"sk-[A-Za-z0-9]{12,}", "openai-like key"),
    (r"AIza[0-9A-Za-z_-]{20,}", "google key"),
    (r"xai-[A-Za-z0-9_-]{10,}", "xai key"),
    (r"gsk_[A-Za-z0-9]{10,}", "groq key"),
    (r"sk-ant-[A-Za-z0-9_-]{10,}", "anthropic key"),
    (r"ghp_[A-Za-z0-9]{10,}|github_pat_[A-Za-z0-9_]{10,}", "github token"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "private key"),
    (r"Bearer [A-Za-z0-9_~.=-]{16,}", "bearer token"),
    (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}['\"]", "password assignment"),
]

ALLOW = re.compile(r"YOUR_API_KEY|YOUR_PASSWORD|<API_KEY>|\$\{|example\.com|test|fake|dummy|redacted|abcd|1234|xxxx| C?HANGE", re.I)
# exact well-known non-secrets (dev defaults, test fixtures) — never real keys
DUMMY_VALUES = {"pw123", "admin123", "password123", "secret123", "changeme",
                "test123", "K" * 16, "SECRET-INV-9999", "SECRET",
                "sk-test-only-fake-1234abcd".lower(), "bogus", "topsecret"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", "venv",
             ".venv", "vendor", "tabler", ".agents"}
SKIP_FILES = {"secret_scan.py", "package-lock.json"}
ALLOW_EXT = {".py", ".js", ".html", ".md", ".json", ".yaml", ".yml", ".toml",
             ".ini", ".env", ".example", ".sh", ".ps1", ".go", ".mod", ".txt"}


def scan_tree():
    hits = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in SKIP_FILES or os.path.splitext(f)[1] not in ALLOW_EXT:
                continue
            p = os.path.join(root, f)
            try:
                text = open(p, encoding="utf-8", errors="strict").read()
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                s = line.strip()
                if not s or s.startswith(("#", "//", "*", "<!--")) and "example" in s.lower():
                    pass
                for pat, label in PATTERNS:
                    for m in re.finditer(pat, line):
                        frag = m.group(0)
                        context = line[max(0, m.start() - 60):m.end() + 60]
                        if ALLOW.search(context) or ALLOW.search(frag):
                            continue
                        # masked tails (••••abcd) are intentional disclosure
                        if "•" in context:
                            continue
                        if label == "password assignment":
                            vm = re.search(r"['\"]([^'\"]+)['\"]\s*$", frag)
                            val = (vm.group(1) if vm else "")
                            if (val in DUMMY_VALUES or len(val) < 8
                                    or "password" in val.lower()):
                                continue
                        hits.append(f"{os.path.relpath(p, ROOT)}:{i}: {label}: {frag[:24]}…")
    return hits


def scan_history():
    try:
        proc = subprocess.run(["git", "log", "-p", "--all", "-S", "sk-",
                               "--pickaxe-regex", "--", "."],
                              capture_output=True, cwd=ROOT, timeout=180)
        out = proc.stdout.decode("utf-8", errors="replace")
    except Exception:
        return ["(history scan unavailable)"]
    hits = []
    for line in out.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            for pat, label in PATTERNS[:7]:
                m = re.search(pat, line[1:])
                if m and not ALLOW.search(line):
                    hits.append(f"history: {label}: {m.group(0)[:24]}…")
                    break
    return hits


def main():
    hits = scan_tree()
    if "--strict" in sys.argv:
        hits += scan_history()
    # never print full secrets — labels + truncated fragments only
    if hits:
        print("SECRET SCAN FAILED:")
        for h in hits[:30]:
            print(" -", h)
        return 1
    print("secret scan clean (placeholders allowed"
          + (", history scanned" if "--strict" in sys.argv else "") + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
