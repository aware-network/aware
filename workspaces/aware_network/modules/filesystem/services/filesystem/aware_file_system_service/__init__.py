from __future__ import annotations

from typing import Any

__all__ = [
    "LocalFileSystemServiceApiConfig",
    "LocalFileSystemServiceApiSession",
    "LocalFileSystemServiceAwareApiClient",
    "build_aware_file_system_service_protocol_handler",
    "build_local_file_system_service_api_client",
    "build_local_file_system_service_api_session",
    "build_service_bindings",
    "dispatch_file_system_service_protocol_endpoint",
    "register_service_plugins",
]


def __getattr__(name: str) -> Any:
    if name == "build_aware_file_system_service_protocol_handler":
        from .api_service_protocol import build_aware_file_system_service_protocol_handler

        value = build_aware_file_system_service_protocol_handler
    elif name in {
        "LocalFileSystemServiceApiConfig",
        "LocalFileSystemServiceApiSession",
        "LocalFileSystemServiceAwareApiClient",
        "build_local_file_system_service_api_client",
        "build_local_file_system_service_api_session",
        "dispatch_file_system_service_protocol_endpoint",
    }:
        from . import local_api_client

        value = getattr(local_api_client, name)
    elif name == "build_service_bindings":
        from .service_bindings import build_service_bindings

        value = build_service_bindings
    elif name == "register_service_plugins":
        from .service_providers import register_plugins

        value = register_plugins
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value
