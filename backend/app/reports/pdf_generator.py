import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable

def generate_pdf_report(scan_data: dict) -> bytes:
    """
    Generates a high-quality, professional PDF health assessment report using ReportLab.
    Returns bytes of the compiled PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#475569"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    bold_style = ParagraphStyle(
        "BodyDarkBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    badge_style = ParagraphStyle(
        "ScoreBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=1,  # Center
    )

    project_name = scan_data.get("project_name", "Software Project")
    health_score = scan_data.get("health_score", 0)
    risk_level = scan_data.get("risk_level", "Unknown")
    readiness_status = scan_data.get("readiness_status", "READY")
    readiness_reasons = scan_data.get("readiness_reasons", [])
    technologies = ", ".join(scan_data.get("detected_technologies", [])) or "None Identified"
    created_at = scan_data.get("created_at", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    total_findings = scan_data.get("total_findings", 0)
    passed_checks = scan_data.get("passed_checks", 0)
    warning_count = scan_data.get("warning_count", 0)
    failed_checks = scan_data.get("failed_checks", 0)
    category_scores = scan_data.get("category_scores", {})

    # 1. Header Banner
    header_table = Table(
        [
            [
                Paragraph("<b>StackDoctor</b> | Project Health Report", subtitle_style),
                Paragraph(f"Generated: {created_at[:19] if isinstance(created_at, str) else created_at}", subtitle_style),
            ]
        ],
        colWidths=[340, 200],
    )
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=4, spaceAfter=14))

    # 2. Main Title and Overview Box
    story.append(Paragraph(f"Project Assessment: {project_name}", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Automated static analysis of architecture, dependencies, containerization, CI/CD pipelines, and secrets exposure.", subtitle_style))
    story.append(Spacer(1, 14))

    # Determine badge color based on health score
    if health_score >= 85:
        score_color = colors.HexColor("#16a34a")  # Emerald green
        badge_bg = colors.HexColor("#f0fdf4")
    elif health_score >= 70:
        score_color = colors.HexColor("#d97706")  # Amber
        badge_bg = colors.HexColor("#fffbeb")
    else:
        score_color = colors.HexColor("#dc2626")  # Red
        badge_bg = colors.HexColor("#fef2f2")

    # Determine readiness color
    if readiness_status == "READY":
        readiness_color = "#16a34a"
    elif readiness_status == "READY WITH WARNINGS":
        readiness_color = "#d97706"
    elif readiness_status == "BLOCKED":
        readiness_color = "#dc2626"
    else:
        readiness_color = "#64748b"

    score_card_data = [
        [
            Paragraph(f"<font color='{score_color.hexval()}'><b>{health_score} / 100</b></font><br/><font size='9' color='#475569'>{risk_level}</font><br/><br/><font size='9' color='{readiness_color}'><b>[{readiness_status}]</b></font>", badge_style),
            Paragraph(
                f"<b>Target Project:</b> {project_name}<br/>"
                f"<b>Deployment Readiness:</b> <font color='{readiness_color}'><b>{readiness_status}</b></font><br/>"
                f"<b>Identified Stack:</b> {technologies}<br/>"
                f"<b>Total Findings:</b> {total_findings} | "
                f"<b>Passed:</b> {passed_checks} | "
                f"<b>Warnings:</b> {warning_count} | "
                f"<b>Failures:</b> {failed_checks}",
                body_style
            ),
        ]
    ]

    score_card = Table(score_card_data, colWidths=[150, 390])
    score_card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), badge_bg),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(score_card)
    story.append(Spacer(1, 16))

    # 3. Module Breakdown
    story.append(Paragraph("Category-Wise Inspection Summary", section_heading))
    summary_dict = scan_data.get("scan_summary", {})

    module_table_data = [
        [
            Paragraph("<b>Inspection Module</b>", bold_style),
            Paragraph("<b>Status</b>", bold_style),
            Paragraph("<b>Findings Detected</b>", bold_style),
        ]
    ]

    for mod_name, mod_info in summary_dict.items():
        status = mod_info.get("status", "Passed")
        count = mod_info.get("findings_count", 0)

        if status == "Passed":
            status_html = "<font color='#16a34a'><b>Passed</b></font>"
        elif status == "Warning":
            status_html = "<font color='#d97706'><b>Warning</b></font>"
        elif status == "Failed":
            status_html = "<font color='#dc2626'><b>Failed</b></font>"
        else:
            status_html = f"<font color='#64748b'><b>{status}</b></font>"

        module_table_data.append([
            Paragraph(mod_name, body_style),
            Paragraph(status_html, body_style),
            Paragraph(str(count), body_style),
        ])

    mod_table = Table(module_table_data, colWidths=[240, 150, 150])
    mod_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(mod_table)
    story.append(Spacer(1, 16))

    # 4. Detailed Findings
    story.append(Paragraph("Detailed Findings & Recommended Actions", section_heading))
    findings = scan_data.get("findings", [])

    if not findings:
        story.append(Paragraph("No critical issues or warnings were discovered. The project meets all baseline static health requirements.", body_style))
    else:
        for idx, finding in enumerate(findings, start=1):
            severity = finding.get("severity", "Medium")
            sev_color = "#dc2626" if severity in ["Critical", "High"] else "#d97706" if severity == "Medium" else "#2563eb"

            finding_flowables = [
                Paragraph(
                    f"<b>{idx}. [{finding.get('rule_id')}] {finding.get('title')}</b> — "
                    f"<font color='{sev_color}'><b>{severity}</b></font>",
                    bold_style
                ),
                Spacer(1, 2),
                Paragraph(f"<b>Location:</b> {finding.get('file_path') or 'Repository Root'}", body_style),
                Spacer(1, 2),
                Paragraph(f"<b>Description:</b> {finding.get('description')}", body_style),
                Spacer(1, 2),
                Paragraph(f"<b>Recommendation:</b> {finding.get('recommendation')}", body_style),
                Spacer(1, 6),
                HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=2, spaceAfter=8),
            ]
            story.append(KeepTogether(finding_flowables))

    # 5. Disclaimer Footer
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "<b>Disclaimer:</b> StackDoctor performs static configuration analysis only. This health score reflects compliance "
        "with automated static inspection heuristics and does not constitute a certified security audit or warranty of runtime readiness.",
        ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#94a3b8"))
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
