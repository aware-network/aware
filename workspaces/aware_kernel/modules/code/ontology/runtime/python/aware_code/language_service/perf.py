from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from collections.abc import Iterator
from dataclasses import dataclass

from aware_code.language_service.json_rpc import JsonValue


@dataclass(frozen=True, slots=True)
class PerfConfig:
    enabled: bool = False
    threshold_ms: float = 0.0


class PerfTracer:
    """Minimal perf tracer for LSP/server diagnostics.

    IMPORTANT: Logging must never write to stdout (LSP protocol stream). The CLI
    configures logging to stderr; we rely on that contract.
    """

    _config: PerfConfig
    _logger: logging.Logger

    def __init__(self, *, config: PerfConfig | None = None, logger: logging.Logger | None = None) -> None:
        self._config = config or PerfConfig(enabled=False, threshold_ms=0.0)
        self._logger = logger or logging.getLogger("aware.language_service.perf")

    @property
    def enabled(self) -> bool:
        return bool(self._config.enabled)

    @contextmanager
    def span(self, name: str, **meta: JsonValue | None) -> Iterator[None]:
        if not self._config.enabled:
            yield
            return
        start = time.perf_counter()
        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            if duration_ms < self._config.threshold_ms:
                return
            # Keep meta compact to avoid log spam.
            safe_meta = {k: v for k, v in meta.items() if v is not None}
            self._logger.info("perf %s %.2fms %s", name, duration_ms, safe_meta)


__all__ = ["PerfConfig", "PerfTracer"]
