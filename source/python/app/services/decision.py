"""CollectionDecisionEngine — stdlib only."""
STRATEGIES = ("DIRECT_HTTP", "OFFICIAL_API", "BROWSER", "OWN_PROXY", "BRIGHT_DATA")
class Policy:
    def __init__(self, allow_browser=True, allow_proxy=True, allow_brightdata=False,
                 max_cost_per_job=1.0, geo=None, require_js=False):
        self.allow_browser = allow_browser; self.allow_proxy = allow_proxy
        self.allow_brightdata = allow_brightdata
        self.max_cost_per_job = max_cost_per_job; self.geo = geo; self.require_js = require_js
class Engine:
    def decide(self, target: dict, policy: Policy, providers: dict):
        """providers: {own_proxy: {healthy,cost}, brightdata:{healthy,cost,configured}}"""
        plan, reasons = [], []
        hist = target.get("success_by_strategy", {})
        def ok(name): return providers.get(name, {}).get("healthy", True)
        # 1 direct/api
        if target.get("has_official_api"): plan.append("OFFICIAL_API"); reasons.append("official api available")
        else: plan.append("DIRECT_HTTP"); reasons.append("default: cheapest first")
        if policy.require_js or target.get("needs_js"):
            if policy.allow_browser: plan.append("BROWSER"); reasons.append("js/render required")
        # proxy escalation on signals
        sig = target.get("last_signals", {})
        if sig.get("rate_limited") or sig.get("blocked"):
            if policy.allow_proxy and ok("own_proxy"): plan.append("OWN_PROXY"); reasons.append("rate-limit/block → own proxy")
            if policy.allow_brightdata and providers.get("brightdata", {}).get("configured") and ok("brightdata"):
                plan.append("BRIGHT_DATA"); reasons.append("escalation: brightdata justified")
        if policy.geo and policy.allow_proxy and "OWN_PROXY" not in plan and ok("own_proxy"):
            plan.append("OWN_PROXY"); reasons.append("geo requirement")
        # learn: move historically-best strategy earlier (after first)
        best = max(hist, key=hist.get) if hist else None
        if best in STRATEGIES and best not in plan: plan.append(best); reasons.append(f"history best={best}")
        return {"plan": plan, "reasons": reasons}
def validate_result(http_status, content_type, size, expected_fields, parsed_ok, completeness):
    """HTTP 200 != success. Returns (ok, diagnostics dict)."""
    d = {}
    if http_status != 200: d["http"] = f"status {http_status}"
    if size <= 0: d["empty"] = True
    if size > 10_000_000: d["oversize"] = True
    if content_type and not any(t in content_type for t in ("html", "json", "xml", "text")):
        d["content_type"] = content_type
    if not parsed_ok: d["parse"] = "parser failed"
    if completeness is not None and completeness < 0.5: d["incomplete"] = completeness
    if expected_fields and completeness == 0: d["missing_fields"] = expected_fields
    return (len(d) == 0, d)
