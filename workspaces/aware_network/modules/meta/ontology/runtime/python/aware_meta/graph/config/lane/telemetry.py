from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Protocol


class SeedTimings(Protocol):
    def add(self, name: str, duration_s: float) -> object: ...

    def metric(self, key: str, value: object) -> object: ...


@contextmanager
def maybe_timed(timings: SeedTimings | None, name: str) -> Iterator[None]:
    """Record a timing substep on a best-effort basis."""
    if timings is None:
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        try:
            _ = timings.add(name, time.perf_counter() - start)
        except Exception:
            pass


def maybe_metric(timings: SeedTimings | None, key: str, value: object) -> None:
    if timings is None or not key:
        return
    try:
        _ = timings.metric(key, value)
    except Exception:
        pass


def maybe_record_orm_session_metrics(*, timings: SeedTimings | None, key_prefix: str) -> None:
    """Best-effort metrics for ORM session/autobind impact on commit rail performance."""
    if not (key_prefix or "").strip():
        return
    try:
        from aware_orm.session.autobind import is_autobind_enabled
        from aware_orm.session.current_session_ctx import current_session_context
    except Exception:
        return

    try:
        ctx = current_session_context()
    except Exception:
        ctx = None

    maybe_metric(timings, f"{key_prefix}_session_context_active", bool(ctx is not None))
    try:
        maybe_metric(timings, f"{key_prefix}_autobind_enabled", bool(is_autobind_enabled()))
    except Exception:
        pass
    if ctx is not None:
        try:
            maybe_metric(timings, f"{key_prefix}_identity_map_size", int(ctx.session.size()))
        except Exception:
            pass


__all__ = [
    "SeedTimings",
    "maybe_metric",
    "maybe_record_orm_session_metrics",
    "maybe_timed",
]
