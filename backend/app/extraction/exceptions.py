"""Typed errors for the Extraction Engine."""


class ExtractionError(Exception):
    """Base extraction failure."""


class UnsupportedFileError(ExtractionError):
    """File type is not supported for extraction."""


class CorruptFileError(ExtractionError):
    """File cannot be opened or is truncated/corrupt."""


class EmptyExtractionError(ExtractionError):
    """Extractor returned empty or whitespace-only text."""


class AllExtractorsFailedError(ExtractionError):
    """Every strategy in the chain failed or was rejected by quality gates."""

    def __init__(self, message: str, *, attempts: list[str] | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts or []


class ExtractorUnavailableError(ExtractionError):
    """Strategy dependency missing or health check failed."""
