import numpy as np
import pytest
from test_retrieval import evidence


class FakeCrossEncoder:
    def __init__(self, scores) -> None:
        self.scores = np.asarray(scores)
        self.pairs = []

    def predict(self, pairs):
        self.pairs = list(pairs)
        return self.scores


def test_cross_encoder_adapts_teaching_pairs_to_application_scores() -> None:
    from agro_rag.infrastructure.reranker import CrossEncoderReranker

    model = FakeCrossEncoder([0.2, 0.9])
    reranker = CrossEncoderReranker(
        model,
        model_name="BAAI/bge-reranker-v2-m3",
        revision="reranker-revision",
    )
    candidates = (evidence("a", "riego"), evidence("b", "humedad"))

    rows = reranker.rank("agua", candidates)

    assert model.pairs == [("agua", "riego"), ("agua", "humedad")]
    assert [(row.evidence_id, row.score) for row in rows] == [("a", 0.2), ("b", 0.9)]
    assert reranker.model_name == "BAAI/bge-reranker-v2-m3"
    assert reranker.revision == "reranker-revision"


def test_cross_encoder_empty_input_does_not_call_model() -> None:
    from agro_rag.infrastructure.reranker import CrossEncoderReranker

    model = FakeCrossEncoder([1.0])
    reranker = CrossEncoderReranker(model, model_name="model", revision="revision")

    assert reranker.rank("agua", ()) == ()
    assert model.pairs == []


def test_cross_encoder_rejects_invalid_provider_output() -> None:
    from agro_rag.infrastructure.reranker import CrossEncoderReranker

    reranker = CrossEncoderReranker(
        FakeCrossEncoder([0.1]),
        model_name="model",
        revision="revision",
    )
    with pytest.raises(ValueError, match="reranker"):
        reranker.rank("agua", (evidence("a", "riego"), evidence("b", "humedad")))
