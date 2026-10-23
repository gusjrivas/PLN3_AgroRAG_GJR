"""Administrative offline ingestion; never exposed as a public URL endpoint."""

import argparse
import json
from pathlib import Path

import httpx

from agro_rag.bootstrap.settings import Settings
from agro_rag.infrastructure.corpus import Manifest, build_catalogue, load_catalogue
from agro_rag.infrastructure.download import download_file
from agro_rag.infrastructure.pinecone import E5Embedder, connect_pinecone, index_catalogue


def main(argv: list[str] | None = None, *, settings: Settings | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgroRAG: catálogo local curado")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("manifest", type=Path)
    ingest.add_argument("--output", type=Path, default=Path("data/processed/catalogue"))
    download = commands.add_parser("download")
    download.add_argument("manifest", type=Path)
    pinecone = commands.add_parser("index-pinecone")
    pinecone.add_argument("--create-index", action="store_true")
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
    if args.command == "index-pinecone":
        config = settings or Settings()
        if config.pinecone_api_key is None or not config.pinecone_index:
            raise ValueError("Configuración de Pinecone incompleta")
        catalogue = load_catalogue(config.catalogue_path)
        namespace = config.pinecone_namespace or f"corpus-{catalogue.version[:16]}"
        embedder = None
        if args.create_index:
            embedder = E5Embedder.load(
                model_name=config.embedding_model,
                revision=config.embedding_revision,
            )
            handle = connect_pinecone(
                api_key=config.pinecone_api_key.get_secret_value(),
                index_name=config.pinecone_index,
                timeout=config.pinecone_timeout,
                create_if_missing=True,
                dimension=embedder.dimension,
                metric=config.pinecone_metric,
                cloud=config.pinecone_cloud,
                region=config.pinecone_region,
            )
        else:
            handle = connect_pinecone(
                api_key=config.pinecone_api_key.get_secret_value(),
                index_name=config.pinecone_index,
                timeout=config.pinecone_timeout,
            )
        try:
            if embedder is None:
                embedder = E5Embedder.load(
                    model_name=config.embedding_model,
                    revision=config.embedding_revision,
                )
            identity = index_catalogue(
                index=handle.index,
                namespace=namespace,
                catalogue=catalogue,
                embedder=embedder,
                batch_size=config.pinecone_batch_size,
            )
        finally:
            handle.close()
        print(
            json.dumps(
                {
                    "corpus_version": identity.corpus_version,
                    "model": identity.model,
                    "revision": identity.revision,
                    "dimension": identity.dimension,
                    "index": config.pinecone_index,
                    "namespace": namespace,
                }
            )
        )
        return 0
    catalogue = build_catalogue(args.manifest, args.output)
    print(json.dumps({"version": catalogue.version, "evidence_count": len(catalogue.evidence)}))
    return 0
