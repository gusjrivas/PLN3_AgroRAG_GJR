"""Build the academic report PDF from its tracked Markdown source."""

from __future__ import annotations

import argparse
import html
import re
from math import atan2, cos, sin
from pathlib import Path
from typing import cast

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _inline(value: str) -> str:
    value = html.escape(value.strip())
    value = re.sub(r"\[([^]]+)]\(([^)]+)\)", r'\1 (<font color="#176B87">\2</font>)', value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    return value


def _styles() -> StyleSheet1:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=33,
            textColor=colors.HexColor("#174A3A"),
            alignment=TA_CENTER,
            spaceAfter=16,
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportH2",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#174A3A"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportH3",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#176B87"),
            spaceBefore=7,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "BodyJustified",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#24312D"),
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            "BulletReport",
            parent=styles["BodyJustified"],
            leftIndent=14,
            firstLineIndent=-7,
            bulletIndent=5,
            spaceAfter=4,
        )
    )
    return styles


def _footer(canvas: Canvas, document: BaseDocTemplate) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#B8C8C2"))
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#52645E"))
    canvas.drawString(18 * mm, 9 * mm, "AgroRAG - Informe técnico reproducible")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Página {document.page}")
    canvas.restoreState()


def _table(lines: list[str], body_style: ParagraphStyle) -> Table:
    rows = [[_inline(cell) for cell in line.strip().strip("|").split("|")] for line in lines]
    if len(rows) > 1 and all(set(cell) <= {"-", ":"} for cell in rows[1]):
        rows.pop(1)
    data = [[Paragraph(cell, body_style) for cell in row] for row in rows]
    width = 174 * mm
    columns = len(data[0])
    table = Table(data, colWidths=[width / columns] * columns, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEBE5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#174A3A")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9DB2AA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


DIAGRAM_INK = colors.HexColor("#174A3A")
DIAGRAM_ACCENT = colors.HexColor("#176B87")


def _box(drawing: Drawing, x: int, y: int, width: int, title: str, detail: str) -> None:
    drawing.add(
        Rect(
            x,
            y,
            width,
            32,
            rx=5,
            ry=5,
            fillColor=colors.HexColor("#EDF5F1"),
            strokeColor=DIAGRAM_INK,
            strokeWidth=0.75,
        )
    )
    center = x + width / 2
    drawing.add(
        String(
            center,
            y + 19,
            title,
            fontName="Helvetica-Bold",
            fontSize=9,
            textAnchor="middle",
            fillColor=DIAGRAM_INK,
        )
    )
    drawing.add(
        String(
            center,
            y + 8,
            detail,
            fontName="Helvetica",
            fontSize=8,
            textAnchor="middle",
            fillColor=DIAGRAM_INK,
        )
    )


def _arrow(
    drawing: Drawing, x1: int, y1: int, x2: int, y2: int, color: colors.Color = DIAGRAM_INK
) -> None:
    drawing.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1))
    angle = atan2(y2 - y1, x2 - x1)
    points = [x2, y2]
    for offset in (-0.5, 0.5):
        points.extend((x2 - 5 * cos(angle + offset), y2 - 5 * sin(angle + offset)))
    drawing.add(Polygon(points, fillColor=color, strokeColor=None))


def _query_flow() -> Drawing:
    """Vector flowchart of the verified-answer path and its early exits."""
    drawing = Drawing(174 * mm, 150)
    drawing.hAlign = "LEFT"

    _box(drawing, 0, 115, 140, "Usuario en Streamlit", "Pregunta y contexto del cultivo")
    _box(drawing, 176, 115, 140, "FastAPI", "Autenticación y validación HTTP")
    _box(drawing, 352, 115, 140, "Caso de uso", "Coordina búsqueda y agentes")
    _box(drawing, 352, 59, 140, "Recuperación y ranking", "BM25 / E5 + Pinecone / RRF")
    _box(drawing, 176, 59, 140, "Agente investigador", "Propone afirmaciones con evidencia")
    _box(drawing, 0, 59, 140, "Agente verificador", "Revisa afirmaciones y citas")
    _box(
        drawing,
        0,
        0,
        492,
        "Respuesta HTTP a Streamlit",
        "Respuesta con citas, pedido de aclaración o abstención",
    )

    _arrow(drawing, 140, 131, 176, 131)
    _arrow(drawing, 316, 131, 352, 131)
    _arrow(drawing, 422, 115, 422, 91)
    _arrow(drawing, 352, 75, 316, 75)
    _arrow(drawing, 176, 75, 140, 75)
    _arrow(drawing, 70, 59, 70, 32)
    drawing.add(Line(111, 59, 111, 48, strokeColor=DIAGRAM_ACCENT))
    drawing.add(Line(111, 48, 228, 48, strokeColor=DIAGRAM_ACCENT))
    _arrow(drawing, 228, 48, 228, 59, DIAGRAM_ACCENT)
    drawing.add(
        String(169, 37, "Una revisión", fontSize=8, textAnchor="middle", fillColor=DIAGRAM_ACCENT)
    )
    return drawing


