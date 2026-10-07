"""Generate docs/AI_PROVIDER_AUDIT.md from the live preset catalog and the
configured-provider API shape. Never includes key material: only counts,
statuses, capabilities and discovery behavior. Run from repo root:

    python scripts/audit/gen_ai_audit.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "source", "python"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient  # noqa: E402
from app.ai import presets as P  # noqa: E402
from app.ai.factory import build_provider  # noqa: E402
from app.main import app  # noqa: E402

c = TestClient(app, follow_redirects=False)


def main():
    presets = P.list_presets()
    lines = ["# Web Intelligence — AI Provider Audit", "",
             "_Catalog vs configured vs tested. No keys, no secrets — only metadata._", "",
             "## Catalog (backend presets, all adapter-backed)", "",
             "| Preset | Protocol | Key | Local | Discovery | Default model | Capabilities |",
             "|---|---|---|---|---|---|---|"]
    for p in presets:
        try:
            build_provider(p["protocol"], p["default_endpoint"] or "https://example.com/v1",
                           "probe", p["default_model"] or "probe-model")
            adapter = "YES"
        except Exception as e:
            adapter = f"NO ({e})"[:60]
        lines.append(f"| {p['id']} | {p['protocol']} | "
                     f"{'required' if p['key_required'] else 'optional'} | "
                     f"{'yes' if p['local'] else 'no'} | "
                     f"{'yes' if p['discovery'] else 'manual'} | "
                     f"{p['default_model'] or '—'} | {', '.join(p['capabilities'])} |")
        if adapter != "YES":
            lines.append(f"  - ADAPTER BUILD FAILED: {adapter}")
    lines += ["", "## Configured providers (live shape, this environment)", ""]
    db = c.get("/api/v1/ai/providers/db").json().get("items", [])
    lines.append(f"Configured right now: **{len(db)}** (fresh test database).")
    lines.append("")
    for p in db:
        leak = "api_key_enc" in p
        lines.append(f"- {p.get('name')}: configured={p.get('configured')} "
                     f"enabled={p.get('enabled')} key={p.get('masked_key', '') or 'none'} "
                     f"last={p.get('last_test_status')} key-material-leak={leak}")
    lines += ["", "## Behaviors verified by tests (`test_ai_registry.py`)", "",
              "- Listing/detail/test responses never contain `api_key_enc` or raw keys.",
              "- Live test against an unreachable endpoint returns structured "
              "PROVIDER_UNAVAILABLE with latency, never a traceback or secret.",
              "- Failed tests persist status/latency/error + discovered models only.",
              "- Defaults cascade (user → org → system) validates providers and models.",
              "- Empty chain answers `AI analysis is not configured` (HTTP 502).",
              "", "## Production use",
              "- Set defaults from any provider card (Set as default) or POST /api/v1/ai/default.",
              "- Test All runs sequentially to respect vendor rate limits.",
              "- Ollama models are discovered live from the local daemon.",
              "- Research/ask accept explicit provider+model or use the cascade.",
              ""]
    open(os.path.join(ROOT, "docs", "AI_PROVIDER_AUDIT.md"), "w", encoding="utf-8").write("\n".join(lines))
    print(f"ai provider audit: {len(presets)} presets, {len(db)} configured here")


if __name__ == "__main__":
    main()
