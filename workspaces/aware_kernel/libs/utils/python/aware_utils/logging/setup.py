from __future__ import annotations

import logging
import logging.config
import os
from threading import Lock
from typing import Dict, Optional

from .config import LoggingConfig
from .handlers import shutdown_queue_listener
from .metrics import LoggingMetric, set_logging_metrics_callback
from .profiles import get_profile
from .registry import get_registry

_ACTIVE_CONFIG: Optional[LoggingConfig] = None
_CONFIG_LOCK = Lock()


def _merge_overrides(config: LoggingConfig, overrides: Optional[Dict[str, str]]) -> LoggingConfig:
    if not overrides:
        return config

    mutable = config.model_copy(deep=True)
    for name, level in overrides.items():
        if name == "root":
            mutable.root.level = level
            continue
        logger_config = mutable.loggers.get(name)
        if logger_config is None:
            logger_config = mutable.loggers[name] = mutable.root.model_copy(deep=True)
            logger_config.handlers = []
        logger_config.level = level
    return mutable


def _apply_environment_overrides(config: LoggingConfig) -> LoggingConfig:
    overrides: Dict[str, str] = {}
    level = os.environ.get("AWARE_LOG_LEVEL")
    if level:
        overrides["root"] = level

    override_str = os.environ.get("AWARE_LOG_OVERRIDES")
    if override_str:
        for item in override_str.split(","):
            if "=" not in item:
                continue
            logger_name, logger_level = item.split("=", 1)
            overrides[logger_name.strip()] = logger_level.strip()
    return _merge_overrides(config, overrides)


def _apply_metrics_environment() -> None:
    option = os.environ.get("AWARE_LOG_METRICS")

    if option == "stdout":

        def stdout_metrics(metric: LoggingMetric) -> None:
            print(
                f"[aware-logs] {metric.handler_name}: emitted={metric.emitted} "
                f"dropped={metric.dropped} queue={metric.queue_size}",
                flush=True,
            )

        set_logging_metrics_callback(stdout_metrics)
    elif option == "none":
        set_logging_metrics_callback(None)


def configure_logging(
    *,
    profile: Optional[str] = None,
    config: Optional[LoggingConfig] = None,
    overrides: Optional[Dict[str, str]] = None,
    reset: bool = True,
) -> LoggingConfig:
    """Configure logging using the declarative LoggingConfig model."""
    global _ACTIVE_CONFIG

    with _CONFIG_LOCK:
        target_config = config.model_copy(deep=True) if config is not None else get_profile(profile)
        target_config = _apply_environment_overrides(target_config)
        target_config = _merge_overrides(target_config, overrides)
        _apply_metrics_environment()

        registry = get_registry()
        if registry:
            for name, logger_cfg in registry.items():
                target_config.loggers[name] = logger_cfg.model_copy(deep=True)

        dict_config = target_config.to_dict()
        dict_config["root"].setdefault("handlers", target_config.root.handlers)
        dict_config.setdefault("loggers", {})
        dict_config.setdefault("handlers", {})
        dict_config.setdefault("formatters", {})
        dict_config["disable_existing_loggers"] = target_config.disable_existing_loggers

        if reset:
            shutdown_queue_listener()
            for logger in [logging.getLogger(name) for name in logging.root.manager.loggerDict.keys()]:
                for handler in getattr(logger, "handlers", []):
                    logger.removeHandler(handler)
                    handler.close()
            for handler in logging.getLogger().handlers[:]:
                logging.getLogger().removeHandler(handler)
                handler.close()

        logging.config.dictConfig(dict_config)

        _ACTIVE_CONFIG = target_config

    return _ACTIVE_CONFIG


def get_active_config() -> Optional[LoggingConfig]:
    return _ACTIVE_CONFIG


def reset_logging_state() -> None:
    """Clear cached configuration and shutdown existing handlers."""
    global _ACTIVE_CONFIG
    with _CONFIG_LOCK:
        shutdown_queue_listener()
        set_logging_metrics_callback(None)
        logging.shutdown()
        _ACTIVE_CONFIG = None