def _deployment_flow() -> Drawing:
    drawing = Drawing(174 * mm, 203)
    drawing.hAlign = "LEFT"
    width = 113
    for x, y, title, detail in (
        (0, 147, "Usuario", "HTTPS"),
        (126, 147, "Gateway Caddy", "TLS y acceso · 80/443"),
        (252, 147, "Streamlit", "Red interna · no root"),
        (378, 147, "FastAPI", "Red interna · no root"),
        (0, 81, "Garak en staging", "Runner y adaptador local"),
        (126, 81, "catalogue-admin", "Ingesta e índice explícitos"),
        (252, 81, "Catálogo SQLite", "Snapshot activo versionado"),
        (378, 81, "Servicios opcionales", "OpenAI y Pinecone"),
        (0, 12, "Reportes restringidos", "Hallazgos y revisión"),
        (126, 12, "Preflight del host", "Imágenes, volumen y secretos"),
        (252, 12, "Backup y rollback", "Snapshot y digests OCI"),
        (378, 12, "Logs JSON", "Gateway y API"),
    ):
        _box(drawing, x, y, width, title, detail)

    for start, stop in ((113, 126), (239, 252), (365, 378)):
        _arrow(drawing, start, 163, stop, 163)
    drawing.add(Line(182, 179, 182, 189, strokeColor=DIAGRAM_INK))
    drawing.add(Line(182, 189, 434, 189, strokeColor=DIAGRAM_INK))
    _arrow(drawing, 434, 189, 434, 179)
    drawing.add(
        String(
            308,
            193,
            "/health/* y /v1/*",
            fontName="Helvetica",
            fontSize=8,
            textAnchor="middle",
            fillColor=DIAGRAM_INK,
        )
    )

    _arrow(drawing, 56, 81, 56, 44, DIAGRAM_ACCENT)
    drawing.add(Line(56, 113, 56, 126, strokeColor=DIAGRAM_ACCENT))
    drawing.add(Line(56, 126, 182, 126, strokeColor=DIAGRAM_ACCENT))
    _arrow(drawing, 182, 126, 182, 147, DIAGRAM_ACCENT)
    _arrow(drawing, 239, 97, 252, 97, DIAGRAM_ACCENT)
    drawing.add(Line(401, 147, 401, 132, strokeColor=DIAGRAM_INK))
    drawing.add(Line(401, 132, 308, 132, strokeColor=DIAGRAM_INK))
    _arrow(drawing, 308, 132, 308, 113)
    _arrow(drawing, 453, 147, 453, 113)
    _arrow(drawing, 308, 81, 308, 44, DIAGRAM_ACCENT)
    return drawing


def build_pdf(source: Path, target: Path) -> None:
    """Render the supported Markdown subset into a stable, paginated PDF."""
    lines = source.read_text(encoding="utf-8").splitlines()
    target.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    story: list[Flowable] = []
    paragraph: list[str] = []
    code: list[str] = []
    in_code = False
    section_count = 0

    def flush_paragraph() -> None:
        if paragraph:
            body = Paragraph(_inline(" ".join(paragraph)), styles["BodyJustified"])
            if story and isinstance(story[-1], Drawing):
                story.append(KeepTogether([story.pop(), Spacer(1, 5), body]))
            else:
                story.append(body)
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(
                    Preformatted(
                        "\n".join(code),
                        ParagraphStyle(
                            "Code",
                            fontName="Courier",
                            fontSize=7.5,
                            leading=10,
                            backColor=colors.HexColor("#F1F5F3"),
                            borderPadding=7,
                            spaceAfter=8,
                        ),
                    )
                )
                code.clear()
            in_code = not in_code
            index += 1
            continue
        if in_code:
            code.append(line)
            index += 1
            continue
        if line.startswith("| "):
            flush_paragraph()
            table_lines = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            body_style = cast(ParagraphStyle, styles["BodyJustified"])
            story.extend((_table(table_lines, body_style), Spacer(1, 7)))
            continue
        if line in {"<!-- query-flow -->", "<!-- deployment-flow -->"}:
            flush_paragraph()
            story.append(_query_flow() if line == "<!-- query-flow -->" else _deployment_flow())
        elif line.startswith("# "):
            flush_paragraph()
            story.extend(
                (
                    Spacer(1, 42 * mm),
                    Paragraph(_inline(line[2:]), styles["CoverTitle"]),
                    Spacer(1, 10 * mm),
                )
            )
        elif line.startswith("## "):
            flush_paragraph()
            if story and section_count in {0, 10}:
                story.append(PageBreak())
            section_count += 1
            story.append(Paragraph(_inline(line[3:]), styles["ReportH2"]))
        elif line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(_inline(line[4:]), styles["ReportH3"]))
        elif line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(_inline(line[2:]), styles["BulletReport"], bulletText="•"))
        elif not line.strip():
            flush_paragraph()
        else:
            paragraph.append(line.strip())
        index += 1
    flush_paragraph()
    if in_code:
        raise ValueError("Bloque de código Markdown sin cerrar")

    document = SimpleDocTemplate(
        str(target),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="AgroRAG - Informe técnico reproducible",
        author="Gustavo Julián Rivas",
        subject="Trabajo integrador de Procesamiento de Lenguaje Natural III",
    )
    document.build(story, onFirstPage=_footer, onLaterPages=_footer)


def main() -> int:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "output/pdf/agro-rag-report.pdf")
    args = parser.parse_args()
    build_pdf(root / "docs/report.md", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
