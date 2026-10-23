from pathlib import Path

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
    catalogue_path: Path = Path("data/processed/catalogue")
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = ""
