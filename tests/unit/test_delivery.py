from pathlib import Path

import pdfplumber
import pytest

ROOT = Path(__file__).parents[2]


def test_del_01_reproduccion_validates_required_package_and_commands(capsys):
    from agro_rag.bootstrap.cli import main
    from agro_rag.evaluation.delivery import validate_delivery

    result = validate_delivery(ROOT)

    assert result.artifact_count >= 7
    assert all(len(artifact.sha256) == 64 for artifact in result.artifacts)
    assert result.commands == (
        "uv sync --frozen",
        "uv run agro-rag download",
        "uv run agro-rag ingest",
        "uv run uvicorn",
        "uv run streamlit",
        "uv run pytest",
    )
    assert main(["verify-delivery", "--root", str(ROOT)]) == 0
    output = capsys.readouterr().out
    assert '"artifact_count": 8' in output
    assert "PINECONE_API_KEY" not in output


def test_del_01_reproduccion_rejects_incomplete_or_placeholder_package(tmp_path):
    from agro_rag.evaluation.delivery import validate_delivery

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "run-local.md").write_text("TODO", encoding="utf-8")

    with pytest.raises(ValueError, match="faltantes|placeholder"):
        validate_delivery(tmp_path)


def test_del_01_informe_builds_a_readable_pdf(tmp_path):
    from scripts.build_report import build_pdf

    target = tmp_path / "agro-rag-report.pdf"
    build_pdf(ROOT / "docs" / "report.md", target)

    with pdfplumber.open(target) as document:
        text = "\n".join(page.extract_text() or "" for page in document.pages)
        assert len(document.pages) >= 6
    assert "AgroRAG" in text
    assert "Resultados y evidencia" in text
    assert "Declaración de asistencia de IA" in text
    assert "pending_human" in text
