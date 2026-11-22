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


def test_vector_ranker_uses_safe_structured_context_filters() -> None:
    from agro_rag.application.retrieval import RetrievalFilters
    from agro_rag.infrastructure.pinecone import PineconeVectorRanker

    index = FakeIndex(identity())
    ranker = PineconeVectorRanker.from_index(
        index=index,
        namespace="agro-v1",
        embedder=build_embedder(),
        expected_identity=identity(),
    )

    ranker.rank(
        "agua",
        RetrievalFilters(
            crop="tomato",
            growth_stage="flowering",
            region="ar-mendoza-oasis-norte",
        ),
    )

    assert index.query_kwargs is not None
    assert index.query_kwargs["filter"] == {
        "$and": [
            {"kind": {"$eq": "chunk"}},
            {"corpus_version": {"$eq": "v1"}},
            {
                "$or": [
                    {"crop": {"$eq": "tomato"}},
                    {"crop": {"$exists": False}},
                ]
            },
            {
                "$or": [
                    {"growth_stages": {"$in": ["flowering"]}},
                    {"applicability": {"$eq": "general"}},
                    {"growth_stages": {"$exists": False}},
                ]
            },
            {
                "$or": [
                    {"applicable_regions": {"$in": ["ar-mendoza-oasis-norte"]}},
                    {"applicability": {"$eq": "general"}},
                    {"applicable_regions": {"$exists": False}},
                ]
            },
        ]
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


def test_index_payload_contains_safe_metadata_without_text() -> None:
    from agro_rag.infrastructure.pinecone import index_catalogue

    index = FakeIndex()
    catalogue = Catalogue(
        "v1",
        (
            evidence(
                "a",
                "riego",
                crop="tomato",
                source_type="technical_manual",
                growth_stages=("flowering", "fruit_set"),
                applicable_regions=("ar-mendoza-oasis-norte",),
                applicability="specific",
            ),
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
    forbidden = {
        "text",
        "original_text",
        "source_url",
        "title",
        "pdf_page",
        "printed_page",
        "section",
        "start",
        "end",
    }
    assert all(forbidden.isdisjoint(row["metadata"]) for row in rows)
    assert rows[0]["metadata"] == {
        "kind": "chunk",
        "evidence_id": "a",
        "corpus_version": "v1",
        "crop": "tomato",
        "source_type": "technical_manual",
        "growth_stages": ["flowering", "fruit_set"],
        "applicable_regions": ["ar-mendoza-oasis-norte"],
        "applicability": "specific",
    }
    assert "crop" not in rows[1]["metadata"]
    assert rows[1]["metadata"]["applicability"] == "unknown"
    assert "growth_stages" not in rows[1]["metadata"]
    assert "applicable_regions" not in rows[1]["metadata"]
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


def test_partial_metadata_index_does_not_publish_manifest() -> None:
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


def _embedder_with(encoded):
    from agro_rag.infrastructure.pinecone import E5Embedder

    class Model(FakeModel):
        def encode(self, texts, **kwargs):
            return encoded

    return E5Embedder(Model(), model_name="m", revision="r")


@pytest.mark.parametrize(
    "encoded",
    ["text", b"bytes", 5, [[1.0, 2.0]], [[1.0, float("nan"), 0.0]], [[1.0, 0.0, 0.0]] * 2],
)
def test_e5_rejects_invalid_embeddings(encoded) -> None:
    with pytest.raises(ValueError, match="embeddings"):
        _embedder_with(encoded).embed_query("agua")


def test_e5_embed_passages_of_nothing_skips_the_model() -> None:
    assert build_embedder().embed_passages(()) == ()


def test_e5_load_builds_sentence_transformer_without_remote_code(monkeypatch) -> None:
    from agro_rag.infrastructure import pinecone as module

    seen = {}

    def model_factory(name, **kwargs):
        seen["call"] = (name, kwargs)
        return FakeModel()

    fake = SimpleNamespace(SentenceTransformer=model_factory)
    monkeypatch.setattr(module, "import_module", lambda name: fake)

    embedder = module.E5Embedder.load(model_name="m", revision="r", local_files_only=True)

    assert embedder.dimension == 3
    assert seen["call"][1] == {
        "revision": "r",
        "device": None,
        "local_files_only": True,
        "trust_remote_code": False,
    }


def _ranker(index):
    from agro_rag.infrastructure.pinecone import PineconeVectorRanker

    return PineconeVectorRanker(index, "agro-v1", build_embedder(), identity())


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(matches=5),
        SimpleNamespace(matches=(SimpleNamespace(id=1, score=0.5),)),
        SimpleNamespace(matches=(SimpleNamespace(id="a", score="x"),)),
    ],
)
def test_ranker_rejects_invalid_pinecone_responses(response) -> None:
    index = FakeIndex()
    index.query = lambda **kwargs: response
    with pytest.raises(ValueError, match="inválida de Pinecone"):
        _ranker(index).rank("riego", None)


def test_ranker_applies_crop_stage_and_region_filters() -> None:
    from agro_rag.application.retrieval import RetrievalFilters

    index = FakeIndex()
    _ranker(index).rank(
        "riego",
        RetrievalFilters(
            crop="tomato", growth_stage="vegetative_growth", region="ar-mendoza-oasis-norte"
        ),
    )
    clauses = index.query_kwargs["filter"]["$and"]
    assert len(clauses) == 5


@pytest.mark.parametrize("count", [-1, True, "3"])
def test_namespace_count_rejects_invalid_statistics(count) -> None:
    from agro_rag.infrastructure.pinecone import _namespace_count

    stats = SimpleNamespace(namespaces={"ns": SimpleNamespace(vector_count=count)})
    with pytest.raises(ValueError, match="Estadísticas"):
        _namespace_count(stats, "ns")


@pytest.mark.parametrize(
    "catalogue",
    [
        Catalogue("", (evidence("a", "x"),)),
        Catalogue("v1", ()),
        Catalogue("v1", (evidence("a", "x"), evidence("a", "y"))),
        Catalogue("v1", (evidence("ñ", "x"),)),
        Catalogue("v1", (evidence("__agro_index_manifest__", "x"),)),
    ],
)
def test_validate_catalogue_rejects_unindexable_catalogues(catalogue) -> None:
    from agro_rag.infrastructure.pinecone import _validate_catalogue

    with pytest.raises(ValueError):
        _validate_catalogue(catalogue)


def test_validate_catalogue_rejects_foreign_corpus_version() -> None:
    from agro_rag.infrastructure.pinecone import _validate_catalogue

    foreign = replace(evidence("a", "x"), corpus_version="other")
    with pytest.raises(ValueError, match="Catálogo inválido"):
        _validate_catalogue(Catalogue("v1", (foreign,)))


def test_index_catalogue_rejects_bad_config_and_wrong_dimension() -> None:
    from agro_rag.infrastructure.pinecone import index_catalogue

    catalogue = Catalogue("v1", (evidence("a", "riego"),))
    with pytest.raises(ValueError, match="namespace"):
        index_catalogue(
            index=FakeIndex(), namespace="", catalogue=catalogue, embedder=build_embedder()
        )
    wrong = FakeIndex()
    wrong.describe_index_stats = lambda: SimpleNamespace(dimension=9, namespaces={})
    with pytest.raises(ValueError, match="Dimensión"):
        index_catalogue(
            index=wrong, namespace="agro-v1", catalogue=catalogue, embedder=build_embedder()
        )


def test_wait_for_ids_detects_foreign_writes_and_malformed_fetch() -> None:
    from agro_rag.infrastructure.pinecone import _wait_for_ids

    grown = FakeIndex(vector_count=5)
    with pytest.raises(ValueError, match="cambió durante"):
        _wait_for_ids(
            index=grown, namespace="agro-v1", ids=("a",), expected_count=1, timeout=1, batch_size=1
        )
    broken = FakeIndex(vector_count=1)
    broken.fetch = lambda **kwargs: {"vectors": []}
    with pytest.raises(ValueError, match="al verificar IDs"):
        _wait_for_ids(
            index=broken, namespace="agro-v1", ids=("a",), expected_count=1, timeout=1, batch_size=1
        )


def test_handle_close_closes_index_and_client_when_available() -> None:
    from agro_rag.infrastructure.pinecone import PineconeHandle

    closed = []
    index = SimpleNamespace(close=lambda: closed.append("index"))
    client = SimpleNamespace(close=lambda: closed.append("client"))
    PineconeHandle(client=client, index=index).close()
    PineconeHandle(client=object(), index=object()).close()
    assert closed == ["index", "client"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"api_key": " ", "index_name": "i"},
        {"api_key": "k", "index_name": ""},
        {"api_key": "k", "index_name": "i", "timeout": 0},
        {"api_key": "k", "index_name": "i", "create_if_missing": True},
    ],
)
def test_connect_pinecone_rejects_invalid_configuration(kwargs) -> None:
    from agro_rag.infrastructure.pinecone import connect_pinecone

    with pytest.raises(ValueError, match="Configuración inválida"):
        connect_pinecone(**kwargs)


