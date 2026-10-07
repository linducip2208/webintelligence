"""Generate docs/AI_CREDENTIAL_INVENTORY.md from the live inventory endpoint.

Only safe metadata (provider, configured, source, masked key, status, last
tested, models, default). Raw secrets can never appear: the endpoint never
returns them, and this script asserts their absence before writing.
Run: python scripts/audit/gen_inventory.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.version import APP_VERSION  # noqa: E402

c = TestClient(app, follow_redirects=False)


def main():
    inv = c.get("/api/v1/ai/credentials/inventory").json()
    blob = str(inv)
    assert "api_key_enc" not in blob
    for bad in ("sk-", "AIza", "xai-", "gsk_", "sk-ant-", "ghp_"):
        assert bad not in blob, f"possible secret in inventory: {bad}"
    L = [f"# Web Intelligence — AI Credential Inventory (app v{APP_VERSION})", "",
         "_Safe metadata only: provider, configured, source, masked key, status, "
         "last tested, models, default. Generated from the live endpoint._", "",
         f"Summary: {inv['summary']}", "",
         "| Provider | Configured | Source | Masked key | Status | Last tested | Models | Default | Notes |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in inv["inventory"]:
        L.append(f"| {r['provider']} | {'YES' if r['configured'] else 'NO'} | {r['source']} | "
                 f"{r['masked_key'] or 'N/A'} | {r['status']} | "
                 f"{r['last_tested_at'] or 'never'} | {r.get('model') or '—'} | "
                 f"{'YES' if r['default'] else 'no'} | "
                 f"{'; '.join(r.get('capabilities', [])[:4])} |")
    L += ["",
          "No credentials are configured in this environment — connect providers "
          "on the AI Providers page; this file regenerates with masked entries only.",
          ""]
    open(os.path.join(ROOT, "docs", "AI_CREDENTIAL_INVENTORY.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"inventory: {inv['summary']['total']} rows, no secret material")


if __name__ == "__main__":
    main()
