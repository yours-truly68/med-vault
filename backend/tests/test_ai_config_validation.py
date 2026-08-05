"""Tests for configuration-driven AI and extraction validation."""

from __future__ import annotations

import pytest

from app.ai.validation import ConfigurationError, validate_ai_configuration, validate_extraction_configuration
from app.core.config.settings import Settings


def _valid_ai_settings(**overrides) -> Settings:
    base = {
        "llm_provider": "ollama",
        "llm_model": "llama3.2:latest",
        "classification_provider": "ollama",
        "classification_model": "llama3.2:latest",
        "metadata_provider": "ollama",
        "metadata_model": "llama3.2:latest",
        "summary_provider": "groq",
        "summary_model": "llama-3.3-70b-versatile",
        "vision_provider": "gemini",
        "vision_model": "gemini-2.0-flash",
        "chat_provider": "groq",
        "chat_model": "llama-3.3-70b-versatile",
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-small",
        "groq_api_key": "test-groq-key",
        "gemini_api_key": "test-gemini-key",
        "openai_api_key": "test-openai-key",
        "ollama_host": "http://localhost:11434",
    }
    base.update(overrides)
    return Settings(**base)


def test_rejects_model_name_in_provider_field() -> None:
    settings = _valid_ai_settings(summary_provider="google/gemini-2.5-flash")
    with pytest.raises(ConfigurationError, match="SUMMARY_PROVIDER"):
        validate_ai_configuration(settings)


def test_rejects_ollama_for_vision_task() -> None:
    settings = _valid_ai_settings(vision_provider="ollama", vision_model="llama3.2:latest")
    with pytest.raises(ConfigurationError, match="VISION provider"):
        validate_ai_configuration(settings)


def test_rejects_missing_gemini_key_for_embedding() -> None:
    settings = _valid_ai_settings(embedding_provider="gemini", gemini_api_key=None)
    with pytest.raises(ConfigurationError, match="EMBEDDING"):
        validate_ai_configuration(settings)


def test_accepts_valid_multi_provider_configuration() -> None:
    settings = _valid_ai_settings()
    validate_ai_configuration(settings)


def test_extraction_requires_docling_enabled_for_secondary() -> None:
    settings = Settings(
        secondary_pdf_extractor="docling",
        docling_enabled=False,
        primary_pdf_extractor="pymupdf",
        image_extractor="tesseract",
    )
    with pytest.raises(ConfigurationError, match="DOCLING_ENABLED"):
        validate_extraction_configuration(settings)


def test_extraction_accepts_configured_extractors() -> None:
    settings = Settings(
        primary_pdf_extractor="pymupdf",
        secondary_pdf_extractor="docling",
        docling_enabled=True,
        image_extractor="tesseract",
        vision_fallback="gemini",
        tesseract_enabled=True,
    )
    validate_extraction_configuration(settings)
