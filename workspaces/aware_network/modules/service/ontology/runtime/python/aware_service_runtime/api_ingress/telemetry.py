from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter
from typing import TypeVar

from aware_utils.logging import logger


_T = TypeVar("_T")
_CURRENT_SERVICE_API_TRACE_TIMINGS: ContextVar[dict[str, float] | None] = ContextVar(
    "aware_service_api_trace_timings",
    default=None,
)


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


def _format_fields(fields: dict[str, object]) -> str:
    parts = [
        f"{key}={value!r}" for key, value in sorted(fields.items()) if value is not None
    ]
    return " ".join(parts)


def _trace_timing_key(*, phase: str) -> str:
    return f"{phase}_s"


def _record_service_api_trace_timing(
    *,
    phase: str,
    duration_s: float,
) -> None:
    timings = _CURRENT_SERVICE_API_TRACE_TIMINGS.get()
    if timings is None:
        return
    key = _trace_timing_key(phase=phase)
    timings[key] = round(timings.get(key, 0.0) + max(duration_s, 0.0), 6)


def record_service_api_trace_timing(
    *,
    phase: str,
    duration_s: float,
) -> None:
    """Record an externally measured child phase in the active Service API trace."""

    _record_service_api_trace_timing(phase=phase, duration_s=duration_s)


@contextmanager
def collect_service_api_trace_timings() -> Iterator[dict[str, float]]:
    """Collect Service API trace timings for the current request context."""

    timings: dict[str, float] = {}
    token = _CURRENT_SERVICE_API_TRACE_TIMINGS.set(timings)
    try:
        yield timings
    finally:
        _CURRENT_SERVICE_API_TRACE_TIMINGS.reset(token)


@contextmanager
def service_api_trace_phase(
    phase: str,
    **fields: object,
) -> Iterator[None]:
    started_at = perf_counter()
    formatted_fields = _format_fields(fields)
    logger.info(
        "Service API trace started phase=%s%s",
        phase,
        f" {formatted_fields}" if formatted_fields else "",
    )
    try:
        yield
    except Exception as exc:
        duration_s = perf_counter() - started_at
        _record_service_api_trace_timing(phase=phase, duration_s=duration_s)
        logger.warning(
            "Service API trace failed phase=%s duration_s=%.6f error=%r%s",
            phase,
            _round_duration_s(duration_s),
            exc,
            f" {formatted_fields}" if formatted_fields else "",
        )
        raise
    else:
        duration_s = perf_counter() - started_at
        _record_service_api_trace_timing(phase=phase, duration_s=duration_s)
        logger.info(
            "Service API trace finished phase=%s duration_s=%.6f%s",
            phase,
            _round_duration_s(duration_s),
            f" {formatted_fields}" if formatted_fields else "",
        )


async def await_with_service_api_trace(
    awaitable: Awaitable[_T],
    *,
    phase: str,
    fields: Mapping[str, object] | None = None,
    heartbeat_s: float = 10.0,
    **extra_fields: object,
) -> _T:
    trace_fields = {**dict(fields or {}), **extra_fields}
    started_at = perf_counter()
    formatted_fields = _format_fields(trace_fields)
    logger.info(
        "Service API trace started phase=%s%s",
        phase,
        f" {formatted_fields}" if formatted_fields else "",
    )
    task = asyncio.ensure_future(awaitable)

    async def _heartbeat() -> None:
        while not task.done():
            await asyncio.sleep(heartbeat_s)
            if task.done():
                return
            logger.info(
                "Service API trace heartbeat phase=%s elapsed_s=%.6f%s",
                phase,
                _round_duration_s(perf_counter() - started_at),
                f" {formatted_fields}" if formatted_fields else "",
            )

    heartbeat_task: asyncio.Task[None] | None = None
    if heartbeat_s > 0:
        heartbeat_task = asyncio.create_task(_heartbeat())
    try:
        result = await task
    except Exception as exc:
        duration_s = perf_counter() - started_at
        _record_service_api_trace_timing(phase=phase, duration_s=duration_s)
        logger.warning(
            "Service API trace failed phase=%s duration_s=%.6f error=%r%s",
            phase,
            _round_duration_s(duration_s),
            exc,
            f" {formatted_fields}" if formatted_fields else "",
        )
        raise
    else:
        duration_s = perf_counter() - started_at
        _record_service_api_trace_timing(phase=phase, duration_s=duration_s)
        logger.info(
            "Service API trace finished phase=%s duration_s=%.6f%s",
            phase,
            _round_duration_s(duration_s),
            f" {formatted_fields}" if formatted_fields else "",
        )
        return result
    finally:
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            await asyncio.gather(heartbeat_task, return_exceptions=True)


__all__ = [
    "await_with_service_api_trace",
    "collect_service_api_trace_timings",
    "record_service_api_trace_timing",
    "service_api_trace_phase",
]
