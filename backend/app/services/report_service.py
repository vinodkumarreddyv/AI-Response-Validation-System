import json
import sqlite3
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.pdfbase.pdfmetrics import stringWidth

from backend.app.database import get_connection


REPORT_TITLE = "AI Response Validation System"
REPORT_SUBTITLE = "Evaluation Report"


def _safe_json(value, default):
    if value is None or value == "":
        return default

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_verdict(value):
    value = str(value or "").strip().upper()

    if value in {"CORRECT", "PASS"}:
        return "PASS"

    if value in {"PARTIALLY CORRECT", "PARTIAL", "NEEDS IMPROVEMENT"}:
        return "NEEDS IMPROVEMENT"

    if value in {"INCORRECT", "FAIL"}:
        return "FAIL"

    return value or "UNKNOWN"


def _fetch_rows(batch_id=None):
    connection = get_connection()

    query = """
        SELECT *
        FROM evaluation_submissions
        WHERE relevance_score IS NOT NULL
          AND accuracy_score IS NOT NULL
          AND hallucination_score IS NOT NULL
          AND completeness_score IS NOT NULL
    """

    params = []

    if batch_id:
        query += " AND COALESCE(batch_id, 'single') = ?"
        params.append(batch_id)

    query += " ORDER BY id ASC"

    rows = connection.execute(query, params).fetchall()
    connection.close()

    return rows


def _row_to_record(row):
    record = dict(row)

    record["relevance"] = _safe_json(record.get("relevance_json"), {})
    record["accuracy"] = _safe_json(record.get("accuracy_json"), {})
    record["hallucination"] = _safe_json(
        record.get("hallucination_json"), {}
    )
    record["completeness"] = _safe_json(
        record.get("completeness_json"), {}
    )

    record["dimension_scores"] = _safe_json(
        record.get("dimension_scores_json"), {}
    )

    record["weights"] = _safe_json(
        record.get("weights_json"), {}
    )

    record["hallucinated_claims"] = _safe_json(
        record.get("hallucinated_claims_json"), []
    )

    record["missing_aspects"] = _safe_json(
        record.get("missing_aspects_json"), []
    )

    record["supporting_evidence"] = _safe_json(
        record.get("supporting_evidence_json"), []
    )

    record["dashboard_verdict"] = _normalize_verdict(
        record.get("verdict")
    )

    return record


def _average(records, key):
    values = [_safe_float(r.get(key), 0) for r in records]
    return sum(values) / len(values) if values else 0.0


def _verdict_counts(records):
    counts = {
        "PASS": 0,
        "NEEDS IMPROVEMENT": 0,
        "FAIL": 0,
    }

    for record in records:
        verdict = record["dashboard_verdict"]
        if verdict in counts:
            counts[verdict] += 1

    return counts


def _percentage(value, total):
    return (value / total * 100) if total else 0.0


def _claim_count(record):
    claims = record.get("hallucinated_claims", [])
    if isinstance(claims, dict):
        claims = claims.get("unsupported_claims", []) or claims.get(
            "contradictory_claims", []
        )
    return len(claims) if isinstance(claims, list) else 0


def _missing_count(record):
    missing = record.get("missing_aspects", [])
    return len(missing) if isinstance(missing, list) else 0


def _recommendations(records):
    recommendations = []

    if not records:
        return recommendations

    low_accuracy = sum(
        1 for r in records if _safe_float(r.get("accuracy_score")) < 3
    )
    low_relevance = sum(
        1 for r in records if _safe_float(r.get("relevance_score")) < 3
    )
    incomplete = sum(
        1 for r in records if _safe_float(r.get("completeness_score")) < 3
    )
    hallucinated = sum(
        1
        for r in records
        if _claim_count(r) > 0
        or bool(
            _safe_json(r.get("hallucination_json"), {}).get(
                "hallucination_detected", False
            )
        )
    )

    if low_accuracy:
        recommendations.append(
            f"Review factual grounding and retrieved evidence for {low_accuracy} "
            "response(s) with low accuracy scores."
        )

    if low_relevance:
        recommendations.append(
            f"Improve response alignment with the question for {low_relevance} "
            "response(s) with low relevance scores."
        )

    if incomplete:
        recommendations.append(
            f"Add missing required information for {incomplete} response(s) "
            "with low completeness scores."
        )

    if hallucinated:
        recommendations.append(
            f"Review unsupported or contradicted claims in {hallucinated} "
            "response(s) flagged by hallucination evaluation."
        )

    if not recommendations:
        recommendations.append(
            "No recurring weaknesses were detected in the evaluated batch."
        )

    return recommendations


