import io
import json
import logging
import sys

import pytest

from aware_utils.logging import (
    LogHelper,
    clear_registry,
    configure_logging,
    get_active_config,
    register_logger,
    reset_logging_state,
    set_logging_metrics_callback,
)
from aware_utils.logging.formatters import AwareColorFormatter, PlainFormatter

# @code-under-test: ../aware_utils/logging/__init__.py


@pytest.fixture(autouse=True)
def reset_logging():
    logging.disable(logging.NOTSET)
    reset_logging_state()
    clear_registry()
    yield
    reset_logging_state()
    clear_registry()
    logging.disable(logging.NOTSET)


@pytest.fixture(autouse=True)
def restore_metrics():
    set_logging_metrics_callback(None)
    yield
    set_logging_metrics_callback(None)


def test_default_configuration_sets_console_handler():
    config = configure_logging(profile="console", reset=True)
    assert config.root.level == "INFO"

    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert root_logger.handlers, "Root logger should have handlers"

    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream in {sys.stdout, getattr(sys, "__stdout__", None)}
    assert isinstance(handler.formatter, AwareColorFormatter)


def test_plain_profile_uses_plain_formatter():
    config = configure_logging(profile="plain", reset=True)
    assert config.root.level == "INFO"

    handler = logging.getLogger().handlers[0]
    assert isinstance(handler.formatter, PlainFormatter)


def test_environment_level_override(monkeypatch):
    monkeypatch.setenv("AWARE_LOG_LEVEL", "DEBUG")
    configure_logging(profile="console", reset=True)

    config = get_active_config()
    assert config is not None
    assert config.root.level == "DEBUG"
    assert logging.getLogger().level == logging.DEBUG


def test_register_logger_override_applies_to_logging_system():
    register_logger("aware.custom", level="DEBUG", propagate=False)
    configure_logging(profile="console", reset=True)

    config = get_active_config()
    assert config is not None
    assert "aware.custom" in config.loggers
    assert config.loggers["aware.custom"].level == "DEBUG"

    custom_logger = logging.getLogger("aware.custom")
    assert custom_logger.level == logging.DEBUG
    assert custom_logger.propagate is False


def test_log_helper_uses_active_logger(monkeypatch):
    configure_logging(profile="plain", reset=True)
    captured: list[str] = []

    original_info = logging.Logger.info

    def capture_info(self, msg, *args, **kwargs):
        captured.append(str(msg))
        return original_info(self, msg, *args, **kwargs)

    monkeypatch.setattr(logging.Logger, "info", capture_info)

    LogHelper.section("Title", description="Details")

    normalized = [message.lower() for message in captured]
    assert any("title" in message for message in normalized)
    assert any("details" in message for message in normalized)


def test_rotating_profile_writes_file(tmp_path, monkeypatch):
    log_file = tmp_path / "aware.log"
    monkeypatch.setenv("AWARE_LOG_PROFILE", "rotating")
    monkeypatch.setenv("AWARE_LOG_FILE", str(log_file))
    monkeypatch.setenv("AWARE_LOG_MAX_BYTES", str(1024 * 1024))
    monkeypatch.setenv("AWARE_LOG_LEVEL", "INFO")
    monkeypatch.delenv("AWARE_LOG_OVERRIDES", raising=False)
    configure_logging(profile="rotating", reset=True)

    logging.getLogger().info("rotating profile message")

    for handler in logging.getLogger().handlers:
        flush = getattr(handler, "flush", None)
        if flush:
            flush()
    logging.shutdown()

    assert log_file.exists()
    contents = log_file.read_text()
    assert "rotating profile message" in contents


def test_json_profile_outputs_structured(monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    monkeypatch.setenv("AWARE_LOG_LEVEL", "INFO")
    monkeypatch.delenv("AWARE_LOG_OVERRIDES", raising=False)

    configure_logging(profile="json", reset=True)
    logging.getLogger().info("json profile message")

    output = buffer.getvalue().strip()
    assert output, "Expected JSON log output"
    data = json.loads(output)
    assert data["message"] == "json profile message"
    assert data["level"] == "INFO"


def test_console_profile_does_not_error_when_stdout_is_swapped_and_closed(monkeypatch):
    """
    Regression:
    pytest capture can swap sys.stdout with a temporary stream and later close it.
    Logging handlers must not keep writing to the closed stream (ValueError: I/O operation on closed file).
    """

    first = io.StringIO()
    monkeypatch.setattr(sys, "stdout", first)
    monkeypatch.setenv("AWARE_LOG_LEVEL", "INFO")
    monkeypatch.delenv("AWARE_LOG_OVERRIDES", raising=False)

    configure_logging(profile="console", reset=True)

    second = io.StringIO()
    monkeypatch.setattr(sys, "stdout", second)
    first.close()

    logging.getLogger().info("stdout swap message")
    assert "stdout swap message" in second.getvalue()


def test_queue_console_profile_emits_and_reports_metrics(monkeypatch):
    emitted_messages: list[str] = []

    original_emit = logging.StreamHandler.emit

    def capture_emit(self, record):
        emitted_messages.append(record.getMessage())
        return original_emit(self, record)

    monkeypatch.setattr(logging.StreamHandler, "emit", capture_emit, raising=False)

    monkeypatch.setenv("AWARE_LOG_LEVEL", "INFO")
    monkeypatch.delenv("AWARE_LOG_OVERRIDES", raising=False)
    configure_logging(profile="queue_console", reset=True)

    metrics: list = []

    def metrics_callback(metric):
        metrics.append(metric)

    set_logging_metrics_callback(metrics_callback)

    logging.getLogger().info("queue profile message")

    reset_logging_state()

    assert any("queue profile message" in message for message in emitted_messages)
    assert metrics, "Expected metrics callback to be invoked"
    latest_metric = metrics[-1]
    assert latest_metric.handler_name == "queue_console"
    assert latest_metric.emitted >= 1
