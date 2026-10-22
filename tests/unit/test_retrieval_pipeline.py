from dataclasses import replace

import pytest
from test_retrieval import evidence

from agro_rag.domain.evidence import Catalogue


def api():
    from agro_rag.application import retrieval_pipeline

    return retrieval_pipeline


class Ranking:
    corpus_version = "v1"

    def __init__(self, ids, failure=False):
        self.ids = ids
        self.failure = failure
        self.calls = []

    def rank(self, question, crop):
        self.calls.append((question, crop))
        if self.failure:
            raise OSError("provider credentials must not leak")
        return tuple(api().ScoredId(id, float(len(self.ids) - i)) for i, id in enumerate(self.ids))


class Reranker:
    def __init__(self, ids):
        self.ids = ids
        self.seen = ()

    def rank(self, question, candidates):
        self.seen = candidates
        return tuple(api().ScoredId(id, float(len(self.ids) - i)) for i, id in enumerate(self.ids))


class Counter:
    # Deterministic fake tokenizer; NOT evidence of real model tokenization.
    def count(self, text):
        return len(text)


def build(mode="hybrid", items=None, **kwargs):
    m = api()
    items = items or [evidence("a", "riego", "A"), evidence("b", "humedad", "B")]
    identity = m.IndexIdentity("v1", "e5", "revision-1", 384)
    options = dict(
        catalogue=Catalogue("v1", tuple(items)),
        lexical=Ranking(["a", "b"]),
        vector=Ranking(["b", "a"]),
        expected_index=identity,
        actual_index=identity,
        reranker=Reranker(["a", "b"]),
        token_counter=Counter(),
        token_budget=10000,
        mode=mode,
    )
    options.update(kwargs)
    return m.RetrievalPipeline(**options)


@pytest.mark.parametrize(
    "mode,order,stages",
    [
        ("bm25", ["a", "b"], {"bm25"}),
        ("vector", ["b", "a"], {"vector"}),
        ("hybrid", ["a", "b"], {"bm25", "vector", "rrf"}),
        ("hybrid_rerank", ["a", "b"], {"bm25", "vector", "rrf", "reranker"}),
    ],
)
def test_ret_01_four_modes_keep_stage_scores_and_stable_order(mode, order, stages):
    result = build(mode).retrieve("riego", "tomato")
    assert [e.evidence_id for e in result.evidence] == order
    assert {s.stage for s in result.stages} == stages
    assert result.corpus_version == "v1" and result.mode == mode
    assert all(s.ranking for s in result.stages)
    assert result.token_count == len(result.context)
    assert build(mode).search("riego", "tomato") == result.evidence


def test_ret_01_no_silent_lexical_fallback_on_vector_failure():
    with pytest.raises(api().RetrievalUnavailable, match="vector") as exc:
        build(vector=Ranking([], failure=True)).retrieve("riego", None)
    assert "credentials" not in str(exc.value)
    assert build("bm25", vector=Ranking([], failure=True)).search("riego", None)


@pytest.mark.parametrize(
    "field,value",
    [
        ("corpus_version", "old"),
        ("model", "another-model"),
        ("revision", "revision-2"),
        ("dimension", 768),
    ],
)
def test_ret_02_reject_incompatible_index_even_same_dimension(field, value):
    identity = api().IndexIdentity("v1", "e5", "revision-1", 384)
    with pytest.raises(ValueError, match="índice"):
        build(actual_index=replace(identity, **{field: value}))


def test_ret_03_filters_stale_ids_crop_and_duplicate_candidates_before_reranking():
    items = [
        evidence("a", "riego"),
        evidence("b", "humedad", "B"),
        evidence("lettuce", "lechuga", crop="lettuce"),
    ]
    ranker = Reranker(["b", "a"])
    result = build(
        "hybrid_rerank",
        items,
        lexical=Ranking(["a", "a", "old"]),
        vector=Ranking(["lettuce", "b", "old"]),
        reranker=ranker,
    ).retrieve("riego", "tomato")
    assert {e.evidence_id for e in ranker.seen} == {"a", "b"}
    assert [e.evidence_id for e in result.evidence] == ["b", "a"]
    assert set(result.excluded_ids) == {"old", "lettuce"}


def test_ret_03_source_cap_counts_pdf_not_page_and_respects_total_limit():
    items = [
        replace(evidence(str(i), "riego", "A" if i < 3 else str(i)), pdf_page=i + 1)
        for i in range(6)
    ]
    result = build("bm25", items, lexical=Ranking([str(i) for i in range(6)])).retrieve(
        "riego", None
    )
    assert [e.evidence_id for e in result.evidence] == ["0", "1", "3", "4"]


