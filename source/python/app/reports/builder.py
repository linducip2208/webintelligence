import datetime
def build(kind, project, rows, evidence, ai_analysis=""):
    return {"kind": kind, "project": project, "generated_at": datetime.datetime.utcnow().isoformat()+"Z",
        "methodology": "direct-first collection; validate; normalize; dedupe; aggregate; evidence-selected AI",
        "source_coverage": len(rows), "rows": rows, "evidence": evidence,
        "ai_analysis": ai_analysis, "limitations": "public data only; no auth bypass; estimates where noted"}
def to_csv(report):
    lines = ["kind,project,generated_at"]
    lines.append(f"{report['kind']},{report['project']},{report['generated_at']}")
    return "\n".join(lines) + "\n"
