"""Commercial entitlements: plans with server-side enforced quotas.
No billing provider; architecture supports attaching one later.
Plans are data (PLANS), enforcement is real, defaults are generous for dev.
"""
import time

PLANS = {
    "starter": {"max_projects": 3, "max_targets": 25, "max_jobs_per_day": 500,
                "max_ai_tokens": 100000, "max_connectors": 5,
                "browser_allowed": False, "retention_days": 30,
                "allowed_models": ["gpt-4o-mini", "muse-spark-1.3", "llama3.1"]},
    "pro": {"max_projects": 25, "max_targets": 500, "max_jobs_per_day": 10000,
            "max_ai_tokens": 5000000, "max_connectors": 50,
            "browser_allowed": True, "retention_days": 365,
            "allowed_models": ["gpt-4o-mini", "gpt-4o", "muse-spark-1.3",
                               "claude-3-5-haiku-latest", "gemini-2.0-flash", "llama3.1"]},
    "enterprise": {"max_projects": 10 ** 9, "max_targets": 10 ** 9,
                   "max_jobs_per_day": 10 ** 9, "max_ai_tokens": 10 ** 9,
                   "max_connectors": 10 ** 9, "browser_allowed": True,
                   "retention_days": 3650, "allowed_models": ["*"]},
}


def plan_for(org: dict):
    return PLANS.get((org or {}).get("plan", "starter"), PLANS["starter"])


def _today():
    return time.strftime("%Y-%m-%d", time.gmtime())


def check(store: dict, org_id: int, resource: str, amount: int = 1):
    """Returns (ok, detail). Enforced before create/collect/AI actions."""
    org = next((o for o in store.get("orgs", []) if o.get("id") == org_id),
               {"plan": "starter"})
    lim = plan_for(org)
    if resource == "projects":
        used = sum(1 for p in store.get("projects", []) if p.get("org", 1) == org_id)
        if used + amount > lim["max_projects"]:
            return False, f"plan {org.get('plan', 'starter')}: max_projects={lim['max_projects']}"
    elif resource == "targets":
        used = sum(1 for t in store.get("targets", []) if t.get("org", 1) == org_id)
        if used + amount > lim["max_targets"]:
            return False, f"plan {org.get('plan', 'starter')}: max_targets={lim['max_targets']}"
    elif resource == "jobs":
        day = _today()
        used = sum(1 for j in store.get("jobs", [])
                   if j.get("org", 1) == org_id and
                   time.strftime("%Y-%m-%d", time.gmtime(j.get("created_at", 0))) == day)
        if used + amount > lim["max_jobs_per_day"]:
            return False, f"plan {org.get('plan', 'starter')}: max_jobs_per_day={lim['max_jobs_per_day']}"
    elif resource == "ai_tokens":
        used = sum(i.get("input_tokens", 0) + i.get("output_tokens", 0)
                   for i in store.get("ai_usage", []) if i.get("org", 1) == org_id)
        if used + amount > lim["max_ai_tokens"]:
            return False, f"plan {org.get('plan', 'starter')}: max_ai_tokens={lim['max_ai_tokens']}"
    elif resource == "connectors":
        used = sum(1 for c in store.get("connectors", []) if c.get("org", 1) == org_id)
        if used + amount > lim["max_connectors"]:
            return False, f"plan {org.get('plan', 'starter')}: max_connectors={lim['max_connectors']}"
    elif resource == "browser":
        if not lim["browser_allowed"]:
            return False, f"plan {org.get('plan', 'starter')}: browser not included"
    return True, "ok"


def usage(store: dict, org_id: int):
    org = next((o for o in store.get("orgs", []) if o.get("id") == org_id),
               {"plan": "starter"})
    lim = plan_for(org)
    ai = sum(i.get("input_tokens", 0) + i.get("output_tokens", 0)
             for i in store.get("ai_usage", []) if i.get("org", 1) == org_id)
    return {"plan": org.get("plan", "starter"), "limits": lim,
            "used": {
                "projects": sum(1 for p in store.get("projects", []) if p.get("org", 1) == org_id),
                "targets": sum(1 for t in store.get("targets", []) if t.get("org", 1) == org_id),
                "jobs_today": sum(1 for j in store.get("jobs", [])
                                  if j.get("org", 1) == org_id and
                                  time.strftime("%Y-%m-%d", time.gmtime(j.get("created_at", 0))) == _today()),
                "ai_tokens": ai,
                "connectors": sum(1 for c in store.get("connectors", []) if c.get("org", 1) == org_id)}}
