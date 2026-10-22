from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGRO_", env_file=".env", extra="ignore")
    reader_key: str = Field(default="", repr=False)
    catalogue_path: Path = Path("data/processed/catalogue")
    ollama_url: str = "http://127.0.0.1:11434"
    model: str = ""
