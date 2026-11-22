"""Explicit tokenizer adapters for retrieval context accounting."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from hashlib import sha1, sha256
from importlib import import_module
from os import environ
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Protocol, cast

# Public encoding asset and checksum from the pinned tiktoken release.
_O200K_ASSET = "https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken"
_O200K_SHA256 = "446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d"


class Tokenizer(Protocol):
    def encode(self, text: str, **kwargs: Any) -> object: ...


class OpenAIEncoding(Protocol):
    def encode_ordinary(self, text: str) -> list[int]: ...


@dataclass(frozen=True)
class TiktokenTokenCounter:
    encoding: OpenAIEncoding

    @classmethod
    def load(cls, *, model_name: str, local_files_only: bool = True) -> TiktokenTokenCounter:
        try:
            tiktoken = import_module("tiktoken")
        except ModuleNotFoundError as exc:
            if exc.name != "tiktoken":
                raise
            raise RuntimeError("Instale el extra semantic para usar tiktoken") from None
        try:
            encoding_name = tiktoken.encoding_name_for_model(model_name)
        except KeyError:
            raise ValueError("Modelo OpenAI sin codificación tiktoken reconocida") from None
        if encoding_name != "o200k_base":
            raise ValueError("El perfil tiktoken requiere un modelo OpenAI con o200k_base")
        if local_files_only:
            cache_dir = environ.get(
                "TIKTOKEN_CACHE_DIR",
                environ.get("DATA_GYM_CACHE_DIR", str(Path(gettempdir()) / "data-gym-cache")),
            )
            cache_key = sha1(_O200K_ASSET.encode(), usedforsecurity=False).hexdigest()
            error = "Prepare la caché local de tiktoken para o200k_base antes del arranque"
            if not cache_dir:
                raise ValueError(error)
            try:
                cached = (Path(cache_dir) / cache_key).read_bytes()
            except OSError:
                raise ValueError(error) from None
            if sha256(cached).hexdigest() != _O200K_SHA256:
                raise ValueError(error)
        return cls(tiktoken.get_encoding(encoding_name))

    def count(self, text: str) -> int:
        return len(self.encoding.encode_ordinary(text))


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
