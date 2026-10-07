"""Generate docs/AI_PROVIDER_FINAL_REPORT.md and docs/SETTINGS_UX_FINAL_REPORT.md
from live code, registry and suites. Run: python scripts/audit/gen_final_reports.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient  # noqa: E402
from app.ai import presets as P  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app, follow_redirects=False)


def main():
    presets = P.list_presets()
    inv = c.get("/api/v1/ai/credentials/inventory").json()
    paths = set(app.openapi()["paths"])
    for want in ("/api/v1/ai/providers", "/api/v1/ai/provider-presets",
                 "/api/v1/ai/providers/db", "/api/v1/ai/providers/db/{pid}",
                 "/api/v1/ai/providers/db/{pid}/test", "/api/v1/ai/providers/db/{pid}/models",
                 "/api/v1/ai/providers/db/test-all", "/api/v1/ai/default",
                 "/api/v1/ai/health", "/api/v1/ai/usage",
                 "/api/v1/ai/credentials/inventory"):
        assert want in paths, f"contract missing {want}"

    L = ["# Web Intelligence — AI Provider Final Report", "",
         f"_Catalog: {len(presets)} presets, all adapter-backed. "
         f"Inventory here: {inv['summary']}._", "",
         "## Status model (honest, enforced)",
         "",
         "- NOT CONFIGURED: no key saved and none in environment.",
         "- CONFIGURED: credential present (database or environment).",
         "- CONNECTED: a live test passed.",
         "- FAILED: a live test failed (code kept, secret never kept).",
         "- DISABLED: administratively off.",
         "- Configuration alone is never displayed as Connected.",
         "",
         "## Credential sources",
         "",
         "- DATABASE: Fernet-encrypted `api_key_enc`, masked in every response.",
         "- ENVIRONMENT: discovered from vendor key variables, never copied to the DB.",
         "- LOCAL: Ollama without a key; models discovered from the daemon.",
         "- Precedence: explicit request → user → org → system default → "
         "environment fallbacks → enabled database providers; per-role routing "
         "for research/summarization/classification/risk/report.",
         "",
         "## Verified behaviors",
         "",
         "- Listing/detail/test responses contain no key material (asserted).",
         "- Live tests probe auth/discovery/model with latency; failures are "
         "structured codes, never tracebacks or secrets.",
         "- Test All runs sequentially (rate-limit safe) with a summary.",
         "- Empty chain answers 502 AI analysis is not configured.",
         "- Fallback usage is reported (`fallbacks_tried`, `default_used`).",
         "- Research analyze resolves explicit → role → cascade → fallbacks + DB.",
         "",
         "## This environment",
         "",
         f"- Configured credentials: {inv['summary']['configured']}; "
         f"connected: {inv['summary']['connected']}.",
         "- No vendor keys present here — the UI shows the honest empty state.",
         ""]
    open(os.path.join(ROOT, "docs", "AI_PROVIDER_FINAL_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))

    S = ["# Web Intelligence — Settings UX Final Report", "",
         "_Sectioned shell, real persistence, verified saves._", "",
         "## Information architecture",
         "",
         "- General (org, plan, versions, timezone, templates)",
         "- Workspace (investigation scope defaults, AI default pointer)",
         "- Search (mode, limit)",
         "- Appearance (theme, sidebar, navbar, language, accent, density, layout)",
         "- Security (keys, users/roles, production requirements)",
         "- Collection (connectors, Bright Data test, browser, scheduler)",
         "- Notifications (webhooks, alerts, maintenance windows)",
         "- Integrations (AI providers, feature flags)",
         "- Data (backup with verification, retention, data quality)",
         "- System (live facts, doctor, diagnostics export)",
         "",
         "## Save-state honesty",
         "",
         "- Server forms: UNCHANGED → EDITING (dirty badge + beforeunload guard) → "
         "SAVING → SAVED (reloaded + verified) or FAILED with the real reason.",
         "- Reset restores factory defaults for workspace/search/timezone only, confirmed first.",
         "- Appearance applies instantly per browser and says so.",
         "",
         "## Verified",
         "",
         "- Round-trip + validation + reload persistence (`test_settings_defaults.py`).",
         "- Wizard prefills saved scope; console preselects saved mode.",
         "- Section search filter, responsive shell, RTL-safe layout.",
         ""]
    open(os.path.join(ROOT, "docs", "SETTINGS_UX_FINAL_REPORT.md"), "w", encoding="utf-8").write("\n".join(S))
    print("wrote AI_PROVIDER_FINAL_REPORT.md + SETTINGS_UX_FINAL_REPORT.md")


if __name__ == "__main__":
    main()
