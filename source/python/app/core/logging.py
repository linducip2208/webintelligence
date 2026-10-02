import json, sys, datetime
def log(event, **kw):
    rec = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "event": event, **kw}
    sys.stdout.write(json.dumps(rec, default=str) + "\n")