def _paragraph(text, style):
    text = str(text if text is not None else "—")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br/>")
    return Paragraph(text, style)


def _draw_page(canvas, doc):
    canvas.saveState()

    width, height = A4

    canvas.setStrokeColor(colors.HexColor("#D9E0EA"))
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(
        18 * mm,
        9 * mm,
        "AI Response Validation System"
    )

    canvas.drawRightString(
        width - 18 * mm,
        9 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


def _styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=colors.HexColor("#172033"),
            alignment=TA_LEFT,
            spaceAfter=5 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#667085"),
            spaceAfter=8 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#172033"),
            spaceBefore=5 * mm,
            spaceAfter=3 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#344054"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyReport",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#344054"),
            spaceAfter=2 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableText",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#344054"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.white,
        )
    )

    return styles


def _table(data, widths=None, header=True):
    style = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0EA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ]
        )

    for row in range(1 if header else 0, len(data)):
        if row % 2 == 0:
            style.append(
                (
                    "BACKGROUND",
                    (0, row),
                    (-1, row),
                    colors.HexColor("#F8FAFC"),
                )
            )

    table = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    table.setStyle(TableStyle(style))
    return table


def _metric_cards(canvas, metrics, y, width):
    card_width = (width - 8 * mm) / len(metrics)

    for index, (label, value) in enumerate(metrics):
        x = index * (card_width + 2 * mm)

        canvas.setFillColor(colors.HexColor("#F8FAFC"))
        canvas.roundRect(
            x,
            y - 18 * mm,
            card_width,
            18 * mm,
            2 * mm,
            fill=1,
            stroke=0,
        )

        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawString(x + 3 * mm, y - 5 * mm, label.upper())

        canvas.setFillColor(colors.HexColor("#172033"))
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(x + 3 * mm, y - 12 * mm, str(value))


