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


class _Tokenizer:
    def encode(self, text: str, **kwargs: Any) -> list[int]:
        return [1]


@pytest.mark.parametrize(("model", "revision"), [("", "rev"), ("model", "")])
def test_transformers_counter_rejects_empty_identity(model: str, revision: str) -> None:
    from agro_rag.infrastructure.tokenizer import TransformersTokenCounter

    with pytest.raises(ValueError, match="Identidad"):
        TransformersTokenCounter(_Tokenizer(), model, revision)
    with pytest.raises(ValueError, match="Identidad"):
        TransformersTokenCounter.load(
            model_name=model, revision=revision, loader=lambda *a, **k: _Tokenizer()
        )


def test_load_uses_transformers_auto_tokenizer_when_no_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from agro_rag.infrastructure import tokenizer as module

    calls: dict[str, Any] = {}

    def from_pretrained(name: str, **kwargs: Any) -> _Tokenizer:
        calls["args"] = (name, kwargs)
        return _Tokenizer()

    fake = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=from_pretrained))
    monkeypatch.setattr(module, "import_module", lambda name: fake)

    counter = module.TransformersTokenCounter.load(model_name="m", revision="r")

    assert counter.count("x") == 1
    assert calls["args"][1]["local_files_only"] is True
    assert calls["args"][1]["trust_remote_code"] is False


@pytest.mark.parametrize(
    "fake_attrs",
    [{}, {"AutoTokenizer": object()}, {"AutoTokenizer": type("A", (), {"from_pretrained": 1})}],
)
def test_load_rejects_incompatible_transformers(
    monkeypatch: pytest.MonkeyPatch, fake_attrs: dict[str, Any]
) -> None:
    from types import SimpleNamespace

    from agro_rag.infrastructure import tokenizer as module

    monkeypatch.setattr(module, "import_module", lambda name: SimpleNamespace(**fake_attrs))

    with pytest.raises(RuntimeError, match="AutoTokenizer"):
        module.TransformersTokenCounter.load(model_name="m", revision="r")
