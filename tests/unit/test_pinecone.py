from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import SecretStr
from test_retrieval import evidence

from agro_rag.application.retrieval_pipeline import IndexIdentity
from agro_rag.bootstrap.settings import Settings
from agro_rag.domain.evidence import Catalogue


class FakeModel:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict[str, object]]] = []

    def get_sentence_embedding_dimension(self) -> int:
        return 3

    def encode(self, texts, **kwargs):
        self.calls.append((list(texts), kwargs))
        return np.asarray([[float(i + 1), 0.5, -0.5] for i, _ in enumerate(texts)])


class FakeIndex:
    def __init__(self, manifest: IndexIdentity | None = None, vector_count: int = 0) -> None:
        self.manifest = manifest
        self.vector_count = vector_count
        self.query_kwargs: dict[str, object] | None = None
        self.upserts: list[dict[str, object]] = []
        self.stored: dict[str, dict[str, object]] = {}

    def fetch(self, *, ids, namespace):
        vectors = {item_id: self.stored[item_id] for item_id in ids if item_id in self.stored}
        if self.manifest is not None:
            vectors["__agro_index_manifest__"] = {
                "metadata": {
                    "kind": "manifest",
                    "corpus_version": self.manifest.corpus_version,
                    "model": self.manifest.model,
                    "revision": self.manifest.revision,
                    "dimension": self.manifest.dimension,
                }
            }
        return {"vectors": vectors}

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return SimpleNamespace(
            matches=(
                SimpleNamespace(id="b", score=0.7),
                SimpleNamespace(id="a", score=0.9),
            )
        )

    def describe_index_stats(self):
        count = self.vector_count or len(self.stored)
        namespaces = {"agro-v1": SimpleNamespace(vector_count=count)} if count else {}
        return SimpleNamespace(dimension=3, namespaces=namespaces)

    def upsert(self, **kwargs):
        self.upserts.append(kwargs)
        for vector in kwargs["vectors"]:
            self.stored[vector["id"]] = vector


def build_embedder():
    from agro_rag.infrastructure.pinecone import E5Embedder

    return E5Embedder(
        FakeModel(),
        model_name="intfloat/multilingual-e5-small",
        revision="model-revision",
    )


def identity() -> IndexIdentity:
    return IndexIdentity(
        "v1",
        "intfloat/multilingual-e5-small",
        "model-revision",
        3,
    )


def test_ret_02_e5_uses_query_and_passage_prefixes_without_truncation() -> None:
    embedder = build_embedder()

    assert embedder.embed_query("agua") == (1.0, 0.5, -0.5)
    assert embedder.embed_passages(("riego", "humedad")) == (
        (1.0, 0.5, -0.5),
        (2.0, 0.5, -0.5),
    )

    assert embedder.model.calls == [
        (
            ["query: agua"],
            {"convert_to_numpy": True, "normalize_embeddings": True},
        ),
        (
            ["passage: riego", "passage: humedad"],
            {"convert_to_numpy": True, "normalize_embeddings": True},
        ),
    ]
    assert embedder.dimension == 3


def test_e5_prefers_current_embedding_dimension_api() -> None:
    from agro_rag.infrastructure.pinecone import E5Embedder

    class ModernModel(FakeModel):
        def get_embedding_dimension(self) -> int:
            return 3

        def get_sentence_embedding_dimension(self) -> int:
            raise AssertionError("deprecated API must not be called")

    embedder = E5Embedder(ModernModel(), model_name="e5", revision="revision")

    assert embedder.dimension == 3


