from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from aware_interface_service.api_service_protocol import (
    build_aware_interface_service_protocol_handler,
)
from aware_interface_service.config import InterfaceHostServiceConfig
from aware_interface_service.control_plane import (
    InterfaceControlPlane,
    InterfaceDaemonMetadata,
)
from aware_interface_service.daemon import resolve_control_socket_path
from aware_interface_service.fingerprint import compute_daemon_source_fingerprint
from aware_interface_service.namespace_registry import InterfaceNamespaceRegistry


def build_service_bindings(
    control_plane: object | None = None,
) -> dict[str, object]:
    resolved_control_plane: Any = (
        control_plane
        if control_plane is not None
        else _build_default_interface_control_plane()
    )
    return {
        "aware_interface": build_aware_interface_service_protocol_handler(
            control_plane=resolved_control_plane,
        )
    }


def _build_default_interface_control_plane() -> InterfaceControlPlane:
    config = InterfaceHostServiceConfig.from_env()
    socket_path = resolve_control_socket_path(state_home=config.state_home)
    daemon_metadata = InterfaceDaemonMetadata(
        daemon_instance_id=uuid4(),
        daemon_started_at=_utc_now(),
        daemon_source_fingerprint=compute_daemon_source_fingerprint(
            repository_root=config.repository_root,
        ),
        repository_root=config.repository_root,
        state_home=config.state_home,
        default_endpoint=config.endpoint,
    )
    registry = InterfaceNamespaceRegistry(
        base_config=config,
        state_home=config.state_home,
    )
    return InterfaceControlPlane(
        base_config=config,
        socket_path=socket_path,
        registry=registry,
        daemon_metadata=daemon_metadata,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


__all__ = ["build_service_bindings"]
