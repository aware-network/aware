from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class FormatterConfig(BaseModel):
    """Configuration for logging formatters."""

    factory: Union[str, Any] = Field(..., description="Formatter class or import path.")
    format: Optional[str] = Field(default=None, description="Message format string.")
    datefmt: Optional[str] = Field(default=None, description="Datetime format string.")
    style: str = Field(default="%", description="Formatting style (% | { | $).")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional keyword arguments.")

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"()": self.factory}
        if self.format is not None:
            data["format"] = self.format
        if self.datefmt is not None:
            data["datefmt"] = self.datefmt
        if self.style != "%":
            data["style"] = self.style
        data.update(self.extra)
        return data


class HandlerConfig(BaseModel):
    """Configuration for logging handlers."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    class_path: Optional[str] = Field(default=None, description="Import path of the handler class.")
    factory: Optional[Any] = Field(
        default=None,
        description="Callable factory used when class_path is not provided.",
    )
    level: Optional[str] = Field(default=None, description="Handler log level.")
    formatter: Optional[str] = Field(default=None, description="Formatter key associated with handler.")
    stream: Optional[str] = Field(default=None, description="Stream path (e.g., ext://sys.stdout).")
    filename: Optional[str] = Field(default=None, description="Filename for file handlers.")
    max_bytes: Optional[int] = Field(default=None, description="Max bytes for rotating handlers.")
    backup_count: Optional[int] = Field(default=None, description="Backup count for rotating handlers.")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional keyword arguments.")

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any]
        if self.factory is not None:
            data = {"()": self.factory}
        elif self.class_path is not None:
            data = {"class": self.class_path}
        else:
            raise ValueError("HandlerConfig requires either class_path or factory.")

        if self.level is not None:
            data["level"] = self.level
        if self.formatter is not None:
            data["formatter"] = self.formatter
        if self.stream is not None:
            data["stream"] = self.stream
        if self.filename is not None:
            data["filename"] = self.filename
        if self.max_bytes is not None:
            data["maxBytes"] = self.max_bytes
        if self.backup_count is not None:
            data["backupCount"] = self.backup_count
        data.update(self.extra)
        return data


class LoggerConfig(BaseModel):
    """Configuration for an individual logger."""

    level: Optional[str] = Field(default=None)
    handlers: List[str] = Field(default_factory=list)
    propagate: Optional[bool] = Field(default=None)
    filters: List[str] = Field(default_factory=list)
    qualname: Optional[str] = Field(default=None)
    extra: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if self.level is not None:
            data["level"] = self.level
        if self.handlers:
            data["handlers"] = self.handlers
        if self.propagate is not None:
            data["propagate"] = self.propagate
        if self.filters:
            data["filters"] = self.filters
        data.update(self.extra)
        return data


class RootLoggerConfig(LoggerConfig):
    """Configuration for the root logger."""

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        return data


class LoggingConfig(BaseModel):
    """Top-level logging configuration."""

    version: int = Field(default=1)
    disable_existing_loggers: bool = Field(default=False)
    root: RootLoggerConfig = Field(default_factory=RootLoggerConfig)
    loggers: Dict[str, LoggerConfig] = Field(default_factory=dict)
    handlers: Dict[str, HandlerConfig] = Field(default_factory=dict)
    formatters: Dict[str, FormatterConfig] = Field(default_factory=dict)
    filters: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    profiles: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "disable_existing_loggers": self.disable_existing_loggers,
            "root": self.root.to_dict(),
            "loggers": {name: cfg.to_dict() for name, cfg in self.loggers.items()},
            "handlers": {name: cfg.to_dict() for name, cfg in self.handlers.items()},
            "formatters": {name: cfg.to_dict() for name, cfg in self.formatters.items()},
            "filters": self.filters,
        }
