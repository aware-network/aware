from __future__ import annotations

from typing import Any

_LAZY_EXPORTS = {
    "AwareMetaServiceProtocolHandler": (
        "aware_meta_service.api_service_protocol",
        "AwareMetaServiceProtocolHandler",
    ),
    "LocalMetaAwarePackageManifestApiSession": (
        "aware_meta_service.local_api_client",
        "LocalMetaAwarePackageManifestApiSession",
    ),
    "LocalMetaAwarePackageManifestResolver": (
        "aware_meta_service.local_api_client",
        "LocalMetaAwarePackageManifestResolver",
    ),
    "LocalMetaServiceApiConfig": (
        "aware_meta_service.local_api_client",
        "LocalMetaServiceApiConfig",
    ),
    "LocalMetaServiceApiSession": (
        "aware_meta_service.local_api_client",
        "LocalMetaServiceApiSession",
    ),
    "LocalMetaServiceAwareApiClient": (
        "aware_meta_service.local_api_client",
        "LocalMetaServiceAwareApiClient",
    ),
    "build_local_meta_service_api_client": (
        "aware_meta_service.local_api_client",
        "build_local_meta_service_api_client",
    ),
    "build_local_meta_service_api_client_for_aware_package_manifests": (
        "aware_meta_service.local_api_client",
        "build_local_meta_service_api_client_for_aware_package_manifests",
    ),
    "build_local_meta_service_api_session": (
        "aware_meta_service.local_api_client",
        "build_local_meta_service_api_session",
    ),
    "build_local_meta_service_api_session_for_aware_package_manifests": (
        "aware_meta_service.local_api_client",
        "build_local_meta_service_api_session_for_aware_package_manifests",
    ),
    "build_local_meta_sdk_client": (
        "aware_meta_service.local_sdk",
        "build_local_meta_sdk_client",
    ),
    "build_local_meta_sdk_client_for_aware_package_manifests": (
        "aware_meta_service.local_sdk",
        "build_local_meta_sdk_client_for_aware_package_manifests",
    ),
    "build_local_meta_sdk_lane_store": (
        "aware_meta_service.local_sdk",
        "build_local_meta_sdk_lane_store",
    ),
    "build_local_meta_sdk_service_graph_gateway": (
        "aware_meta_service.local_sdk",
        "build_local_meta_sdk_service_graph_gateway",
    ),
    "MetaLocalStateConfig": (
        "aware_meta_service.local_state",
        "MetaLocalStateConfig",
    ),
    "MetaCommitEventBus": (
        "aware_meta_service.api_service_protocol",
        "MetaCommitEventBus",
    ),
    "MetaCommitEventStore": (
        "aware_meta_service.api_service_protocol",
        "MetaCommitEventStore",
    ),
    "MetaTemporalSessionStateStore": (
        "aware_meta_service.local_state",
        "MetaTemporalSessionStateStore",
    ),
    "build_aware_meta_service_protocol_handler": (
        "aware_meta_service.api_service_protocol",
        "build_aware_meta_service_protocol_handler",
    ),
    "ensure_meta_service_local_state_registry": (
        "aware_meta_service.local_state",
        "ensure_meta_service_local_state_registry",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module 'aware_meta_service' has no attribute {name!r}")
    module_name, attr_name = target
    from importlib import import_module

    return getattr(import_module(module_name), attr_name)


__all__ = [
    "AwareMetaServiceProtocolHandler",
    "LocalMetaAwarePackageManifestApiSession",
    "LocalMetaAwarePackageManifestResolver",
    "LocalMetaServiceApiConfig",
    "LocalMetaServiceApiSession",
    "LocalMetaServiceAwareApiClient",
    "MetaLocalStateConfig",
    "MetaCommitEventBus",
    "MetaCommitEventStore",
    "MetaTemporalSessionStateStore",
    "build_aware_meta_service_protocol_handler",
    "build_local_meta_service_api_client",
    "build_local_meta_service_api_client_for_aware_package_manifests",
    "build_local_meta_service_api_session",
    "build_local_meta_service_api_session_for_aware_package_manifests",
    "build_local_meta_sdk_client",
    "build_local_meta_sdk_client_for_aware_package_manifests",
    "build_local_meta_sdk_lane_store",
    "build_local_meta_sdk_service_graph_gateway",
    "ensure_meta_service_local_state_registry",
]
