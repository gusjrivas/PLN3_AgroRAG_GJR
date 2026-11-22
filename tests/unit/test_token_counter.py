from pathlib import Path
from types import SimpleNamespace
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


def test_tiktoken_counts_literal_context_without_special_token_interpretation(monkeypatch) -> None:
    from agro_rag.infrastructure import tokenizer

    calls = []

    def encode_ordinary(text: str) -> list[int]:
        calls.append(text)
        return [1, 2, 3]

    fake = SimpleNamespace(
        encoding_name_for_model=lambda model: {"gpt-4o": "o200k_base"}[model],
        get_encoding=lambda name: SimpleNamespace(encode_ordinary=encode_ordinary),
    )
    monkeypatch.setattr(tokenizer, "import_module", lambda _name: fake)
    counter = tokenizer.TiktokenTokenCounter.load(model_name="gpt-4o", local_files_only=False)
    assert counter.count("contexto <|endoftext|>") == 3
    assert calls == ["contexto <|endoftext|>"]


@pytest.mark.parametrize("cached", [False, True])
def test_tiktoken_missing_or_invalid_cache_fails_before_loading(
    monkeypatch, tmp_path: Path, cached: bool
) -> None:
    import hashlib

    from agro_rag.infrastructure import tokenizer

    monkeypatch.setenv("TIKTOKEN_CACHE_DIR", str(tmp_path))
    if cached:
        url = b"https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken"
        (tmp_path / hashlib.sha1(url, usedforsecurity=False).hexdigest()).write_bytes(b"invalid")

    def unexpected(_encoding: str) -> None:
        pytest.fail("Loading a missing or corrupt encoding could attempt a download")

    fake = SimpleNamespace(
        encoding_name_for_model=lambda _model: "o200k_base", get_encoding=unexpected
    )
    monkeypatch.setattr(tokenizer, "import_module", lambda _name: fake)
    with pytest.raises(ValueError, match="caché"):
        tokenizer.TiktokenTokenCounter.load(model_name="gpt-4o")
