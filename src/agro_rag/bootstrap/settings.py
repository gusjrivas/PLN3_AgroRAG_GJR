from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGRO_",
        env_file=".env",
        env_ignore_empty=True,
        populate_by_name=True,
        extra="ignore",
    )
    reader_key: str = Field(default="", repr=False)
    pinecone_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="PINECONE_API_KEY",
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
    retrieval_max_items: int = Field(default=4, gt=0)
    retrieval_candidate_limit: int = Field(default=20, gt=0)
    semantic_local_files_only: bool = True
    catalogue_path: Path = Path("data/processed/catalogue")
    model_provider: Literal["ollama", "openai"] = "ollama"
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = ""
    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
        repr=False,
    )
    openai_model: str = ""
    openai_url: str = "https://api.openai.com/v1"
