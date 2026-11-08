from dataclasses import replace

import pytest

from agro_rag.domain.evidence import Catalogue, Evidence


def evidence(id, text, source="A", crop="tomato", **metadata):
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
        **metadata,
    )


def retriever(items):
    from agro_rag.infrastructure.retrieval import LexicalRetriever

    return LexicalRetriever(Catalogue("v1", tuple(items)))


def test_exact_metadata_precedes_general_and_unknown() -> None:
    from agro_rag.application.retrieval import RetrievalFilters, prioritize_evidence

    items = (
        evidence("unknown-a", "riego", crop=None),
        evidence(
            "exact-a",
            "riego",
            growth_stages=("flowering",),
            applicable_regions=("ar-mendoza-oasis-norte",),
            applicability="specific",
        ),
        evidence("general-a", "riego", crop=None, applicability="general"),
        evidence("unknown-b", "riego", crop=None),
        evidence(
            "exact-b",
            "riego",
            growth_stages=("flowering",),
            applicable_regions=("ar-mendoza-oasis-norte",),
            applicability="specific",
        ),
        evidence(
            "other-stage",
            "riego",
            growth_stages=("pre_harvest",),
            applicability="specific",
        ),
        evidence("wrong-crop", "riego", crop="lettuce", applicability="general"),
    )
    filters = RetrievalFilters(
        crop="tomato", growth_stage="flowering", region="ar-mendoza-oasis-norte"
    )

    prioritized, excluded = prioritize_evidence(items, filters)

    assert [item.evidence_id for item in prioritized] == [
        "exact-a",
        "exact-b",
        "general-a",
        "unknown-a",
        "unknown-b",
    ]
    assert excluded == ("other-stage", "wrong-crop")


def test_incompatible_crop_is_excluded_and_general_evidence_survives() -> None:
    from agro_rag.application.retrieval import RetrievalFilters, prioritize_evidence

    lettuce = evidence("lettuce", "riego", crop="lettuce", applicability="specific")
    general = evidence("general", "riego", crop=None, applicability="general")

    prioritized, excluded = prioritize_evidence((lettuce, general), RetrievalFilters(crop="tomato"))

    assert prioritized == (general,)
    assert excluded == ("lettuce",)


def test_crop_only_excludes_contradictions_without_reordering_compatible_items() -> None:
    from agro_rag.application.retrieval import RetrievalFilters, prioritize_evidence

    untagged = evidence("untagged", "riego", crop=None)
    tomato = evidence("tomato", "riego", crop="tomato")

    prioritized, excluded = prioritize_evidence((untagged, tomato), RetrievalFilters(crop="tomato"))

    assert prioritized == (untagged, tomato)
    assert excluded == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("crop", []),
        ("growth_stage", []),
        ("region", []),
        ("growth_stage", 1),
        ("region", object()),
    ],
)
def test_retrieval_filters_reject_non_string_values_with_value_error(field, value) -> None:
    from agro_rag.application.retrieval import RetrievalFilters

    with pytest.raises(ValueError, match=field):
        RetrievalFilters(**{field: value})


def test_absent_stage_and_region_preserve_baseline_order() -> None:
    from agro_rag.application.retrieval import RetrievalFilters, prioritize_evidence

    items = (
        evidence("specific", "riego", growth_stages=("flowering",)),
        evidence("general", "riego", applicability="general"),
        evidence("unknown", "riego", crop=None),
    )

    prioritized, excluded = prioritize_evidence(items, RetrievalFilters())

    assert prioritized == items
    assert excluded == ()


def test_meta_02_bm25_uses_shared_structured_policy() -> None:
    from agro_rag.application.retrieval import RetrievalFilters

    exact = evidence(
        "exact",
        "humedad cultivo",
        source="E",
        growth_stages=("flowering",),
        applicable_regions=("ar-mendoza-oasis-norte",),
        applicability="specific",
    )
    general = evidence("general", "humedad cultivo", source="G", crop=None, applicability="general")
    unknown = evidence("unknown", "humedad cultivo", source="U", crop=None)
    incompatible = evidence(
        "incompatible",
        "humedad cultivo",
        source="I",
        growth_stages=("pre_harvest",),
        applicability="specific",
    )

    result = retriever([unknown, general, incompatible, exact]).search(
        "humedad cultivo",
        RetrievalFilters(crop="tomato", growth_stage="flowering", region="ar-mendoza-oasis-norte"),
    )

    assert [item.evidence_id for item in result] == ["exact", "general", "unknown"]


def test_search_crop_filter_empty_and_accent_normalization():
    a = evidence("a", "Tomate: riego durante cuajado de frutos.")
    b = evidence("b", "Lechuga: humedad constante.", crop="lettuce")
    r = retriever([a, b])
    assert r.search("CUAJÁDO", "tomato")[0] == a
    assert r.search("cuajado", "lettuce") == ()
    assert r.search("hipoteca bancaria", None) == ()
    assert r.search("de la el", None) == ()
    assert r.search("humedad", "lettuce")[0] == b


def test_spanish_water_loss_query_matches_english_fao_terms() -> None:
    english = evidence(
        "fao",
        "Crops predominately lose their water through stomata, small openings in plant leaves.",
        crop=None,
    )
    distractor = evidence(
        "distractor",
        "Los cultivos necesitan agua disponible para mantener el crecimiento.",
        crop=None,
    )

    ranked = retriever([distractor, english]).rank(
        "¿Por qué estructuras pierden principalmente agua los cultivos?", None
    )

    assert ranked[0].evidence_id == "fao"


def test_recommended_humidity_query_prioritizes_retention_recommendation() -> None:
    recommendation = evidence(
        "recommendation",
        "Lo ideal es mantener el suelo al 70 % de su capacidad de retención máxima.",
    )
    generic = evidence(
        "generic",
        "El cultivo requiere abundante humedad del suelo durante su desarrollo.",
    )

    ranked = retriever([generic, recommendation]).rank(
        "¿Qué nivel de humedad del suelo se recomienda?", "tomato"
    )

    assert ranked[0].evidence_id == "recommendation"


def test_lexical_search_honors_configured_context_breadth() -> None:
    from agro_rag.infrastructure.retrieval import LexicalRetriever

    items = [
        evidence(str(index), "humedad del suelo recomendada", source=f"S{index}")
        for index in range(7)
    ]

    result = LexicalRetriever(Catalogue("v1", tuple(items)), max_items=6).search(
        "humedad suelo", None
    )

    assert len(result) == 6


def test_leading_list_number_does_not_change_query_terms():
    from agro_rag.infrastructure.retrieval import tokens

    question = "¿Qué métodos de riego pueden utilizarse en lechuga?"

    assert tokens("2. " + question) == tokens(question)


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
