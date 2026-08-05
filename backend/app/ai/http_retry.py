"""Shared HTTP retry helpers for AI provider requests."""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.ai.errors import RateLimitError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def _parse_retry_after(response: httpx.Response | None) -> float | None:
    if response is None:
        return None
    header = response.headers.get("Retry-After")
    if not header:
        return None
    try:
        return float(header)
    except ValueError:
        return None


async def post_json_with_retry(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict,
    timeout: float,
    error_label: str,
    max_retries: int = 2,
    base_delay_seconds: float = 0.5,
    max_delay_seconds: float = 2.0,
    extra_params: dict[str, str] | None = None,
) -> dict:
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    params=extra_params,
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError(f"{error_label} response must be a JSON object")
                return data
        except httpx.HTTPStatusError as exc:
            last_error = exc
            status = exc.response.status_code if exc.response is not None else None
            if status == 429:
                retry_after = _parse_retry_after(exc.response)
                delay = min(
                    retry_after if retry_after is not None else base_delay_seconds * attempt,
                    max_delay_seconds,
                )
                if attempt == max_retries:
                    raise RateLimitError(
                        f"{error_label} rate limit exceeded",
                        retry_after_seconds=delay,
                        provider_label=error_label,
                    ) from exc
                logger.warning(
                    "%s returned 429; fail-fast switching provider in %.1fs (%s/%s)",
                    error_label,
                    delay,
                    attempt,
                    max_retries,
                )
                await asyncio.sleep(delay)
                continue

            if status not in RETRYABLE_STATUS_CODES or attempt == max_retries:
                raise
            delay = min(base_delay_seconds * attempt, max_delay_seconds)
            logger.warning(
                "%s returned %s; retrying in %.0fs (%s/%s)",
                error_label,
                status,
                delay,
                attempt,
                max_retries,
            )
            await asyncio.sleep(delay)
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt == max_retries:
                raise
            delay = min(base_delay_seconds * attempt, max_delay_seconds)
            logger.warning(
                "%s request failed; retrying in %.0fs (%s/%s): %s",
                error_label,
                delay,
                attempt,
                max_retries,
                exc,
            )
            await asyncio.sleep(delay)

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"{error_label} request failed without a captured error")
