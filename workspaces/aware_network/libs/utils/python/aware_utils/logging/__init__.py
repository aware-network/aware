"""
Extensible logging utilities for the Aware platform.

This package provides a structured configuration pipeline while keeping the
original `from aware_utils.logging import logger` contract intact.
"""

# @doc-ref: ../docs/logging.md
# @test-ref: ../tests/logging/test_logging_configuration.py

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .config import LoggingConfig
from .metrics import set_logging_metrics_callback
from .profiles import get_profile, list_profiles, register_profile
from .registry import clear_registry, get_registry, register_logger
from .setup import configure_logging, get_active_config, reset_logging_state

__all__ = [
    "configure_logging",
    "get_active_config",
    "get_profile",
    "list_profiles",
    "register_profile",
    "register_logger",
    "get_registry",
    "clear_registry",
    "set_logging_metrics_callback",
    "reset_logging_state",
    "logger",
    "LogHelper",
    "log_section",
    "log_stage",
    "log_substage",
    "log_progress",
    "log_success",
    "log_warning",
    "log_error",
    "log_summary",
    "log_metrics",
    "log_file_ops",
    "log_changes",
    "log_debug",
    "log_separator",
]


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name)


class LogHelper:
    """Helper class for structured, colorful logging in evolution pipeline."""

    @staticmethod
    def _logger() -> logging.Logger:
        return get_logger()

    @classmethod
    def section(cls, title: str, description: Optional[str] = None):
        logger = cls._logger()
        logger.info("=" * 80, stacklevel=2)
        if description:
            logger.info(f"🚀 {title.upper()}", stacklevel=2)
            logger.info(f"   {description}", stacklevel=2)
        else:
            logger.info(f"🚀 {title.upper()}", stacklevel=2)
        logger.info("=" * 80, stacklevel=2)

    @classmethod
    def stage(cls, step_num: int, title: str, description: Optional[str] = None):
        logger = cls._logger()
        if description:
            logger.info(f"📋 STEP {step_num}: {title}", stacklevel=2)
            logger.info(f"   {description}", stacklevel=2)
        else:
            logger.info(f"📋 STEP {step_num}: {title}", stacklevel=2)

    @classmethod
    def substage(cls, title: str, level: int = 1):
        logger = cls._logger()
        indent = "   " * level
        logger.info(f"{indent}⚙️  {title}", stacklevel=2)

    @classmethod
    def progress(cls, message: str, details: Optional[str] = None):
        logger = cls._logger()
        if details:
            logger.info(f"🔄 {message}", stacklevel=2)
            logger.info(f"   {details}", stacklevel=2)
        else:
            logger.info(f"🔄 {message}", stacklevel=2)

    @classmethod
    def success(cls, message: str, details: Optional[str] = None):
        logger = cls._logger()
        if details:
            logger.info(f"✅ {message}", stacklevel=2)
            logger.info(f"   {details}", stacklevel=2)
        else:
            logger.info(f"✅ {message}", stacklevel=2)

    @classmethod
    def warning(cls, message: str, details: Optional[str] = None):
        logger = cls._logger()
        if details:
            logger.warning(f"⚠️  {message}", stacklevel=2)
            logger.warning(f"   {details}", stacklevel=2)
        else:
            logger.warning(f"⚠️  {message}", stacklevel=2)

    @classmethod
    def error(cls, message: str, details: Optional[str] = None):
        logger = cls._logger()
        if details:
            logger.error(f"❌ {message}", stacklevel=2)
            logger.error(f"   {details}", stacklevel=2)
        else:
            logger.error(f"❌ {message}", stacklevel=2)

    @classmethod
    def summary(cls, title: str, items: list[str], show_count: bool = True):
        logger = cls._logger()
        if show_count:
            logger.info(f"📊 {title} ({len(items)} items)", stacklevel=2)
        else:
            logger.info(f"📊 {title}", stacklevel=2)
        for item in items:
            logger.info(f"   • {item}", stacklevel=2)

    @classmethod
    def metrics(cls, title: str, metrics: Dict[str, Any]):
        logger = cls._logger()
        logger.info(f"📈 {title}", stacklevel=2)
        for key, value in metrics.items():
            logger.info(f"   {key}: {value}", stacklevel=2)

    @classmethod
    def file_ops(cls, operation: str, files: list[str], show_paths: bool = False):
        logger = cls._logger()
        if len(files) <= 3 or show_paths:
            logger.info(f"📁 {operation}: {len(files)} files", stacklevel=2)
            for file in files:
                logger.info(f"   📄 {file}", stacklevel=2)
        else:
            logger.info(f"📁 {operation}: {len(files)} files", stacklevel=2)
            for file in files[:2]:
                logger.info(f"   📄 {file}", stacklevel=2)
            logger.info(f"   📄 ... and {len(files) - 2} more files", stacklevel=2)

    @classmethod
    def changes(cls, changes: list[str], title: str = "Changes Applied"):
        logger = cls._logger()
        if not changes:
            logger.info(f"📝 {title}: No changes", stacklevel=2)
            return
        logger.info(f"📝 {title} ({len(changes)})", stacklevel=2)
        for idx, change in enumerate(changes, start=1):
            short = change if len(change) <= 100 else f"{change[:97]}..."
            logger.info(f"   {idx}. {short}", stacklevel=2)

    @classmethod
    def debug_only(cls, message: str, details: Optional[str] = None):
        logger = cls._logger()
        if details:
            logger.debug(f"🔍 {message}", stacklevel=2)
            logger.debug(f"   {details}", stacklevel=2)
        else:
            logger.debug(f"🔍 {message}", stacklevel=2)

    @classmethod
    def separator(cls):
        logger = cls._logger()
        logger.info("-" * 60, stacklevel=2)


def _initialize_default_logging() -> LoggingConfig:
    active = get_active_config()
    if active is not None:
        return active
    return configure_logging(reset=True)


_initialize_default_logging()

logger = get_logger()

log_section = LogHelper.section
log_stage = LogHelper.stage
log_substage = LogHelper.substage
log_progress = LogHelper.progress
log_success = LogHelper.success
log_warning = LogHelper.warning
log_error = LogHelper.error
log_summary = LogHelper.summary
log_metrics = LogHelper.metrics
log_file_ops = LogHelper.file_ops
log_changes = LogHelper.changes
log_debug = LogHelper.debug_only
log_separator = LogHelper.separator
