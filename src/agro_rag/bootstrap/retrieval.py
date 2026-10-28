"""Runtime composition for lexical and explicitly enabled semantic retrieval."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agro_rag.application.retrieval import Retriever
from agro_rag.application.retrieval_pipeline import IndexIdentity, Mode, RetrievalPipeline
from agro_rag.bootstrap.settings import Settings
from agro_rag.domain.evidence import Catalogue
from agro_rag.infrastructure.pinecone import (
    E5Embedder,
    PineconeVectorRanker,
    connect_pinecone,
)
from agro_rag.infrastructure.reranker import CrossEncoderReranker
from agro_rag.infrastructure.retrieval import LexicalRetriever
from agro_rag.infrastructure.tokenizer import TransformersTokenCounter


@dataclass(frozen=True)
class RetrievalFactories:
    connect_pinecone: Callable[..., Any] = connect_pinecone
    load_embedder: Callable[..., Any] = E5Embedder.load
    load_reranker: Callable[..., Any] = CrossEncoderReranker.load
    load_token_counter: Callable[..., Any] = TransformersTokenCounter.load


@dataclass
class RetrievalRuntime:
    retriever: Retriever
    mode: Mode
    _close: Callable[[], None] | None = None

    def close(self) -> None:
        if self._close is not None:
            self._close()
            self._close = None


def _validate_semantic_config(config: Settings) -> None:
    if (
        config.pinecone_api_key is None
        or not config.pinecone_index
        or not config.embedding_model
        or not config.embedding_revision
        or not config.retrieval_tokenizer_model
        or not config.retrieval_tokenizer_revision
        or (config.retrieval_mode == "hybrid_rerank" and not config.reranker_model)
        or (config.retrieval_mode == "hybrid_rerank" and not config.reranker_revision)
    ):
        raise ValueError("Configuración semántica incompleta")


def build_retrieval_runtime(
    config: Settings,
    catalogue: Catalogue,
    *,
    factories: RetrievalFactories | None = None,
) -> RetrievalRuntime:
    lexical = LexicalRetriever(catalogue)
    mode = config.retrieval_mode
    if mode == "bm25":
        return RetrievalRuntime(lexical, mode)

    _validate_semantic_config(config)
    providers = factories or RetrievalFactories()
    embedder = providers.load_embedder(
        model_name=config.embedding_model,
        revision=config.embedding_revision,
        local_files_only=config.semantic_local_files_only,
    )
    expected = IndexIdentity(
        catalogue.version,
        config.embedding_model,
        config.embedding_revision,
        embedder.dimension,
    )
    assert config.pinecone_api_key is not None
    handle = providers.connect_pinecone(
        api_key=config.pinecone_api_key.get_secret_value(),
        index_name=config.pinecone_index,
        timeout=config.pinecone_timeout,
    )
    try:
        token_counter = providers.load_token_counter(
            model_name=config.retrieval_tokenizer_model,
            revision=config.retrieval_tokenizer_revision,
            local_files_only=config.semantic_local_files_only,
        )
        namespace = config.pinecone_namespace or f"corpus-{catalogue.version[:16]}"
        vector = PineconeVectorRanker.from_index(
            index=handle.index,
            namespace=namespace,
            embedder=embedder,
            expected_identity=expected,
            top_k=config.retrieval_candidate_limit,
        )
        reranker = None
        if mode == "hybrid_rerank":
            reranker = providers.load_reranker(
                model_name=config.reranker_model,
                revision=config.reranker_revision,
                local_files_only=config.semantic_local_files_only,
            )
        pipeline = RetrievalPipeline(
            catalogue=catalogue,
            lexical=lexical,
            vector=vector,
            expected_index=expected,
            actual_index=vector.identity,
            reranker=reranker,
            token_counter=token_counter,
            token_budget=config.retrieval_token_budget,
            source_cap=config.retrieval_source_cap,
            max_items=config.retrieval_max_items,
            candidate_limit=config.retrieval_candidate_limit,
            mode=mode,
        )
    except Exception:
        handle.close()
        raise
    return RetrievalRuntime(pipeline, mode, handle.close)
