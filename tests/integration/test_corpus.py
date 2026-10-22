import hashlib
import json
from pathlib import Path

import pytest
from reportlab.pdfgen.canvas import Canvas


def fixture_source(tmp_path: Path, *, blank=False):
    path = tmp_path / "source.pdf"
    pdf = Canvas(str(path))
    if not blank:
        pdf.drawString(50, 750, "Lechuga: humedad constante. Evitar excesos de agua.")
    pdf.showPage()
    pdf.save()
    source = {
        "source_id": "TEST",
        "title": "Manual de prueba",
        "authors": ["Autor"],
        "institution": "Test",
        "edition": "2026",
        "language": "es",
        "source_url": "https://example.org/manual.pdf",
        "access_date": "2026-10-22",
        "local_file": "source.pdf",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rights_status": "synthetic_test",
        "review_status": "reviewed",
        "pages": [{"pdf_page": 1, "printed_page": "7", "section": "Riego", "crop": "lettuce"}],
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"sources": [source]}))
    return manifest, source


def build(manifest, output):
    from agro_rag.infrastructure.corpus import build_catalogue

    return build_catalogue(manifest, output)


def test_real_pdf_provenance_and_idempotency(tmp_path):
    manifest, source = fixture_source(tmp_path)
    first = build(manifest, tmp_path / "catalogues")
    again = build(manifest, tmp_path / "catalogues")
    assert first == again
    assert len(first.evidence) == 1
    evidence = first.evidence[0]
    assert evidence.pdf_page == 1 and evidence.printed_page == "7"
    assert evidence.source_id == "TEST"
    assert "humedad constante" in evidence.text
    assert evidence.text == evidence.original_text[evidence.start : evidence.end]
    assert evidence.corpus_version == first.version
    assert (tmp_path / "catalogues" / "active.json").exists()


@pytest.mark.parametrize("failure", ["hash", "rights", "review", "pages", "empty", "duplicate"])
def test_invalid_admission_preserves_previous_catalogue(tmp_path, failure):
    manifest, source = fixture_source(tmp_path)
    output = tmp_path / "catalogues"
    first = build(manifest, output)
    previous = (output / "active.json").read_bytes()
    if failure == "hash":
        source["sha256"] = "0" * 64
    if failure == "rights":
        source["rights_status"] = ""
    if failure == "review":
        source["review_status"] = "pending"
    if failure == "pages":
        source["pages"][0]["pdf_page"] = 99
    sources = [source]
    if failure == "empty":
        sources = []
    if failure == "duplicate":
        sources.append(source)
    manifest.write_text(json.dumps({"sources": sources}))
    with pytest.raises(ValueError):
        build(manifest, output)
    assert (output / "active.json").read_bytes() == previous
    assert (output / (first.version + ".sqlite")).is_file()


def test_blank_pdf_is_rejected(tmp_path):
    manifest, _ = fixture_source(tmp_path, blank=True)
    with pytest.raises(ValueError, match="texto"):
        build(manifest, tmp_path / "catalogues")
    assert not (tmp_path / "catalogues" / "active.json").exists()


def test_metadata_changes_create_new_version(tmp_path):
    manifest, source = fixture_source(tmp_path)
    first = build(manifest, tmp_path / "catalogues")
    source["edition"] = "2026 corrected"
    manifest.write_text(json.dumps({"sources": [source]}))
    second = build(manifest, tmp_path / "catalogues")
    assert second.version != first.version
    assert second.evidence[0].evidence_id != first.evidence[0].evidence_id


def test_table_rows_preserve_headers_and_only_selected_crops(tmp_path):
    manifest, source = fixture_source(tmp_path)
    source["pages"][0]["table"] = {
        "headers": ["Cultivo", "Periodo critico"],
        "rows": [["Lechuga", "Humedad constante"]],
        "reviewed": True,
    }
    manifest.write_text(json.dumps({"sources": [source]}))
    item = build(manifest, tmp_path / "catalogues").evidence[0]
    assert "Cultivo: Lechuga" in item.text
    assert "Periodo critico: Humedad constante" in item.text
    assert item.transformation == "reviewed_table_rows"
    source["pages"][0]["table"]["reviewed"] = False
    manifest.write_text(json.dumps({"sources": [source]}))
    with pytest.raises(ValueError):
        build(manifest, tmp_path / "catalogues")


def test_corrupt_existing_snapshot_is_never_activated(tmp_path):
    manifest, _ = fixture_source(tmp_path)
    output = tmp_path / "catalogues"
    first = build(manifest, output)
    (output / (first.version + ".sqlite")).write_bytes(b"broken")
    with pytest.raises(ValueError, match="Catálogo"):
        build(manifest, output)


def test_cli_ingest_and_read_snapshot(tmp_path, capsys):
    from agro_rag.bootstrap.cli import main
    from agro_rag.infrastructure.corpus import load_catalogue

    manifest, _ = fixture_source(tmp_path)
    output = tmp_path / "catalogues"
    assert main(["ingest", str(manifest), "--output", str(output)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert load_catalogue(output).version == result["version"]
    assert result["evidence_count"] == 1


def test_long_page_chunks_preserve_verbatim_offsets(tmp_path):
    from agro_rag.infrastructure.corpus import Page, excerpts

    text = " ".join(f"palabra{i}" for i in range(450))
    page = Page(pdf_page=1, printed_page="1", section="Riego")
    parts = excerpts(text, page)
    assert len(parts) == 3
    assert all(t == text[start:end] for t, start, end, _ in parts)
    assert parts[-1][0].endswith("palabra449")


def test_download_cli_uses_existing_verified_files(tmp_path, capsys):
    from agro_rag.bootstrap.cli import main

    manifest, source = fixture_source(tmp_path)
    source["source_url"] = "https://www.argentina.gob.ar/a.pdf"
    manifest.write_text(json.dumps({"sources": [source]}))
    assert main(["download", str(manifest)]) == 0
    assert json.loads(capsys.readouterr().out) == {"sources": 1}
