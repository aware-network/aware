from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from queue import Queue
from threading import RLock
from typing import Callable, Optional

from .config import HandlerConfig
from .metrics import LoggingMetric, emit_logging_metric


_QUEUE: Optional[Queue] = None
_QUEUE_LISTENER: Optional[logging.handlers.QueueListener] = None
_QUEUE_LOCK = RLock()


class AwareStreamHandler(logging.StreamHandler):
    """
    StreamHandler that is resilient to pytest's capture swapping/closing sys.stdout/sys.stderr.

    Why:
    - pytest capture can temporarily replace sys.stdout/sys.stderr with a file-like object
      which may be closed when capture is stopped.
    - if a logging handler captures that stream at configuration time, later log writes can
      raise ValueError("I/O operation on closed file"), producing extremely noisy "Logging error"
      traces that obscure the real test failure.

    Contract:
    - when `target_stream` is set ("stdout" or "stderr"), the handler re-resolves the active
      stream on every emit and falls back to sys.__stdout__/sys.__stderr__ if needed.
    - when `target_stream` is None, this behaves like a normal StreamHandler.
    """

    def __init__(self, stream=None, target_stream: str | None = "stdout"):
        self._target_stream = target_stream
        if target_stream in {"stdout", "stderr"}:
            super().__init__(stream=self._resolve_target_stream())
        else:
            super().__init__(stream=stream)

    def _resolve_target_stream(self):
        if self._target_stream == "stderr":
            candidate = sys.stderr
            fallback = getattr(sys, "__stderr__", None)
        else:
            candidate = sys.stdout
            fallback = getattr(sys, "__stdout__", None)

        if getattr(candidate, "closed", False) and fallback is not None and not getattr(fallback, "closed", False):
            return fallback
        return candidate

    def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        if self._target_stream in {"stdout", "stderr"}:
            self.stream = self._resolve_target_stream()

        try:
            super().emit(record)
        except ValueError:
            # Closed capture stream (common under pytest). Fall back to the original stdio stream.
            try:
                self.stream = self._resolve_target_stream()
                super().emit(record)
            except Exception:
                # Drop the log rather than emitting a secondary "Logging error" traceback.
                return


class MetricsQueueListener(logging.handlers.QueueListener):
    def __init__(self, queue: Queue, *handlers: logging.Handler, name: str = "queue_listener"):
        super().__init__(queue, *handlers)
        self.name = name
        self._processed = 0
        self._dropped = 0

    def handle(self, record: logging.LogRecord) -> None:  # type: ignore[override]
        self._processed += 1
        try:
            super().handle(record)
        except Exception:
            self._dropped += 1
            raise
        emit_logging_metric(
            LoggingMetric(
                handler_name=self.name,
                emitted=self._processed,
                dropped=self._dropped,
                queue_size=self.queue.qsize(),
            )
        )

    def stop(self) -> None:  # type: ignore[override]
        super().stop()
        emit_logging_metric(
            LoggingMetric(
                handler_name=self.name,
                emitted=self._processed,
                dropped=self._dropped,
                queue_size=self.queue.qsize(),
            )
        )


def ensure_queue_listener(
    handler_factory: Callable[[], logging.Handler],
    formatter_factory: Callable[[], logging.Formatter],
    name: str = "queue_console",
) -> tuple[Queue, logging.handlers.QueueListener]:
    global _QUEUE, _QUEUE_LISTENER
    with _QUEUE_LOCK:
        if _QUEUE is None:
            _QUEUE = Queue()
        if _QUEUE_LISTENER is None:
            listener_handler = handler_factory()
            listener_handler.setFormatter(formatter_factory())
            listener = MetricsQueueListener(_QUEUE, listener_handler, name=name)
            listener.start()
            _QUEUE_LISTENER = listener
        return _QUEUE, _QUEUE_LISTENER


def shutdown_queue_listener() -> None:
    global _QUEUE_LISTENER, _QUEUE
    with _QUEUE_LOCK:
        if _QUEUE_LISTENER is not None:
            _QUEUE_LISTENER.stop()
            _QUEUE_LISTENER = None
        _QUEUE = None


def queue_listener_config(
    handler_factory: Callable[[], logging.Handler],
    formatter_factory: Callable[[], logging.Formatter],
    name: str = "queue_console",
) -> HandlerConfig:
    def queue_handler_factory() -> logging.handlers.QueueHandler:
        queue, _ = ensure_queue_listener(handler_factory, formatter_factory, name=name)
        return logging.handlers.QueueHandler(queue)

    return HandlerConfig(factory=queue_handler_factory)


def rotating_file_handler_config(
    *,
    filename: Path,
    level: str = "INFO",
    formatter: str = "plain",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> HandlerConfig:
    filename.parent.mkdir(parents=True, exist_ok=True)

    def rotating_handler_factory() -> logging.Handler:
        handler = logging.handlers.RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        return handler

    return HandlerConfig(factory=rotating_handler_factory, level=level, formatter=formatter)
