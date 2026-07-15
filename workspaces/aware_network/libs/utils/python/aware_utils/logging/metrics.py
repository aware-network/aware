from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Callable, Optional


@dataclass(frozen=True)
class LoggingMetric:
    handler_name: str
    emitted: int
    dropped: int
    queue_size: Optional[int] = None


_metrics_callback: Optional[Callable[[LoggingMetric], None]] = None
_metrics_lock = RLock()


def set_logging_metrics_callback(callback: Optional[Callable[[LoggingMetric], None]]) -> None:
    """Register a metrics callback for logging events."""
    global _metrics_callback
    with _metrics_lock:
        _metrics_callback = callback


def emit_logging_metric(metric: LoggingMetric) -> None:
    callback = _metrics_callback
    if callback:
        callback(metric)
