"""Administrative offline ingestion; never exposed as a public URL endpoint."""

import argparse
import json
from pathlib import Path

import httpx

from agro_rag.infrastructure.corpus import Manifest, build_catalogue
from agro_rag.infrastructure.download import download_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgroRAG: catálogo local curado")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("manifest", type=Path)
    ingest.add_argument("--output", type=Path, default=Path("data/processed/catalogue"))
    download = commands.add_parser("download")
    download.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    if args.command == "download":
        manifest = Manifest.model_validate_json(args.manifest.read_text())
        with httpx.Client(timeout=60.0) as client:
            for source in manifest.sources:
                target = (args.manifest.parent / source.local_file).resolve()
                if not target.is_relative_to(args.manifest.parent.resolve()):
                    raise ValueError("Archivo fuera de raíz curada")
                download_file(source.source_url, target, source.sha256, client)
        print(json.dumps({"sources": len(manifest.sources)}))
        return 0
    catalogue = build_catalogue(args.manifest, args.output)
    print(json.dumps({"version": catalogue.version, "evidence_count": len(catalogue.evidence)}))
    return 0