def test_vector_ranker_reads_manifest_and_queries_only_compatible_namespace() -> None:
    from agro_rag.infrastructure.pinecone import PineconeVectorRanker

    index = FakeIndex(identity())
    ranker = PineconeVectorRanker.from_index(
        index=index,
        namespace="agro-v1",
        embedder=build_embedder(),
        expected_identity=identity(),
        top_k=20,
    )

    rows = ranker.rank("agua", "tomato")

    assert [(row.evidence_id, row.score) for row in rows] == [("b", 0.7), ("a", 0.9)]
    assert ranker.corpus_version == "v1"
    assert ranker.identity == identity()
    assert index.query_kwargs == {
        "vector": [1.0, 0.5, -0.5],
        "top_k": 20,
        "include_metadata": False,
        "namespace": "agro-v1",
        "filter": {
            "$and": [
                {"kind": {"$eq": "chunk"}},
                {"corpus_version": {"$eq": "v1"}},
                {
                    "$or": [
                        {"crop": {"$eq": "tomato"}},
                        {"crop": {"$exists": False}},
                    ]
                },
            ]
        },
    }


@pytest.mark.parametrize(
    "actual",
    [None, replace(identity(), model="other"), replace(identity(), dimension=4)],
)
def test_vector_ranker_rejects_missing_or_incompatible_manifest(actual) -> None:
    from agro_rag.infrastructure.pinecone import PineconeVectorRanker

    with pytest.raises(ValueError, match="identidad"):
        PineconeVectorRanker.from_index(
            index=FakeIndex(actual),
            namespace="agro-v1",
            embedder=build_embedder(),
            expected_identity=identity(),
        )


def test_catalogue_indexing_uses_evidence_ids_and_publishes_manifest_last() -> None:
    from agro_rag.infrastructure.pinecone import index_catalogue

    index = FakeIndex()
    catalogue = Catalogue(
        "v1",
        (
            evidence("a", "riego", crop="tomato"),
            evidence("b", "humedad", source="B", crop=None),
            evidence("c", "suelo", source="C", crop="lettuce"),
        ),
    )

    result = index_catalogue(
        index=index,
        namespace="agro-v1",
        catalogue=catalogue,
        embedder=build_embedder(),
        batch_size=2,
    )

    assert result == identity()
    assert [len(call["vectors"]) for call in index.upserts] == [2, 1, 1]
    rows = [row for call in index.upserts[:-1] for row in call["vectors"]]
    assert [row["id"] for row in rows] == ["a", "b", "c"]
    assert all("text" not in row["metadata"] for row in rows)
    assert rows[0]["metadata"] == {
        "kind": "chunk",
        "evidence_id": "a",
        "corpus_version": "v1",
        "crop": "tomato",
    }
    assert "crop" not in rows[1]["metadata"]
    manifest = index.upserts[-1]["vectors"][0]
    assert manifest["id"] == "__agro_index_manifest__"
    assert manifest["values"] == [1.0, 0.0, 0.0]
    assert manifest["metadata"]["kind"] == "manifest"


def test_catalogue_indexing_refuses_to_overwrite_existing_namespace() -> None:
    from agro_rag.infrastructure.pinecone import index_catalogue

    index = FakeIndex(vector_count=1)
    with pytest.raises(ValueError, match="namespace"):
        index_catalogue(
            index=index,
            namespace="agro-v1",
            catalogue=Catalogue("v1", (evidence("a", "riego"),)),
            embedder=build_embedder(),
        )
    assert index.upserts == []


def test_catalogue_indexing_does_not_publish_manifest_until_all_ids_are_visible() -> None:
    from agro_rag.infrastructure.pinecone import MANIFEST_ID, index_catalogue

    class EventuallyInvisibleIndex(FakeIndex):
        def fetch(self, *, ids, namespace):
            return {"vectors": {}}

    index = EventuallyInvisibleIndex()
    with pytest.raises(TimeoutError, match="verificar"):
        index_catalogue(
            index=index,
            namespace="agro-v1",
            catalogue=Catalogue("v1", (evidence("a", "riego"),)),
            embedder=build_embedder(),
            verification_timeout=0,
        )

    assert all(vector["id"] != MANIFEST_ID for call in index.upserts for vector in call["vectors"])


