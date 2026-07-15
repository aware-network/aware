"""Interface SDK operation catalog provider for generic CLI renderers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aware_interface_sdk.client import InterfaceSdkClient, InterfaceSdkError


INTERFACE_SDK_OPERATION_CATALOG_CONTRACT = "aware.sdk_operation_catalog.v0"
INTERFACE_SDK_PING_OPERATION_REF = "interface_sdk.ping_interface_host"
INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF = "interface_sdk.list_interface_namespaces"

_EMPTY_OBJECT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
}

_LOCAL_SERVICE_HOST_CONTEXT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "socket_path": {"type": "string"},
        "state_home": {"type": "string"},
    },
    "additionalProperties": True,
}


def get_sdk_operation_catalog() -> dict[str, object]:
    """Return the explicit Interface SDK operation catalog for CLI renderers."""

    return {
        "catalog_contract": INTERFACE_SDK_OPERATION_CATALOG_CONTRACT,
        "sdk_name": "interface_sdk",
        "package_name": "aware-interface-sdk",
        "version_number": 1,
        "operations": [
            {
                "operation_ref": INTERFACE_SDK_PING_OPERATION_REF,
                "title": "Ping Interface Host",
                "description": (
                    "Read Interface Host readiness through the Interface service boundary."
                ),
                "endpoint_refs": ["interface.ping_interface_host.ping_interface_host"],
                "input_schema": _EMPTY_OBJECT_SCHEMA,
                "context_schema": _LOCAL_SERVICE_HOST_CONTEXT_SCHEMA,
                "effect": "read",
                "stability": "preview",
                "handler_ref": (
                    "aware_interface_sdk.operation_catalog:"
                    "dispatch_interface_sdk_operation"
                ),
                "requires_confirmation": False,
            },
            {
                "operation_ref": INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF,
                "title": "List Interface Namespaces",
                "description": (
                    "List admitted Interface namespaces through the Interface service boundary."
                ),
                "endpoint_refs": [
                    "interface.list_interface_namespaces.list_interface_namespaces",
                ],
                "input_schema": _EMPTY_OBJECT_SCHEMA,
                "context_schema": _LOCAL_SERVICE_HOST_CONTEXT_SCHEMA,
                "effect": "read",
                "stability": "preview",
                "handler_ref": (
                    "aware_interface_sdk.operation_catalog:"
                    "dispatch_interface_sdk_operation"
                ),
                "requires_confirmation": False,
            },
        ],
    }


async def dispatch_interface_sdk_operation(
    *,
    operation_ref: str,
    request_payload: Mapping[str, Any],
    context: Mapping[str, object],
    timeout_s: float | None = None,
) -> object:
    """Dispatch one catalog-declared Interface SDK operation."""

    _ = request_payload, timeout_s
    client = InterfaceSdkClient.from_local_service_host(
        socket_path=_optional_path(context.get("socket_path")),
        state_home=_optional_path(context.get("state_home")),
    )
    if operation_ref == INTERFACE_SDK_PING_OPERATION_REF:
        return await client.ping()
    if operation_ref == INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF:
        return await client.list_namespaces()
    raise InterfaceSdkError(f"Unsupported Interface SDK operation: {operation_ref}")


def _optional_path(raw: object) -> Path | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return Path(text).expanduser() if text else None


__all__ = [
    "INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF",
    "INTERFACE_SDK_OPERATION_CATALOG_CONTRACT",
    "INTERFACE_SDK_PING_OPERATION_REF",
    "dispatch_interface_sdk_operation",
    "get_sdk_operation_catalog",
]
