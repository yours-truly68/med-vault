"""Shared AI layer errors."""


class RateLimitError(Exception):
    """Raised when an upstream AI provider returns HTTP 429."""

    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: float | None = None,
        provider_label: str = "AI provider",
    ) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
        self.provider_label = provider_label


def is_rate_limit_message(message: str) -> bool:
    lower = message.lower()
    return (
        "429" in lower
        or "rate limit" in lower
        or "free tier" in lower
        or "quota" in lower
        or "too many requests" in lower
    )