def test_administrative_cli_indexes_active_catalogue_and_closes_clients(
    monkeypatch, capsys
) -> None:
    from agro_rag.bootstrap import cli

    catalogue = Catalogue("v1", (evidence("a", "riego"),))
    embedder = build_embedder()
    handle = SimpleNamespace(index=FakeIndex(), closed=False)
    handle.close = lambda: setattr(handle, "closed", True)
    calls: dict[str, object] = {}

    monkeypatch.setattr(cli, "load_catalogue", lambda path: catalogue)
    monkeypatch.setattr(cli, "E5Embedder", SimpleNamespace(load=lambda **kwargs: embedder))
    monkeypatch.setattr(
        cli,
        "connect_pinecone",
        lambda **kwargs: calls.update(connection=kwargs) or handle,
    )

    def fake_index_catalogue(**kwargs):
        calls["indexing"] = kwargs
        return identity()

    monkeypatch.setattr(cli, "index_catalogue", fake_index_catalogue)
    settings = Settings(
        pinecone_api_key=SecretStr("test-pinecone-key"),
        pinecone_index="agro-rag",
        pinecone_namespace="agro-v1",
        catalogue_path="catalogue",
    )

    assert cli.main(["index-pinecone"], settings=settings) == 0

    assert calls["connection"] == {
        "api_key": "test-pinecone-key",
        "index_name": "agro-rag",
        "timeout": 30.0,
    }
    assert calls["indexing"] == {
        "index": handle.index,
        "namespace": "agro-v1",
        "catalogue": catalogue,
        "embedder": embedder,
        "batch_size": 100,
    }
    assert handle.closed is True
    output = capsys.readouterr().out
    assert '"corpus_version": "v1"' in output
    assert "test-pinecone-key" not in output


def test_administrative_cli_requires_complete_pinecone_configuration(monkeypatch, tmp_path) -> None:
    from agro_rag.bootstrap import cli

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    monkeypatch.setattr(
        cli,
        "connect_pinecone",
        lambda **kwargs: pytest.fail("must fail before connecting"),
        raising=False,
    )
    with pytest.raises(ValueError, match="Pinecone"):
        cli.main(["index-pinecone"], settings=Settings())


def test_administrative_cli_checks_existing_index_before_loading_model(monkeypatch) -> None:
    from agro_rag.bootstrap import cli

    settings = Settings(
        pinecone_api_key=SecretStr("test-pinecone-key"),
        pinecone_index="missing-index",
    )
    monkeypatch.setattr(cli, "load_catalogue", lambda path: Catalogue("v1", (evidence("a", "x"),)))
    monkeypatch.setattr(
        cli,
        "connect_pinecone",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("El índice no existe")),
    )
    monkeypatch.setattr(
        cli,
        "E5Embedder",
        SimpleNamespace(load=lambda **kwargs: pytest.fail("must check index first")),
    )

    with pytest.raises(ValueError, match="no existe"):
        cli.main(["index-pinecone"], settings=settings)


def test_connect_requires_explicit_opt_in_before_creating_index(monkeypatch) -> None:
    from agro_rag.infrastructure import pinecone as adapter

    class Indexes:
        def __init__(self) -> None:
            self.present = False

        def exists(self, name):
            return self.present

    class Client:
        def __init__(self) -> None:
            self.indexes = Indexes()
            self.created = []

        def create_index(self, **kwargs):
            self.created.append(kwargs)
            self.indexes.present = True

        def index(self, name):
            return ("index", name)

    client = Client()
    sdk = SimpleNamespace(
        Pinecone=lambda **kwargs: client,
        ServerlessSpec=lambda **kwargs: kwargs,
    )
    monkeypatch.setattr(adapter, "import_module", lambda name: sdk)

    with pytest.raises(ValueError, match="no existe"):
        adapter.connect_pinecone(api_key="test-key", index_name="agro")
    assert client.created == []

    handle = adapter.connect_pinecone(
        api_key="test-key",
        index_name="agro",
        create_if_missing=True,
        dimension=384,
        metric="cosine",
        cloud="aws",
        region="us-east-1",
    )
    assert handle.index == ("index", "agro")
    assert client.created == [
        {
            "name": "agro",
            "dimension": 384,
            "metric": "cosine",
            "spec": {"cloud": "aws", "region": "us-east-1"},
        }
    ]
