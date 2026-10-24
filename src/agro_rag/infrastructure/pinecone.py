"""Pinecone/E5 adapters derived from the Teoria1 RAG example.

The teaching ``PineconeSearcher`` supplies the provider pattern. This adaptation keeps
provider I/O behind application ports, resolves returned IDs through the local catalogue,
and never creates, clears, or loads external resources at import time.
"""

from __future__ import annotations

import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Protocol

from agro_rag.application.retrieval_pipeline import IndexIdentity, ScoredId
from agro_rag.domain.evidence import Catalogue

MANIFEST_ID = "__agro_index_manifest__"


class SentenceEmbeddingModel(Protocol):
    def encode(self, texts: Sequence[str], **kwargs: object) -> object: ...


class VectorIndex(Protocol):
    def fetch(self, **kwargs: object) -> object: ...

    def query(self, **kwargs: object) -> object: ...

    def describe_index_stats(self) -> object: ...

    def upsert(self, **kwargs: object) -> object: ...


def _field(value: object, name: str, default: object = None) -> object:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _vector(values: object, dimension: int) -> tuple[float, ...]:
    if hasattr(values, "tolist"):
        values = values.tolist()
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise ValueError("El modelo devolvió embeddings inválidos")
    vector = tuple(float(value) for value in values)
    if len(vector) != dimension or any(not math.isfinite(value) for value in vector):
        raise ValueError("El modelo devolvió embeddings inválidos")
    return vector


def _embedding_dimension(model: SentenceEmbeddingModel) -> object:
    getter = getattr(model, "get_embedding_dimension", None)
    if not callable(getter):
        getter = getattr(model, "get_sentence_embedding_dimension", None)
    return getter() if callable(getter) else None


