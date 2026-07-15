from __future__ import annotations

from importlib import import_module
from typing import Any


_LAZY_EXPORTS = {
    "InterfaceHostUnavailableError": (
        "aware_interface_sdk.client",
        "InterfaceHostUnavailableError",
    ),
    "InterfaceSdkClient": ("aware_interface_sdk.client", "InterfaceSdkClient"),
    "InterfaceSdkError": ("aware_interface_sdk.client", "InterfaceSdkError"),
    "InterfaceExperienceSessionNarrationEvent": (
        "aware_interface_sdk.models",
        "InterfaceExperienceSessionNarrationEvent",
    ),
    "InterfaceExperienceSessionNarrationSnapshot": (
        "aware_interface_sdk.models",
        "InterfaceExperienceSessionNarrationSnapshot",
    ),
    "InterfaceSurfacePane": (
        "aware_interface_sdk.models",
        "InterfaceSurfacePane",
    ),
    "InterfaceSurfaceSnapshot": (
        "aware_interface_sdk.models",
        "InterfaceSurfaceSnapshot",
    ),
    "INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF": (
        "aware_interface_sdk.operation_catalog",
        "INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF",
    ),
    "INTERFACE_SDK_OPERATION_CATALOG_CONTRACT": (
        "aware_interface_sdk.operation_catalog",
        "INTERFACE_SDK_OPERATION_CATALOG_CONTRACT",
    ),
    "INTERFACE_SDK_PING_OPERATION_REF": (
        "aware_interface_sdk.operation_catalog",
        "INTERFACE_SDK_PING_OPERATION_REF",
    ),
    "InterfaceAttachment": ("aware_interface_sdk.attachment", "InterfaceAttachment"),
    "InterfaceAttachmentStore": (
        "aware_interface_sdk.attachment",
        "InterfaceAttachmentStore",
    ),
    "InterfaceAuthSession": ("aware_interface_sdk.auth_store", "InterfaceAuthSession"),
    "InterfaceTransportBindingState": (
        "aware_interface_sdk.transport",
        "InterfaceTransportBindingState",
    ),
    "InterfaceTransportProfile": (
        "aware_interface_sdk.transport",
        "InterfaceTransportProfile",
    ),
    "InterfaceTransportSession": (
        "aware_interface_sdk.transport",
        "InterfaceTransportSession",
    ),
    "InterfaceLocalHostContext": (
        "aware_interface_sdk.local_host",
        "InterfaceLocalHostContext",
    ),
    "create_interface_attachment": (
        "aware_interface_sdk.attachment",
        "create_interface_attachment",
    ),
    "ensure_local_interface_host": (
        "aware_interface_sdk.local_host",
        "ensure_local_interface_host",
    ),
    "load_interface_auth_session": (
        "aware_interface_sdk.auth_store",
        "load_interface_auth_session",
    ),
    "login_interface_token_attachment": (
        "aware_interface_sdk.auth_store",
        "login_interface_token_attachment",
    ),
    "save_interface_auth_session": (
        "aware_interface_sdk.auth_store",
        "save_interface_auth_session",
    ),
    "resolve_interface_local_host_context": (
        "aware_interface_sdk.local_host",
        "resolve_interface_local_host_context",
    ),
    "dispatch_interface_sdk_operation": (
        "aware_interface_sdk.operation_catalog",
        "dispatch_interface_sdk_operation",
    ),
    "get_sdk_operation_catalog": (
        "aware_interface_sdk.operation_catalog",
        "get_sdk_operation_catalog",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module 'aware_interface_sdk' has no attribute {name!r}")
    module_name, attr_name = target
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value


__all__ = list(_LAZY_EXPORTS)
