import asyncio
import threading
import time

import pytest
from test_retrieval import evidence, retriever


class FakeModel:
    def __init__(self, results):
        self.results = iter(results)
        self.roles = []
        self.payloads = []

    async def generate(self, role, payload, timeout):
        from agro_rag.application.query import Generation

        self.roles.append(role)
        self.payloads.append(payload)
        return Generation(next(self.results), 100, 20)


def draft(ids=("a",)):
    return {
        "status": "answered",
        "claims": [{"text": "Mantener humedad constante.", "evidence_ids": list(ids)}],
        "missing_information": [],
    }


def execute(model, question="riego lechuga"):
    from agro_rag.application.query import QueryService

    r = retriever([evidence("a", "Lechuga: riego y humedad constante.", crop="lettuce")])
    return asyncio.run(QueryService(r, model, "v1").run(question, "lettuce", {}))


def execute_with_context(model, question, crop, context=None):
    from agro_rag.application.query import QueryService

    r = retriever(
        [
            evidence(
                "a",
                "Tomate: riego, costo, calor, frecuencia, suelo húmedo y momento crítico.",
            ),
            evidence(
                "b",
                "Lechuga: riego, herbicida, dosis, precio de venta, ciclo y suelo húmedo.",
                crop="lettuce",
            ),
        ]
    )
    return asyncio.run(QueryService(r, model, "v1").run(question, crop, context or {}))


def test_two_agents_approve_only_existing_evidence():
    model = FakeModel([draft(), {"decision": "approve", "feedback": ""}])
    result = execute(model)
    assert result["status"] == "answered"
    assert result["citations"][0]["evidence_id"] == "a"
    assert result["usage"]["llm_calls"] == 2
    assert model.roles == ["researcher", "verifier"]
    assert model.payloads[0]["question"] == "riego lechuga"
    assert result["answer"] == result["claims"][0]["text"]


def test_eva_02_without_verifier_returns_validated_researcher_draft_once():
    from agro_rag.application.query import QueryService

    model = FakeModel([draft()])
    r = retriever([evidence("a", "Lechuga: riego y humedad constante.", crop="lettuce")])

    result = asyncio.run(
        QueryService(r, model, "v1", verifier_enabled=False).run("riego lechuga", "lettuce", {})
    )

    assert result["status"] == "answered"
    assert result["verification"]["decision"] == "not_run"
    assert result["usage"]["llm_calls"] == 1
    assert model.roles == ["researcher"]


def test_response_limitations_disclose_configured_retrieval_mode():
    from agro_rag.application.query import QueryService

    model = FakeModel([draft(), {"decision": "approve", "feedback": ""}])
    r = retriever([evidence("a", "Lechuga: riego y humedad constante.", crop="lettuce")])

    result = asyncio.run(
        QueryService(r, model, "v1", retrieval_mode="hybrid").run("riego lechuga", "lettuce", {})
    )

    assert any("hybrid" in limitation for limitation in result["limitations"])
    assert all("lexical" not in limitation for limitation in result["limitations"])


def test_revision_is_dynamic_and_bounded():
    model = FakeModel(
        [
            draft(),
            {"decision": "revise", "feedback": "Precisar cultivo"},
            draft(),
            {"decision": "revise", "feedback": "Todavía incorrecto"},
        ]
    )
    result = execute(model)
    assert result["status"] == "insufficient_evidence"
    assert result["verification"]["revision_count"] == 1
    assert model.payloads[2]["feedback"] == "Precisar cultivo"
    assert len(model.roles) == 4


@pytest.mark.parametrize(
    "output", [draft(("invented",)), draft(()), {"status": "answered", "claims": []}]
)
def test_invalid_model_evidence_is_operational_error(output):
    from agro_rag.application.query import UpstreamError

    with pytest.raises(UpstreamError):
        execute(FakeModel([output]))


def test_no_evidence_makes_no_model_calls():
    model = FakeModel([])
    assert execute(model, "hipoteca bancaria")["status"] == "insufficient_evidence"
    assert not model.roles


def test_clarification_requires_missing_information():
    model = FakeModel(
        [{"status": "needs_clarification", "missing_information": ["Etapa del cultivo"]}]
    )
    assert execute(model)["missing_information"] == ["Etapa del cultivo"]
    from agro_rag.application.query import UpstreamError

    with pytest.raises(UpstreamError):
        execute(FakeModel([{"status": "needs_clarification", "missing_information": []}]))