def _fake_sdk(client):
    return SimpleNamespace(
        Pinecone=lambda **kwargs: client,
        ServerlessSpec=lambda **kwargs: ("spec", kwargs),
    )


def test_connect_pinecone_lists_indexes_when_sdk_lacks_exists(monkeypatch) -> None:
    from agro_rag.infrastructure import pinecone as module

    class Client:
        def list_indexes(self):
            return [SimpleNamespace(name="i")]

        def Index(self, name):
            return f"index:{name}"

    monkeypatch.setattr(module, "import_module", lambda name: _fake_sdk(Client()))
    assert module.connect_pinecone(api_key="k", index_name="i").index == "index:i"


def test_connect_pinecone_creates_missing_index_when_requested(monkeypatch) -> None:
    from agro_rag.infrastructure import pinecone as module

    created = {}

    class Client:
        indexes = SimpleNamespace(exists=lambda name: False)

        def create_index(self, **kwargs):
            created.update(kwargs)

        def index(self, name):
            return f"index:{name}"

    monkeypatch.setattr(module, "import_module", lambda name: _fake_sdk(Client()))
    handle = module.connect_pinecone(
        api_key="k", index_name="i", create_if_missing=True, dimension=3
    )
    assert handle.index == "index:i"
    assert created["dimension"] == 3 and created["name"] == "i"


def test_connect_pinecone_closes_client_when_index_is_missing_or_sdk_incompatible(
    monkeypatch,
) -> None:
    from agro_rag.infrastructure import pinecone as module

    closed = []

    class Missing:
        indexes = SimpleNamespace(exists=lambda name: False)

        def close(self):
            closed.append("missing")

    monkeypatch.setattr(module, "import_module", lambda name: _fake_sdk(Missing()))
    with pytest.raises(ValueError, match="no existe"):
        module.connect_pinecone(api_key="k", index_name="i")

    class Incompatible:
        indexes = SimpleNamespace(exists=lambda name: True)

        def close(self):
            closed.append("incompatible")

    monkeypatch.setattr(module, "import_module", lambda name: _fake_sdk(Incompatible()))
    with pytest.raises(RuntimeError, match="incompatible"):
        module.connect_pinecone(api_key="k", index_name="i")
    assert closed == ["missing", "incompatible"]
