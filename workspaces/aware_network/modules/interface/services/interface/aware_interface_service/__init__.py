"""Standalone Interface host service bootstrap package.

The package barrel is intentionally lazy. Local ServiceHost entrypoints import
submodules such as ``aware_interface_service.local_host`` and must not pay for
the full control-plane/app/generated ontology stack before the process starts
serving.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aware_interface_service.app import (
        InterfaceHostServiceApp,
        InterfaceHostServiceBundleFactory,
        InterfaceHostServiceConfig,
        InterfaceHostServiceLiveBundle,
        build_bootstrap_snapshot,
        build_live_service_bundle,
    )
    from aware_interface_service.config import InterfaceHostDevAdapterSpec
    from aware_interface_service.control_plane import (
        InterfaceControlPlane,
        InterfaceControlPlaneServer,
    )
    from aware_interface_service.daemon import (
        InterfaceServiceDaemon,
        InterfaceServiceDaemonConfig,
        main,
        resolve_control_socket_path,
    )
    from aware_interface_service.dev_adapters import InterfaceHostDevAdapterSelection
    from aware_interface_service.models import (
        InterfaceHostedNamespaceState,
        InterfaceHostServiceAllowedAction,
        InterfaceHostServiceCurrentScreen,
        InterfaceHostServiceLaneSyncState,
        InterfaceHostServiceState,
        InterfaceHostServiceTransportState,
    )
    from aware_interface_service.namespace_registry import (
        HostedInterfaceNamespace,
        InterfaceNamespaceRegistry,
    )
    from aware_interface_service.runtime import InterfaceHostServiceRuntime


_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "HostedInterfaceNamespace": (
        "aware_interface_service.namespace_registry",
        "HostedInterfaceNamespace",
    ),
    "InterfaceControlPlane": (
        "aware_interface_service.control_plane",
        "InterfaceControlPlane",
    ),
    "InterfaceControlPlaneServer": (
        "aware_interface_service.control_plane",
        "InterfaceControlPlaneServer",
    ),
    "InterfaceHostDevAdapterSelection": (
        "aware_interface_service.dev_adapters",
        "InterfaceHostDevAdapterSelection",
    ),
    "InterfaceHostDevAdapterSpec": (
        "aware_interface_service.config",
        "InterfaceHostDevAdapterSpec",
    ),
    "InterfaceHostedNamespaceState": (
        "aware_interface_service.models",
        "InterfaceHostedNamespaceState",
    ),
    "InterfaceHostServiceAllowedAction": (
        "aware_interface_service.models",
        "InterfaceHostServiceAllowedAction",
    ),
    "InterfaceHostServiceApp": (
        "aware_interface_service.app",
        "InterfaceHostServiceApp",
    ),
    "InterfaceHostServiceBundleFactory": (
        "aware_interface_service.app",
        "InterfaceHostServiceBundleFactory",
    ),
    "InterfaceHostServiceConfig": (
        "aware_interface_service.config",
        "InterfaceHostServiceConfig",
    ),
    "InterfaceHostServiceCurrentScreen": (
        "aware_interface_service.models",
        "InterfaceHostServiceCurrentScreen",
    ),
    "InterfaceHostServiceLaneSyncState": (
        "aware_interface_service.models",
        "InterfaceHostServiceLaneSyncState",
    ),
    "InterfaceHostServiceLiveBundle": (
        "aware_interface_service.app",
        "InterfaceHostServiceLiveBundle",
    ),
    "InterfaceHostServiceRuntime": (
        "aware_interface_service.runtime",
        "InterfaceHostServiceRuntime",
    ),
    "InterfaceHostServiceState": (
        "aware_interface_service.models",
        "InterfaceHostServiceState",
    ),
    "InterfaceHostServiceTransportState": (
        "aware_interface_service.models",
        "InterfaceHostServiceTransportState",
    ),
    "InterfaceNamespaceRegistry": (
        "aware_interface_service.namespace_registry",
        "InterfaceNamespaceRegistry",
    ),
    "InterfaceServiceDaemon": (
        "aware_interface_service.daemon",
        "InterfaceServiceDaemon",
    ),
    "InterfaceServiceDaemonConfig": (
        "aware_interface_service.daemon",
        "InterfaceServiceDaemonConfig",
    ),
    "build_bootstrap_snapshot": (
        "aware_interface_service.config",
        "build_bootstrap_snapshot",
    ),
    "build_live_service_bundle": (
        "aware_interface_service.app",
        "build_live_service_bundle",
    ),
    "main": ("aware_interface_service.daemon", "main"),
    "resolve_control_socket_path": (
        "aware_interface_service.daemon",
        "resolve_control_socket_path",
    ),
}

__all__ = [
    "HostedInterfaceNamespace",
    "InterfaceControlPlane",
    "InterfaceControlPlaneServer",
    "InterfaceHostServiceApp",
    "InterfaceHostServiceBundleFactory",
    "InterfaceHostServiceConfig",
    "InterfaceHostedNamespaceState",
    "InterfaceHostServiceAllowedAction",
    "InterfaceHostServiceCurrentScreen",
    "InterfaceHostDevAdapterSelection",
    "InterfaceHostDevAdapterSpec",
    "InterfaceHostServiceLaneSyncState",
    "InterfaceHostServiceLiveBundle",
    "InterfaceHostServiceRuntime",
    "InterfaceHostServiceState",
    "InterfaceHostServiceTransportState",
    "InterfaceNamespaceRegistry",
    "InterfaceServiceDaemon",
    "InterfaceServiceDaemonConfig",
    "build_bootstrap_snapshot",
    "build_live_service_bundle",
    "main",
    "resolve_control_socket_path",
]


def __getattr__(name: str) -> Any:
    try:
        module_name, attr_name = _LAZY_EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