def test_empty_clarification_with_supported_claims_is_sent_to_verifier():
    inconsistent = draft()
    inconsistent["status"] = "needs_clarification"
    model = FakeModel([inconsistent, {"decision": "approve", "feedback": ""}])

    result = execute(model)

    assert result["status"] == "answered"
    assert model.roles == ["researcher", "verifier"]


def test_abstention_and_approved_revision():
    assert (
        execute(FakeModel([{"status": "insufficient_evidence"}]))["status"]
        == "insufficient_evidence"
    )
    model = FakeModel(
        [
            draft(),
            {"decision": "revise", "feedback": "revisar"},
            draft(),
            {"decision": "approve", "feedback": ""},
        ]
    )
    assert execute(model)["verification"]["revision_count"] == 1


def test_verifier_abstention_and_clarification():
    assert (
        execute(FakeModel([draft(), {"decision": "abstain", "feedback": "sin soporte"}]))["status"]
        == "insufficient_evidence"
    )
    result = execute(FakeModel([draft(), {"decision": "clarify", "feedback": "Indicar etapa"}]))
    assert result["status"] == "needs_clarification"


def test_deadline_cancels_slow_model():
    from agro_rag.application.query import QueryService

    class Slow:
        async def generate(self, *args):
            await asyncio.sleep(1)

    r = retriever([evidence("a", "riego")])
    with pytest.raises(TimeoutError):
        asyncio.run(QueryService(r, Slow(), "v1", deadline_seconds=0.01).run("riego", None, {}))


def test_retrieval_runs_outside_the_event_loop_thread():
    from agro_rag.application.query import QueryService

    class RecordingRetriever:
        thread_id = 0

        def search(self, question, crop):
            self.thread_id = threading.get_ident()
            return ()

    async def exercise():
        retriever = RecordingRetriever()
        event_loop_thread = threading.get_ident()
        result = await QueryService(retriever, FakeModel([]), "v1").run("riego", None, {})
        assert result["status"] == "insufficient_evidence"
        assert retriever.thread_id != event_loop_thread

    asyncio.run(exercise())


def test_deadline_covers_blocking_retrieval():
    from agro_rag.application.query import QueryService

    class SlowRetriever:
        def search(self, question, crop):
            time.sleep(0.05)
            return ()

    with pytest.raises(TimeoutError):
        asyncio.run(
            QueryService(SlowRetriever(), FakeModel([]), "v1", deadline_seconds=0.01).run(
                "riego", None, {}
            )
        )


def test_ops_01_retrieval_cache_hit_is_normalized_and_observable():
    from agro_rag.application.query import QueryService

    class CountingRetriever:
        calls = 0

        def search(self, question, crop):
            self.calls += 1
            return ()

    async def exercise():
        retriever = CountingRetriever()
        service = QueryService(retriever, FakeModel([]), "v1")

        first = await service.run("  RÍEGO   TOMATE  ", "tomato", {})
        second = await service.run("riego tomate", "tomato", {})

        assert retriever.calls == 1
        assert first["usage"]["cache_hit"] is False
        assert second["usage"]["cache_hit"] is True

    asyncio.run(exercise())


def test_ops_01_retrieval_cache_invalidates_on_filter_and_version():
    from agro_rag.application.query import QueryService

    class CountingRetriever:
        calls = 0

        def search(self, question, crop):
            self.calls += 1
            return ()

    async def exercise():
        retriever = CountingRetriever()
        v1 = QueryService(retriever, FakeModel([]), "v1")
        v2 = QueryService(retriever, FakeModel([]), "v2")

        first = await v1.run("riego", "tomato", {})
        changed_filter = await v1.run("riego", "lettuce", {})
        changed_version = await v2.run("riego", "tomato", {})

        assert retriever.calls == 3
        assert first["usage"]["cache_hit"] is False
        assert changed_filter["usage"]["cache_hit"] is False
        assert changed_version["usage"]["cache_hit"] is False

    asyncio.run(exercise())


