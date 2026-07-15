from __future__ import annotations

from typing import Dict

from .config import LoggerConfig

_LOGGER_REGISTRY: Dict[str, LoggerConfig] = {}


def register_logger(
    name: str,
    *,
    level: str | None = None,
    handlers: list[str] | None = None,
    propagate: bool | None = None,
) -> None:
    """Register or update a logger configuration prior to calling configure_logging."""
    config = _LOGGER_REGISTRY.get(name, LoggerConfig())
    if level is not None:
        config.level = level
    if handlers is not None:
        config.handlers = handlers
    if propagate is not None:
        config.propagate = propagate
    _LOGGER_REGISTRY[name] = config


def clear_registry() -> None:
    """Remove all custom logger overrides."""
    _LOGGER_REGISTRY.clear()


def get_registry() -> Dict[str, LoggerConfig]:
    """Return a copy of the current logger registry."""
    return {name: cfg for name, cfg in _LOGGER_REGISTRY.items()}