@dataclass(frozen=True)
class E5Embedder:
    """Sentence Transformer adapter with the prefixes required by multilingual E5."""

    model: SentenceEmbeddingModel
    model_name: str
    revision: str

    def __post_init__(self) -> None:
        dimension = _embedding_dimension(self.model)
        if (
            not self.model_name
            or not self.revision
            or not isinstance(dimension, int)
            or dimension <= 0
        ):
            raise ValueError("Identidad inválida del modelo de embeddings")

    @property
    def dimension(self) -> int:
        dimension = _embedding_dimension(self.model)
        assert isinstance(dimension, int) and dimension > 0
        return dimension

    @classmethod
    def load(
        cls,
        *,
        model_name: str,
        revision: str,
        device: str | None = None,
        local_files_only: bool = False,
    ) -> E5Embedder:
        """Load only when the administrative bootstrap explicitly asks for the model."""
        sentence_transformers = import_module("sentence_transformers")
        model = sentence_transformers.SentenceTransformer(
            model_name,
            revision=revision,
            device=device,
            local_files_only=local_files_only,
            trust_remote_code=False,
        )
        return cls(model=model, model_name=model_name, revision=revision)

    def _encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        encoded = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        if isinstance(encoded, (str, bytes)):
            raise ValueError("El modelo devolvió embeddings inválidos")
        try:
            raw_rows = list(encoded)  # type: ignore[call-overload]
        except TypeError as exc:
            raise ValueError("El modelo devolvió embeddings inválidos") from exc
        rows = tuple(_vector(row, self.dimension) for row in raw_rows)
        if len(rows) != len(texts):
            raise ValueError("El modelo devolvió una cantidad inválida de embeddings")
        return rows

    def embed_query(self, text: str) -> tuple[float, ...]:
        return self._encode((f"query: {text}",))[0]

    def embed_passages(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        return self._encode(tuple(f"passage: {text}" for text in texts))


def read_index_identity(index: VectorIndex, namespace: str) -> IndexIdentity:
    response = index.fetch(ids=[MANIFEST_ID], namespace=namespace)
    vectors = _field(response, "vectors", {})
    if not isinstance(vectors, Mapping) or MANIFEST_ID not in vectors:
        raise ValueError("Falta identidad verificable del índice")
    metadata = _field(vectors[MANIFEST_ID], "metadata", {})
    if not isinstance(metadata, Mapping) or metadata.get("kind") != "manifest":
        raise ValueError("Falta identidad verificable del índice")
    corpus_version = metadata.get("corpus_version")
    model = metadata.get("model")
    revision = metadata.get("revision")
    dimension = metadata.get("dimension")
    if (
        not isinstance(corpus_version, str)
        or not corpus_version
        or not isinstance(model, str)
        or not model
        or not isinstance(revision, str)
        or not revision
        or not isinstance(dimension, int)
        or isinstance(dimension, bool)
        or dimension <= 0
    ):
        raise ValueError("Identidad inválida del índice")
    return IndexIdentity(corpus_version, model, revision, dimension)


@dataclass(frozen=True)
class PineconeVectorRanker:
    index: VectorIndex
    namespace: str
    embedder: E5Embedder
    identity: IndexIdentity
    top_k: int = 20

    def __post_init__(self) -> None:
        if not self.namespace or self.top_k <= 0:
            raise ValueError("Configuración inválida de Pinecone")

    @classmethod
    def from_index(
        cls,
        *,
        index: VectorIndex,
        namespace: str,
        embedder: E5Embedder,
        expected_identity: IndexIdentity,
        top_k: int = 20,
    ) -> PineconeVectorRanker:
        actual = read_index_identity(index, namespace)
        model_identity = (embedder.model_name, embedder.revision, embedder.dimension)
        expected_model = (
            expected_identity.model,
            expected_identity.revision,
            expected_identity.dimension,
        )
        if actual != expected_identity or model_identity != expected_model:
            raise ValueError("La identidad del índice no es compatible")
        return cls(index, namespace, embedder, actual, top_k)

    @property
    def corpus_version(self) -> str:
        return self.identity.corpus_version

    def rank(self, question: str, crop: str | None) -> tuple[ScoredId, ...]:
        clauses: list[dict[str, object]] = [
            {"kind": {"$eq": "chunk"}},
            {"corpus_version": {"$eq": self.corpus_version}},
        ]
        if crop:
            clauses.append(
                {
                    "$or": [
                        {"crop": {"$eq": crop}},
                        {"crop": {"$exists": False}},
                    ]
                }
            )
        response = self.index.query(
            vector=list(self.embedder.embed_query(question)),
            top_k=self.top_k,
            include_metadata=False,
            namespace=self.namespace,
            filter={"$and": clauses},
        )
        matches = _field(response, "matches", ())
        if not isinstance(matches, Sequence):
            raise ValueError("Respuesta inválida de Pinecone")
        rows = []
        for match in matches:
            evidence_id = _field(match, "id")
            score = _field(match, "score")
            if not isinstance(evidence_id, str) or not isinstance(score, (int, float)):
                raise ValueError("Respuesta inválida de Pinecone")
            rows.append(ScoredId(evidence_id, float(score)))
        return tuple(rows)


def _namespace_count(stats: object, namespace: str) -> int:
    namespaces = _field(stats, "namespaces", {})
    if not isinstance(namespaces, Mapping) or namespace not in namespaces:
        return 0
    count = _field(namespaces[namespace], "vector_count", 0)
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError("Estadísticas inválidas de Pinecone")
    return count


def _validate_catalogue(catalogue: Catalogue) -> None:
    ids = [item.evidence_id for item in catalogue.evidence]
    if not catalogue.version or not ids or len(ids) != len(set(ids)):
        raise ValueError("Catálogo inválido para indexar")
    for item in catalogue.evidence:
        try:
            item.evidence_id.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("evidence_id incompatible con Pinecone") from exc
        if (
            item.corpus_version != catalogue.version
            or not 1 <= len(item.evidence_id) <= 512
            or item.evidence_id == MANIFEST_ID
        ):
            raise ValueError("Catálogo inválido para indexar")


def _wait_for_ids(
    *,
    index: VectorIndex,
    namespace: str,
    ids: tuple[str, ...],
    expected_count: int,
    timeout: float,
    batch_size: int,
) -> None:
    deadline = time.monotonic() + timeout
    while True:
        count = _namespace_count(index.describe_index_stats(), namespace)
        visible: set[str] = set()
        for start in range(0, len(ids), batch_size):
            response = index.fetch(ids=list(ids[start : start + batch_size]), namespace=namespace)
            vectors = _field(response, "vectors", {})
            if not isinstance(vectors, Mapping):
                raise ValueError("Respuesta inválida de Pinecone al verificar IDs")
            visible.update(item_id for item_id in vectors if isinstance(item_id, str))
        if count == expected_count and visible == set(ids):
            return
        if count > expected_count:
            raise ValueError("El namespace cambió durante la indexación")
        if time.monotonic() >= deadline:
            raise TimeoutError("No se pudo verificar la indexación completa en Pinecone")
        time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))


