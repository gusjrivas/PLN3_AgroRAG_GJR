import json
import sqlite3
import zipfile
from dataclasses import asdict
from pathlib import Path

import pytest

from agro_rag.domain.evidence import Evidence


def _catalogue(path: Path, marker: str = "a") -> str:
    version = marker * 64
    path.mkdir(parents=True)
    item = Evidence(
        evidence_id=marker * 64,
        corpus_version=version,
        source_id="TEST",
        title="Manual",
        edition="2026",
        source_url="https://example.org/manual.pdf",
        pdf_page=1,
        printed_page="1",
        section="Riego",
        crop="tomato",
        text="Riego verificable",
        original_text="Riego verificable",
        start=0,
        end=18,
    )
    with sqlite3.connect(path / f"{version}.sqlite") as database:
        database.execute("CREATE TABLE evidence (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        database.execute(
            "INSERT INTO evidence VALUES (?, ?)",
            (item.evidence_id, json.dumps(asdict(item))),
        )
    (path / "active.json").write_text(
        json.dumps({"version": version, "count": 1, "mode": "catalogue_preview"}),
        encoding="utf-8",
    )
    return version


def test_ops_v2_backup_restore_preserves_snapshots_and_activates_last(tmp_path: Path) -> None:
    from agro_rag.infrastructure.backup import backup_catalogue, restore_catalogue
    from agro_rag.infrastructure.corpus import load_catalogue

    source = tmp_path / "source"
    version = _catalogue(source)
    archive = tmp_path / "backup" / "catalogue.zip"

    metadata = backup_catalogue(
        source,
        archive,
        release="2.0.0-rc.1",
        commit="b" * 40,
        image="registry.example/api@sha256:" + "c" * 64,
    )
    assert metadata.corpus_version == version
    assert metadata.release == "2.0.0-rc.1"
    assert metadata.image.endswith("c" * 64)

    target = tmp_path / "target"
    previous = _catalogue(target, marker="c")
    restored = restore_catalogue(archive, target)

    assert restored.version == version
    assert (target / f"{previous}.sqlite").is_file()
    assert load_catalogue(target) == restored


def test_ops_v2_restore_rejects_tampering_before_changing_active_pointer(tmp_path: Path) -> None:
    from agro_rag.infrastructure.backup import backup_catalogue, restore_catalogue

    source = tmp_path / "source"
    version = _catalogue(source)
    archive = tmp_path / "catalogue.zip"
    backup_catalogue(
        source,
        archive,
        release="2.0.0",
        commit="d" * 40,
        image="registry.example/api@sha256:" + "e" * 64,
    )
    corrupt = tmp_path / "corrupt.zip"
    with zipfile.ZipFile(archive) as original, zipfile.ZipFile(corrupt, "w") as changed:
        for name in original.namelist():
            payload = original.read(name)
            if name == f"{version}.sqlite":
                payload += b"tampered"
            changed.writestr(name, payload)

    target = tmp_path / "target"
    previous = _catalogue(target, marker="e")
    active_before = (target / "active.json").read_bytes()
    with pytest.raises(ValueError, match="integridad"):
        restore_catalogue(corrupt, target)

    assert (target / "active.json").read_bytes() == active_before
    assert (target / f"{previous}.sqlite").is_file()


def test_ops_v2_backup_cli_emits_sanitized_metadata(tmp_path: Path, capsys) -> None:
    from agro_rag.bootstrap.cli import main

    source = tmp_path / "source"
    version = _catalogue(source)
    archive = tmp_path / "catalogue.zip"

    assert (
        main(
            [
                "backup-catalogue",
                "--catalogue",
                str(source),
                "--destination",
                str(archive),
                "--release",
                "2.0.0",
                "--commit",
                "f" * 40,
                "--image",
                "registry.example/api@sha256:" + "a" * 64,
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output == {"archive": str(archive), "corpus_version": version, "evidence_count": 1}
