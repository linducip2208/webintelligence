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
def to_markdown(report):
    lines = [f"# {report.get('kind', 'report')} — {report.get('project', '')}", "",
             f"_Generated: {report.get('generated_at', '')}_", "",
             "## Methodology", str(report.get("methodology", "")), "",
             f"## Data ({report.get('source_coverage', 0)} points)"]
    for row in (report.get("rows") or [])[:100]:
        lines.append(f"- {row}")
    lines += ["", "## Evidence", str(report.get("evidence", ""))[:3000], "",
              "## AI analysis", str(report.get("ai_analysis", ""))[:3000], "",
              "## Limitations", str(report.get("limitations", ""))]
    return "\n".join(lines) + "\n"
