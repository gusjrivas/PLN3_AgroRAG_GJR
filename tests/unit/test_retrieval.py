from dataclasses import replace

import pytest

from agro_rag.domain.evidence import Catalogue, Evidence


def evidence(id, text, source="A", crop="tomato"):
    return Evidence(
        id,
        "v1",
        source,
        "Manual",
        "2026",
        "https://example.org/a.pdf",
        1,
        "1",
        "Riego",
        crop,
        text,
        text,
        0,
        len(text),
    )


def retriever(items):
    from agro_rag.infrastructure.retrieval import LexicalRetriever

    return LexicalRetriever(Catalogue("v1", tuple(items)))


def test_search_crop_filter_empty_and_accent_normalization():
    a = evidence("a", "Tomate: riego durante cuajado de frutos.")
    b = evidence("b", "Lechuga: humedad constante.", crop="lettuce")
    r = retriever([a, b])
    assert r.search("CUAJÁDO", "tomato")[0] == a
    assert r.search("cuajado", "lettuce") == ()
    assert r.search("hipoteca bancaria", None) == ()
    assert r.search("de la el", None) == ()
    assert r.search("humedad", "lettuce")[0] == b


def test_source_cap_and_cache_do_not_leak_versions():
    items = [evidence(str(i), "riego tomate", source="A") for i in range(5)]
    items.append(evidence("z", "riego tomate", source="B"))
    r = retriever(items)
    hits = r.search("riego", None)
    assert len(hits) == 3 and sum(e.source_id == "A" for e in hits) == 2
    assert r.search("riego", None) == hits
    other = retriever([replace(items[0], corpus_version="v2")])
    assert other.search("riego", None)[0].corpus_version == "v2"


def test_rrf_is_stable_and_fuses_duplicate_ids():
    from agro_rag.application.retrieval import reciprocal_rank_fusion

    result = reciprocal_rank_fusion([["a", "b"], ["b", "c"]])
    assert result[0] == "b"
    assert len(result) == 3
    assert reciprocal_rank_fusion([]) == []
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([["a"]], k=0)
