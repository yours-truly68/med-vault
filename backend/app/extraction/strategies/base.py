"""Base extractor strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.extraction.models import (
    ExtractionRequest,
    ExtractorHealth,
    ExtractorName,
    FileProbe,
    RawExtraction,
)


class BaseExtractor(ABC):
    name: ClassVar[ExtractorName]

    @abstractmethod
    def supports(self, probe: FileProbe) -> bool:
        """Return True if this extractor can handle the probed file."""

    @abstractmethod
    async def extract(self, request: ExtractionRequest) -> RawExtraction:
        """Extract text. CPU-bound work must use asyncio.to_thread internally."""

    @abstractmethod
    async def health_check(self) -> ExtractorHealth:
        """Verify dependencies are available."""