def _build_pdf(records, batch_id):
    styles = _styles()

    buffer = BytesIO()

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=f"{REPORT_TITLE} - {REPORT_SUBTITLE}",
        author="AI Response Validation System",
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )

    doc.addPageTemplates(
        [
            PageTemplate(
                id="main",
                frames=frame,
                onPage=_draw_page,
            )
        ]
    )

    story = []

    total = len(records)
    avg_score = _average(records, "score")
    avg_relevance = _average(records, "relevance_score")
    avg_accuracy = _average(records, "accuracy_score")
    avg_hallucination = _average(records, "hallucination_score")
    avg_completeness = _average(records, "completeness_score")

    verdicts = _verdict_counts(records)

    hallucinated_responses = sum(
        1 for record in records if _claim_count(record) > 0
    )

    unsupported_claims = sum(
        len(
            _safe_json(
                record.get("hallucination_json"), {}
            ).get("unsupported_claims", [])
            or []
        )
        for record in records
    )

    contradictory_claims = sum(
        len(
            _safe_json(
                record.get("hallucination_json"), {}
            ).get("contradictory_claims", [])
            or []
        )
        for record in records
    )

    incomplete_responses = sum(
        1 for record in records if _missing_count(record) > 0
    )

    generated_at = datetime.now().strftime("%d %B %Y, %H:%M")

    story.append(
        Paragraph(REPORT_TITLE, styles["ReportTitle"])
    )

    story.append(
        Paragraph(
            f"{REPORT_SUBTITLE} — Batch: {batch_id}",
            styles["ReportSubtitle"],
        )
    )

    metadata = [
        [
            _paragraph("Report Generated", styles["TableHeader"]),
            _paragraph(generated_at, styles["TableText"]),
        ],
        [
            _paragraph("Evaluation Batch", styles["TableHeader"]),
            _paragraph(batch_id, styles["TableText"]),
        ],
        [
            _paragraph("Records Included", styles["TableHeader"]),
            _paragraph(total, styles["TableText"]),
        ],
        [
            _paragraph("Data Source", styles["TableHeader"]),
            _paragraph(
                "Stored structured evaluation results from SQLite",
                styles["TableText"],
            ),
        ],
    ]

    metadata_table = Table(
        metadata,
        colWidths=[45 * mm, 125 * mm],
    )

    metadata_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#172033")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E0EA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(metadata_table)
    story.append(Spacer(1, 6 * mm))

    story.append(
        Paragraph("1. Batch Scoring Summary", styles["Section"])
    )

    summary = [
        [
            _paragraph("Metric", styles["TableHeader"]),
            _paragraph("Value", styles["TableHeader"]),
        ],
        [
            _paragraph("Total responses", styles["TableText"]),
            _paragraph(total, styles["TableText"]),
        ],
        [
            _paragraph("Pass", styles["TableText"]),
            _paragraph(
                f"{verdicts['PASS']} ({_percentage(verdicts['PASS'], total):.1f}%)",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Needs Improvement", styles["TableText"]),
            _paragraph(
                f"{verdicts['NEEDS IMPROVEMENT']} "
                f"({_percentage(verdicts['NEEDS IMPROVEMENT'], total):.1f}%)",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Fail", styles["TableText"]),
            _paragraph(
                f"{verdicts['FAIL']} ({_percentage(verdicts['FAIL'], total):.1f}%)",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Average final score", styles["TableText"]),
            _paragraph(f"{avg_score:.2f} / 100", styles["TableText"]),
        ],
        [
            _paragraph("Hallucination frequency", styles["TableText"]),
            _paragraph(
                f"{_percentage(hallucinated_responses, total):.1f}%",
                styles["TableText"],
            ),
        ],
    ]

    story.append(
        _table(
            summary,
            widths=[85 * mm, 85 * mm],
        )
    )

    story.append(
        Paragraph("2. Dimension Breakdown", styles["Section"])
    )

    dimension_data = [
        [
            _paragraph("Dimension", styles["TableHeader"]),
            _paragraph("Average Score / 5", styles["TableHeader"]),
            _paragraph("Weight", styles["TableHeader"]),
        ],
        [
            _paragraph("Relevance", styles["TableText"]),
            _paragraph(f"{avg_relevance:.2f}", styles["TableText"]),
            _paragraph(
                f"{_safe_float(records[0].get('weights', {}).get('relevance'), 0.20) * 100:.0f}%",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Accuracy", styles["TableText"]),
            _paragraph(f"{avg_accuracy:.2f}", styles["TableText"]),
            _paragraph(
                f"{_safe_float(records[0].get('weights', {}).get('accuracy'), 0.35) * 100:.0f}%",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Hallucination Detection", styles["TableText"]),
            _paragraph(f"{avg_hallucination:.2f}", styles["TableText"]),
            _paragraph(
                f"{_safe_float(records[0].get('weights', {}).get('hallucination'), 0.25) * 100:.0f}%",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Completeness", styles["TableText"]),
            _paragraph(f"{avg_completeness:.2f}", styles["TableText"]),
            _paragraph(
                f"{_safe_float(records[0].get('weights', {}).get('completeness'), 0.20) * 100:.0f}%",
                styles["TableText"],
            ),
        ],
    ]

    story.append(
        _table(
            dimension_data,
            widths=[75 * mm, 55 * mm, 40 * mm],
        )
    )

    story.append(
        Paragraph("3. Hallucination & Completeness Summary", styles["Section"])
    )

    issue_data = [
        [
            _paragraph("Finding", styles["TableHeader"]),
            _paragraph("Count", styles["TableHeader"]),
            _paragraph("Frequency", styles["TableHeader"]),
        ],
        [
            _paragraph("Responses with hallucinated claims", styles["TableText"]),
            _paragraph(hallucinated_responses, styles["TableText"]),
            _paragraph(
                f"{_percentage(hallucinated_responses, total):.1f}%",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Unsupported claims", styles["TableText"]),
            _paragraph(unsupported_claims, styles["TableText"]),
            _paragraph(
                f"{_percentage(unsupported_claims, total):.1f} claims/response",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Contradictory claims", styles["TableText"]),
            _paragraph(contradictory_claims, styles["TableText"]),
            _paragraph(
                f"{_percentage(contradictory_claims, total):.1f} claims/response",
                styles["TableText"],
            ),
        ],
        [
            _paragraph("Responses with missing information", styles["TableText"]),
            _paragraph(incomplete_responses, styles["TableText"]),
            _paragraph(
                f"{_percentage(incomplete_responses, total):.1f}%",
                styles["TableText"],
            ),
        ],
    ]

    story.append(
        _table(
            issue_data,
            widths=[85 * mm, 30 * mm, 55 * mm],
        )
    )

    story.append(
        Paragraph("4. Improvement Recommendations", styles["Section"])
    )

    for recommendation in _recommendations(records):
        story.append(
            Paragraph(
                f"• {recommendation}",
                styles["BodyReport"],
            )
        )

    story.append(PageBreak())

    story.append(
        Paragraph("5. Individual Evaluation Results", styles["Section"])
    )

    for index, record in enumerate(records, start=1):
        verdict = record["dashboard_verdict"]

        title = (
            f"Response {index} — Submission #{record.get('id')} — {verdict}"
        )

        story.append(
            Paragraph(title, styles["Section"])
        )

        individual = [
            [
                _paragraph("Field", styles["TableHeader"]),
                _paragraph("Value", styles["TableHeader"]),
            ],
            [
                _paragraph("Question", styles["TableText"]),
                _paragraph(record.get("question"), styles["TableText"]),
            ],
            [
                _paragraph("AI Response", styles["TableText"]),
                _paragraph(record.get("ai_response"), styles["TableText"]),
            ],
            [
                _paragraph("Reference Answer", styles["TableText"]),
                _paragraph(
                    record.get("reference_answer") or "Not provided",
                    styles["TableText"],
                ),
            ],
            [
                _paragraph("Source Document", styles["TableText"]),
                _paragraph(
                    record.get("source_document") or "Not provided",
                    styles["TableText"],
                ),
            ],
            [
                _paragraph("Final Score", styles["TableText"]),
                _paragraph(
                    f"{_safe_float(record.get('score')):.2f} / 100",
                    styles["TableText"],
                ),
            ],
            [
                _paragraph("Weighted Score", styles["TableText"]),
                _paragraph(
                    f"{_safe_float(record.get('weighted_score')):.2f} / 5",
                    styles["TableText"],
                ),
            ],
            [
                _paragraph("Final Verdict", styles["TableText"]),
                _paragraph(verdict, styles["TableText"]),
            ],
        ]

        story.append(
            _table(
                individual,
                widths=[45 * mm, 125 * mm],
            )
        )

        dimensions_row = [
            [
                _paragraph("Relevance", styles["TableHeader"]),
                _paragraph("Accuracy", styles["TableHeader"]),
                _paragraph("Hallucination", styles["TableHeader"]),
                _paragraph("Completeness", styles["TableHeader"]),
            ],
            [
                _paragraph(
                    f"{_safe_float(record.get('relevance_score')):.1f}/5",
                    styles["TableText"],
                ),
                _paragraph(
                    f"{_safe_float(record.get('accuracy_score')):.1f}/5",
                    styles["TableText"],
                ),
                _paragraph(
                    f"{_safe_float(record.get('hallucination_score')):.1f}/5",
                    styles["TableText"],
                ),
                _paragraph(
                    f"{_safe_float(record.get('completeness_score')):.1f}/5",
                    styles["TableText"],
                ),
            ],
        ]

        story.append(Spacer(1, 3 * mm))
        story.append(
            _table(
                dimensions_row,
                widths=[42.5 * mm] * 4,
            )
        )

        story.append(
            Paragraph("Dimension Reasoning", styles["Section"])
        )

        reasoning_rows = [
            [
                _paragraph("Dimension", styles["TableHeader"]),
                _paragraph("Reasoning", styles["TableHeader"]),
            ],
            [
                _paragraph("Relevance", styles["TableText"]),
                _paragraph(
                    record.get("relevance", {}).get(
                        "reasoning",
                        "—",
                    ),
                    styles["TableText"],
                ),
            ],
            [
                _paragraph("Accuracy", styles["TableText"]),
                _paragraph(
                    record.get("accuracy", {}).get(
                        "reasoning",
                        "—",
                    ),
                    styles["TableText"],
                ),
            ],
            [
                _paragraph("Hallucination", styles["TableText"]),
                _paragraph(
                    record.get("hallucination", {}).get(
                        "reasoning",
                        "—",
                    ),
                    styles["TableText"],
                ),
            ],
            [
                _paragraph("Completeness", styles["TableText"]),
                _paragraph(
                    record.get("completeness", {}).get(
                        "reasoning",
                        "—",
                    ),
                    styles["TableText"],
                ),
            ],
        ]

        story.append(
            _table(
                reasoning_rows,
                widths=[40 * mm, 130 * mm],
            )
        )

        claims = record.get("hallucinated_claims", [])

        if claims:
            story.append(
                Paragraph("Hallucinated / Unsupported Claims", styles["Section"])
            )

            claim_rows = [
                [
                    _paragraph("Claim", styles["TableHeader"]),
                    _paragraph("Status", styles["TableHeader"]),
                    _paragraph("Reasoning", styles["TableHeader"]),
                ]
            ]

            for claim in claims:
                if isinstance(claim, dict):
                    claim_rows.append(
                        [
                            _paragraph(
                                claim.get("claim", "—"),
                                styles["TableText"],
                            ),
                            _paragraph(
                                claim.get("status", "—"),
                                styles["TableText"],
                            ),
                            _paragraph(
                                claim.get("reasoning", "—"),
                                styles["TableText"],
                            ),
                        ]
                    )
                else:
                    claim_rows.append(
                        [
                            _paragraph(claim, styles["TableText"]),
                            _paragraph("Flagged", styles["TableText"]),
                            _paragraph("Flagged by hallucination evaluation.", styles["TableText"]),
                        ]
                    )

            story.append(
                _table(
                    claim_rows,
                    widths=[65 * mm, 35 * mm, 70 * mm],
                )
            )

        missing = record.get("missing_aspects", [])

        if missing:
            story.append(
                Paragraph("Missing / Incomplete Aspects", styles["Section"])
            )

            for aspect in missing:
                story.append(
                    Paragraph(
                        f"• {aspect}",
                        styles["BodyReport"],
                    )
                )

        evidence = record.get("supporting_evidence", [])

        if evidence:
            story.append(
                Paragraph("Supporting Evidence", styles["Section"])
            )

            evidence_rows = [
                [
                    _paragraph("Evidence", styles["TableHeader"]),
                    _paragraph("Similarity", styles["TableHeader"]),
                    _paragraph("Source", styles["TableHeader"]),
                ]
            ]

            for item in evidence:
                if isinstance(item, dict):
                    evidence_rows.append(
                        [
                            _paragraph(
                                item.get("text")
                                or item.get("evidence")
                                or "—",
                                styles["TableText"],
                            ),
                            _paragraph(
                                f"{_safe_float(item.get('similarity')):.3f}",
                                styles["TableText"],
                            ),
                            _paragraph(
                                item.get("source", "rag_evidence"),
                                styles["TableText"],
                            ),
                        ]
                    )
                else:
                    evidence_rows.append(
                        [
                            _paragraph(item, styles["TableText"]),
                            _paragraph("—", styles["TableText"]),
                            _paragraph("rag_evidence", styles["TableText"]),
                        ]
                    )

            story.append(
                _table(
                    evidence_rows,
                    widths=[105 * mm, 25 * mm, 40 * mm],
                )
            )

        verdict_reasoning = record.get("verdict_reasoning")

        if verdict_reasoning:
            story.append(
                Paragraph("Final Verdict Reasoning", styles["Section"])
            )
            story.append(
                Paragraph(
                    verdict_reasoning,
                    styles["BodyReport"],
                )
            )

        if index != len(records):
            story.append(PageBreak())

    doc.build(story)

    buffer.seek(0)
    return buffer


def generate_evaluation_report(batch_id="single"):
    records = [_row_to_record(row) for row in _fetch_rows(batch_id)]

    if not records:
        raise ValueError(
            f"No structured evaluation records found for batch '{batch_id}'."
        )

    return _build_pdf(records, batch_id)


def get_available_report_batches():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            COALESCE(batch_id, 'single') AS batch_id,
            COUNT(*) AS total_responses,
            MIN(created_at) AS first_created_at,
            MAX(created_at) AS last_created_at
        FROM evaluation_submissions
        WHERE relevance_score IS NOT NULL
          AND accuracy_score IS NOT NULL
          AND hallucination_score IS NOT NULL
          AND completeness_score IS NOT NULL
        GROUP BY COALESCE(batch_id, 'single')
        ORDER BY MAX(created_at) DESC
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]