def test_ops_01_retrieval_errors_are_never_cached():
    from agro_rag.application.query import QueryService
    from agro_rag.application.retrieval_pipeline import RetrievalUnavailable

    class FlakyRetriever:
        calls = 0

        def search(self, question, crop):
            self.calls += 1
            if self.calls == 1:
                raise RetrievalUnavailable("sentinel-secret")
            return ()

    async def exercise():
        retriever = FlakyRetriever()
        service = QueryService(retriever, FakeModel([]), "v1")

        with pytest.raises(RetrievalUnavailable):
            await service.run("riego", "tomato", {})
        recovered = await service.run("riego", "tomato", {})
        cached = await service.run("riego", "tomato", {})

        assert retriever.calls == 2
        assert recovered["usage"]["cache_hit"] is False
        assert cached["usage"]["cache_hit"] is True

    asyncio.run(exercise())


def test_token_limit_fails_before_extra_calls():
    from agro_rag.application.query import BudgetExceeded, Generation, QueryService

    class Expensive:
        async def generate(self, *args):
            return Generation(draft(), 12000, 1)

    r = retriever([evidence("a", "riego")])
    with pytest.raises(BudgetExceeded):
        asyncio.run(QueryService(r, Expensive(), "v1").run("riego", None, {}))


def test_percentage_alone_never_becomes_litres():
    from agro_rag.application.query import QueryService

    model = FakeModel([])
    r = retriever([evidence("a", "riego tomate")])
    result = asyncio.run(
        QueryService(r, model, "v1").run(
            "¿Cuántos litros de riego necesita?",
            "tomato",
            {
                "measurement": {
                    "value": 30,
                    "unit": "%",
                    "measurement_type": "volumetric_water_content",
                }
            },
        )
    )
    assert result["status"] == "needs_clarification"
    assert result["missing_information"]
    assert not model.roles


@pytest.mark.parametrize(
    ("question", "crop"),
    [
        ("¿Qué herbicida selectivo se recomienda para lechuga y en qué dosis?", "lettuce"),
        ("¿Cuánto costará regar una hectárea de tomate este mes?", "tomato"),
        ("¿Cuál será el precio de venta de la lechuga la semana próxima?", "lettuce"),
        ("¿Qué marca y modelo de sensor de humedad debería comprar?", None),
        ("¿Cuál es la salinidad actual de mi suelo sin medirla?", None),
    ],
)
def test_out_of_scope_or_live_market_questions_abstain_without_model(question, crop):
    model = FakeModel([])

    result = execute_with_context(model, question, crop)

    assert result["status"] == "insufficient_evidence"
    assert result["missing_information"] == []
    assert not model.roles


@pytest.mark.parametrize(
    ("question", "crop"),
    [
        ("¿Cuál es el momento crítico?", None),
        ("Hace mucho calor, ¿cambio el riego?", None),
        ("¿Ya debería aumentar la frecuencia?", "tomato"),
        ("¿El suelo está demasiado húmedo?", None),
        ("El sensor marca 20, ¿riego ahora?", None),
        ("¿Es suficiente para completar el ciclo?", "lettuce"),
    ],
)
def test_context_dependent_decisions_request_clarification_without_model(question, crop):
    model = FakeModel([])

    result = execute_with_context(model, question, crop)

    assert result["status"] == "needs_clarification"
    assert result["missing_information"]
    assert not model.roles


def test_resolved_reference_can_continue_after_clarification():
    model = FakeModel([draft(("b",)), {"decision": "approve", "feedback": ""}])

    result = execute_with_context(
        model,
        "¿Es suficiente para completar el ciclo?",
        "lettuce",
        {
            "clarification_context": {
                "original_question": "¿Es suficiente para completar el ciclo?",
                "answers": ["Me refiero a 140 mm disponibles durante el verano."],
            }
        },
    )

    assert result["status"] == "answered"
    assert model.roles == ["researcher", "verifier"]


def test_context_dependent_question_can_continue_when_context_is_complete():
    model = FakeModel([draft(), {"decision": "approve", "feedback": ""}])

    result = execute_with_context(
        model,
        "Hace mucho calor, ¿cambio el riego?",
        "tomato",
        {"growth_stage": "floración", "soil_description": "franco, humedad medida 20 %"},
    )

    assert result["status"] == "answered"
    assert model.roles == ["researcher", "verifier"]


def test_factual_stage_question_is_not_treated_as_a_situational_decision():
    model = FakeModel([draft(), {"decision": "approve", "feedback": ""}])

    result = execute_with_context(
        model,
        "¿Desde qué etapa conviene aumentar la frecuencia de riego del tomate?",
        "tomato",
    )

    assert result["status"] == "answered"
    assert model.roles == ["researcher", "verifier"]
