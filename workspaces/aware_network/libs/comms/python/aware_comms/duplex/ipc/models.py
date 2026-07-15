"""Shared IPC endpoint models for duplex transports."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class DuplexIpcTransportKind(str, Enum):
    """Concrete local IPC transport kinds supported by aware_comms."""

    STDIO = "stdio"
    UNIX_SOCKET = "unix_socket"


class DuplexIpcEndpoint(BaseModel):
    """Transport-only endpoint definition for local duplex IPC."""

    transport: DuplexIpcTransportKind
    command: list[str] = Field(default_factory=list)
    socket_path: str | None = None
    working_directory: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_shape(self) -> "DuplexIpcEndpoint":
        if self.transport is DuplexIpcTransportKind.STDIO:
            if not self.command:
                raise ValueError(
                    "stdio IPC endpoints require at least one command item"
                )
            if self.socket_path is not None:
                raise ValueError("stdio IPC endpoints must not define socket_path")
        elif self.transport is DuplexIpcTransportKind.UNIX_SOCKET:
            if not self.socket_path:
                raise ValueError("unix_socket IPC endpoints require socket_path")
            if self.command:
                raise ValueError("unix_socket IPC endpoints must not define command")
        return self

    @classmethod
    def stdio(
        cls,
        *,
        command: list[str],
        working_directory: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> "DuplexIpcEndpoint":
        return cls(
            transport=DuplexIpcTransportKind.STDIO,
            command=list(command),
            working_directory=working_directory,
            environment=dict(environment or {}),
        )

    @classmethod
    def unix_socket(cls, *, socket_path: str) -> "DuplexIpcEndpoint":
        return cls(
            transport=DuplexIpcTransportKind.UNIX_SOCKET,
            socket_path=socket_path,
        )


__all__ = ["DuplexIpcEndpoint", "DuplexIpcTransportKind"]
