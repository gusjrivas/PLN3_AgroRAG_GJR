"""Explicit Hugging Face tokenizer adapter for retrieval context accounting."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Protocol, cast


class Tokenizer(Protocol):
    def encode(self, text: str, **kwargs: Any) -> object: ...


@dataclass(frozen=True)
class TransformersTokenCounter:
    tokenizer: Tokenizer
    model_name: str
    revision: str

    def __post_init__(self) -> None:
        if not self.model_name or not self.revision:
            raise ValueError("Identidad inválida del tokenizer")

    @classmethod
    def load(
        cls,
        *,
        model_name: str,
        revision: str,
        local_files_only: bool = True,
        loader: Callable[..., Tokenizer] | None = None,
    ) -> TransformersTokenCounter:
        if not model_name or not revision:
            raise ValueError("Identidad inválida del tokenizer")
        if loader is None:
            transformers = import_module("transformers")
            auto_tokenizer = getattr(transformers, "AutoTokenizer", None)
            from_pretrained = getattr(auto_tokenizer, "from_pretrained", None)
            if not callable(from_pretrained):
                raise RuntimeError("Transformers no ofrece AutoTokenizer compatible")
            loader = cast(Callable[..., Tokenizer], from_pretrained)
        tokenizer = loader(
            model_name,
            revision=revision,
            local_files_only=local_files_only,
            trust_remote_code=False,
        )
        return cls(tokenizer, model_name, revision)

    def count(self, text: str) -> int:
        tokens = self.tokenizer.encode(
            text,
            add_special_tokens=False,
            truncation=False,
        )
        if (
            not isinstance(tokens, Sequence)
            or isinstance(tokens, (str, bytes))
            or any(not isinstance(token, int) or isinstance(token, bool) for token in tokens)
        ):
            raise ValueError("Respuesta inválida del tokenizer")
        return len(tokens)
