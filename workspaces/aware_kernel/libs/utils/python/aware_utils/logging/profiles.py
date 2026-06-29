from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict

from typing import Callable

from .config import (
    FormatterConfig,
    HandlerConfig,
    LoggingConfig,
    LoggerConfig,
    RootLoggerConfig,
)
from .formatters import AwareColorFormatter, JSONFormatter, PlainFormatter
from .handlers import (
    AwareStreamHandler,
    queue_listener_config,
    rotating_file_handler_config,
)

DEFAULT_MESSAGE_FORMAT = (
    "%(asctime)s - %(purple)s%(name)s%(reset)s - %(log_color)s%(levelname)s%(reset)s - %(message_log_color)s%(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

PROFILE_BUILDERS: Dict[str, Callable[[], LoggingConfig]] = {}
CUSTOM_PROFILES: Dict[str, LoggingConfig] = {}


def _console_profile(default_level: str = "INFO") -> LoggingConfig:
    formatter = FormatterConfig(
        factory=AwareColorFormatter,
        format=DEFAULT_MESSAGE_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )
    handler = HandlerConfig(
        factory=lambda: AwareStreamHandler(target_stream="stdout"),
        level="DEBUG",
        formatter="aware_color",
    )
    root_logger = RootLoggerConfig(level=default_level, handlers=["console"])
    return LoggingConfig(
        root=root_logger,
        handlers={"console": handler},
        formatters={"aware_color": formatter},
    )


def _plain_profile(default_level: str = "INFO") -> LoggingConfig:
    formatter = FormatterConfig(
        factory=PlainFormatter,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=DEFAULT_DATE_FORMAT,
    )
    handler = HandlerConfig(
        factory=lambda: AwareStreamHandler(target_stream="stdout"),
        level="DEBUG",
        formatter="plain",
    )
    root_logger = RootLoggerConfig(level=default_level, handlers=["console"])
    return LoggingConfig(
        root=root_logger,
        handlers={"console": handler},
        formatters={"plain": formatter},
    )


def _rotating_profile(default_level: str = "INFO") -> LoggingConfig:
    log_file_env = os.environ.get("AWARE_LOG_FILE")
    log_file = Path(log_file_env) if log_file_env else Path.home() / "aware_logs" / "aware.log"
    max_bytes = int(os.environ.get("AWARE_LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    backup_count = int(os.environ.get("AWARE_LOG_BACKUP_COUNT", "5"))
    handler_level = os.environ.get("AWARE_LOG_FILE_LEVEL", default_level)

    formatter = FormatterConfig(
        factory=PlainFormatter,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=DEFAULT_DATE_FORMAT,
    )

    handler = rotating_file_handler_config(
        filename=log_file,
        level=handler_level,
        formatter="plain",
        max_bytes=max_bytes,
        backup_count=backup_count,
    )

    root_logger = RootLoggerConfig(level=default_level, handlers=["file"])
    return LoggingConfig(
        root=root_logger,
        handlers={"file": handler},
        formatters={"plain": formatter},
    )


def _json_profile(default_level: str = "INFO") -> LoggingConfig:
    formatter = FormatterConfig(
        factory=JSONFormatter,
        extra={"ensure_ascii": False},
    )
    handler = HandlerConfig(
        factory=lambda: AwareStreamHandler(target_stream="stdout"),
        level="DEBUG",
        formatter="aware_json",
    )
    root_logger = RootLoggerConfig(level=default_level, handlers=["console"])
    return LoggingConfig(
        root=root_logger,
        handlers={"console": handler},
        formatters={"aware_json": formatter},
    )


def _lsp_profile(default_level: str = "INFO") -> LoggingConfig:
    """Profile suitable for stdio-based LSP servers.

    LSP uses stdout for protocol frames, so logs must go to stderr.
    """
    formatter = FormatterConfig(
        factory=PlainFormatter,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=DEFAULT_DATE_FORMAT,
    )
    handler = HandlerConfig(
        factory=lambda: AwareStreamHandler(target_stream="stderr"),
        level="DEBUG",
        formatter="plain",
    )
    root_logger = RootLoggerConfig(level=default_level, handlers=["console"])
    return LoggingConfig(
        root=root_logger,
        handlers={"console": handler},
        formatters={"plain": formatter},
    )


def _queue_console_profile(default_level: str = "INFO") -> LoggingConfig:
    formatter = FormatterConfig(
        factory=AwareColorFormatter,
        format=DEFAULT_MESSAGE_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    def stream_handler_factory() -> logging.Handler:
        return logging.StreamHandler()

    def formatter_factory() -> logging.Formatter:
        return AwareColorFormatter(fmt=DEFAULT_MESSAGE_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    handler = queue_listener_config(
        handler_factory=stream_handler_factory,
        formatter_factory=formatter_factory,
        name="queue_console",
    )
    handler.level = "DEBUG"
    handler.formatter = "aware_color"

    root_logger = RootLoggerConfig(level=default_level, handlers=["queue_console"])
    return LoggingConfig(
        root=root_logger,
        handlers={"queue_console": handler},
        formatters={"aware_color": formatter},
    )


PROFILE_BUILDERS["console"] = _console_profile
PROFILE_BUILDERS["plain"] = _plain_profile
PROFILE_BUILDERS["rotating"] = _rotating_profile
PROFILE_BUILDERS["json"] = _json_profile
PROFILE_BUILDERS["lsp"] = _lsp_profile
PROFILE_BUILDERS["queue_console"] = _queue_console_profile


def get_profile(name: str | None) -> LoggingConfig:
    """Return a copy of the requested profile."""
    if not name:
        name = os.environ.get("AWARE_LOG_PROFILE", "console")
    if name in CUSTOM_PROFILES:
        return CUSTOM_PROFILES[name].model_copy(deep=True)
    builder = PROFILE_BUILDERS.get(name)
    if builder is None:
        raise KeyError(f"Logging profile '{name}' is not defined.")
    return builder().model_copy(deep=True)


def list_profiles() -> Dict[str, LoggingConfig]:
    profiles: Dict[str, LoggingConfig] = {
        name: builder().model_copy(deep=True) for name, builder in PROFILE_BUILDERS.items()
    }
    profiles.update({name: cfg.model_copy(deep=True) for name, cfg in CUSTOM_PROFILES.items()})
    return profiles


def register_profile(name: str, config: LoggingConfig) -> None:
    CUSTOM_PROFILES[name] = config.model_copy(deep=True)
