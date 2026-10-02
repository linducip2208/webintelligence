"""Alert storm guard: dedupe + cooldown + grouping — stdlib."""
import time
def should_fire(rule_key: str, history: dict, cooldown_s=3600, now=None):
    now = now or time.time()
    last = history.get(rule_key, 0)
    if now - last < cooldown_s: return False
    history[rule_key] = now
    return True
def group(alerts: list):
    groups = {}
    for a in alerts: groups.setdefault(a.get("rule"), []).append(a)
    return [{"rule": k, "count": len(v), "sample": v[0].get("message", "")[:200]} for k, v in groups.items()]
