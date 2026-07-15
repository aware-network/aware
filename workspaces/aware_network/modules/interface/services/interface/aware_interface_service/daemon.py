from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
from uuid import uuid4

from aware_utils.logging import logger

from aware_interface_service.app import (
    InterfaceHostServiceBundleFactory,
    InterfaceHostServiceConfig,
)
from aware_interface_service.control_plane import (
    InterfaceDaemonMetadata,
    InterfaceControlPlane,
    InterfaceControlPlaneServer,
)
from aware_interface_service.fingerprint import compute_daemon_source_fingerprint
from aware_interface_service.namespace_registry import InterfaceNamespaceRegistry


_DEFAULT_CONTROL_SOCKET_FILENAME = "interface-control.sock"
_DEFAULT_CONTROL_PID_FILENAME = "interface-control.pid"
def resolve_control_socket_path(*, state_home: Path) -> Path:
    override = str(os.environ.get("AWARE_INTERFACE_CONTROL_SOCKET") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (state_home / _DEFAULT_CONTROL_SOCKET_FILENAME).resolve()


def resolve_control_pid_path(*, state_home: Path) -> Path:
    override = str(os.environ.get("AWARE_INTERFACE_CONTROL_PID_PATH") or "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (state_home / _DEFAULT_CONTROL_PID_FILENAME).resolve()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

@dataclass(frozen=True, slots=True)
class InterfaceServiceDaemonConfig:
    base_config: InterfaceHostServiceConfig
    socket_path: Path
    pid_path: Path

    @classmethod
    def from_env(
        cls,
        *,
        base_config: InterfaceHostServiceConfig | None = None,
    ) -> "InterfaceServiceDaemonConfig":
        resolved_base = base_config or InterfaceHostServiceConfig.from_env()
        return cls(
            base_config=resolved_base,
            socket_path=resolve_control_socket_path(state_home=resolved_base.state_home),
            pid_path=resolve_control_pid_path(state_home=resolved_base.state_home),
        )


@dataclass(slots=True)
class InterfaceServiceDaemon:
    config: InterfaceServiceDaemonConfig
    registry: InterfaceNamespaceRegistry
    server: InterfaceControlPlaneServer
    daemon_metadata: InterfaceDaemonMetadata
    _started: bool = field(init=False, default=False)
    _stop_event: asyncio.Event = field(init=False, default_factory=asyncio.Event)

    @classmethod
    def create(
        cls,
        *,
        config: InterfaceServiceDaemonConfig | None = None,
        bundle_factory: InterfaceHostServiceBundleFactory | None = None,
    ) -> "InterfaceServiceDaemon":
        resolved_config = config or InterfaceServiceDaemonConfig.from_env()
        daemon_metadata = InterfaceDaemonMetadata(
            daemon_instance_id=uuid4(),
            daemon_started_at=_utc_now(),
            daemon_source_fingerprint=compute_daemon_source_fingerprint(
                repository_root=resolved_config.base_config.repository_root,
            ),
            repository_root=resolved_config.base_config.repository_root,
            state_home=resolved_config.base_config.state_home,
            default_endpoint=resolved_config.base_config.endpoint,
        )
        registry = InterfaceNamespaceRegistry(
            bundle_factory=bundle_factory,
            base_config=resolved_config.base_config,
            state_home=resolved_config.base_config.state_home,
        )
        control_plane = InterfaceControlPlane(
            base_config=resolved_config.base_config,
            socket_path=resolved_config.socket_path,
            registry=registry,
            daemon_metadata=daemon_metadata,
        )
        server = InterfaceControlPlaneServer(
            socket_path=resolved_config.socket_path,
            control_plane=control_plane,
        )
        return cls(
            config=resolved_config,
            registry=registry,
            server=server,
            daemon_metadata=daemon_metadata,
        )

    async def start(self) -> Path:
        if self._started:
            return self.config.socket_path
        await self.server.start()
        self.config.pid_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
        self._started = True
        logger.info(
            "aware_interface_service daemon ready socket=%s repository_root=%s state_home=%s",
            self.config.socket_path,
            self.config.base_config.repository_root,
            self.config.base_config.state_home,
        )
        return self.config.socket_path

    async def run_until_stopped(self) -> None:
        await self.start()
        await self._stop_event.wait()

    def request_stop(self) -> None:
        self._stop_event.set()

    async def close(self) -> None:
        self.request_stop()
        await self.server.close()
        await self.registry.close()
        with suppress(FileNotFoundError):
            self.config.pid_path.unlink()
        self._started = False


async def _serve() -> int:
    daemon = InterfaceServiceDaemon.create()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _request_stop() -> None:
        stop_event.set()
        daemon.request_stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, _request_stop)

    await daemon.start()
    try:
        await stop_event.wait()
    finally:
        await daemon.close()
    return 0


def main() -> int:
    try:
        return asyncio.run(_serve())
    except KeyboardInterrupt:
        return 0


__all__ = [
    "InterfaceServiceDaemon",
    "InterfaceServiceDaemonConfig",
    "compute_daemon_source_fingerprint",
    "main",
    "resolve_control_pid_path",
    "resolve_control_socket_path",
]
