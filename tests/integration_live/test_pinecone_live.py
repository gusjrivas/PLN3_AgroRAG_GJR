from pathlib import Path

import pytest

from agro_rag.application.retrieval_pipeline import IndexIdentity
from agro_rag.bootstrap.settings import Settings
from agro_rag.evaluation.retrieval import load_cases
from agro_rag.infrastructure.corpus import load_catalogue
from agro_rag.infrastructure.pinecone import E5Embedder, PineconeVectorRanker, connect_pinecone

pytestmark = pytest.mark.integration_live


def test_versioned_pinecone_namespace_matches_manifest_and_dev_qrels() -> None:
    settings = Settings()
    if settings.pinecone_api_key is None:
        pytest.skip("PINECONE_API_KEY no configurada")
    if not settings.pinecone_namespace:
        pytest.fail("PINECONE_NAMESPACE debe identificar el namespace aislado ya indexado")

    catalogue = load_catalogue(settings.catalogue_path)
    dataset = load_cases(Path("data/evaluation/retrieval-dev-draft.jsonl"), catalogue)
    embedder = E5Embedder.load(
        model_name=settings.embedding_model,
        revision=settings.embedding_revision,
        local_files_only=True,
    )
    expected = IndexIdentity(
        catalogue.version,
        embedder.model_name,
        embedder.revision,
        embedder.dimension,
    )
    handle = connect_pinecone(
        api_key=settings.pinecone_api_key.get_secret_value(),
        index_name=settings.pinecone_index,
        timeout=settings.pinecone_timeout,
    )
    try:
        ranker = PineconeVectorRanker.from_index(
            index=handle.index,
            namespace=settings.pinecone_namespace,
            embedder=embedder,
            expected_identity=expected,
            top_k=5,
        )
        for case in dataset.cases:
            returned = {row.evidence_id for row in ranker.rank(case.question, case.crop)}
            assert returned & case.relevant_evidence_ids
    finally:
        handle.close()
