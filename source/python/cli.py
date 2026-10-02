#!/usr/bin/env python3
"""webintel CLI: operate the platform from a terminal.

Usage: python cli.py [--api URL] [--token T] <command> [args]
Commands: health, doctor, jobs, job STATUS|RETRY|cancel, research, report,
          migrate, backup, version
"""
import argparse
import json
import os
import sys
import urllib.request

API = os.getenv("API_BASE", "http://127.0.0.1:8000")
TOKEN = os.getenv("API_TOKEN", "")


def call(method, path, payload=None):
    data = json.dumps(payload or {}).encode() if payload is not None or method == "POST" else None
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode() or "{}"
            return r.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def cmd_health(_):
    s, b = call("GET", "/healthz")
    print(s, b)
    return s == 200


def cmd_doctor(_):
    s, b = call("GET", "/api/v1/system/doctor")
    print(json.dumps(b, indent=1)[:3000])
    return s == 200 and b.get("healthy", False)


def cmd_jobs(a):
    s, b = call("GET", f"/api/v1/jobs?size={a.size}&status={a.status}")
    for j in b.get("items", []):
        print(j.get("job_id", "")[:8], j.get("status"), j.get("strategy"), j.get("url", "")[:60])
    print("total:", b.get("total"))
    return s == 200


def cmd_job(a):
    verb = a.action.lower()
    if verb == "status":
        s, b = call("GET", "/api/v1/jobs?size=100")
        m = [j for j in b.get("items", []) if j.get("job_id", "").startswith(a.job_id)]
        print(json.dumps(m[:1], indent=1)[:2000])
        return bool(m)
    s, b = call("POST", f"/api/v1/jobs/{a.job_id}/{verb}", {})
    print(s, json.dumps(b)[:500])
    return s == 200


def cmd_research(a):
    s, p = call("POST", "/api/v1/research/plan", {"question": a.question})
    print("plan intents:", p.get("intents"))
    s, r = call("POST", "/api/v1/research/runs", {"question": a.question, "plan": p})
    print("run:", r.get("id"), r.get("status"))
    return s == 200


def cmd_report(a):
    s, b = call("POST", "/api/v1/reports", {"kind": a.kind, "project": a.project or ""})
    print(s, "report", b.get("id"), "coverage", b.get("source_coverage"))
    return s == 200


def cmd_migrate(_):
    from app.db.migrations.env import run
    run()
    return True


def cmd_backup(_):
    import datetime
    dest = f"backup-{datetime.date.today().isoformat()}.json"
    ok = True
    bundle = {}
    for path in ("/api/v1/projects", "/api/v1/targets", "/api/v1/jobs?size=100",
                 "/api/v1/alerts?size=100", "/api/v1/reports"):
        s, b = call("GET", path)
        ok = ok and s == 200
        bundle[path] = b
    json.dump(bundle, open(dest, "w"), default=str)
    print("wrote", dest, "ok=", ok)
    return ok


def cmd_version(_):
    s, b = call("GET", "/api/version")
    print(s, b)
    return s == 200


def main(argv=None):
    ap = argparse.ArgumentParser(prog="webintel")
    ap.add_argument("--api", default=API)
    ap.add_argument("--token", default=TOKEN)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health")
    sub.add_parser("doctor")
    sub.add_parser("version")
    sub.add_parser("migrate")
    sub.add_parser("backup")
    j = sub.add_parser("jobs")
    j.add_argument("--size", default=20)
    j.add_argument("--status", default="")
    jj = sub.add_parser("job")
    jj.add_argument("job_id")
    jj.add_argument("action", choices=["status", "run", "retry", "cancel"])
    r = sub.add_parser("research")
    r.add_argument("question")
    rp = sub.add_parser("report")
    rp.add_argument("--kind", default="price")
    rp.add_argument("--project", default="")
    a = ap.parse_args(argv)
    global API, TOKEN
    API, TOKEN = a.api, a.token
    fns = {"health": cmd_health, "doctor": cmd_doctor, "version": cmd_version,
           "migrate": cmd_migrate, "backup": cmd_backup, "jobs": cmd_jobs,
           "job": cmd_job, "research": cmd_research, "report": cmd_report}
    sys.exit(0 if fns[a.cmd](a) else 1)


if __name__ == "__main__":
    main()
