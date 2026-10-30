from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_secret_file(
    *,
    value_name: str,
    value: str | None,
    file_name: str,
    file_path: Path | None,
) -> str | None:
    if value and file_path is not None:
        raise ValueError(f"Configure sólo {value_name} o {file_name}, no ambos")
    if file_path is None:
        return value
    try:
        resolved = file_path.read_text(encoding="utf-8").strip()
    except OSError:
        raise ValueError(f"{file_name} debe apuntar a un archivo legible") from None
    if not resolved:
        raise ValueError(f"{file_name} debe apuntar a un archivo no vacío")
    return resolved


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGRO_",
        env_file=".env",
        env_ignore_empty=True,
        populate_by_name=True,
        extra="ignore",
        hide_input_in_errors=True,
    )
    reader_key: str = Field(default="", repr=False)
    reader_key_file: Path | None = Field(default=None, repr=False)
    pinecone_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="PINECONE_API_KEY",
        repr=False,
    )
    pinecone_api_key_file: Path | None = Field(
        default=None,
        validation_alias="PINECONE_API_KEY_FILE",
        repr=False,
    )
    pinecone_index: str = Field(
        default="pln3-agrorag-e5-384",
        validation_alias="PINECONE_INDEX",
    )
    pinecone_namespace: str = Field(default="", validation_alias="PINECONE_NAMESPACE")
    pinecone_cloud: str = Field(default="aws", validation_alias="PINECONE_CLOUD")
    pinecone_region: str = Field(default="us-east-1", validation_alias="PINECONE_REGION")
    pinecone_metric: str = "cosine"
    pinecone_timeout: float = 30.0
    pinecone_batch_size: int = 100
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_revision: str = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_revision: str = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
    retrieval_mode: Literal["bm25", "vector", "hybrid", "hybrid_rerank"] = "bm25"
    retrieval_tokenizer_model: str = ""
    retrieval_tokenizer_revision: str = ""
    retrieval_token_budget: int = Field(default=3000, gt=0)
    retrieval_source_cap: int = Field(default=2, gt=0)
    retrieval_max_items: int = Field(default=6, gt=0)
    retrieval_candidate_limit: int = Field(default=20, gt=0)
    semantic_local_files_only: bool = True
    catalogue_path: Path = Path("data/processed/catalogue")
    healthcheck_url: str = "http://127.0.0.1:8000/health/ready"
    model_provider: Literal["ollama", "openai"] = "ollama"
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = ""
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        repr=False,
    )
    openai_api_key_file: Path | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY_FILE",
        repr=False,
    )
    openai_model: str = ""
    openai_url: str = "https://api.openai.com/v1"

    @model_validator(mode="after")
    def resolve_secret_files(self) -> "Settings":
        self.reader_key = (
            _resolve_secret_file(
                value_name="AGRO_READER_KEY",
                value=self.reader_key,
                file_name="AGRO_READER_KEY_FILE",
                file_path=self.reader_key_file,
            )
            or ""
        )
        openai_value = _resolve_secret_file(
            value_name="OPENAI_API_KEY",
            value=self.openai_api_key.get_secret_value() if self.openai_api_key else None,
            file_name="OPENAI_API_KEY_FILE",
            file_path=self.openai_api_key_file,
        )
        self.openai_api_key = SecretStr(openai_value) if openai_value else None
        pinecone_value = _resolve_secret_file(
            value_name="PINECONE_API_KEY",
            value=self.pinecone_api_key.get_secret_value() if self.pinecone_api_key else None,
            file_name="PINECONE_API_KEY_FILE",
            file_path=self.pinecone_api_key_file,
        )
        self.pinecone_api_key = SecretStr(pinecone_value) if pinecone_value else None
        return self
