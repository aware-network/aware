from __future__ import annotations

from collections.abc import Awaitable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter
from typing import TypeVar

from aware_utils.logging import logger


_T = TypeVar("_T")
_CURRENT_API_INVOCATION_TRACE_TIMINGS: ContextVar[dict[str, float] | None] = (
    ContextVar(
        "aware_api_invocation_trace_timings",
        default=None,
    )
)


def _round_duration_s(duration_s: float) -> float:
    return round(max(duration_s, 0.0), 6)


def _format_fields(fields: Mapping[str, object]) -> str:
    parts = [
        f"{key}={value!r}" for key, value in sorted(fields.items()) if value is not None
    ]
    return " ".join(parts)


def _trace_timing_key(*, phase: str) -> str:
    return f"{phase}_s"


def _record_api_invocation_trace_timing(
    *,
    phase: str,
    duration_s: float,
) -> None:
    timings = _CURRENT_API_INVOCATION_TRACE_TIMINGS.get()
    if timings is None:
        return
    key = _trace_timing_key(phase=phase)
    timings[key] = round(timings.get(key, 0.0) + max(duration_s, 0.0), 6)


@contextmanager
def collect_api_invocation_trace_timings() -> Iterator[dict[str, float]]:
    timings: dict[str, float] = {}
    token = _CURRENT_API_INVOCATION_TRACE_TIMINGS.set(timings)
    try:
        yield timings
    finally:
        _CURRENT_API_INVOCATION_TRACE_TIMINGS.reset(token)


@contextmanager
def api_invocation_trace_phase(
    phase: str,
    **fields: object,
) -> Iterator[None]:
    started_at = perf_counter()
    formatted_fields = _format_fields(fields)
    logger.info(
        "API invocation trace started phase=%s%s",
        phase,
        f" {formatted_fields}" if formatted_fields else "",
    )
    try:
        yield
    except Exception as exc:
        duration_s = perf_counter() - started_at
        _record_api_invocation_trace_timing(phase=phase, duration_s=duration_s)
        logger.warning(
            "API invocation trace failed phase=%s duration_s=%.6f error=%r%s",
            phase,
            _round_duration_s(duration_s),
            exc,
            f" {formatted_fields}" if formatted_fields else "",
        )
        raise
    else:
        duration_s = perf_counter() - started_at
        _record_api_invocation_trace_timing(phase=phase, duration_s=duration_s)
        logger.info(
            "API invocation trace finished phase=%s duration_s=%.6f%s",
            phase,
            _round_duration_s(duration_s),
            f" {formatted_fields}" if formatted_fields else "",
        )


async def await_with_api_invocation_trace(
    awaitable: Awaitable[_T],
    *,
    phase: str,
    fields: Mapping[str, object] | None = None,
    **extra_fields: object,
) -> _T:
    trace_fields = {**dict(fields or {}), **extra_fields}
    started_at = perf_counter()
    formatted_fields = _format_fields(trace_fields)
    logger.info(
        "API invocation trace started phase=%s%s",
        phase,
        f" {formatted_fields}" if formatted_fields else "",
    )
    try:
        result = await awaitable
    except Exception as exc:
        duration_s = perf_counter() - started_at
        _record_api_invocation_trace_timing(phase=phase, duration_s=duration_s)
        logger.warning(
            "API invocation trace failed phase=%s duration_s=%.6f error=%r%s",
            phase,
            _round_duration_s(duration_s),
            exc,
            f" {formatted_fields}" if formatted_fields else "",
        )
        raise
    else:
        duration_s = perf_counter() - started_at
        _record_api_invocation_trace_timing(phase=phase, duration_s=duration_s)
        logger.info(
            "API invocation trace finished phase=%s duration_s=%.6f%s",
            phase,
            _round_duration_s(duration_s),
            f" {formatted_fields}" if formatted_fields else "",
        )
        return result


__all__ = [
    "api_invocation_trace_phase",
    "await_with_api_invocation_trace",
    "collect_api_invocation_trace_timings",
]
