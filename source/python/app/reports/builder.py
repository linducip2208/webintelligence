import datetime
def build(kind, project, rows, evidence, ai_analysis="", extra=None):
    rep = {"kind": kind, "project": project, "generated_at": datetime.datetime.utcnow().isoformat()+"Z",
        "methodology": "direct-first collection; validate; normalize; dedupe; aggregate; evidence-selected AI",
        "source_coverage": len(rows), "rows": rows, "evidence": evidence,
        "ai_analysis": ai_analysis, "limitations": "public data only; no auth bypass; estimates where noted"}
    if extra:
        rep.update({k: v for k, v in extra.items()
                    if k in ("executive_summary", "scope", "risk_summary", "key_findings",
                             "entities", "timeline", "recommendations")})
    return rep
def to_csv(report):
    lines = ["kind,project,generated_at"]
    lines.append(f"{report['kind']},{report['project']},{report['generated_at']}")
    return "\n".join(lines) + "\n"
def to_pdf(report):
    """Real PDF via reportlab. Raises ImportError when unavailable."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    import io as _io
    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"WebIntel {report.get('kind')} report")
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Intelligence Report: {report.get('kind')}", styles["Title"]),
             Spacer(1, 12),
             Paragraph(f"Project: {report.get('project')} | Generated: {report.get('generated_at')}", styles["Normal"]),
             Spacer(1, 12),
             Paragraph("Methodology", styles["Heading2"]),
             Paragraph(str(report.get("methodology", ""))[:2000], styles["Normal"]),
             Spacer(1, 12),
             Paragraph(f"Source coverage: {report.get('source_coverage')}", styles["Heading3"])]
    rows = [[str(x)] for x in (report.get("rows") or [])[:50]]
    if rows:
        t = Table([["value"]] + rows)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story += [Paragraph("Data", styles["Heading2"]), t, Spacer(1, 12)]
    for title, body, is_list in _sections(report):
        story.append(Paragraph(title, styles["Heading2"]))
        if is_list and isinstance(body, list):
            for b in body[:100]:
                story.append(Paragraph(str(b)[:300], styles["Normal"]))
        else:
            story.append(Paragraph(str(body)[:4000], styles["Normal"]))
        story.append(Spacer(1, 12))
    story += [Paragraph("Evidence", styles["Heading2"]),
              Paragraph(str(report.get("evidence", []))[:3000], styles["Normal"]),
              Spacer(1, 12),
              Paragraph("AI analysis", styles["Heading2"]),
              Paragraph(str(report.get("ai_analysis", ""))[:3000], styles["Normal"]),
              Spacer(1, 12),
              Paragraph("Limitations", styles["Heading2"]),
              Paragraph(str(report.get("limitations", ""))[:2000], styles["Normal"])]
    doc.build(story)
    return buf.getvalue()
def _sections(report):
    """Optional professional sections (newest first). Missing = skipped."""
    out = []
    if report.get("executive_summary"):
        out.append(("Executive summary", str(report["executive_summary"])[:4000], False))
    if report.get("scope"):
        out.append(("Scope", str(report["scope"])[:2000], False))
    if report.get("risk_summary"):
        out.append(("Risk summary", str(report["risk_summary"])[:2000], False))
    if report.get("key_findings"):
        out.append(("Key findings", report["key_findings"], True))
    if report.get("entities"):
        out.append(("Entities", report["entities"], True))
    if report.get("timeline"):
        out.append(("Timeline", report["timeline"], True))
    if report.get("recommendations"):
        out.append(("Recommendations", report["recommendations"], True))
    return out


def to_markdown(report):
    lines = [f"# {report.get('kind', 'report')} — {report.get('project', '')}", "",
             f"_Generated: {report.get('generated_at', '')}_", "",
             "## Methodology", str(report.get("methodology", "")), "",
             f"## Data ({report.get('source_coverage', 0)} points)"]
    for row in (report.get("rows") or [])[:100]:
        lines.append(f"- {row}")
    for title, body, is_list in _sections(report):
        lines += ["", f"## {title}"]
        if is_list and isinstance(body, list):
            for b in body[:100]:
                lines.append(f"- {b}")
        else:
            lines.append(str(body)[:4000])
    lines += ["", "## Evidence", str(report.get("evidence", ""))[:3000], "",
              "## AI analysis", str(report.get("ai_analysis", ""))[:3000], "",
              "## Limitations", str(report.get("limitations", ""))]
    return "\n".join(lines) + "\n"
def to_html(report):
    """Standalone Tabler-styled report page (offline vendor CSS)."""
    import html as _h
    rows = "".join(f"<tr><td>{_h.escape(str(x))[:200]}</td></tr>"
                    for x in (report.get("rows") or [])[:100])
    extra = "".join(
        f'<div class="card"><div class="card-body"><h3 class="card-title">{_h.escape(t)}</h3>'
        + (f"<ul>{''.join(f'<li>{_h.escape(str(b))[:300]}</li>' for b in (body or [])[:100])}</ul>"
           if is_list and isinstance(body, list)
           else f"<p>{_h.escape(str(body))[:4000]}</p>")
        + "</div></div>"
        for t, body, is_list in _sections(report))
    return f"""<!doctype html><html lang="en" data-bs-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Report: {_h.escape(str(report.get('kind', '')))} — {_h.escape(str(report.get('project', '')))}</title>
<link href="/static/vendor/tabler/tabler.min.css" rel="stylesheet"></head>
<body><div class="page"><div class="page-wrapper"><div class="page-body"><div class="container-xl">
<h2 class="page-title">Intelligence Report: {_h.escape(str(report.get('kind', '')))}</h2>
<p class="text-muted">Project: {_h.escape(str(report.get('project', '')))} | Generated: {_h.escape(str(report.get('generated_at', '')))}</p>
<div class="card"><div class="card-body"><h3 class="card-title">Methodology</h3>
<p>{_h.escape(str(report.get('methodology', ''))[:2000])}</p></div></div>
<div class="card"><div class="card-body"><h3 class="card-title">Data ({report.get('source_coverage', 0)} points)</h3>
<div class="table-responsive"><table class="table table-vcenter"><tbody>{rows}</tbody></table></div></div></div>
{extra}
<div class="card"><div class="card-body"><h3 class="card-title">Evidence</h3>
<pre>{_h.escape(str(report.get('evidence', ''))[:3000])}</pre></div></div>
<div class="card"><div class="card-body"><h3 class="card-title">AI analysis</h3>
<p>{_h.escape(str(report.get('ai_analysis', ''))[:3000])}</p></div></div>
<div class="card"><div class="card-body"><h3 class="card-title">Limitations</h3>
<p class="text-muted">{_h.escape(str(report.get('limitations', ''))[:2000])}</p></div></div>
</div></div></div></div>
<script src="/static/vendor/tabler/tabler.min.js"></script></body></html>"""
