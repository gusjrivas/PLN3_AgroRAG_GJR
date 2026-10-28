"""Build the fillable manual validation checklist for the 60-case benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.acroform import AcroForm
from reportlab.pdfgen.canvas import Canvas

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)
MARGIN = 28
NAVY = HexColor("#17324D")
GREEN = HexColor("#1E6B52")
PALE = HexColor("#EEF5F2")
GRAY = HexColor("#59636E")


def load_benchmark(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _lines(canvas: Canvas, text: str, x: float, y: float, width: float, size: int = 8) -> float:
    words = text.replace("\n", " ").split()
    current = ""
    line_height = size + 2
    for word in words:
        candidate = f"{current} {word}".strip()
        if canvas.stringWidth(candidate, "Helvetica", size) <= width:
            current = candidate
        else:
            canvas.drawString(x, y, current)
            y -= line_height
            current = word
    if current:
        canvas.drawString(x, y, current)
        y -= line_height
    return y


def _field_label(canvas: Canvas, label: str, value: str, x: float, y: float, width: float) -> float:
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(x, y, label)
    canvas.setFillColor(HexColor("#20262C"))
    canvas.setFont("Helvetica", 8)
    return _lines(canvas, value, x, y - 10, width, 8)


def _draw_case(
    canvas: Canvas, form: AcroForm, case: dict[str, Any], number: int, top: float
) -> None:
    box_height = 246
    x = MARGIN
    y = top - box_height
    width = PAGE_WIDTH - 2 * MARGIN
    canvas.setFillColor(PALE)
    canvas.roundRect(x, y, width, box_height, 6, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(x + 10, top - 18, f"{number:02d}. {case['query_id']}")
    crop = {"lettuce": "Lechuga", "tomato": "Tomate"}.get(case.get("crop"), "Sin especificar")
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(x + width - 10, top - 18, f"Cultivo: {crop}")

    cursor = top - 34
    cursor = _field_label(canvas, "PREGUNTA", case["question"], x + 10, cursor, width - 20) - 2
    expected = f"{case['expected_status']}. {case.get('reference_answer', '')}".strip()
    cursor = _field_label(canvas, "RESULTADO ESPERADO", expected, x + 10, cursor, width - 20) - 2
    claims = "; ".join(case.get("required_claims", [])) or "No aplica"
    cursor = _field_label(canvas, "CONTENIDO MINIMO", claims, x + 10, cursor, width - 20) - 2
    sources = ", ".join(case.get("source_pages", [])) or "No aplica"
    _field_label(canvas, "FUENTES ESPERADAS", sources, x + 10, cursor, width - 20)

    field_y = y + 52
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(x + 10, field_y + 22, "VALIDACION MANUAL")
    form.checkbox(
        name=f"pass_{case['query_id']}",
        x=x + 10,
        y=field_y,
        size=13,
        buttonStyle="check",
        borderColor=GREEN,
        fillColor=None,
        textColor=GREEN,
    )
    canvas.setFillColor(GREEN)
    canvas.drawString(x + 28, field_y + 3, "PASS")
    form.checkbox(
        name=f"fail_{case['query_id']}",
        x=x + 76,
        y=field_y,
        size=13,
        buttonStyle="check",
        borderColor=HexColor("#A33A36"),
        fillColor=None,
        textColor=HexColor("#A33A36"),
    )
    canvas.setFillColor(HexColor("#A33A36"))
    canvas.drawString(x + 94, field_y + 3, "FAIL")
    canvas.setFillColor(NAVY)
    canvas.drawString(x + 142, field_y + 22, "RESULTADO OBSERVADO")
    form.textfield(
        name=f"observed_{case['query_id']}",
        x=x + 142,
        y=field_y - 1,
        width=width - 152,
        height=18,
        borderWidth=1,
        borderColor=HexColor("#8A959F"),
        fillColor=HexColor("#FFFFFF"),
        fontName="Helvetica",
        fontSize=7,
    )
    canvas.setFillColor(NAVY)
    canvas.drawString(x + 10, y + 34, "OBSERVACIONES / CITAS / LATENCIA / ERROR")
    form.textfield(
        name=f"notes_{case['query_id']}",
        x=x + 10,
        y=y + 7,
        width=width - 20,
        height=24,
        borderWidth=1,
        borderColor=HexColor("#8A959F"),
        fillColor=HexColor("#FFFFFF"),
        fontName="Helvetica",
        fontSize=7,
        fieldFlags="multiline",
    )


def _cover(canvas: Canvas, form: AcroForm, total: int) -> None:
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_HEIGHT - 125, PAGE_WIDTH, 125, fill=1, stroke=0)
    canvas.setFillColor(HexColor("#FFFFFF"))
    canvas.setFont("Helvetica-Bold", 23)
    canvas.drawString(MARGIN, PAGE_HEIGHT - 56, "AgroRAG - Checklist de validacion")
    canvas.setFont("Helvetica", 12)
    canvas.drawString(MARGIN, PAGE_HEIGHT - 82, f"Benchmark manual de {total} preguntas")
    canvas.setFillColor(HexColor("#20262C"))
    canvas.setFont("Helvetica", 10)
    intro = (
        "Use la app en modo Respuesta verificada. Compare estado, contenido minimo y fuentes. "
        "Marque PASS solo si el caso completo cumple; use FAIL ante cualquier diferencia "
        "y detallela."
    )
    _lines(canvas, intro, MARGIN, PAGE_HEIGHT - 160, PAGE_WIDTH - 2 * MARGIN, 10)
    labels = [
        ("Tester", "tester"),
        ("Fecha", "test_date"),
        ("Commit", "commit"),
        ("Modelo/proveedor", "model"),
    ]
    y = PAGE_HEIGHT - 215
    for label, name in labels:
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN, y + 6, label)
        form.textfield(
            name=name,
            x=MARGIN + 110,
            y=y,
            width=360,
            height=20,
            borderWidth=1,
            borderColor=HexColor("#8A959F"),
            fillColor=HexColor("#FFFFFF"),
            fontName="Helvetica",
            fontSize=9,
        )
        y -= 38
    canvas.setFillColor(PALE)
    canvas.roundRect(MARGIN, 48, PAGE_WIDTH - 2 * MARGIN, 115, 6, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(MARGIN + 12, 142, "Alcance de Playwright")
    canvas.setFillColor(HexColor("#20262C"))
    canvas.setFont("Helvetica", 9)
    note = (
        "La automatizacion registra estado observado, tiempo y texto visible. No reemplaza la "
        "revision humana del contenido agronomico ni de la pertinencia de las citas. Guarde una "
        "copia completada "
        "para adjuntarla como evidencia de testing."
    )
    _lines(canvas, note, MARGIN + 12, 124, PAGE_WIDTH - 2 * MARGIN - 24, 9)


def build_checklist(benchmark_path: Path, output_path: Path) -> None:
    cases = load_benchmark(benchmark_path)
    if len(cases) != 60:
        raise ValueError(f"Expected 60 benchmark cases, found {len(cases)}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(output_path), pagesize=landscape(A4), pageCompression=1)
    canvas.setTitle("AgroRAG - Checklist benchmark 60")
    form = canvas.acroForm
    _cover(canvas, form, len(cases))
    canvas.showPage()
    for index in range(0, len(cases), 2):
        _draw_case(canvas, form, cases[index], index + 1, PAGE_HEIGHT - 22)
        _draw_case(canvas, form, cases[index + 1], index + 2, PAGE_HEIGHT - 278)
        canvas.setFillColor(GRAY)
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 12, f"Pagina {index // 2 + 2} de 31")
        canvas.showPage()
    canvas.save()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark", type=Path, default=Path("data/evaluation/benchmark-60-draft.jsonl")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("output/pdf/agro-rag-benchmark-checklist.pdf")
    )
    args = parser.parse_args()
    build_checklist(args.benchmark, args.output)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
