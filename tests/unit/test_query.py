import asyncio

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


def test_two_agents_approve_only_existing_evidence():
    model = FakeModel([draft(), {"decision": "approve", "feedback": ""}])
    result = execute(model)
    assert result["status"] == "answered"
    assert result["citations"][0]["evidence_id"] == "a"
    assert result["usage"]["llm_calls"] == 2
    assert model.roles == ["researcher", "verifier"]
    assert model.payloads[0]["question"] == "riego lechuga"
    assert result["answer"] == result["claims"][0]["text"]


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
