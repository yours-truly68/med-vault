"""Shared HTTP retry helpers for AI provider requests."""

from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


async def post_json_with_retry(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict,
    timeout: float,
    error_label: str,
    max_retries: int = 5,
    base_delay_seconds: float = 15.0,
) -> dict:
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError(f"{error_label} response must be a JSON object")
                return data
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code not in RETRYABLE_STATUS_CODES or attempt == max_retries:
                raise
            delay = base_delay_seconds * attempt
            logger.warning(
                "%s returned %s; retrying in %.0fs (%s/%s)",
                error_label,
                exc.response.status_code,
                delay,
                attempt,
                max_retries,
            )
            await asyncio.sleep(delay)
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt == max_retries:
                raise
            delay = base_delay_seconds * attempt
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
