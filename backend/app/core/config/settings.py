from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[3]
_REPO_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Local backend overrides first; monorepo root `.env` wins for shared keys.
        env_file=(
            _BACKEND_DIR / ".env",
            _REPO_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # Application
    app_name: str = "MedVault API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://medvault:changeme@localhost:5432/medvault"
    )

    # Security
    secret_key: str = "changeme-generate-a-secure-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_token_cookie_name: str = "refresh_token"
    refresh_token_cookie_path: str = "/auth"

    # CORS (comma-separated in .env, not JSON)
    cors_origins: Annotated[list[str], NoDecode] = Field(default=["http://localhost:3000"])

    # File storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 25

    # OCR / document processing
    tesseract_cmd: str | None = None
    ocr_pdf_dpi: int = 150
    ocr_min_native_text_chars: int = 20
    ocr_max_workers: int = 4
    document_worker_concurrency: int = 2
    embedding_retry_base_seconds: float = 60.0
    embedding_retry_max_seconds: float = 900.0
    deferred_retry_poll_seconds: float = 30.0

    # LLM / classification
    llm_provider: str = "openai"
    llm_api_key: str | None = None
    llm_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_BASE_URL"),
    )
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    vercel_ai_api_key: str | None = None
    ollama_api_key: str | None = None
    local_llm_api_key: str | None = None
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("DEFAULT_BASE_URL", "OPENAI_BASE_URL"),
    )
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 60.0

    # Embeddings
    embedding_provider: str = "openai"
    embedding_api_key: str | None = None
    embedding_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EMBEDDING_BASE_URL"),
    )
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_timeout_seconds: float = 60.0

    # RAG / chat
    rag_top_k: int = 5
    rag_min_score: float = 0.15

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