def index_catalogue(
    *,
    index: VectorIndex,
    namespace: str,
    catalogue: Catalogue,
    embedder: E5Embedder,
    batch_size: int = 100,
    verification_timeout: float = 60.0,
) -> IndexIdentity:
    """Write a fresh namespace and publish its identity only after all chunk batches succeed."""
    if not namespace or batch_size <= 0 or verification_timeout < 0:
        raise ValueError("Configuración inválida de namespace")
    _validate_catalogue(catalogue)
    stats = index.describe_index_stats()
    stats_dimension = _field(stats, "dimension")
    if stats_dimension != embedder.dimension:
        raise ValueError("Dimensión incompatible del índice Pinecone")
    if _namespace_count(stats, namespace):
        raise ValueError("El namespace ya contiene vectores; use uno nuevo")

    items = catalogue.evidence
    for start in range(0, len(items), batch_size):
        batch = items[start : start + batch_size]
        vectors = embedder.embed_passages(tuple(item.text for item in batch))
        payload = []
        for item, vector in zip(batch, vectors, strict=True):
            metadata: dict[str, str] = {
                "kind": "chunk",
                "evidence_id": item.evidence_id,
                "corpus_version": catalogue.version,
            }
            if item.crop:
                metadata["crop"] = item.crop
            payload.append({"id": item.evidence_id, "values": list(vector), "metadata": metadata})
        index.upsert(vectors=payload, namespace=namespace)

    evidence_ids = tuple(item.evidence_id for item in items)
    _wait_for_ids(
        index=index,
        namespace=namespace,
        ids=evidence_ids,
        expected_count=len(evidence_ids),
        timeout=verification_timeout,
        batch_size=batch_size,
    )

    identity = IndexIdentity(
        catalogue.version,
        embedder.model_name,
        embedder.revision,
        embedder.dimension,
    )
    index.upsert(
        vectors=[
            {
                "id": MANIFEST_ID,
                # Pinecone rejects all-zero dense vectors. Metadata filters keep this sentinel
                # out of retrieval queries, so a deterministic unit vector is safe here.
                "values": [1.0, *([0.0] * (embedder.dimension - 1))],
                "metadata": {
                    "kind": "manifest",
                    "corpus_version": identity.corpus_version,
                    "model": identity.model,
                    "revision": identity.revision,
                    "dimension": identity.dimension,
                },
            }
        ],
        namespace=namespace,
    )
    _wait_for_ids(
        index=index,
        namespace=namespace,
        ids=(MANIFEST_ID,),
        expected_count=len(evidence_ids) + 1,
        timeout=verification_timeout,
        batch_size=batch_size,
    )
    return identity


@dataclass
class PineconeHandle:
    client: Any
    index: VectorIndex

    def close(self) -> None:
        close_index = getattr(self.index, "close", None)
        if callable(close_index):
            close_index()
        close_client = getattr(self.client, "close", None)
        if callable(close_client):
            close_client()


def connect_pinecone(
    *,
    api_key: str,
    index_name: str,
    timeout: float = 30.0,
    create_if_missing: bool = False,
    dimension: int | None = None,
    metric: str = "cosine",
    cloud: str = "aws",
    region: str = "us-east-1",
) -> PineconeHandle:
    """Construct the real SDK client only from an explicit administrative/runtime bootstrap."""
    if not api_key.strip() or not index_name.strip() or timeout <= 0:
        raise ValueError("Configuración inválida de Pinecone")
    if create_if_missing and (
        dimension is None or dimension <= 0 or not metric or not cloud or not region
    ):
        raise ValueError("Configuración inválida para crear el índice Pinecone")
    pinecone = import_module("pinecone")
    client = pinecone.Pinecone(api_key=api_key, timeout=timeout)
    indexes = getattr(client, "indexes", None)
    exists = getattr(indexes, "exists", None)
    if callable(exists):
        index_exists = bool(exists(index_name))
    else:
        listing = client.list_indexes()
        names = listing.names() if hasattr(listing, "names") else [item.name for item in listing]
        index_exists = index_name in names
    if not index_exists:
        if not create_if_missing:
            close = getattr(client, "close", None)
            if callable(close):
                close()
            raise ValueError("El índice Pinecone configurado no existe")
        assert dimension is not None
        client.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=pinecone.ServerlessSpec(cloud=cloud, region=region),
        )
    index_factory = getattr(client, "index", None) or getattr(client, "Index", None)
    if not callable(index_factory):
        close = getattr(client, "close", None)
        if callable(close):
            close()
        raise RuntimeError("SDK de Pinecone incompatible")
    return PineconeHandle(client=client, index=index_factory(index_name))