def test_ret_03_budget_counts_serialized_context_and_skips_whole_long_passages():
    items = [evidence("long", "x" * 1000), evidence("short", "agua", "B")]
    all_result = build("bm25", [items[1]], lexical=Ranking(["short"])).retrieve("agua", None)
    budget = len(all_result.context)
    result = build("bm25", items, lexical=Ranking(["long", "short"]), token_budget=budget).retrieve(
        "agua", None
    )
    assert result.evidence == (items[1],)
    assert result.token_count == budget
    empty = build("bm25", token_budget=1).retrieve("riego", None)
    assert empty.evidence == () and empty.context == "" and empty.token_count == 0


def test_empty_query_never_calls_providers_and_no_candidates_never_calls_reranker():
    lexical, vector, reranker = Ranking([], True), Ranking([], True), Reranker(["invented"])
    assert build(lexical=lexical, vector=vector).retrieve("  ", None).evidence == ()
    assert not lexical.calls and not vector.calls
    assert (
        build("hybrid_rerank", lexical=Ranking([]), vector=Ranking([]), reranker=reranker).search(
            "riego", None
        )
        == ()
    )


def test_reranker_cannot_invent_ids_or_reintroduce_filtered_evidence():
    with pytest.raises(api().RetrievalContractError, match="reranker"):
        build("hybrid_rerank", reranker=Reranker(["invented"])).retrieve("riego", None)


@pytest.mark.parametrize(
    "options",
    [
        {"mode": "unknown"},
        {"token_budget": 0},
        {"source_cap": 0},
        {"max_items": 0},
        {"candidate_limit": 0},
        {"vector": None},
        {"actual_index": None},
        {"expected_index": None},
        {"mode": "hybrid_rerank", "reranker": None},
    ],
)
def test_invalid_configuration_fails_before_query(options):
    with pytest.raises(ValueError):
        build(**options)


def test_catalogue_and_ranker_versions_must_match():
    with pytest.raises(ValueError, match="catálogo"):
        build(items=[replace(evidence("a", "riego"), corpus_version="old")])
    with pytest.raises(ValueError, match="catálogo"):
        build(items=[evidence("a", "riego"), evidence("a", "duplicate")])
    ranking = Ranking(["a"])
    ranking.corpus_version = "old"
    with pytest.raises(ValueError, match="versión"):
        build(lexical=ranking)


def test_lexical_adapter_exposes_candidates_before_diversity_cap():
    from agro_rag.infrastructure.retrieval import LexicalRetriever

    r = LexicalRetriever(Catalogue("v1", tuple(evidence(str(i), "riego") for i in range(5))))
    assert r.corpus_version == "v1"
    assert len(r.rank("riego", "tomato")) == 5
    assert r.rank("sin coincidencia", None) == ()
    assert r.rank("riego", "lettuce") == ()
    assert len(r.search("riego", "tomato")) == 2


@pytest.mark.parametrize("score", [float("nan"), float("inf"), -float("inf")])
def test_provider_nonfinite_scores_are_rejected(score):
    class BadRanking(Ranking):
        def rank(self, question, crop):
            return (api().ScoredId("a", score),)

    with pytest.raises(api().RetrievalContractError, match="score"):
        build("bm25", lexical=BadRanking([])).search("riego", None)


def test_reranker_failure_is_operational_not_empty_evidence():
    class Broken:
        def rank(self, question, candidates):
            raise OSError("secret")

    with pytest.raises(api().RetrievalUnavailable, match="reranker"):
        build("hybrid_rerank", reranker=Broken()).search("riego", None)


@pytest.mark.parametrize("value", [0, -1, 1.5, True])
def test_tokenizer_invalid_count_is_rejected(value):
    class InvalidCounter:
        def count(self, text):
            return value

    with pytest.raises(api().RetrievalContractError, match="tokenizer"):
        build(token_counter=InvalidCounter()).search("riego", None)


@pytest.mark.parametrize(
    "field,value", [("model", ""), ("revision", ""), ("dimension", 0), ("corpus_version", "old")]
)
def test_both_index_identities_must_be_valid_not_just_equal(field, value):
    invalid = replace(api().IndexIdentity("v1", "e5", "revision-1", 384), **{field: value})
    with pytest.raises(ValueError, match="índice"):
        build(expected_index=invalid, actual_index=invalid)


def test_candidate_limit_applies_before_reranker():
    reranker = Reranker(["a"])
    result = build("hybrid_rerank", candidate_limit=1, reranker=reranker).retrieve("riego", None)
    assert [e.evidence_id for e in reranker.seen] == ["a"]
    assert len(result.evidence) == 1


def test_tokenizer_failure_is_sanitized_operational_error():
    class BrokenCounter:
        def count(self, text):
            raise OSError("private tokenizer path")

    with pytest.raises(api().RetrievalUnavailable, match="tokenizer") as exc:
        build(token_counter=BrokenCounter()).retrieve("riego", None)
    assert "private" not in str(exc.value)
