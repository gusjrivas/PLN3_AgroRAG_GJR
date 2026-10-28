from typing import Any

import pytest


def test_transformers_counter_loads_fixed_revision_and_counts_without_truncation() -> None:
    from agro_rag.infrastructure.tokenizer import TransformersTokenCounter

    calls: dict[str, Any] = {}

    class Tokenizer:
        def encode(self, text: str, **kwargs: Any) -> list[int]:
            calls["encode"] = (text, kwargs)
            return [1, 2, 3]

    def loader(model_name: str, **kwargs: Any) -> Tokenizer:
        calls["load"] = (model_name, kwargs)
        return Tokenizer()

    counter = TransformersTokenCounter.load(
        model_name="tokenizer-model",
        revision="fixed-revision",
        local_files_only=True,
        loader=loader,
    )

    assert counter.count("contexto") == 3
    assert calls["load"] == (
        "tokenizer-model",
        {
            "revision": "fixed-revision",
            "local_files_only": True,
            "trust_remote_code": False,
        },
    )
    assert calls["encode"] == (
        "contexto",
        {"add_special_tokens": False, "truncation": False},
    )


@pytest.mark.parametrize("tokens", [None, "invalid", [1, "bad"]])
def test_transformers_counter_rejects_invalid_tokenizer_output(tokens: object) -> None:
    from agro_rag.infrastructure.tokenizer import TransformersTokenCounter

    class Tokenizer:
        def encode(self, text: str, **kwargs: Any) -> object:
            return tokens

    with pytest.raises(ValueError, match="tokenizer"):
        TransformersTokenCounter(Tokenizer(), "model", "revision").count("contexto")
