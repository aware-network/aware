from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import colorlog


DEFAULT_LOG_COLORS: Dict[str, str] = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "light_red",
    "CRITICAL": "light_red,bg_white",
}

DEFAULT_SECONDARY_COLORS: Dict[str, Dict[str, str]] = {
    "message": {
        "DEBUG": "black",
        "INFO": "light_white",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    }
}


class AwareColorFormatter(colorlog.ColoredFormatter):
    """Colored formatter that preserves multiline readability."""

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        log_colors: Optional[Dict[str, str]] = None,
        secondary_log_colors: Optional[Dict[str, Dict[str, str]]] = None,
        **kwargs: Any,
    ):
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            log_colors=log_colors or DEFAULT_LOG_COLORS,
            secondary_log_colors=secondary_log_colors or DEFAULT_SECONDARY_COLORS,
            **kwargs,
        )

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        if "\n" not in rendered:
            return rendered

        color_code = "\033[30m" if record.levelno == logging.DEBUG else "\033[37m"
        lines = rendered.split("\n")
        if len(lines) <= 1:
            return rendered
        first_line, rest = lines[0], lines[1:]
        rest_colored = [f"{color_code}{line}\033[0m" for line in rest]
        return "\n".join([first_line, *rest_colored])


class PlainFormatter(logging.Formatter):
    """Simple non-colored formatter used for non-TTY environments."""

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        **kwargs: Any,
    ):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)


class JSONFormatter(logging.Formatter):
    """Structured JSON formatter for logging records."""

    def __init__(self, *, ensure_ascii: bool = False, **kwargs: Any):
        super().__init__(**kwargs)
        self.ensure_ascii = ensure_ascii

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            data["stack_info"] = record.stack_info
        for attr in ("request_id", "trace_id", "span_id"):
            if hasattr(record, attr):
                data[attr] = getattr(record, attr)
        return json.dumps(data, ensure_ascii=self.ensure_ascii)
