from typing import Any, cast

import pytest

from agro_rag.application.retrieval_pipeline import IndexIdentity, ScoredId
from agro_rag.bootstrap.settings import Settings
from agro_rag.domain.evidence import Catalogue, Evidence


def evidence() -> Evidence:
    return Evidence(
        "abc",
        "v1",
        "S",
        "Manual",
        "2008",
        "https://example.org/doc.pdf",
        3,
        "1",
        "Riego",
        "tomato",
        "Humedad constante",
        "Humedad constante",
        0,
        17,
    )


class ForbiddenFactory:
    def __call__(self, **kwargs: Any) -> Any:
        raise AssertionError("BM25 must not initialize semantic providers")


def test_bm25_runtime_does_not_initialize_semantic_providers() -> None:
    from agro_rag.bootstrap.retrieval import RetrievalFactories, build_retrieval_runtime

    forbidden = ForbiddenFactory()
    runtime = build_retrieval_runtime(
        Settings(retrieval_mode="bm25"),
        Catalogue("v1", (evidence(),)),
        factories=RetrievalFactories(
            connect_pinecone=forbidden,
            load_embedder=forbidden,
            load_reranker=forbidden,
            load_token_counter=forbidden,
        ),
    )

    assert runtime.mode == "bm25"
    assert runtime.retriever.search("humedad", "tomato")[0].evidence_id == "abc"
    runtime.close()


@pytest.mark.parametrize("mode", ["vector", "hybrid", "hybrid_rerank"])
def test_semantic_runtime_requires_explicit_secret_and_tokenizer(mode: str) -> None:
    from agro_rag.bootstrap.retrieval import build_retrieval_runtime

    config = Settings(retrieval_mode=mode)

    with pytest.raises(ValueError, match="semántica incompleta"):
        build_retrieval_runtime(config, Catalogue("v1", (evidence(),)))


def test_hybrid_runtime_composes_verified_providers_and_closes_resources() -> None:
    from agro_rag.bootstrap.retrieval import RetrievalFactories, build_retrieval_runtime

    calls: dict[str, Any] = {}
    expected = IndexIdentity("v1", "e5", "revision-1", 3)

    class Embedder:
        model_name = "e5"
        revision = "revision-1"
        dimension = 3

        def embed_query(self, text: str) -> tuple[float, ...]:
            calls["embedded"] = text
            return (1.0, 0.0, 0.0)

    class Index:
        def fetch(self, *, ids: list[str], namespace: str) -> dict[str, Any]:
            calls["identity_namespace"] = namespace
            return {
                "vectors": {
                    "__agro_index_manifest__": {
                        "metadata": {
                            "kind": "manifest",
                            "corpus_version": expected.corpus_version,
                            "model": expected.model,
                            "revision": expected.revision,
                            "dimension": expected.dimension,
                        }
                    }
                }
            }

        def query(self, **kwargs: Any) -> dict[str, Any]:
            calls["query"] = kwargs
            return {"matches": [{"id": "abc", "score": 0.9}]}

    class Handle:
        index = Index()
        closed = False

        def close(self) -> None:
            self.closed = True

    handle = Handle()

    class Counter:
        def count(self, text: str) -> int:
            calls["counted"] = text
            return 10

    class Reranker:
        def rank(self, question: str, candidates: tuple[Evidence, ...]) -> tuple[ScoredId, ...]:
            calls["reranked"] = (question, candidates)
            return (ScoredId("abc", 1.0),)

    def connect(**kwargs: Any) -> Any:
        calls["connect"] = kwargs
        return handle

    def load_embedder(**kwargs: Any) -> Any:
        calls["embedder"] = kwargs
        return Embedder()

    def load_counter(**kwargs: Any) -> Any:
        calls["tokenizer"] = kwargs
        return Counter()

    def load_reranker(**kwargs: Any) -> Any:
        calls["reranker"] = kwargs
        return Reranker()

    config = Settings(
        retrieval_mode="hybrid_rerank",
        pinecone_api_key="test-secret",
        pinecone_index="agro-test",
        pinecone_namespace="corpus-v1",
        embedding_model="e5",
        embedding_revision="revision-1",
        reranker_model="reranker",
        reranker_revision="revision-r",
        retrieval_tokenizer_model="tokenizer",
        retrieval_tokenizer_revision="revision-t",
        semantic_local_files_only=True,
    )
    runtime = build_retrieval_runtime(
        config,
        Catalogue("v1", (evidence(),)),
        factories=RetrievalFactories(
            connect_pinecone=connect,
            load_embedder=load_embedder,
            load_reranker=load_reranker,
            load_token_counter=load_counter,
        ),
    )

    assert runtime.mode == "hybrid_rerank"
    assert runtime.retriever.search("humedad", "tomato")[0].evidence_id == "abc"
    assert calls["identity_namespace"] == "corpus-v1"
    assert calls["query"]["namespace"] == "corpus-v1"
    assert calls["connect"]["api_key"] == "test-secret"
    assert calls["tokenizer"]["local_files_only"] is True
    assert calls["reranked"][0] == "humedad"

    runtime.close()
    assert handle.closed is True


def test_semantic_runtime_closes_pinecone_when_later_provider_fails() -> None:
    from agro_rag.bootstrap.retrieval import RetrievalFactories, build_retrieval_runtime

    class Handle:
        index = cast(Any, object())
        closed = False

        def close(self) -> None:
            self.closed = True

    handle = Handle()

    class Embedder:
        model_name = "e5"
        revision = "revision-1"
        dimension = 3

    def connect(**kwargs: Any) -> Any:
        return handle

    def load_embedder(**kwargs: Any) -> Any:
        return Embedder()

    def fail(**kwargs: Any) -> Any:
        raise RuntimeError("tokenizer unavailable")

    config = Settings(
        retrieval_mode="vector",
        pinecone_api_key="test-secret",
        embedding_model="e5",
        embedding_revision="revision-1",
        retrieval_tokenizer_model="tokenizer",
        retrieval_tokenizer_revision="revision-t",
    )

    with pytest.raises(RuntimeError, match="tokenizer unavailable"):
        build_retrieval_runtime(
            config,
            Catalogue("v1", (evidence(),)),
            factories=RetrievalFactories(
                connect_pinecone=connect,
                load_embedder=load_embedder,
                load_reranker=fail,
                load_token_counter=fail,
            ),
        )

    assert handle.closed is True
