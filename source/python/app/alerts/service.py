import json, urllib.request
RULES = ("price_changed","new_product","unavailable","competitor_change","site_change","new_article","anomaly","collection_failure","quality_degradation")
def build(rule, message, project_id=0, channel="inapp"):
    assert rule in RULES, rule
    return {"rule": rule, "message": message, "channel": channel, "project_id": project_id}
def send_webhook(url, payload, timeout=10):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return r.status
