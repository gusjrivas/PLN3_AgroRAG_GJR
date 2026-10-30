"""Build the academic report PDF from its tracked Markdown source."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
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


def _styles():
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


def _footer(canvas, document) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#B8C8C2"))
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#52645E"))
    canvas.drawString(18 * mm, 9 * mm, "AgroRAG - Informe técnico reproducible")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Página {document.page}")
    canvas.restoreState()


def _table(lines: list[str], body_style) -> Table:
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


def build_pdf(source: Path, target: Path) -> None:
    """Render the supported Markdown subset into a stable, paginated PDF."""
    lines = source.read_text(encoding="utf-8").splitlines()
    target.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    story = []
    paragraph: list[str] = []
    code: list[str] = []
    in_code = False
    section_count = 0

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(_inline(" ".join(paragraph)), styles["BodyJustified"]))
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
            story.extend((_table(table_lines, styles["BodyJustified"]), Spacer(1, 7)))
            continue
        if line.startswith("# "):
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
            if story and section_count in {0, 5, 10}:
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
    build_pdf(root / "docs/report.md", root / "output/pdf/agro-rag-report.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
