"""Pipeline instrumentation — structured stage-level telemetry for processing & indexing."""

from __future__ import annotations

import logging
import time
import traceback
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, AsyncIterator
from uuid import UUID

logger = logging.getLogger("medvault.pipeline")

# ──────────────────────────────────────────────────────────
# Structured context for a single pipeline run
# ──────────────────────────────────────────────────────────


@dataclass
class PipelineContext:
    """Carries identity and timing context through an entire pipeline run."""

    document_id: UUID
    job_id: str | None = None
    queue_name: str = ""
    worker_name: str = ""
    provider: str = ""
    model: str = ""
    retry_count: int = 0
    _stages: list[StageTrace] = field(default_factory=list, repr=False)
    _run_start: float = field(default_factory=time.perf_counter, repr=False)

    @property
    def prefix(self) -> str:
        parts = [f"doc={self.document_id}"]
        if self.job_id:
            parts.append(f"job={self.job_id}")
        if self.queue_name:
            parts.append(f"queue={self.queue_name}")
        if self.worker_name:
            parts.append(f"worker={self.worker_name}")
        return " | ".join(parts)


@dataclass
class StageTrace:
    """Captures timing and result for a single pipeline stage."""

    stage: str
    started_at: str
    ended_at: str = ""
    duration_ms: float = 0.0
    success: bool = False
    provider: str = ""
    model: str = ""
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    retry_count: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────
# Core logging functions
# ──────────────────────────────────────────────────────────


def _ts() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def log_stage_enter(ctx: PipelineContext, stage: str, **extra: Any) -> float:
    """Log that a stage is starting. Returns perf_counter for timing."""
    ts = _ts()
    extra_str = " ".join(f"{k}={v}" for k, v in extra.items()) if extra else ""
    logger.info(
        "▶ STAGE_START | %s | stage=%s | ts=%s%s",
        ctx.prefix,
        stage,
        ts,
        f" | {extra_str}" if extra_str else "",
    )
    return time.perf_counter()


def log_stage_exit(
    ctx: PipelineContext,
    stage: str,
    start_time: float,
    *,
    provider: str = "",
    model: str = "",
    **extra: Any,
) -> StageTrace:
    """Log successful completion of a stage."""
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    ts = _ts()
    prov = provider or ctx.provider
    mdl = model or ctx.model
    extra_str = " ".join(f"{k}={v}" for k, v in extra.items()) if extra else ""
    logger.info(
        "✔ STAGE_DONE  | %s | stage=%s | duration_ms=%.2f | provider=%s | model=%s | ts=%s%s",
        ctx.prefix,
        stage,
        elapsed_ms,
        prov,
        mdl,
        ts,
        f" | {extra_str}" if extra_str else "",
    )
    trace = StageTrace(
        stage=stage,
        started_at="",
        ended_at=ts,
        duration_ms=elapsed_ms,
        success=True,
        provider=prov,
        model=mdl,
        extra=dict(extra),
    )
    ctx._stages.append(trace)
    return trace


def log_stage_error(
    ctx: PipelineContext,
    stage: str,
    start_time: float,
    exc: BaseException,
    *,
    provider: str = "",
    model: str = "",
) -> StageTrace:
    """Log a stage failure with full exception context."""
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    ts = _ts()
    prov = provider or ctx.provider
    mdl = model or ctx.model
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    tb_str = "".join(tb)

    logger.error(
        "✘ STAGE_FAIL  | %s | stage=%s | duration_ms=%.2f | provider=%s | model=%s "
        "| exception_type=%s | exception_message=%s | retry_count=%d | ts=%s\n%s",
        ctx.prefix,
        stage,
        elapsed_ms,
        prov,
        mdl,
        type(exc).__qualname__,
        str(exc)[:500],
        ctx.retry_count,
        ts,
        tb_str,
    )
    trace = StageTrace(
        stage=stage,
        started_at="",
        ended_at=ts,
        duration_ms=elapsed_ms,
        success=False,
        provider=prov,
        model=mdl,
        error_type=type(exc).__qualname__,
        error_message=str(exc)[:500],
        stack_trace=tb_str,
        retry_count=ctx.retry_count,
    )
    ctx._stages.append(trace)
    return trace


@asynccontextmanager
async def instrument_stage(
    ctx: PipelineContext,
    stage: str,
    *,
    provider: str = "",
    model: str = "",
    **extra: Any,
) -> AsyncIterator[dict[str, Any]]:
    """Context manager that instruments a pipeline stage with enter/exit/error logging.

    Usage:
        async with instrument_stage(ctx, "extraction") as meta:
            result = await do_extraction()
            meta["extractor"] = result.extractor  # optional extra metadata
    """
    t0 = log_stage_enter(ctx, stage, **extra)
    meta: dict[str, Any] = {}
    try:
        yield meta
        # If meta contains 'model' or 'provider', use them as overrides
        effective_provider = meta.pop("provider", None) or provider
        effective_model = meta.pop("model", None) or model
        log_stage_exit(ctx, stage, t0, provider=effective_provider, model=effective_model, **meta)
    except BaseException as exc:
        effective_provider = meta.pop("provider", None) or provider
        effective_model = meta.pop("model", None) or model
        log_stage_error(ctx, stage, t0, exc, provider=effective_provider, model=effective_model)
        raise


# ──────────────────────────────────────────────────────────
# Worker-level lifecycle logging
# ──────────────────────────────────────────────────────────


def log_worker_pickup(ctx: PipelineContext) -> None:
    logger.info(
        "⚡ WORKER_PICKUP | %s | ts=%s",
        ctx.prefix,
        _ts(),
    )


def log_worker_exit(ctx: PipelineContext, *, success: bool, error: str = "") -> None:
    total_ms = round((time.perf_counter() - ctx._run_start) * 1000, 2)
    status = "SUCCESS" if success else "FAILED"
    logger.info(
        "⏹ WORKER_EXIT | %s | status=%s | total_duration_ms=%.2f | stages_completed=%d | ts=%s%s",
        ctx.prefix,
        status,
        total_ms,
        sum(1 for s in ctx._stages if s.success),
        _ts(),
        f" | error={error}" if error else "",
    )


def log_pipeline_summary(ctx: PipelineContext) -> None:
    """Emit a full chronological execution trace for the pipeline run."""
    lines = [
        "",
        "=" * 80,
        f"  PIPELINE TRACE | {ctx.prefix}",
        "=" * 80,
    ]
    for i, trace in enumerate(ctx._stages, 1):
        status = "✔" if trace.success else "✘"
        line = (
            f"  {i:>2}. {status} {trace.stage:<30} "
            f"{trace.duration_ms:>10.2f}ms  "
            f"provider={trace.provider or '-':<12} "
            f"model={trace.model or '-'}"
        )
        lines.append(line)
        if not trace.success:
            lines.append(f"      └─ {trace.error_type}: {trace.error_message[:200]}")
    total_ms = round((time.perf_counter() - ctx._run_start) * 1000, 2)
    lines.append("-" * 80)
    lines.append(f"  Total: {total_ms:.2f}ms | Stages: {len(ctx._stages)}")
    lines.append("=" * 80)
    logger.info("\n".join(lines))
