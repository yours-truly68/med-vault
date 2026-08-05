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

    # OCR / document processing (used by Tesseract + PyMuPDF strategies)
    tesseract_enabled: bool = True
    tesseract_cmd: str | None = None
    ocr_language: str = "eng"
    ocr_pdf_dpi: int = 150
    ocr_min_native_text_chars: int = 20
    ocr_max_workers: int = 4
    document_worker_concurrency: int = 2
    embedding_retry_base_seconds: float = 60.0
    embedding_retry_max_seconds: float = 900.0
    deferred_retry_poll_seconds: float = 30.0

    # Extraction Engine
    extraction_cache_enabled: bool = True
    extraction_cache_dir: str = "./.cache/extraction"
    extraction_cache_ttl_seconds: int | None = None
    extraction_quality_accept_threshold: float = 0.9
    extraction_quality_warn_threshold: float = 0.6
    extraction_allow_low_quality_last_resort: bool = False
    extraction_timeout_seconds: float = 60.0
    primary_pdf_extractor: str = "pymupdf"
    secondary_pdf_extractor: str | None = "docling"
    image_extractor: str = "tesseract"
    vision_fallback: str | None = "gemini_vision"
    extraction_w_printable: float = 0.25
    extraction_w_ocr_confidence: float = 0.25
    extraction_w_density: float = 0.20
    extraction_w_medical: float = 0.15
    extraction_w_garbled: float = 0.15

    # Docling (optional heavyweight extractor)
    docling_enabled: bool = False
    docling_timeout_seconds: float = 120.0

    # Gemini Vision (last-resort extractor)
    gemini_api_key: str | None = None
    gemini_vision_enabled: bool = False
    gemini_vision_model: str = "gemini-2.0-flash"
    gemini_vision_timeout_seconds: float = 90.0
    gemini_vision_max_pages: int = 20

    # xAI (Grok)
    xai_api_key: str | None = None
    xai_base_url: str = Field(
        default="https://api.x.ai/v1",
        validation_alias=AliasChoices("XAI_BASE_URL"),
    )

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_api_key: str | None = None

    # Provider base URLs (configuration-driven — no inline URLs in business logic)
    openai_default_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("OPENAI_DEFAULT_BASE_URL"),
    )
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias=AliasChoices("GROQ_BASE_URL"),
    )
    vercel_base_url: str = Field(
        default="https://ai-gateway.vercel.sh/v1",
        validation_alias=AliasChoices("VERCEL_BASE_URL", "DEFAULT_BASE_URL"),
    )
    gemini_api_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        validation_alias=AliasChoices("GEMINI_API_BASE_URL"),
    )

    # LLM / classification (legacy global defaults)
    llm_provider: str = "openai"
    llm_api_key: str | None = None
    llm_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_BASE_URL"),
    )
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    vercel_ai_api_key: str | None = None
    local_llm_api_key: str | None = None
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias=AliasChoices("OPENAI_BASE_URL"),
    )
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 60.0

    # AI router retries / health cache
    ai_router_max_retries: int = 3
    ai_router_base_delay_seconds: float = 2.0
    ai_router_max_delay_seconds: float = 60.0
    ai_health_check_ttl_seconds: float = 60.0

    # Task-specific AI routing
    classification_provider: str | None = None
    classification_model: str | None = None
    classification_fallback_provider: str | None = None
    classification_fallback_model: str | None = None

    metadata_provider: str | None = None
    metadata_model: str | None = None
    metadata_fallback_provider: str | None = None
    metadata_fallback_model: str | None = None

    summary_provider: str | None = None
    summary_model: str | None = None
    summary_fallback_provider: str | None = None
    summary_fallback_model: str | None = None

    vision_provider: str | None = None
    vision_model: str | None = None
    vision_fallback_provider: str | None = None
    vision_fallback_model: str | None = None

    chat_provider: str | None = None
    chat_model: str | None = None
    chat_fallback_provider: str | None = None
    chat_fallback_model: str | None = None

    embedding_fallback_provider: str | None = None
    embedding_fallback_model: str | None = None

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
